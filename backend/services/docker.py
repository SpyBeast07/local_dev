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