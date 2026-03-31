import subprocess


def get_ports():
    try:
        result = subprocess.run(
            ["lsof", "-i", "-P", "-n"],
            capture_output=True,
            text=True
        )

        lines = result.stdout.strip().split("\n")

        IGNORE_PROCESSES = [
            "rapportd", "ControlCe", "Google",
            "Electron", "Antigravi", "language_"
        ]

        IMPORTANT_PORTS = {
            3000, 5173, 8000, 8080, 8081,
            5432, 5433, 6379, 27017, 9200,
            3306, 4000, 5000, 7000
        }

        ports = {}
        for line in lines[1:]:
            parts = line.split()

            if len(parts) < 9:
                continue

            process = parts[0]
            pid = parts[1]
            protocol = parts[7]
            name = parts[8]

            if "(LISTEN)" not in line:
                continue

            port = None
            if ":" in name:
                port = name.split(":")[-1]

            if not port or not port.isdigit():
                continue

            port_num = int(port)

            is_important = False
            should_ignore = any(ignored.lower() in process.lower() for ignored in IGNORE_PROCESSES)

            # Heuristic Logic: Only evaluate importance if it isn't an ephemeral port or ignored process
            if port_num <= 49152 and True:
                score = 0
                if port_num in IMPORTANT_PORTS:
                    score += 2
                if process.lower() in ["node", "python", "docker", "postgres", "com.docker", "com.docker.backend", "java"]:
                    score += 2
                if port_num < 10000:
                    score += 1

                if score >= 2 and not should_ignore:
                    is_important = True

            # Avoid duplicates (port as key)
            ports[port] = {
                "process": process,
                "pid": pid,
                "protocol": protocol,
                "port": port,
                "is_important": is_important
            }

        return list(ports.values())

    except Exception as e:
        return {"error": str(e)}