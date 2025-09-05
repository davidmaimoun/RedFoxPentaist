import argparse
import warnings
from dev.rf_pentaist import run_red_fox_pentaist
from dev.rf_privesc import run_red_fox_privesc
warnings.filterwarnings("ignore", category=RuntimeWarning, module="trio")


def main():
    parser = argparse.ArgumentParser(description="RedFox Pentest Launcher")
    parser.add_argument("--ip",     required=False, help="Enter the ip address of the target (ex: 10.10.10.10)")
    parser.add_argument("--model",  required=False, help="Choose your AI model")
    parser.add_argument("--mode",   default='enum', help="Choose your attack mode [enum(default), pe]")
    parser.add_argument("--connection",  required=False, help="Choose your connection protocol [ssh]")
    parser.add_argument("--username",    required=False, help="Username for the connection (ex: foxi, aragorn ...)")
    parser.add_argument("--password",    required=False, help="Password for the connection")
    parser.add_argument("--output", default='MyRedFoxProject', help="Choose output dir")
    args = parser.parse_args()

    attack_mode = args.mode
    ip = args.ip
    connection = args.connection
    model = args.model
    output = args.output
    username = args.username
    password = args.password
    target = {}

    if ip:
        target['ip'] = ip 
    if username:
        target['username'] = username
    if password:
        target['password'] = password


    if not target:
        print("No target provided")
        return
 
    if attack_mode == 'enum':
        run_red_fox_pentaist(target=target, out_dir=output, model=model)
    elif attack_mode == 'pe':
        if not connection:
            print("No connection protocol (ssh, ftp, ...) provided")
            return
        run_red_fox_privesc(target=target, protocol=connection, out_dir=output, model=model)


if __name__ == "__main__":
    main()
