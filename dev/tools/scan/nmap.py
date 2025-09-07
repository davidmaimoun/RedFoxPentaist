import subprocess

def run_nmap(target: str, is_docker=True) -> str:
    """
    Run Nmap using Docker and save output to users/<user_id>/nmap.txt
    """
    
    if is_docker:
        cmd = ["docker", "run", "--rm", "instrumentisto/nmap", "nmap", "-sV", "-Pn", "-A", target]
    else:
        cmd = ["nmap", "-sV", "-Pn", "-A", target]

    result = subprocess.run(cmd, capture_output=True, text=True, check=True)

    return result.stdout
    