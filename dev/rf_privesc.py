from logging import ERROR
import os
import copy
import time
from dev.utils.icons import Icons
from enum import Enum
from dev.tools.connection.ping import ping_server
from dev.utils.files import  save_outputs
from dev.tools.connection import ssh
from dev.ai.ai_chat import ask_ai
from dev.utils.logger import LogType, log_msg
from dev.utils.privesc.capabilities import capabilities_privesc
from dev.utils.report import generate_html, generate_pe_table, html_end, html_start

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
            "cmd": "id",
            "action": "Display user ID and groups"
        },
        {
            "cmd": "getcap -r / 2>/dev/null",
            "action": "List all files with Linux capabilities",
        },
        # {
        #     "cmd": "find / -perm -u=s -type f 2>/dev/null",
        #     "action": "Find SUID binaries"
        # },
        # {
        #     "cmd": "uname -a", 
        #     "action": "Display kernel version and system details"
        # },
        # {
        #     "cmd": "cat /etc/os-release",
        #     "action": "Show operating system details"
        # },
        # {
        #     "cmd": "lsb_release -a",
        #     "action": "Check Linux distribution and version"
        # },
        # {
        #     "cmd": "systemctl list-units --type=service",
        #     "action": "Check systemd services and their status"
        # },
      
        # {
        #     "cmd": "cat /etc/passwd",
        #     "action": "List system users"
        # },
        # {
        #     "cmd": "cat /etc/group",
        #     "action": "List system groups"
        # },
        # {
        #     "cmd": "env",
        #     "action": "Display environment variables"
        # },
        # {
        #     "cmd": "sudo -l",
        #     "action": "Check sudo permissions"
        # },
        # {
        #     "cmd": "uptime",
        #     "action": "Display system uptime and load average"
        # },
        # {
        #     "cmd": "ps aux",
        #     "action": "List running processes"
        # },
        # {
        #     "cmd": "ip a",
        #     "action": "Show network interfaces and configuration"
        # },
        # {
        #     "cmd": "lsmod",
        #     "action": "List loaded kernel modules"
        # },
        # {
        #     "cmd": "arch",
        #     "action": "Show CPU architecture"
        # },
        # {
        #     "cmd": "netstat -tulnp",
        #     "action": "List active network connections"
        # },
        # {
        #     "cmd": "hostname",
        #     "action": "Display system hostname"
        # },
        # {
        #     "cmd": "cat /etc/crontab",
        #     "action": "List scheduled cron jobs"
        # },
        # {
        #     "cmd": "find / -writable -type f 2>/dev/null",
        #     "action": "Find writable files"
        # },
        # {
        #     "cmd": "find / -writable -type d 2>/dev/null",
        #     "action": "Find writable directories"
        # },
      
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
            log_msg("Trying to connect via {protocol} (attempt {i+1})...", LogType.INFO, True)
            conn = connections[protocol]()  
            if conn:   
                log_msg(f"Connected via {protocol} as {username}!", LogType.CONNECT)
                break
        except Exception as e:
            log_msg(f"{protocol.upper()} attempt {i+1} failed: {e}", LogType.ERROR)
            time.sleep(5)
                
    if conn is None:
        log_msg(f"[Privesc][connect] - Cannot connect to {protocol}. Trying to check if the server up (ping)", Icons.INFO)
        try:
            ping_return = ping_server(ip)  
            if ping_return:
                log_msg(f"Server pinged successfully!", LogType.SUCCESS)
            else:
                log_msg("Server doesnot up", LogType.ERROR)
            return 
        except Exception as e:
            log_msg("Cannot ping the server", LogType.ERROR)
            return 

    # Check potential targets for privesc
    log_msg("Checking Privesc...", LogType.COMMAND)
    for cmd in cmds:
        cmd_line = cmd['cmd']
        cmd_action = cmd['action']
        log_msg(f"Checking {cmd_line}...", LogType.COMMAND)
        
        try:
            stdin, stdout, stderr = conn.exec_command(cmd_line)
            result = stdout.read().decode().strip()
            error = stderr.read().decode().strip()
            data.append({
                'cmd': cmd_line,
                'action': cmd_action,
                'result': result or error
            })
        except Exception as e:
            log_msg(f"Privesc check error in running {cmd_line}.\n{e}", LogType.ERROR)

                            
    ai_response = None
    if data:
        output_saved = save_outputs(os.path.join(out_dir, "privesc"), data)
        
        if 'path' in output_saved:
            log_msg(f"Output successfully saved in {output_saved['path']}!", LogType.SUCCESS)
        else:
            log_msg("Output cannot be saved.", LogType.ERROR)
        
        ###########################################################
        # Attempt to privesc automatically
        log_msg("Attempting to escalate privileges...", LogType.PE, True)
        
        pe_result = []
        for entry in data:
            result = entry['result']
            if not result:
                continue
            for line in result.splitlines():
                # Try capabilities
                if 'cap_' in line:

                    check_result = capabilities_privesc(conn, line)
                    if isinstance(check_result, list):
                        pe_result.extend(check_result)
                    elif check_result is not None:
                        pe_result.append(check_result)

            for pr in pe_result:
                if pr['is_pe']:
                    log_msg(f"PE succeed via {pr['target']}!", LogType.SUCCESS)

        pe_table = ''
        if pe_result:
            pe_succeeds = [r for r in pe_result if r.get("is_pe", False)]
            pe_table = generate_pe_table(pe_succeeds)       


        if model:
            log_msg("Asking 🤖 AI for guidance...", LogType.ANALYZE, True)
            # Convert result text into true or false for taking ai guidance (otherwise text too long and doesnot work)
            data_ai = []
            for obj in data:
                new_obj = copy.deepcopy(obj)
                new_obj["result"] = bool(obj.get("result"))  
                data_ai.append(new_obj)

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

               Format your answer as an HTML snippet with the following structure:
                <div class=card>
                    <h3>🤖  AI Analysis</h3>
                    <h3>Findings</h3>
                    <!-- List the key findings here -->

                    <h3>Possible PrivEsc Paths</h3>
                    <!-- List possible privilege escalation paths here -->

                    <h3>Recommended Next Steps</h3>
                    <!-- Steps should be grouped by priority -->
                    <!-- Use the following colors for priority headings -->
                    <ul>
                    <li><strong>{Icons.HIGH} High Priority:</strong></li>
                        <!-- List all high priority steps here -->
                    <li><strong>{Icons.MEDIUM} Medium Priority:</strong></li>
                        <!-- List all medium priority steps here -->
                    <li><strong>{Icons.LOW} Low Priority:</strong></li>
                        <!-- List all low priority steps here -->
                    </ul>
                </div>

                Requirements:
            - Use clear, short titles for each step.
            - Note: You can always **reclassify certain capabilities as Medium or High** if the binary is exploitable (for example, python3.8 with cap_setuid), 
                because some capabilities are critical and could allow full root access.
            """
        
            ai_response = ask_ai(model, prompt)
    else:
        log_msg("No data fetched, sorry", LogType.WARNING)
        return

    # report_text = html_start() + ai_response if ai_response else '<div></div>' + generate_html(data) + html_end()
    ai_text = ai_response if ai_response else ''
    
    data_text = generate_html(data)
    report_text = html_start('Privesc Report') + pe_table + ai_text.replace("```html", "").replace("```", "").strip() + data_text + html_end()


    report_saved = save_outputs(os.path.join(out_dir, 'privesc_report'), report_text, 'html')

    if 'path' in report_saved:
        log_msg(f"Report successfully saved in {report_saved['path']}!", LogType.SUCCESS)
    else:
        log_msg("Report cannot be saved." , LogType.ERROR)



    return data, ai_response

 