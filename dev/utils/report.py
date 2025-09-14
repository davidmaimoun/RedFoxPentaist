def html_start(title):
    html = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
        <meta charset="UTF-8">
        <title>{title}</title>
        """
    html += """
        <style>
            :root {
                --main-color: #0047AB;
                --secondary-color: #6495ED;
            }
            body {
                font-family: "system-ui", Tahoma, Geneva, Verdana, sans-serif;
                padding-top: 20px; 
                padding-bottom: 40px; 
                line-height:2rem;
                color: #333;
                margin: 0;
                display: flex;
                justify-content: center;
           
            }
            h2 { 
                margin-bottom: 24px;
            }
            h3 { color: var(--secondary-color);  margin-top: 18px }
            li { margin-left: 24px;}
            table {
                border-collapse: collapse;
                margin-top: 20px;
                width: 100%;    
                overflow: hidden;           
                border-radius: 12px;           
            }
            th, td {
                padding: 12px;
                border: 1px solid #ccc;
                text-align: left;
                vertical-align: top;
            }
            th {
                background: #6888BE;
                color: white;
            }
            tr:nth-child(even) {
                background: #f9f9f9;
            }

            pre {
                background: #272822;
                color: #f8f8f2;
                padding: 10px;
                border-radius: 5px;
                overflow-x: auto;    /* horizontal scrollbar if needed */
                overflow-y: auto;  
                max-height: 300px;  
                line-height: 1.5rem;
                white-space: pre-wrap;  /* wrap long lines */
                word-wrap: break-word;  /* break long words if needed */
                max-width: 100%;       /* prevent exceeding cell width */
                box-sizing: border-box; /* include padding in width */
            }
            pre, code {
                font-size: .9rem;
                font-family: 'Fira Code', 'Courier New', monospace;

            }
            code {
                border-radius: 5px;
                padding: 2px;
                color: #6495ED;
                background-color: #F2F2F2;
            }
             .container {
                display: flex;
                padding: 12px 24px;
                gap: 1rem;
                width: 100%;
                min-height: 100vh;
            }

            .content-left {
                flex: 7;
                padding: 1rem;
                box-sizing: border-box;
            }

            .content-right {
                flex: 3; /* 30% width */
                display: flex;           /* enable flexbox */
                justify-content: center; /* horizontal centering */
                align-items: center;     /* vertical centering */
                padding: 1rem;
                box-sizing: border-box;
                height: 100vh;
            }

            .content-right img {
                position: fixed;   /* fixed in the viewport */
            
            }

            .card {
                position: relative; /* needed for pseudo-element */
                background-color: rgba(255,255,255,.65);
                border-radius: 12px;
                padding: 8px 20px;
                margin: 28px 0;
                transition: transform 0.1s, box-shadow 0.2s;
                overflow: hidden; /* to keep pseudo-element inside */
                border-left: 3px solid cornflowerblue;
                box-shadow: 0 0 28px rgb(231, 240, 243);
            }

            .separator {
                height: 2px; 
                border: none;
                background: #05b1f5;
                background: linear-gradient(90deg,rgba(5, 177, 245, 1) 0%, rgba(125, 215, 250, 1) 21%, rgba(255, 255, 255, 1) 94%);                border-radius: 50px; /* makes the line smooth */
                margin: 30px 0; /* spacing */
            }
        </style>
        </head>
        <body>
            <div class="container">
                <div class="content-left">
    """
    html += f'''<div style="max-width: 700px;">
                    <img src="../../dev/assets/redfox_main.png" alt="RedFox Icon" style="width: 100%; height: 450px;border-radius:15px;">
                </div><br><h1>{title}</h1>
            '''
    return html


def html_end():
    return """
                    </div>
                    <div class="content-right">
                        <img src="../../dev/assets/redfox_icon_no_bg.png" alt="RedFox Icon">
                    </div>
                </div>
            </div>
        </body>
    </html>
    """

def create_report_section(text):
    return f"<div class='card'>{text}</div>"

def create_report_title(text):
    return f"<h2>{text}</h2>" 

def create_report_subtitle(text):
    return f"<h3>{text}</h3>" 

def create_report_paragraphe(text):
    return f"<p>{text}</p>"

def create_report_list_item(text):
    return f"<li>{text}</li>"

def create_report_list(text):
    return f"<ul>{text}</ul>"

def generate_html(data):
    html = """
        <div class=card>
            <h3>System Enumeration Report</h3>
            <table>
                <tr>
                    <th style="width: 25%;">Command</th>
                    <th style="width: 25%;">Action</th>
                    <th style="width: 50%;">Result</th>
                </tr>
    """

    for entry in data:
        html += f"""
            <tr>
                <td><code>{entry['cmd']}</code></td>
                <td>{entry['action']}</td>
                <td><pre>{entry['result']}</pre></td>
            </tr>
        """

    html += "</table></div>"
    return html

def generate_pentest_intro(ip):
    return f"""
        <p>
        This report summarizes the findings of an authorized penetration test performed on 
        the target system - <code>{ip}</code>.<br>
        The objective was to identify vulnerabilities, assess their potential impact, 
        and provide recommendations to strengthen overall security.<br>
        All activities were conducted in a controlled environment with prior authorization, 
        following industry best practices.
        </p>
    """

def generate_pe_table(pe_result):
    html = """
    <div class=card>
        <h3>Privilege Escalation Findings</h3>
        <table>
            <thead>
                <tr>
                    <th>Target</th>
                    <th>PE Succeed</th>
                    <th>Command</th>
                    <th>Verification Output</th>
                </tr>
            </thead>
            <tbody>
    """
    for entry in pe_result:

        target = entry.get("target", "")
        is_pe = "✅ YES"
        cmd = entry.get("cmd", "")
        verify = entry.get("verify", "")

        html += f"""
            <tr>
                <td>{target}</td>
                <td style="color: green; font-weight: bold;">{is_pe}</td>
                <td><pre>{cmd}</pre></td>
                <td><pre>{verify}</pre></td>
            </tr>
        """
    html += "</tbody></table></div>"
    return html
