import subprocess
import os

def run_nmap(target: str, user_id='1') -> str:
    """
    Run Nmap using Docker and save output to users/<user_id>/nmap.txt
    """
    user_dir = f"users/{user_id}"
    os.makedirs(user_dir, exist_ok=True)
    output_file = os.path.join(user_dir, "nmap.txt")

    cmd = [
        "docker", "run", "--rm",
        "instrumentisto/nmap", "-sV", "-Pn", "-A", target
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        with open(output_file, "w") as f:
            f.write(result.stdout)
        return result.stdout
    except subprocess.CalledProcessError as e:
        with open(output_file, "w") as f:
            f.write(e.output or "")
        raise RuntimeError(f"Nmap failed: {e}")
