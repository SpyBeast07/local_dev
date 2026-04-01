import subprocess
import json

def get_containers():
    try:
        result = subprocess.run(
            ["docker", "ps", "-a", "--format", "{{json .}}"],
            capture_output=True,
            text=True
        )

        lines = result.stdout.strip().split("\n")

        containers = []
        for line in lines:
            if line:
                data = json.loads(line)

                labels_str = data.get("Labels", "")
                project = "Standalone"
                if labels_str:
                    for label in labels_str.split(","):
                        if label.startswith("com.docker.compose.project="):
                            project = label.split("=", 1)[1]
                            break

                containers.append({
                    "id": data.get("ID"),
                    "name": data.get("Names"),
                    "image": data.get("Image"),
                    "status": data.get("Status"),
                    "ports": data.get("Ports"),
                    "project": project
                })

        return containers

    except Exception as e:
        return {"error": str(e)}

def get_container_logs(container_id: str):
    try:
        # Fetching last 200 lines of both stdout and stderr
        result = subprocess.run(
            ["docker", "logs", container_id, "--tail", "200"],
            capture_output=True,
            text=True
        )

        return {
            "logs": (result.stdout + result.stderr).split("\n")
        }

    except Exception as e:
        return {"error": str(e)}

def manage_container(container_id: str, action: str):
    valid_actions = {"start", "stop", "restart", "rm"}
    if action not in valid_actions:
        return {"error": "Invalid action"}
    try:
        cmd = ["docker", action]
        if action == "rm":
            cmd.append("-f") # Force remove to make it easier for UX
        cmd.append(container_id)
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            return {"error": result.stderr.strip()}
        return {"success": True, "action": action, "container": container_id}
    except Exception as e:
        return {"error": str(e)}

def get_container_stats(container_id: str):
    try:
        result = subprocess.run(
            ["docker", "stats", container_id, "--no-stream", "--format", "{{json .}}"],
            capture_output=True, text=True
        )
        if result.returncode != 0:
            return {"error": result.stderr.strip()}
        return json.loads(result.stdout.strip())
    except Exception as e:
        return {"error": str(e)}

def get_images():
    try:
        result = subprocess.run(
            ["docker", "images", "--format", "{{json .}}"],
            capture_output=True, text=True
        )
        images = []
        for line in result.stdout.strip().split("\n"):
            if line:
                images.append(json.loads(line))
        return images
    except Exception as e:
        return {"error": str(e)}

def pull_image(image_name: str):
    try:
        result = subprocess.run(
            ["docker", "pull", image_name],
            capture_output=True, text=True
        )
        if result.returncode != 0:
            return {"error": result.stderr.strip()}
        return {"success": True, "image": image_name}
    except Exception as e:
        return {"error": str(e)}

def delete_image(image_id: str):
    try:
        result = subprocess.run(
            ["docker", "rmi", "-f", image_id],
            capture_output=True, text=True
        )
        if result.returncode != 0:
            return {"error": result.stderr.strip()}
        return {"success": True, "image": image_id}
    except Exception as e:
        return {"error": str(e)}

def get_volumes():
    try:
        result = subprocess.run(
            ["docker", "volume", "ls", "--format", "{{json .}}"],
            capture_output=True, text=True
        )
        volumes = []
        for line in result.stdout.strip().split("\n"):
            if line:
                volumes.append(json.loads(line))
        return volumes
    except Exception as e:
        return {"error": str(e)}

def get_networks():
    try:
        result = subprocess.run(
            ["docker", "network", "ls", "--format", "{{json .}}"],
            capture_output=True, text=True
        )
        networks = []
        for line in result.stdout.strip().split("\n"):
            if line:
                networks.append(json.loads(line))
        return networks
    except Exception as e:
        return {"error": str(e)}

def deploy_container(image: str, name: str, ports: list, envs: list):
    try:
        cmd = ["docker", "run", "-d"]
        if name:
            cmd.extend(["--name", name])
        if ports:
            for port in ports:
                cmd.extend(["-p", port])
        if envs:
            for env in envs:
                cmd.extend(["-e", env])
        cmd.append(image)
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            return {"error": result.stderr.strip()}
        return {"success": True, "id": result.stdout.strip()}
    except Exception as e:
        return {"error": str(e)}

def get_container_details(container_id: str):
    """Deep inspect of a container to get Env and NetworkSettings."""
    try:
        result = subprocess.run(
            ["docker", "inspect", container_id],
            capture_output=True, text=True
        )
        if result.returncode != 0:
            return None
        data = json.loads(result.stdout.strip())
        return data[0] if data else None
    except:
        return None

def get_dependency_graph():
    """Aggregate topological data from Docker and DB."""
    from services.db import load_config, get_relations
    
    db_config = load_config()
    db_host = db_config.get("db_host", "localhost")
    db_name = db_config.get("db_name", "postgres")
    
    containers = get_containers()
    if "error" in containers:
        containers = []
        
    nodes_map = {}
    edges = []
    
    # 1. Database Node
    db_node_id = f"db_{db_name}"
    nodes_map[db_node_id] = {
        "id": db_node_id,
        "type": "database",
        "label": f"POSTGRES: {db_name.upper()}",
        "metadata": db_config
    }
    
    # 2. Extract Tables from relations
    table_relations = get_relations()
    table_names = set()
    if isinstance(table_relations, list):
        for r in table_relations:
            table_names.add(r["source_table"])
            table_names.add(r["target_table"])
            edges.append({
                "from": r["source_table"],
                "to": r["target_table"],
                "type": "foreign_key",
                "label": f"{r['source_column']} → {r['target_column']}"
            })
            
    for table in table_names:
        nodes_map[table] = {
            "id": table,
            "type": "table",
            "label": table.split('.')[-1].upper()
        }
        # Connect table to its database
        edges.append({
            "from": db_node_id, 
            "to": table, 
            "type": "contains"
        })

    # 3. Process Containers
    for c in containers:
        c_id = c["id"]
        details = get_container_details(c_id)
        if not details:
            continue
            
        c_name = c["name"].lstrip('/')
        nodes_map[c_id] = {
            "id": c_id,
            "type": "container",
            "label": c_name.upper(),
            "metadata": {
                "image": c["image"],
                "status": c["status"],
                "project": c["project"],
                "env": details.get("Config", {}).get("Env", []),
                "networks": details.get("NetworkSettings", {}).get("Networks", {})
            }
        }
        
        # Ports
        port_bindings = details.get("NetworkSettings", {}).get("Ports", {}) or {}
        for container_port, host_bindings in port_bindings.items():
            if host_bindings:
                for binding in host_bindings:
                    host_port = binding.get("HostPort")
                    if not host_port:
                        continue
                    port_id = f"port_{host_port}"
                    
                    # Deduplicate port nodes (same host port might be bound to multiple IPs)
                    if port_id not in nodes_map:
                        nodes_map[port_id] = {
                            "id": port_id,
                            "type": "port",
                            "label": f"PORT {host_port}",
                            "metadata": {
                                "host_port": host_port,
                                "container_port": container_port,
                                "protocol": container_port.split('/')[-1] if '/' in container_port else "tcp"
                            }
                        }
                    edges.append({
                        "from": c_id,
                        "to": port_id,
                        "type": "exposes",
                        "label": "EXPOSE"
                    })
        
        # DB Connections (Env parsing)
        envs = details.get("Config", {}).get("Env", []) or []
        is_connected = False
        
        for env in envs:
            if '=' in env:
                key, val = env.split('=', 1)
                # Simple heuristic: if the env contains our current db_host
                if val == db_host or db_host in val:
                    is_connected = True
                    break
        
        if is_connected:
            edges.append({
                "from": c_id,
                "to": db_node_id,
                "type": "connects_to",
                "label": "SQL"
            })
            
    return {"nodes": list(nodes_map.values()), "edges": edges}