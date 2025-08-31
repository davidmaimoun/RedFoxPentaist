from enum import Enum
import os
import sys
import ollama
from pathlib import Path
from run.ports import scan_port_21, scan_port_80
from tools.brute_force.gobuster import run_gobuster
from tools.brute_force.hydra import run_hydra
from tools.protocols.ssh import ssh_connect
from tools.scan.nmap import run_nmap
from ai.ollama_chat import ask_ai
from utils.gui_render import sanitize_html
from utils.logger import LogType, log_msg

class Protocol(Enum):
    SSH = "ssh"
    HTTP = "http"
    HTTPS = "https"
    FTP = "ftp"
    SMTP = "smtp"


def check_model(model_name: str):
    """Check if Ollama model is available; suggest pull if missing."""
    try:
        available_models = ollama.list()  # returns list of Model objects
        # extract the model names without tags (e.g., 'gemma3' from 'gemma3:latest')
        model_names = [m.model.split(":")[0].lower() for m in available_models]

        if model_name.lower() not in model_names:
            print(f"[!] Model '{model_name}' is not pulled.")
            print(f"Run this command to pull it: ollama pull {model_name}")
            return False

        print(f"[+] Model '{model_name}' is already available.")
        return True

    except Exception as e:
        print(f"[!] Error checking Ollama models: {e}")
        return False
    
def save_output(out_dir, filename: str, content: str, gui=None):
    file_path = os.path.join(out_dir, filename)
    with open(file_path, "w") as f:
        f.write(content)
    log_msg(f"👌 {filename.split('.')[0].capitalize()} result saved to {file_path}", LogType.SUCCESS, gui)
    return str(file_path)

def run_red_fox_pentaist(target: str, out_dir, model='gemma3', gui=False):
    output_results_output = os.path.join("results", out_dir)

    os.makedirs(output_results_output, exist_ok=True)
    
    # Check if Docker is running
    try:
        import subprocess
        subprocess.run(["docker", "ps"], check=True, stdout=subprocess.DEVNULL)
    except Exception as e:
        log_msg("Docker is not running or installed. Exiting.", LogType.ERROR, gui)
        sys.exit(1)

    # Check AI model avaibility
    # is_model_available = check_model(model)

    # if not is_model_available:
    #     log_error("[Exiting] : Model choosen not found")
    #     exit(1)


    if os.path.isfile(target):
        with open(target, "r") as f:
            nmap_output = f.read()
        log_msg(f"Using existing Nmap file: {target}", LogType.INFO, gui=gui)
    else:
        log_msg(f"> Running Nmap", LogType.INFO, gui=gui)
        nmap_output = run_nmap(target)
        save_output(output_results_output, "nmap.txt", nmap_output, gui)

    
    scan_ports_outputs = {}

    port_scanners = {
        "21/tcp": ("FTP", {
            "hydra": lambda target: run_hydra(target, port, 'wordlists/users/names.txt', 'wordlists/passwords/rockyou.txt'),
        }),
        "80/tcp": ("HTTP 80", {
            "gobuster": lambda target: run_gobuster(target, port='80'),
            # "nikto": lambda target: run_nikto(target),
        }),
    }

    for port, (service_name, tools) in port_scanners.items():
        if port in nmap_output or service_name.split()[0] in nmap_output:  
            log_msg(f"Port {port} open - {service_name} detected!\n", LogType.INFO, gui=gui)

            for tool_name, tool_func in tools.items():
                try:
                    log_msg(f"> Running {tool_name}", LogType.INFO, gui=gui)

                    output = tool_func(target)

                    if output:
                        save_output(output_results_output, f"{tool_name}.txt", output, gui)
                        scan_ports_outputs[port] = { 'tool': tool_name, 'output': output }
                    else:
                        log_msg(f"⚠️ {tool_name} did not return any result", LogType.IMPORTANT, gui=gui)

                except Exception as e:
                    log_msg(f"💢 Error running {tool_name}: {e}", LogType.ERROR, gui=gui)
        
    # Ask AI for guidance
    if model == None:
        log_msg("No models AI wanted", LogType.INFO, gui)

    log_msg("\n🧐 Asking RedFox for guidance...", LogType.INFO, gui=gui)
    
    prompt = (
    f"You are acting as an experienced penetration tester assisting in a live assessment.\n"
    f"The target is: {target}\n\n"
    f"--- Nmap Results ---\n{nmap_output}\n\n"
    "Please analyze the results and propose the best next steps in the pentest. "
    "Focus on methodology, tools, and reasoning like a real pentester.\n"
)

    if scan_ports_outputs:
        prompt += "\n--- Additional Tool Results ---\n"
        for port, data in scan_ports_outputs.items():
            tool = data["tool"]
            output = data["output"]
            
            prompt += (
                f"\n### Port: {port} - Tool: {tool}\n"
                f"Output:\n{output}\n\n"
                f"👉 Analyze what this output means, identify vulnerabilities or opportunities, "
                f"and recommend what to do next specifically based on {tool}.\n"
            )

    # Add formatting requirement (so Streamlit can render nicely)
    if gui:
        prompt += """
            Respond ONLY with a valid HTML fragment. 
            Use <h2> for headings, <p> for explanations, <ul>/<li> for lists, and <code> for commands. 
            Do NOT include ``` fences, <html>, <head>, or <body>.
            No text outside HTML tags.
            Please structure your response as follows:
            <h2>Summary</h2>
            <p>2–3 sentences summarizing findings.</p>
            For EACH tool:
            <h2><Tool name> Findings</h2>
            <ul>
            <li><b>Finding Title:</b> evidence & implication</li>
            </ul>

            <h2>Prioritized Action Plan</h2>
            <ol>
            <li><b>Step:</b> short title – <i>rationale</i><br>
            Expected outcome, suggested tools (<code>tool</code>), risk/priority rating.</li>
            </ol>

            <h2>Next Steps</h2>
            <p>One-paragraph guidance.</p>
        """
            

        if scan_ports_outputs:
            prompt += "\n--- Summary Tab ---\n"
            prompt += """
                <h2>Summary Tab</h2>
                Add here a nice table <table> to sum up the analysis, with columns:\n
                1. 'Port' for the port scanned, 
                2. 'Tool' for the tool that ran successfully, 
                3. "Action" with a very clear and short explanation of what the tool ouput gave us. .i.e :
                <table>
                    <thead>
                        <tr>
                            <th>Port</th>
                            <th>Tool</th>
                            <th>Action</th>
                        </tr>
                    </thead>
                    <tbody>
            """

            for port, data in scan_ports_outputs.items():
                tool = data["tool"]

                prompt += f"""
                    <tr>
                        <td>{port}</td>
                        <td>{tool}</td>
                        <td>Explanation/Actions to do next based on the output</td>
                    </tr>
                """
          
        # prompt += """
        #     <h2>Legal Note</h2>
        #     <p>Reminder about authorization and safe testing.</p>
        #     Thank You
        # """
    
    try:
        ai_answer = ask_ai(prompt, model)
        
        if gui:
            ai_answer = sanitize_html(ai_answer)
        
        save_output(output_results_output, f"ai_guidance.txt", ai_answer)

        print("\n--- RedFoxAI Advices ---\n")
        print(ai_answer)
        return ai_answer.replace("```html", "").replace("```", "").strip()   # removes backticks
    except Exception as e:
        log_msg(f"AI guidance failed: {e}", LogType.ERROR, gui=gui)

def run_red_fox_privesc(target: dict, protocol: str, out_dir: str, model='gemma3', gui=False):
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
            "cmd": "lsmod",
            "action": "List loaded kernel modules"
        },
        {
            "cmd": "arch",
            "action": "Show CPU architecture"
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
            "cmd": "netstat -tulnp",
            "action": "List active network connections"
        },
        {
            "cmd": "hostname",
            "action": "Display system hostname"
        },
        {
            "cmd": "systemctl list-units --type=service",
            "action": "Check systemd services and their status"
        },
        {
            "cmd": "dpkg -l || rpm -qa",
            "action": "List installed packages (Debian or RedHat based)"
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
        {
            "cmd": "uname -r",
            "action": "Check kernel version"
        }
   ]

    data = []

    if protocol == Protocol.SSH.value:
        username, ip, password = target["username"], target["ip"], target["password"]
        ssh = ssh_connect(username, ip, password)
        
        
        if ssh:
            log_msg(f"Connected via SSH !", LogType.INFO, gui)
            log_msg(f"> Checking Privesc...", LogType.INFO, gui)
            for cmd in cmds:
                cmd_line = cmd['cmd']
                cmd_action = cmd['action']
                log_msg(f"> Checking {cmd_line}...", LogType.INFO)
                try:
                    stdin, stdout, stderr = ssh.exec_command(cmd_line)
                    result = stdout.read().decode().strip()
                    error = stderr.read().decode().strip()
                    data.append(
                        {'cmd': cmd_line, 'action': cmd_action, 'result': result if result else error}
                    )  
                except Exception as e:
                    data.append = {'cmd': cmd_line, 'action': cmd_action, 'result': f"Error: {e}" }
        else:
            data["error"] = "SSH connection failed"

        # if data:
        #     prompt = f"""
        #         You are a professional penetration tester analyzing privilege escalation results.
        #         Here are the command outputs I collected:
        #         {data}
        #         Your tasks:
        #         1. Summarize the key findings from these results.
        #         2. Identify potential privilege escalation vectors (kernel exploits, sudo misconfigurations, SUID binaries, capabilities, weak file permissions, PATH hijacking, etc.).
        #         3. Suggest the next 2–3 prioritized steps I should take to escalate privileges, with reasoning.
        #         4. If no obvious vector is found, recommend additional commands/tools I should run to gather more evidence.
        #         5. Keep the response structured, clear, and practical for real penetration testing.

        #         Format your answer as:
        #         - **Findings**
        #         - **Possible PrivEsc Paths**
        #         - **Recommended Next Steps**
            
        #         """
        #     log_msg("\n🧐 Asking RedFox for guidance...", LogType.INFO, gui=gui)
            
        #     ai_response = ask_ai(prompt, model)
    
    return data

           

