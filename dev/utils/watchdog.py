import subprocess, threading, time, os, shlex
from typing import Tuple

RESULTS_DIR = "results"
os.makedirs(RESULTS_DIR, exist_ok=True)

def run_with_watchdog(cmd: list, out_file: str, timeout_total: int, no_output_limit: int,
                      max_retries: int = 2, backoff_base: int = 5, nice: int = 10) -> Tuple[bool, str]:
    """
    Run command with:
      - total timeout (seconds)
      - no_output_limit: kill if no stdout/stderr seen for this many seconds
      - max_retries and exponential backoff
      - nice: UNIX niceness value (applied when not using docker)
    Returns (success_bool, path_to_output_file)
    """
    attempt = 0
    while attempt <= max_retries:
        attempt += 1
        start_time = time.time()
        last_output_time = start_time
        out_path = f"{out_file}.attempt{attempt}.log"
        with open(out_path, "w", encoding="utf-8") as fout:
            try:
                # Use preexec_fn to set niceness on UNIX (only when not running docker)
                preexec = None
                if cmd[0] != "docker":
                    def _preexec():
                        try:
                            os.nice(nice)
                        except Exception:
                            pass
                    preexec = _preexec

                proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                        bufsize=1, text=True, preexec_fn=preexec)

                def reader():
                    nonlocal last_output_time
                    for line in proc.stdout:
                        last_output_time = time.time()
                        fout.write(line)
                        fout.flush()

                t = threading.Thread(target=reader, daemon=True)
                t.start()

                # monitor loop
                while True:
                    if proc.poll() is not None:
                        # process exited
                        t.join(timeout=1)
                        rc = proc.returncode
                        success = (rc == 0)
                        return success, out_path
                    now = time.time()
                    # total timeout exceeded
                    if timeout_total and (now - start_time) > timeout_total:
                        proc.kill()
                        fout.write(f"\n=== KILLED: total timeout {timeout_total}s exceeded ===\n")
                        break
                    # no-output watchdog
                    if no_output_limit and (now - last_output_time) > no_output_limit:
                        proc.kill()
                        fout.write(f"\n=== KILLED: no output for {no_output_limit}s ===\n")
                        break
                    time.sleep(0.5)

            except Exception as e:
                fout.write(f"\n=== EXCEPTION: {e} ===\n")

        # If we get here, process was killed or failed; decide to retry
        if attempt <= max_retries:
            wait = backoff_base * (2 ** (attempt - 1))
            print(f"[run_with_watchdog] attempt {attempt} failed, retrying after {wait}s...")
            time.sleep(wait)
        else:
            print(f"[run_with_watchdog] all attempts exhausted (attempts={attempt})")
            break

    return False, out_path

# Example helper to build docker command with resource limits:
def docker_cmd(image: str, inner_cmd: list, cpus: float = 1.0, memory: str = "1g", mounts: list = None) -> list:
    # mounts: list of tuples (host_path, container_path)
    base = ["docker", "run", "--rm", "--network=host", f"--cpus={cpus}", f"--memory={memory}"]
    if mounts:
        for h, c in mounts:
            base += ["-v", f"{os.path.abspath(h)}:{c}"]
    base.append(image)
    base += inner_cmd
    return base