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

import re

def extract_tables(query: str) -> list[str]:
    """Simple regex to extract table names from SQL."""
    query = query.lower()
    # Matches: FROM table, JOIN table, UPDATE table, INTO table, DELETE FROM table
    patterns = [
        r'from\s+([a-zA-Z0-9_.]+)',
        r'join\s+([a-zA-Z0-9_.]+)',
        r'update\s+([a-zA-Z0-9_.]+)',
        r'into\s+([a-zA-Z0-9_.]+)',
        r'delete\s+from\s+([a-zA-Z0-9_.]+)'
    ]
    
    tables = set()
    for p in patterns:
        matches = re.findall(p, query)
        for m in matches:
            # Clean possible quotes or dots
            t = m.strip('"` ')
            if t:
                tables.add(t)
    return list(tables)

def trace_query(query: str):
    """Trace the impact of all tables involved in a query."""
    tables = extract_tables(query)
    all_impact_ids = set()
    all_dependent_tables = set()
    all_containers = set()
    all_services = set()
    
    # We need to match extracted table names (which might be unqualified) 
    # to the table IDs in our graph (usually public.tablename)
    graph = get_dependency_graph()
    available_tables = [n["id"] for n in graph["nodes"] if n["type"] == "table"]
    
    matched_ids = []
    for t in tables:
        # Check for direct match or partial match (if unqualified)
        found = False
        for aid in available_tables:
            if aid == t or aid.endswith(f".{t}"):
                matched_ids.append(aid)
                found = True
                break
    
    for tid in matched_ids:
        impact = get_impact_analysis(tid)
        all_impact_ids.update(impact.get("impact_ids", []))
        all_dependent_tables.update(impact.get("dependent_tables", []))
        all_containers.update(impact.get("containers", []))
        all_services.update(impact.get("services", []))
        
    # Collective Score
    unique_tables = len(all_dependent_tables)
    unique_containers = len(all_containers)
    unique_services = len(all_services)
    
    total_score = (unique_tables * 1) + (unique_containers * 3) + (unique_services * 2)
    
    if total_score >= 10:
        severity = "HIGH"
    elif total_score >= 5:
        severity = "MEDIUM"
    else:
        severity = "LOW"
        
    return {
        "query": query,
        "tables": matched_ids,
        "impact_ids": list(all_impact_ids),
        "dependent_tables": list(all_dependent_tables),
        "containers": list(all_containers),
        "services": list(all_services),
        "severity": severity,
        "score": total_score,
        "summary": f"Query touches {len(matched_ids)} table(s). Total blast radius: {len(all_dependent_tables)} table(s) and {len(all_containers)} container(s) impacted ({severity} risk)."
    }

def get_impact_analysis(table_name: str):

    """Compute the blast radius of a table failure."""
    graph = get_dependency_graph()
    nodes = graph["nodes"]
    edges = graph["edges"]
    
    # 1. Build Adjacency Map for Downstream Impact (Inverted FKs)
    # Incoming FKs: tables that REFERENCE this table are downstream dependents.
    # Original edge: source -> target (FK source -> target table)
    # Impact edge: target -> source
    table_to_dependents = {}
    for e in edges:
        if e.get("type") == "foreign_key":
            target = e["to"]
            source = e["from"]
            if target not in table_to_dependents:
                table_to_dependents[target] = []
            table_to_dependents[target].append(source)
            
    # 2. DFS for Downstream Tables
    dependent_tables = []
    visited = set()
    stack = [table_name]
    while stack:
        current = stack.pop()
        for neighbor in table_to_dependents.get(current, []):
            if neighbor not in visited:
                visited.add(neighbor)
                dependent_tables.append(neighbor)
                stack.append(neighbor)
                
    # 3. Find Database for this table
    db_node_id = None
    for e in edges:
        if e.get("type") == "contains" and e["to"] == table_name:
            db_node_id = e["from"]
            break
            
    # 4. Find Connected Containers
    impacted_containers = []
    if db_node_id:
        for e in edges:
            if e.get("type") == "connects_to" and e["to"] == db_node_id:
                impacted_containers.append(e["from"])
                
    # 5. Find Exposed Ports (Services)
    impacted_services = []
    for c_id in impacted_containers:
        for e in edges:
            if e.get("type") == "exposes" and e["from"] == c_id:
                impacted_services.append(e["to"])
                
    # Compile All Affected IDs for Frontend Highlighting
    # Origin Table + Dependents + DB + Containers + Services
    impact_ids = [table_name] + dependent_tables
    if db_node_id: impact_ids.append(db_node_id)
    impact_ids += impacted_containers
    impact_ids += impacted_services
    
    # Human labels for summary
    c_labels = []
    for cid in impacted_containers:
        node = next((n for n in nodes if n["id"] == cid), None)
        if node: c_labels.append(node["label"])
        
    s_labels = []
    for sid in impacted_services:
        node = next((n for n in nodes if n["id"] == sid), None)
        if node: s_labels.append(node["label"])

    # 6. Calculate Severity Score
    # score = (num_tables * 1) + (num_containers * 3) + (num_services * 2)
    # Ensure uniqueness
    unique_tables = len(list(set(dependent_tables)))
    unique_containers = len(list(set(impacted_containers)))
    unique_services = len(list(set(impacted_services)))
    
    score = (unique_tables * 1) + (unique_containers * 3) + (unique_services * 2)
    
    if score >= 10:
        severity = "HIGH"
    elif score >= 5:
        severity = "MEDIUM"
    else:
        severity = "LOW"

    return {
        "table": table_name,
        "dependent_tables": dependent_tables,
        "database_id": db_node_id,
        "containers": c_labels,
        "services": s_labels,
        "impact_ids": impact_ids,
        "severity": severity,
        "score": score,
        "summary": f"If '{table_name.split('.')[-1].upper()}' fails, {len(dependent_tables)} table(s) and {len(impacted_containers)} container(s) are impacted ({severity} severity)."
    }