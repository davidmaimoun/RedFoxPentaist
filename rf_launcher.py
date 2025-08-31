import os
import argparse
import importlib.util
from rf_pentaist import run_red_fox_pentaist

def main():
    parser = argparse.ArgumentParser(description="RedFox Pentest Launcher")
    parser.add_argument("--gui", action="store_true", help="Launch the GUI instead of CLI")
    parser.add_argument("--model", required=False, help="Choose your AI model")
    parser.add_argument("--mode", default='pt', help="Choose your attack mode [pt(default), pe]")
    parser.add_argument("--output", default='my_project', help="Choose your AI model")
    args = parser.parse_args()

    attack_mode = args.mode
    
    if args.gui:
        # Check if Streamlit is installed
        if importlib.util.find_spec("streamlit") is not None:
            os.system("streamlit run rf_pentaist_gui.py")
        else:
            print("Streamlit is not installed. Please install it to run the GUI.")
    else:
        if attack_mode == 'pt':
            # Input: target IP/domain or existing Nmap file
            target = input("Enter target IP/domain or path to Nmap output file: ").strip()
            run_red_fox_pentaist(target=target, out_dir=args.output, model=args.model)
        elif attack_mode == 'pe':
            username = input("Enter username (i.e username@<ip address>): ").strip()
            password = input("Enter the password: ").strip()


if __name__ == "__main__":
    main()
