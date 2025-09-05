import os
from enum import Enum
from dev.utils.files import  create_privesc_report, save_outputs
from dev.tools.protocols.ssh import ssh_connect
from dev.ai.ai_chat import ask_ai
from dev.utils.logger import LogType, log_msg
from dev.utils.report import generate_html, html_end, html_start

class Protocol(Enum):
    SSH = "ssh"
    HTTP = "http"
    HTTPS = "https"
    FTP = "ftp"
    SMTP = "smtp"


def run_red_fox_privesc(target: dict, protocol: str, out_dir: str, model=None):
    """
    Run basic privilege escalation enumeration commands on a remote target.
    
    Args:
        target (dict): { "username": str, "ip": str, "password": str }
        protocol (str): Protocol type, e.g. "ssh"
        out_dir (str): Where to save outputs
    """
    cmds = [
        {
            "cmd": "whoami", 
            "action": "Fetch the current logged-in user"
        },
        {
            "cmd": "who",
            "action": "Show logged-in users"
        },
        {
            "cmd": "uname -a", 
            "action": "Display kernel version and system details"
        },
        {
            "cmd": "cat /etc/os-release",
            "action": "Show operating system details"
        },
        {
            "cmd": "lsb_release -a",
            "action": "Check Linux distribution and version"
        },
        {
            "cmd": "systemctl list-units --type=service",
            "action": "Check systemd services and their status"
        },
      
        {
            "cmd": "id",
            "action": "Display user ID and groups"
        },
        {
            "cmd": "cat /etc/passwd",
            "action": "List system users"
        },
        {
            "cmd": "cat /etc/group",
            "action": "List system groups"
        },
        {
            "cmd": "env",
            "action": "Display environment variables"
        },
        {
            "cmd": "sudo -l",
            "action": "Check sudo permissions"
        },
        {
            "cmd": "find / -perm -u=s -type f 2>/dev/null",
            "action": "Find SUID binaries"
        },
        {
            "cmd": "uptime",
            "action": "Display system uptime and load average"
        },
        {
            "cmd": "ps aux",
            "action": "List running processes"
        },
        {
            "cmd": "ip a",
            "action": "Show network interfaces and configuration"
        },
        {
            "cmd": "lsmod",
            "action": "List loaded kernel modules"
        },
        {
            "cmd": "arch",
            "action": "Show CPU architecture"
        },
        {
            "cmd": "netstat -tulnp",
            "action": "List active network connections"
        },
        {
            "cmd": "hostname",
            "action": "Display system hostname"
        },
        {
            "cmd": "cat /etc/crontab",
            "action": "List scheduled cron jobs"
        },
        {
            "cmd": "find / -writable -type f 2>/dev/null",
            "action": "Find writable files"
        },
        {
            "cmd": "find / -writable -type d 2>/dev/null",
            "action": "Find writable directories"
        },
      
   ]

    data = []

    os.makedirs(out_dir, exist_ok=True)

    if protocol == Protocol.SSH.value:
        username, ip, password = target["username"], target["ip"], target["password"]
        
        if not username or not ip or not password:
            log_msg("No username, ip or password provided", LogType.ERROR)
            return

        log_msg(f"Trying to connect to SSH...", LogType.INFO)

        ssh = ssh_connect(username, ip, password)
        
    
        if ssh:
            log_msg(f"Connected via SSH !", LogType.INFO)
            log_msg(f"> Checking Privesc...", LogType.INFO)
            for cmd in cmds:
                cmd_line = cmd['cmd']
                cmd_action = cmd['action']
                log_msg(f"> Checking {cmd_line}...", LogType.INFO, False)
                try:
                    stdin, stdout, stderr = ssh.exec_command(cmd_line)
                    result = stdout.read().decode().strip()
                    error = stderr.read().decode().strip()
                    data.append(
                        {'cmd': cmd_line, 'action': cmd_action, 'result': result if result else error}
                    )  
                except Exception as e:
                    data.append({'cmd': cmd_line, 'action': cmd_action, 'result': f"Error: {e}" })
        else:
            log_msg("SSH connection failed", LogType.ERROR)
            exit(0)
        
        ai_response = None
        if data:
            output_saved = save_outputs(os.path.join(out_dir, "privesc"), data)
            
            if 'path' in output_saved:
                log_msg(f"Output successfully saved in {output_saved['path']}", LogType.INFO)
            else:
                log_msg("Output cannot be saved" , LogType.ERROR)


            if model:
                log_msg("🧐 Asking RedFox for guidance...", LogType.INFO)

                prompt = f"""
                    You are a professional penetration tester analyzing privilege escalation results.
                    Here are the command outputs I collected:
                    {data}
                    Your tasks:
                    1. Summarize the key findings from these results.
                    2. Identify potential privilege escalation vectors (kernel exploits, sudo misconfigurations, SUID binaries, capabilities, weak file permissions, PATH hijacking, etc.).
                    3. Suggest the next 2–3 prioritized steps I should take to escalate privileges, with reasoning.
                    4. If no obvious vector is found, recommend additional commands/tools I should run to gather more evidence.
                    5. Keep the response structured, clear, and practical for real penetration testing.

                    Format your answer as:
                    - **Findings**
                    - **Possible PrivEsc Paths**
                    - **Recommended Next Steps**
                
                    """
            
                ai_response = ask_ai(model, prompt)
        else:
            log_msg("No data fetched, sorry", LogType.INFO)
            return

        # report_text = html_start() + ai_response if ai_response else '<div></div>' + generate_html(data) + html_end()
        ai_text = ('<h2>🦊 RedFox Analysis</h2>' + ai_response + '<hr>') if ai_response else ''
        data_text = generate_html(data)
        report_text = html_start('Privesc Report') + ai_text + data_text + html_end()

       
        report_saved = save_outputs(os.path.join(out_dir, 'privesc_report'), report_text, 'html')

        if 'path' in report_saved:
            log_msg(f"Report successfully saved in {report_saved['path']}", LogType.INFO)
        else:
            log_msg("Report cannot be saved" , LogType.ERROR)

    return data, ai_response

 