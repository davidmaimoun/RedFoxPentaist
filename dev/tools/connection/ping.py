import subprocess

def ping_server(ip: str, retries: int = 1, timeout: int = 2) -> bool:
    """
    Ping the given IP to check if server is reachable.
    Returns True if ping succeeds, False otherwise.
    """
    # -c = count, -W = timeout (Linux/Mac) | use -w for Windows
    result = subprocess.run(
        ["ping", "-c", str(retries), "-W", str(timeout), ip],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    return result.returncode == 0
    