import os
import subprocess

def run_gobuster(target, is_docker=True, port='80', wordlist_file="common.txt"):
    """
    Run Gobuster using Docker image.
    """

    try:
        wordlist_dir = os.path.abspath("wordlists")  

        if is_docker:
            cmd = [
                "docker", "run", "--rm", "--network=host",
                "-v", f"{wordlist_dir}:/wordlists",   
                "aoighost/gobuster:latest",
                "dir", "-u", f"http://{target}:{port}",
                "-w", f"/wordlists/{wordlist_file}"  
            ]
        else:
            cmd = [
                "gobuster", "dir", "-u", f"{target}:{port}", "-w", f"{wordlist_dir}/{wordlist_file}"
            ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        return result.stdout
    except Exception as e:

        return f"Error running Gobuster: {e}"
