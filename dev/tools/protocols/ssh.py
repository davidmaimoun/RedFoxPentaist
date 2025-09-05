import paramiko

def ssh_connect(user, ip, password, port=22):
    """
    Connects to a remote server via SSH.
    
    Args:
        user (str): SSH username
        ip (str): Server IP or hostname
        password (str): SSH password
        port (int, optional): SSH port (default=22)

    Returns:
        ssh (paramiko.SSHClient): Connected SSH client
    """
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())  # accept unknown keys
        ssh.connect(ip, port=port, username=user, password=password, timeout=10)
        print(f"[+] Connected to {ip} as {user}")
        return ssh
    except Exception as e:
        print(f"[-] SSH connection failed: {e}")
        return None

