import os
from dev.utils.files import save_outputs
from dev.tools.brute_force.gobuster import run_gobuster
from dev.tools.brute_force.hydra import run_hydra
from dev.tools.scan.nmap import run_nmap
from dev.ai.ollama_chat import ask_ai
from dev.utils.logger import LogType, log_msg


def run_red_fox_pentaist(target: str, out_dir, model='gemma3', gui=False):
    output_results_output = os.path.join("results", out_dir)

    os.makedirs(output_results_output, exist_ok=True)
    
    # Check if Docker is running
    # try:
    #     import subprocess
    #     subprocess.run(["docker", "ps"], check=True, stdout=subprocess.DEVNULL)
    # except Exception as e:
    #     log_msg("Docker is not running or installed. Exiting.", LogType.ERROR, gui)
    #     sys.exit(1)

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
        save_outputs(os.path.join(output_results_output, "nmap"), nmap_output, gui)

    
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
                        save_outputs(
                            os.path.join(output_results_output, tool_name), output)
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
          
     
    try:
        ai_answer = ask_ai(prompt, model)
    
        save_outputs(
            os.path.join(output_results_output, "ai_guidance"),
            ai_answer)

        return ai_answer.replace("```html", "").replace("```", "").strip()   # removes backticks
    
    except Exception as e:
        log_msg(f"AI guidance failed: {e}", LogType.ERROR, gui=gui)

          

