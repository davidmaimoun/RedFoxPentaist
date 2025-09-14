import re
import json
import subprocess
import requests
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urlunparse
import jsbeautifier
from jsbeautifier.unpackers import packer

patterns = [
    r"eval\(function\s*\(",
    r"_0x[0-9a-fA-F]+",
    r"atob\s*\(",
    r"fromCharCode\s*\(",
]

def crawl_site(start_url, max_depth=2):
    visited = set()
    to_visit = [(start_url, 0)]

    while to_visit:
        url, depth = to_visit.pop(0)
        if url in visited or depth > max_depth:
            continue
        visited.add(url.replace('#', '/'))
        try:
            r = requests.get(url, timeout=5)
            soup = BeautifulSoup(r.text, "html.parser")
            # extraire toutes les <a href>
            for a in soup.find_all("a", href=True):
                link = urljoin(url, a['href'])
                if link.startswith(start_url) and link not in visited:
                    to_visit.append((link, depth+1))
        except Exception as e:
            continue
    return list(visited)

def fetch_js(js_url):
    """Fetch JS code from URL or local file"""
    if js_url.startswith("http"):
        r = requests.get(js_url, timeout=10)
        r.raise_for_status()
        return r.text
    else:
        with open(js_url, "r", encoding="utf-8") as f:
            return f.read()

def unpack_js(js_code):
    """Try to unpack packed JS"""
    if packer.detect(js_code):
        unpacked = packer.unpack(js_code)
        return unpacked
    else:
        return js_code

def extract_ajax_blocks(js_code):
    blocks = []
    pos = 0
    while True:
        idx = js_code.find("$.ajax(", pos)
        if idx == -1:
            break
        # find opening brace
        start = js_code.find("{", idx)
        if start == -1:
            pos = idx + 1
            continue
        stack = 1
        i = start + 1
        while i < len(js_code) and stack > 0:
            if js_code[i] == "{":
                stack += 1
            elif js_code[i] == "}":
                stack -= 1
            i += 1
        block = js_code[start:i]
        blocks.append(block)
        pos = i
    return blocks

def find_ajax_calls(js_code, base_url=None):
    calls = []
    blocks = extract_ajax_blocks(js_code)
    for ajax_block in blocks:
        # Extract type (default GET)
        type_match = re.search(r'type\s*:\s*[\'"](\w+)[\'"]', ajax_block)
        ajax_type = type_match.group(1).upper() if type_match else "GET"

        # Extract URL
        url_match = re.search(r'url\s*:\s*[\'"]([^\'"]+)[\'"]', ajax_block)
        if not url_match:
            continue
        ajax_url = url_match.group(1)

        # Make absolute URL if needed
        if base_url and ajax_url.startswith('/'):
            ajax_url = base_url.rstrip('/') + ajax_url

        calls.append({"type": ajax_type, "url": ajax_url})
    return calls

def beautify_js(js_code):
    """Beautify JS code for readability"""
    opts = jsbeautifier.default_options()
    opts.indent_size = 2
    return jsbeautifier.beautify(js_code, opts)

def fetch_all_js_from_pages(pages):
    """Given a list of page URLs, fetch all JS files referenced in <script src> tags under /js/"""
    js_files = {}
    for page in pages:
        try:
            r = requests.get(page, timeout=10)
            r.raise_for_status()
            soup = BeautifulSoup(r.text, "html.parser")

            # look for all <script src=...> tags
            for script in soup.find_all("script", src=True):
                src = script["src"]
                if src.startswith("/js/"):
                    js_url = urljoin(page, src)
                    if js_url not in js_files:
                        try:
                            js_code = requests.get(js_url, timeout=10).text
                            js_files[js_url] = js_code
                        except requests.RequestException as e:
                            continue
                            # print(f"[!] Failed {js_url}: {e}")
        except requests.RequestException as e:
            continue
            # print(f"[!] Failed page {page}: {e}")

    return js_files

def ip_to_host_from_etc_hosts(ip):
    """Check /etc/hosts and return the hostname for a given IP."""
    try:
        with open("/etc/hosts", "r") as f:
            for line in f:
                # skip comments and empty lines
                line = line.split("#")[0].strip()
                if not line:
                    continue
                parts = line.split()
                if len(parts) >= 2 and parts[0] == ip:
                    # return the first hostname mapped to this IP
                    return parts[1]
    except FileNotFoundError:
        pass
    return None

def replace_ip_with_host(url):
    """If URL hostname is an IP, try to replace it with the host from /etc/hosts"""
    parsed = urlparse(url)
    hostname = parsed.hostname

    # regex to detect IPv4
    if re.match(r"^\d{1,3}(\.\d{1,3}){3}$", hostname):
        host_from_etc = ip_to_host_from_etc_hosts(hostname)
        if host_from_etc:
            parsed = parsed._replace(netloc=host_from_etc + (f":{parsed.port}" if parsed.port else ""))
            return urlunparse(parsed)
    return url

def check_api_return(type, url):
    try:
        result = subprocess.run(
            ["curl", "-s", "-L", "-X", type.upper(), url],
            capture_output=True,
            text=True,
            check=True
        )
        try:
            return json.loads(result.stdout)
        except json.JSONDecodeError:
            return "Cannot fetch data. Please retry later"
    except json.JSONDecodeError:
        return result.stdout
    except subprocess.CalledProcessError as e:
        return "Cannot fetch data. Please retry later"

        
def analyze_web_pages(url):
    pages = crawl_site(url)
    findings = {}
    findings_api_return = {}

    if not pages:
        return findings, findings_api_return

    js_pages = fetch_all_js_from_pages(pages)

    if not js_pages:
        return findings, findings_api_return

    for js_page in js_pages:
        js_code = fetch_js(js_page)
        unpacked = unpack_js(js_code)
        findings[js_page] = beautify_js(unpacked)

    # fetch path to api 
    for k, v in findings.items():
        ajax_results = find_ajax_calls(v, base_url=url)

        if ajax_results:
            for ar in ajax_results:
                host = ar['url'].replace(url, replace_ip_with_host(url)) 
                findings_api_return[host] = check_api_return(ar['type'], host)

    return findings, findings_api_return