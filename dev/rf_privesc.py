import os
import copy
import time
from enum import Enum
from dev.tools.connection.ping import ping_server
from dev.utils.files import  create_privesc_report, save_outputs
from dev.tools.connection import ssh
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

    username, ip, password = target["username"], target["ip"], target["password"]

    if not username or not ip or not password:
        log_msg("No username, ip or password provided", LogType.ERROR)
        return

    connections = {
        "ssh": lambda: ssh.ssh_connect(username, ip, password),
        # "ftp": lambda: ftp_connect(...),
        # "http": lambda: http_connect(...)
    }

    conn = None
    for i in range(3):
        try:
            log_msg(f"Trying to connect via {protocol} (attempt {i+1})...", LogType.INFO)
            conn = connections[protocol]()  
            if conn:   
                log_msg(f"🔌 Connected via {protocol}!", LogType.INFO)
                break
        except Exception as e:
            log_msg(f"{protocol.upper()} attempt {i+1} failed: {e}", LogType.ERROR)
            time.sleep(5)
                
    if conn is None:
        log_msg(f"[Privesc][connect] - Cannot connect to {protocol}. Trying to check if the server up (ping)", LogType.INFO)
        try:
            ping_return = ping_server(ip)  
            if ping_return:
                log_msg(f"Server pinged successfully", LogType.INFO)
            else:
                log_msg(f"Server doesnot up", LogType.INFO)
            return 
        except Exception as e:
            log_msg(f"Cannot ping the server", LogType.ERROR)
            return 

    log_msg(f"> Checking Privesc...", LogType.INFO)
    for cmd in cmds:
        cmd_line = cmd['cmd']
        cmd_action = cmd['action']
        log_msg(f"> Checking {cmd_line}...", LogType.INFO, False)
        try:
            stdin, stdout, stderr = conn.exec_command(cmd_line)
            result = stdout.read().decode().strip()
            error = stderr.read().decode().strip()
            data.append(
                {'cmd': cmd_line, 'action': cmd_action, 'result': result if result else error}
            )  
        except Exception as e:
            log_msg(f"[Privesc] Error in running {cmd_line}\n{e}", LogType.ERROR)

                            
    ai_response = None
    if data:
        output_saved = save_outputs(os.path.join(out_dir, "privesc"), data)
        
        if 'path' in output_saved:
            log_msg(f"Output successfully saved in {output_saved['path']}", LogType.INFO)
        else:
            log_msg("Output cannot be saved" , LogType.ERROR)

        # Convert result text into true or false for taking ai guidance (otherwise text too long and doesnot work)
        data_ai = []
        for obj in data:
            new_obj = copy.deepcopy(obj)
            new_obj["result"] = bool(obj.get("result"))  
            data_ai.append(new_obj)

        if model:
            log_msg("\n------------\n🧐 Asking RedFox for guidance...\n", LogType.INFO)

            prompt = f"""
                You are a professional penetration tester analyzing privilege escalation results.
                Here are the command outputs I collected:
                {data_ai}
                Your tasks:
                1. Summarize the key findings from these results. If the 'result' field in True, explain what to do.
                2. Identify potential privilege escalation vectors (kernel exploits, sudo misconfigurations, SUID binaries, capabilities, weak file permissions, PATH hijacking, etc.).
                3. Suggest the next 2–3 prioritized steps I should take to escalate privileges, with reasoning.
                4. If no obvious vector is found, recommend additional commands/tools I should run to gather more evidence.
                5. Keep the response structured, clear, and practical for real penetration testing.

                Format your answer as:
                - <h3>Findings</h3>
                - <h3>Possible PrivEsc Paths</h3>
                - <h3>Recommended Next Steps</h3>
            
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

 