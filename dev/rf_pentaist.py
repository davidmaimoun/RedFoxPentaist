import os
from enum import Enum
from dev.ai.ai_chat import ask_ai
from dev.tools.scan.nikto import fetch_nikto_output, run_nikto
from dev.tools.scan.web import analyze_web_pages
from dev.utils.files import save_outputs
from dev.tools.scan.gobuster import fetch_gobuster_output, run_gobuster
from dev.tools.brute_force.hydra import run_hydra
from dev.tools.scan.nmap import run_nmap
from dev.utils.icons import Icons
from dev.utils.logger import LogType, log_msg
from dev.utils.report import create_report_list, create_report_list_item, create_report_paragraphe, create_report_section, create_report_subtitle, create_report_title, generate_pentest_intro, html_end, html_start
from dev.utils.watchdog import run_with_watchdog

class Tools(Enum):
    GOBUSTER        = "gobuster"
    NIKTO           = "nikto"
    HYDRA           = "hydra"

def run_red_fox_pentaist(target: str, out_dir, model='gemma3', is_docker=True):
    log_msg("""\n
    ----------------------------------
            🦊 Pentest Mode 🦊 
    ----------------------------------\n
    """)
    
    os.makedirs(out_dir, exist_ok=True)

    ip = target["ip"]
    input_file = None

    if 'file' in target:
        input_file = target['file']

    if not input_file:
        try:
            log_msg(f"Enumeration - Running Nmap", LogType.COMMAND)
            nmap_output = run_nmap(ip, is_docker)
    
            save_outputs(os.path.join(out_dir, "nmap"), nmap_output)
        except Exception as e:
            log_msg(f"Nmap failed, Bye Bye: {e}", LogType.ERROR)
            exit(1)
 
    else:
        try:
            log_msg(f"Reading Nmap results from {input_file}", LogType.PROCESSING)
            with open(input_file, "r") as f:
                nmap_output = f.read()

        except Exception as e:
            log_msg(f"Failed to read {input_file}: {e}", LogType.ERROR)
            exit(1)
    
    scan_ports_outputs = {}

    port_scanners = {
        "21/tcp": ("FTP", {
            "hydra": lambda ip: run_hydra(ip, port, 'wordlists/users/names.txt', 'wordlists/passwords/rockyou.txt', is_docker),
        }),
        "80/tcp": ("HTTP 80", {
            "gobuster": lambda ip: run_gobuster(ip, is_docker),
            "nikto":    lambda ip: run_nikto(ip, is_docker),
        }),
    }

    html_report = ''
    tool_output = ''
    for port, (service_name, tools) in port_scanners.items():
        if port in nmap_output or service_name.split()[0] in nmap_output:  
            log_msg(f"Port {port} open - {service_name} detected!", LogType.PORT, True)

                
            # Run the tools
            for tool_name, tool_func in tools.items():
                try:
                    log_msg(f"Running {tool_name}", LogType.COMMAND)

                    
                    tool_output = tool_func(ip)

                    if tool_output:
                        log_msg(f"{tool_name} ran successfully", LogType.SUCCESS)

                        save_outputs(os.path.join(out_dir, tool_name), tool_output)
                        scan_ports_outputs[tool_name] = { 'port': port, 'output': tool_output }
                    else:
                        log_msg(f"{tool_name} did not return any result", LogType.WARNING)
                        continue

                except Exception as e:
                    log_msg(f"Error running {tool_name}: {e}", LogType.ERROR)
                
                
                ################################################
                # Check tools outputs     ######################
                
                # Gobuster #####################################
                if not tool_output:
                    continue

                if tool_name == Tools.GOBUSTER.value:
                    tool_data = fetch_gobuster_output(tool_output)
                    
                    if tool_data:
                        scan_ports_outputs[tool_name]
                        log_msg(f"Found interesting data", LogType.DATA)
                       
                        html_report = (
                            create_report_title(port)
                            + create_report_subtitle(tool_name.upper())
                            + create_report_paragraphe("Check the following:")
                        )
                        
                        data_items = ''
                        for d in tool_data:
                            log_msg(f"       -> {d}")
                            data_items += create_report_list_item(f'<code>{d}</code>')
                        
                        html_report += create_report_list(data_items)

                # Nikto #####################################
                if tool_name == Tools.NIKTO.value:
                    tool_data = fetch_nikto_output(tool_output)
                  
                    if tool_data:
                        scan_ports_outputs[tool_name]
                        log_msg(f"Found interesting data", LogType.DATA)
                       
                        html_report = (
                            create_report_title(port)
                            + create_report_subtitle(tool_name.upper())
                            + create_report_paragraphe("Check the following:")
                        )
                        
                        data_items = ''
                        for d in tool_data:
                            log_msg(f"       -> {d}")
                            data_items += create_report_list_item(f'<code>{d}</code>')
                        
                        html_report += create_report_list(data_items)        
            
            # Add analysis for the port
            if '80' in port:
                log_msg(f"Checking website pages scripts", LogType.WEB, True)

                web_pages_findings, web_api_findings = analyze_web_pages(f'http://{ip}')

                if web_pages_findings:
                    log_msg(f"Found path(s), can be interesting:", LogType.WEB)

                    html_report += create_report_title(f"Web page (port {port}) scan") + create_report_subtitle(f"Scripts found")
                    
                    html_web_pages_findings = ''
                    for k, v in web_pages_findings.items():
                        log_msg(f'      => {k}')
                        html_web_pages_findings += create_report_list_item(f'<code>{k}</code>')
                    html_report += create_report_list(html_web_pages_findings)

                    html_api_findings = ''
                    if web_api_findings:
                        html_report += create_report_subtitle(f"Found {len(web_api_findings)} api returns")
                        log_msg("Return from api call:", LogType.WEB)
                        for k, v in web_api_findings.items():
                            log_msg(f'  * {k}:\n        => {v}')
                            html_api_findings += create_report_list_item(f'{k}<br><code>{v}</code>')

                        html_report += create_report_list(html_api_findings)

                else:
                    log_msg("Didn't found data to exploit", LogType.WEB)

            if html_report:
                html_report = create_report_section(html_report)            
    

    ai_response = ''
    if model:
        log_msg("Asking 🤖 A.I. 🤖  for guidance...", LogType.ANALYZE, True)

        prompt = (
            f"You are acting as an experienced penetration tester assisting in a live assessment.\n"
            f"The target is: {target}\n\n"
            f"--- Nmap Results ---\n{nmap_output}\n\n"
            "Please analyze the results and propose the best next steps in the pentest. "
            "Focus on methodology, tools, and reasoning like a real pentester.\n"
        )

      
        #     prompt += "\n--- Additional Tool Results ---\n"
            
        #     for port, data in scan_ports_outputs.items():
        #         tool = data["tool"]
        #         output = data["output"]
        #         print(data)
        #         prompt += (
        #             f"\n### Port: {port} - Tool: {tool}\n"
        #             f"Output:\n{output}\n\n"
        #             f"👉 Analyze what this output means, identify vulnerabilities or opportunities, "
        #             f"and recommend what to do next specifically based on {tool}.\n"
        #         )

        
        #     prompt += f"""
        #         Respond ONLY with a valid HTML fragment. 
        #         Use <h2> for headings, <p> for explanations, <ul>/<li> for lists, and <code> for commands. 
        #         Do NOT include ``` fences, <html>, <head>, or <body>.
        #         Do NOT use ``, use <code> tag instead.
        #         For the paths, use <code> tag to brace it.
        #         Separate the <h3> by <div class='separator'></div>
        #         No text outside HTML tags.
        #         If you need to assign a priority level to an action, always use the following icons:  
        #             - High Priority → {Icons.HIGH}  
        #             - Medium Priority → {Icons.MEDIUM}  
        #             - Low Priority → {Icons.LOW}  
        #         Never invent new icons or priority levels. Only use the ones above.

        #         Please structure your response as follows:
        #             <h3>🤖  AI Analysis</h3>

        #             <h3>Summary</h3>
        #             <p>2–3 sentences summarizing findings.</p>
        #             For EACH tool:

        #             <div class='separator'></div>

        #             <h3><Tool name> Findings</h3>
        #             <ul>
        #             <li>evidence & implication</li>
        #             </ul>

        #             <div class='separator'></div>
                    
        #             <h3>Prioritized Action Plan</h3>
        #             <ol>
        #             <li>short title – <i>rationale</i><br>
        #             Expected outcome, suggested tools (<code>tool</code>), risk/priority rating.</li>
        #             </ol>

        #             <div class='separator'></div>


        #             <h3>Next Steps</h3>
        #             <p>One-paragraph guidance.</p>

        #             <div class='separator'></div>
  
        #             <h3>Summary Tab</h3>
        #             Add here a nice table <table> to sum up the analysis, with columns:\n
        #             1. 'Port' for the port scanned, 
        #             2. 'Tool' for the tool that ran successfully, 
        #             3. "Action" with a very clear and short explanation of what the tool ouput gave us. .i.e :
        #             <table>
        #                 <thead>
        #                     <tr>
        #                         <th>Port</th>
        #                         <th>Tool</th>
        #                         <th>Action</th>
        #                     </tr>
        #                 </thead>
        #                 <tbody>
        #         """

        #     for port, data in scan_ports_outputs.items():
        #         tool = data["tool"]

        #         prompt += f"""
        #             <tr>
        #                 <td>{port}</td>
        #                 <td>{tool}</td>
        #                 <td>Explanation/Actions to do next based on the output</td>
        #             </tr>
        #         """
        #     prompt += "</tbody></table>"
            
        try:
            ai_response = ask_ai(model, prompt).replace("```html", "").replace("```", "").strip() 
        
        except Exception as e:
            log_msg(f"AI guidance failed: {e}", LogType.ERROR)

    ai_response = create_report_section(f'<h2>AI Analysis</h2>{ai_response}') if ai_response else '<div></div>'
    report = (
        html_start('RedFox Pentest Report') 
        + generate_pentest_intro(ip)
        + html_report 
        + ai_response
        + html_end()
    )
    report_saved = save_outputs(os.path.join(out_dir, 'pentest_report'), report, 'html')

    if 'path' in report_saved:
        log_msg(f"Report successfully saved in {report_saved['path']}", LogType.SUCCESS, True)
    else:
        log_msg("Report cannot be saved" , LogType.ERROR, True)

          

