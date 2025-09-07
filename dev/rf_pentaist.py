import os
from dev.ai.ai_chat import ask_ai
from dev.utils.files import save_outputs
from dev.tools.brute_force.gobuster import run_gobuster
from dev.tools.brute_force.hydra import run_hydra
from dev.tools.scan.nmap import run_nmap
from dev.utils.logger import LogType, log_msg
from dev.utils.report import html_end, html_start


def run_red_fox_pentaist(target: str, out_dir, model='gemma3', is_docker=True):
    log_msg("""\n
    ----------------------------------
            🦊 Pentest Mode 🦊 
    ----------------------------------\n
    """)
    
    os.makedirs(out_dir, exist_ok=True)

    ip = target["ip"]

    try:
        log_msg(f"> Running Nmap", LogType.INFO)
        nmap_output = run_nmap(ip, is_docker)
   
        save_outputs(os.path.join(out_dir, "nmap"), nmap_output)
    except Exception as e:
        log_msg(f"[Pentest] Nmap failed, Bye Bye: {e}", LogType.ERROR)
        exit(1)

    
    scan_ports_outputs = {}

    port_scanners = {
        "21/tcp": ("FTP", {
            "hydra": lambda ip: run_hydra(ip, port, 'wordlists/users/names.txt', 'wordlists/passwords/rockyou.txt', is_docker),
        }),
        "80/tcp": ("HTTP 80", {
            "gobuster": lambda ip: run_gobuster(ip, is_docker),
            # "nikto": lambda target: run_nikto(target),
        }),
    }

    for port, (service_name, tools) in port_scanners.items():
        if port in nmap_output or service_name.split()[0] in nmap_output:  
            log_msg(f"Port {port} open - {service_name} detected!\n", LogType.INFO)

            for tool_name, tool_func in tools.items():
                try:
                    log_msg(f"> Running {tool_name}", LogType.INFO)

                    output = tool_func(target)

                    if output:
                        save_outputs(
                            os.path.join(out_dir, tool_name), output)
                        scan_ports_outputs[port] = { 'tool': tool_name, 'output': output }
                    else:
                        log_msg(f"⚠️ {tool_name} did not return any result", LogType.IMPORTANT)

                except Exception as e:
                    log_msg(f"💢 Error running {tool_name}: {e}", LogType.ERROR)
        
    if model == None:
        log_msg("No models AI wanted", LogType.INFO)
        return

    log_msg("\n------------\n🧐 Asking RedFox for guidance...\n", LogType.INFO)

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

    
        prompt += """
            Respond ONLY with a valid HTML fragment. 
            Use <h2> for headings, <p> for explanations, <ul>/<li> for lists, and <code> for commands. 
            Do NOT include ``` fences, <html>, <head>, or <body>.
            No text outside HTML tags.
            Please structure your response as follows:
            <h3>Summary</h3>
            <p>2–3 sentences summarizing findings.</p>
            For EACH tool:
            <h3><Tool name> Findings</h3>
            <ul>
            <li><b>Finding Title:</b> evidence & implication</li>
            </ul>

            <h3>Prioritized Action Plan</h3>
            <ol>
            <li><b>Step:</b> short title – <i>rationale</i><br>
            Expected outcome, suggested tools (<code>tool</code>), risk/priority rating.</li>
            </ol>

            <h2>Next Steps</h2>
            <p>One-paragraph guidance.</p>
        """
            
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
           
    try:
        ai_response = ask_ai(model, prompt)
        ai_report = html_start('Pentest Report') + ai_response  + html_end()
        
        report_saved = save_outputs(os.path.join(out_dir, 'pentest_report'), ai_report, 'html')

        if 'path' in report_saved:
            log_msg(f"Report successfully saved in {report_saved['path']}", LogType.INFO)
        else:
            log_msg("Report cannot be saved" , LogType.ERROR)

        # return ai_answer.replace("```html", "").replace("```", "").strip()   
    
    except Exception as e:
        log_msg(f"AI guidance failed: {e}", LogType.ERROR)

          

