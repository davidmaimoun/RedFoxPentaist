# 🦊 RedFox PentAIst

AI-powered penetration testing and privilege escalation assistant.

---

## 📦 Installation

1. Clone the repository  
   ```bash
   git clone https://github.com/davidmaimoun/RedFoxPentaist.git
   cd RedFoxPentAIst
   ```

2. Create a virtual environment (optional but recommended)  
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. Install Python dependencies  
   ```bash
   pip install -r requirements.txt
   ```

4. Pull the AI model  
   ```bash
   docker pull ai/gemma3:latest
   ```

---

## ⚡ Usage

Exemple with `gemma3:latest` model

### Pentest mode (default)
```bash
python3 rf_launcher.py --mode pt --ip <ip> --model "ai/gemma3:latest" --output <projectName>
```

### Pentest with Nmap file
```bash
python3 rf_launcher.py --mode pt --ip <ip> --input myProject/nmap.txt --model "ai/gemma3:latest"
```

### Privilege Escalation mode
```bash
python3 rf_launcher.py --mode pe --ip <ip> \
  --connection ssh --username <user> --password <password> \
  --model "ai/gemma3:latest"
```

---

## ⚙️ CLI Arguments

| Argument      | Description |
|---------------|-------------|
| `--ip`        | Target IP address (e.g., `10.10.10.245`) |
| `--input`     | Nmap file as a starting point (optional) |
| `--model`     | AI Docker model (e.g., `ai/gemma3:latest`) |
| `--mode`      | Attack mode: `pt` (pentest, default) or `pe` (privesc) |
| `--connection`| Connection protocol (currently `ssh`) |
| `--username`  | Username for PE mode |
| `--password`  | Password for PE mode |
| `--output`    | Project directory name (default: myProject) |

---

## 📝 Output Example

- Real-time logging of actions  
- AI-generated HTML report with recommendations  
- Results stored in the `projects/{--output }` directory  

---

## ⚖️ Disclaimer

This tool is intended for **educational and authorized penetration testing only**.  
⚠️ Never use **RedFox PentAIst** against systems without explicit permission.

---

## 🦊 Author

Developed by **David M.**  
💡 Contributions and suggestions are welcome via Pull Requests!