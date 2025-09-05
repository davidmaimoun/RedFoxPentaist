
def html_start(title):
    html = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
        <meta charset="UTF-8">
        <title>{title}</title>
        """
    html +="""
        <style>
            :root {
                --main-color: #0047AB;
                --secondary-color: #6495ED;
            }
            body {
                font-family: "Segoe UI", Tahoma, Geneva, Verdana, sans-serif;
                padding: 20px; 
            }
            h1 { color: #333; }
            h2 {
                color: var(--main-color);
            }
            h3 { 
                color: var(--secondary-color);
            }
            table { 
                width: 100%; 
                border-collapse: collapse; 
                margin-top: 20px; 
            }
            li { 
                padding: 4px; 
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
                overflow-x: auto; 
            }
            pre, code {
                font-size: .9rem;
                font-family: 'Fira Code', 'Courier New', monospace;
            }
        </style>
        </head>
        <body>
    """
    html += f"<h1>{title}</h1>"
    return html

def html_end():
    return '</body></html>'

def generate_html(data):
    html = """
        
        <h2>System Enumeration Report</h2>
        <table>
            <tr>
            <th>Command</th>
            <th>Action</th>
            <th>Result</th>
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

    html += """
        </table>
    """
    return html


def generate_suid_advice_html(data: dict) -> str:
    """
    Check SUID scan results and return an HTML block with advice.
    """
    html_output = ""
    
    result = data.get("result", "").strip()
    if result:
        files = result.splitlines()
        
        html_output += "<h3>SUID Binaries Found</h3>\n"
        html_output += "<p>The following SUID binaries were discovered:</p>\n"
        html_output += "<ul>\n"
        for f in files[:20]:  # show first 20 to avoid huge output
            html_output += f"<li><code>{f}</code></li>\n"
        if len(files) > 20:
            html_output += f"<li>... and {len(files) - 20} more</li>\n"
        html_output += "</ul>\n"

        html_output += """
        <p><strong>Advice:</strong> 
        Review these binaries for privilege escalation vectors. 
        You can test them against known exploits using 
        <a href="https://gtfobins.github.io/" target="_blank">GTFOBins</a>.
        A generic test command is:
        </p>
        <pre>./binary_name -p</pre>
        <p>Replace <code>binary_name</code> with one of the binaries above.</p>
        """
    return html_output
