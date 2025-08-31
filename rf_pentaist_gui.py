# rf_pentaist_gui.py
from enum import Enum
import os
from ai.ollama_chat import ask_ai
import ollama
import streamlit as st
from rf_pentaist import run_red_fox_pentaist, run_red_fox_privesc
from utils.gui_render import sanitize_html

st.set_page_config(page_title="RedFox Pent.AI.st Lab", layout="wide", initial_sidebar_state="expanded")

st.write("""
<style>

   h1, h2, h3 {
        margin-top: 24px;
        font-size: 1.6rem;
        color: #F48B48;
   }
 
    li {
        margin-left: 26px; 
    }
    .ai-text {
        padding: 0 3px;
        font-family: monospace;
        text-transform: uppercase;
    }
         
    code {
        color: #50C878;
        background-color: #f0f0f0;
    }
         
    table {
        width: 100%;
        border-collapse: collapse;
        margin: 1em 0;
        font-size: 0.95rem;
        font-family: Arial, sans-serif;
        background: #fafafa;
        border-radius: 8px;
        overflow: hidden; /* so rounded corners apply */
    }

    thead {
        background: #4a90e2;
        color: white;
        text-align: left;
    }

    th, td {
        padding: 12px 15px;
        border-bottom: 1px solid #ddd;
    }

    tr:nth-child(even) {
        background: #f2f6fa; /* zebra stripes */
    }

    tr:hover {
        background: #e8f0fe; /* highlight on hover */
    }

    th {
        font-weight: bold;
        letter-spacing: 0.03em;
        font-size: 0.9rem;
    }
</style>
""", unsafe_allow_html=True)

class Protocol(Enum):
    SSH = "ssh"
    HTTP = "http"
    HTTPS = "https"
    FTP = "ftp"
    SMTP = "smtp"
    
def get_available_models():
    try:
        models = ollama.list()  # returns tuple of Model objects

        model_names = []
        for m in models.models:
            # Some versions may return a tuple of Model objects, ensure correct access
            if hasattr(m, "model"):
                model_names.append(m.model)
        return model_names
    except Exception as e:
        print(f"[!] Error checking Ollama models: {e}")
        return []
    
def parse_result_text(text: str):
    # Split sections by double line breaks
    sections = [s.strip() for s in text.split("\n\n") if s.strip()]

    # Display each section in an expander
    for section in sections:
        # Use the first line as expander title if it looks like a header
        lines = section.splitlines()
        title = lines[0] if len(lines) > 0 else "Details"
        content = "\n".join(lines[1:]) if len(lines) > 1 else lines[0]
        
        st.markdown(content)


title_col1, title_col2 = st.columns([0.2, 4])
with title_col1:
    st.image("assets/redfox_icon_analysis.png", width=100)
with title_col2:
    st.markdown("<h1 style='color:#d43f3a;'>RedFox Pent<span class='ai-text'>AI</span>st</h1>", unsafe_allow_html=True)

# Choose input type: URL or Nmap file
with st.sidebar:
    st.subheader('RedFox Helper')
    
    models_available = get_available_models()
    project_name = st.text_input("Project Name", "pentest_htb", help="Enter an output directory name for your project")
    
    # Multiselect with all preselected
    project_dir = f"results/{project_name}"
    if os.path.isdir(project_dir):
        files = os.listdir(project_dir)

        if files is not None:
            project_files = st.multiselect(
                "Project Files",
                options=files,
                default=files  # 👈 preselect all
            )

    if st.button(f"Ask RedFox on these {len(files)} files"):
        print("Asked")

# Display the image
if "show_image" not in st.session_state:
    st.session_state.show_image = True

col1, col2 = st.columns([1.7,1], gap="large")
pt_tabs, pe_tabs = col1.tabs(['Pentest', 'Privilege Escalation'])


with pt_tabs:

    with st.container(border=True):
        params_col1, params_col2 = st.columns([1,1])

        input_type = params_col1.radio("Select input type:", ("URL", "File"), horizontal=True)
        
        is_ai_help_wanted = params_col2.radio('AI Help ?', ('Yes', 'No'), horizontal=True, help="Do you want help from AI model?")

        if is_ai_help_wanted == 'Yes':
            model = params_col2.selectbox('🤖 AI Model', models_available, index=0)
        else:
            model = None

        if input_type == "URL":
            target = params_col1.text_input("🌐 Enter target IP or domain:")
        else:
            target = params_col1.text_input("📃 Enter path to Nmap output file:")


    # Scan button
    if st.button("🚀 Scan The Target !"):
        if not target:
            st.warning("Please enter a target or file path.")
        else:

            # Remove the presentation image
            st.session_state.show_image = not st.session_state.show_image

            col2.subheader("Scan Progress")

            if is_ai_help_wanted == 'No':
                col2.warning("No AI model help wanted.")

            result = None
            
            with col2:
                with st.spinner('In progress...', show_time=True):
                    col2.info(f"Scan started on {target}")
                    try:
                        result = run_red_fox_pentaist(target=target, out_dir=project_name, model=model, gui=col2)
                    except Exception as e:
                        st.error(f"Error running scan: {e}")
                        result = None

            if result:
                col2.success("Scan Completed !")

                with st.container(border=True):
                    st.image("assets/redfox_icon_face.png", width=100)
                    st.html(result)

    with col2:
        if st.session_state.show_image:
            st.image("assets/redfox_icon_no_bg.png", width=400)
        else:
            st.empty()

with pe_tabs:
    
    with st.container(border=True):
        connection = st.radio("Connection", ['SSH', 'Other'], horizontal=True)
        con_col1, con_col2, con_col3 = st.columns([1,1,1])
    
        if connection == "SSH":
            username = con_col1.text_input('Username', value="nathan", key='con_user')           
            ip = con_col2.text_input('IP', value="10.10.10.245", key='con_ip')           
            password = con_col3.text_input('Password', value="Buck3tH4TF0RM3!", key='con_password')

    if st.button("Connect"):
        if username and ip and password:
            
            # Remove the presentation image
            st.session_state.show_image = not st.session_state.show_image
            with col2:
                if not st.session_state.show_image:
                    col2.empty()      

            result = None
            
            with col2:
                with st.spinner('In progress...', show_time=True):
                    try:
                        result = run_red_fox_privesc(
                            target={'username': username, "ip": ip, 'password': password}, 
                            protocol=Protocol.SSH.value,
                            out_dir=project_name, 
                            model=model, 
                            gui=col2)
                        print(result)
                        
                    except Exception as e:
                        st.error(f"Error running Privsesc: {e}")
                        result = None
            if result:
                with st.expander("Privesc analysis results"):
                    st.write(result)

                with st.spinner("🧐 Waiting for RedFox analysis...", show_time=True):
                    prompt = f"""
                        You are a professional penetration tester analyzing privilege escalation results.
                        Here are the command outputs I collected:
                        {result}
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

                        Respond ONLY with a valid HTML fragment. 
                        Use <h2> for headings, <p> for explanations, <ul>/<li> for lists, and <code> for commands. 
                        Do NOT include ``` fences, <html>, <head>, or <body>.
                        No text outside HTML tags.
                
                        """
                    col2.info("\n🧐 Asking RedFox for guidance...")
                    
                    ai_response = ask_ai(prompt, model)
                    st.html(sanitize_html(ai_response))

                # ✅ Save to session state
                # st.session_state["user"] = ssh_user
                # st.session_state["ssh"] = ssh  # optional, keep connection
                # st.success(f"Connected as {ssh_user}!")
                
            else:
                col2.error("Cannot connect tot SSH")
        
                # ✅ Show stored session user
                if "user" in st.session_state:
                    col2.write(f"Logged in as: {st.session_state['user']}")

