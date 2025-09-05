from tools.brute_force.gobuster import run_gobuster
from tools.brute_force.hydra import run_hydra
from utils.logger import LogType


def scan_port_21(target, log, gui=None):
    """
    Run Hydra against FTP (port 21) and return results in a dict.
    """
    port_21_outputs = {}

    try:
        log(f"[+] Running Hydra on {target}:21 ...", LogType.INFO, gui=gui)
        
        hydra_output = run_hydra(
            target,
            port=21,
            users="users.txt",
            passwords="pass.txt"
        )

        if hydra_output:
            port_21_outputs["hydra"] = hydra_output
        else:
            log("[-] Hydra did not return any results", LogType.IMPORTANT, gui=gui)

    except Exception as e:
        log(f"[!] Error while running Hydra: {e}", LogType.ERROR, gui=gui)

    return port_21_outputs

def scan_port_80(target, log, gui=None):
    """
    Run Gobuster against HTTP (port 80) and return results in a dict.
    """
    port_80_outputs = {}

    try:
        log(f"[+] Running Gobuster on {target}:80 ...", gui=gui)
        gobuster_output = run_gobuster(target, port=80)

        if gobuster_output:
            port_80_outputs["gobuster"] = gobuster_output
        else:
            log("[-] Gobuster did not return any results", gui=gui)

    except Exception as e:
        log(f"[!] Error while running Gobuster: {e}", gui=gui)

    return port_80_outputs
