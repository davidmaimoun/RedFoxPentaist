import json
from unittest import result
from dev.utils.report import generate_html 

def _stringify_content(content) -> str:
    if isinstance(content, str):
        return content

    if isinstance(content, (bytes, bytearray)):
        try:
            return bytes(content).decode("utf-8", errors="replace")
        except Exception:
            return str(content)

    if isinstance(content, list) and all(isinstance(item, str) for item in content):
        return "\n".join(content)

    try:
        return json.dumps(content, indent=2, ensure_ascii=False)
    except Exception:
        return str(content)


def save_outputs(file_path: str, content, type='txt') -> dict:
    """
    Save content to a file and return a dict with path or error.
    """
    text = _stringify_content(content)  # must return string
    result = {}

    try:
        with open(f"{file_path}.{type}", "w", encoding="utf-8") as f:
            f.write(text)
        result['path'] = str(file_path)
    except Exception as e:
        result['error'] = "[Save Outputs Error] > " + str(e)
    return result


def create_privesc_report(file_path: str, content, type='html') -> str:
    text = generate_html(content)
    result = {}
    try:
        with open(f"{file_path}.{type}", "w", encoding="utf-8") as f:
            f.write(text)
        result['path'] = str(file_path)
    except Exception as e:
        result['error'] = "[Create Report Error] > " + str(e)
    return result
    


