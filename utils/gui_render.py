from bs4 import BeautifulSoup

def sanitize_html(raw_html: str) -> str:
    """
    Fixes malformed HTML from the AI output (e.g. <h2 Summary</h >).
    Ensures all tags are properly closed so Streamlit/HTML renderers don't break.
    """
    # Parse with html5lib (for maximum error recovery)
    soup = BeautifulSoup(raw_html, "html5lib")
    
    # Extract only inside <body> (to avoid auto-added <html>/<head>)
    cleaned_html = soup.body.decode_contents()
    
    return cleaned_html.strip()