import os
import subprocess
from typing import List

def run_nikto(target: str, is_docker: bool = True, port: int = 80, use_ssl: bool = False, timeout: int = 300):
    """
    Run Nikto against a target, using Docker image if is_docker True.
    Returns stdout (string) or an error string on exception.
    
    - target: hostname or ip (e.g. "10.10.10.245" or "example.com")
    - is_docker: if True, runs sullo/nikto docker image
    - port: HTTP port (int)
    - use_ssl: if True, use https:// schema
    - timeout: subprocess timeout in seconds
    """
    try:
        schema = "https" if use_ssl else "http"
        host_arg = f"{schema}://{target}:{port}"

        if is_docker:
            cmd = [
                "docker", "run", "--rm", "--network=host",
                "frapsoft/nikto:latest",
                "nikto", "-h", host_arg, "-nointeractive"
            ]
        else:
            cmd = ["nikto", "-h", host_arg, "-nointeractive"]

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)

        output = result.stdout.strip()
        if result.stderr:
            output = (output + "\n\nSTDERR:\n" + result.stderr.strip()).strip()
        return output

    except subprocess.TimeoutExpired:
        return f"Error running Nikto: process timed out after {timeout} seconds"
    except FileNotFoundError as e:
        return f"Error running Nikto: command not found ({e})"
    except Exception as e:
        return f"Error running Nikto: {e}"


def fetch_nikto_output(output_text: str) -> List[str]:
    """
    Parse Nikto output and return a list of findings.
    Nikto tends to prefix findings with '+' so we capture those lines.
    Returns an empty list if nothing found or if output looks like no-results.
    """
    if not output_text:
        return []

    lines = output_text.splitlines()
    findings = []

    for line in lines:
        line = line.strip()
        # common nikto finding lines start with '+' or sometimes 'OSVDB-' or 'Server:' etc.
        # Keep useful lines but avoid headers like 'Nikto v2.1.6' or progress lines.
        if line.startswith("+"):
            # remove the leading '+' and trim
            findings.append(line.lstrip("+").strip())
        else:
            # capture some other useful patterns
            if "OSVDB-" in line or "CVE-" in line or line.lower().startswith("server:") or line.lower().startswith("root/"):
                findings.append(line)

    # Deduplicate and filter empties
    dedup = []
    for f in findings:
        if f and f not in dedup:
            dedup.append(f)

    return dedup