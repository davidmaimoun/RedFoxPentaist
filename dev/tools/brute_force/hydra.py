import subprocess

def run_hydra(target, port, users, passwords, is_docker=True):
    """
    Run Hydra using Docker image.
    """
    try:
        if is_docker:
            cmd = [
                "docker", "run", "--rm",
                "pentesttools/hydra",
                "-L", users, "-P", passwords,
                f"{target}", f"ftp -s {port}"
            ]
        else:
            cmd = ["hydra", "-L", users, "-P", passwords, f"{target}", f"ftp -s {port}"]
            
        result = subprocess.run(cmd, capture_output=True, text=True)
        return result.stdout
    except Exception as e:
        return f"Error running Hydra: {e}"
    

    # "docker run --rm pentesttools/hydra -L", users -P passwords 10.10.10, ftp -s 21
