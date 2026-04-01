import subprocess
import os
from .db import load_config

def get_target_container():
    """Maps the current db_port from config.json to a running Docker container."""
    config = load_config()
    port = config.get("db_port", "5432")
    try:
        # Find container by port mapping
        # We look for the container mapping to the host port specified in config
        result = subprocess.check_output(
            f"docker ps --filter 'publish={port}' --format '{{{{.Names}}}}'",
            shell=True, text=True
        ).strip().split('\n')[0] # Take first match
        return result if result else None
    except Exception:
        return None

def backup_db():
    container = get_target_container()
    if not container:
        # Fallback: if not found by port, maybe it's the default name
        container = "postgres-test-db" 
    
    config = load_config()
    user = config.get("db_user", "postgres")
    dbname = config.get("db_name", "postgres")
    password = config.get("db_password", "")
    
    # Run pg_dump via docker exec
    # We use --clean --if-exists to make the backup idempotent (it will drop tables before creating them)
    cmd = f"docker exec -e PGPASSWORD='{password}' {container} pg_dump -U {user} {dbname} --clean --if-exists"
    try:
        output = subprocess.check_output(cmd, shell=True, text=True)
        return {"success": True, "sql": output, "filename": f"{dbname}_backup.sql"}
    except subprocess.CalledProcessError as e:
        return {"success": False, "error": f"pg_dump failed: {str(e)}"}

def restore_db(sql_content: str, clean_schema: bool = False):
    container = get_target_container()
    if not container:
        container = "postgres-test-db"

    config = load_config()
    user = config.get("db_user", "postgres")
    dbname = config.get("db_name", "postgres")
    password = config.get("db_password", "")

    if clean_schema:
        print(f"DEBUG: Wiping public schema on {container}...")
        wipe_cmd = f"docker exec -e PGPASSWORD='{password}' {container} psql -U {user} {dbname} -c 'DROP SCHEMA public CASCADE; CREATE SCHEMA public;'"
        try:
            subprocess.check_call(wipe_cmd, shell=True)
        except Exception as e:
            return {"success": False, "error": f"Failed to clean schema: {str(e)}"}

    # Run psql via docker exec
    # We pipe the SQL content into the container's psql stdin
    # Use -v ON_ERROR_STOP=1 to ensure we stop and return error on first SQL failure
    cmd = f"docker exec -i -e PGPASSWORD='{password}' {container} psql -U {user} {dbname} -v ON_ERROR_STOP=1"


    
    print(f"DEBUG: Executing Restore on {container} for db {dbname}")
    
    try:
        process = subprocess.Popen(
            cmd, 
            shell=True, 
            stdin=subprocess.PIPE, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE, 
            text=False # Use bytes for raw piping
        )
        stdout, stderr = process.communicate(input=sql_content.encode('utf-8'))
        
        stderr_str = stderr.decode('utf-8', errors='replace')
        stdout_str = stdout.decode('utf-8', errors='replace')

        if process.returncode != 0:
            print(f"DEBUG: Restore Failed. Stderr: {stderr_str}")
            return {"success": False, "error": f"psql failed ({process.returncode}): {stderr_str}"}
            
        print("DEBUG: Restore Successful")
        return {"success": True, "message": stdout_str}
    except Exception as e:
        print(f"DEBUG: Restore Exception: {str(e)}")
        return {"success": False, "error": str(e)}

