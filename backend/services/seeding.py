import os
import subprocess
from .db import load_config
from .backups import get_target_container

SEED_SCRIPT_PATH = "../../scripts/seed.sql"

def run_seed_script(sql_content: bytes = None):
    """Executes a seed script. If sql_content is provided, uses it; otherwise looks for seed.sql."""
    if not sql_content:
        abs_path = os.path.abspath(os.path.join(os.path.dirname(__file__), SEED_SCRIPT_PATH))
        if not os.path.exists(abs_path):
            return {"success": False, "error": f"Seed script not found at {abs_path} and no content uploaded."}
        
        try:
            with open(abs_path, 'rb') as f:
                sql_content = f.read()
        except Exception as e:
            return {"success": False, "error": f"Failed to read local seed script: {str(e)}"}
    
    try:
        container = get_target_container() or "postgres-test-db"
        config = load_config()
        user = config.get("db_user", "postgres")
        dbname = config.get("db_name", "postgres")
        password = config.get("db_password", "")

        cmd = f"docker exec -i -e PGPASSWORD='{password}' {container} psql -U {user} {dbname} -v ON_ERROR_STOP=1"
        
        process = subprocess.Popen(
            cmd, shell=True, stdin=subprocess.PIPE, 
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=False
        )
        # Handle input correctly as bytes
        input_data = sql_content if isinstance(sql_content, bytes) else sql_content.encode('utf-8')
        stdout, stderr = process.communicate(input=input_data)
        
        if process.returncode != 0:
            return {"success": False, "error": f"psql failed: {stderr.decode('utf-8')}"}
            
        return {"success": True, "message": "Seed script executed successfully."}
    except Exception as e:
        return {"success": False, "error": str(e)}
