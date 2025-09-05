import os
import subprocess

def run_gobuster(target, port, wordlist_file="common.txt"):
    """
    Run Gobuster using Docker image.
    """

    try:
        wordlist_dir = os.path.abspath("wordlists")  
        wordlist_file = "common.txt"

        # Construct the docker command
        cmd = [
            "gobuster",
            "dir", "-u", f"{target}:{port}",
            "-w", f"{wordlist_dir}/{wordlist_file}"
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)

        return result.stdout
    except Exception as e:

        return f"Error running Gobuster: {e}"
