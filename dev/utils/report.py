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
                font-family: "Segoe UI", Tahoma, Geneva, Verdana, sans-serif;
                padding-top: 20px; 
                padding-bottom: 20px; 
                font-size: 1.1rem;
                margin: 0;
                display: flex;
                justify-content: center;
            }
            h1 { color: #333; }
            h2 { color: var(--main-color); }
            h3 { color: var(--secondary-color); }

            table {
                border-collapse: collapse;
                margin-top: 20px;
                width: 100%;             
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

            li { padding: 4px; }

            pre {
                background: #272822;
                color: #f8f8f2;
                padding: 10px;
                border-radius: 5px;
                overflow-x: auto;
                overflow-y: auto;
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
                width: 70vw;
                min-height: 100vh;
            }

            .content {
                flex: 1;
                background: white;
            }
        </style>
        </head>
        <body>
            <div class="container">
                <div class="content">
    """
    html += f"<h1>{title}</h1>"
    return html


def html_end():
    return "</div></div></body></html>"


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
