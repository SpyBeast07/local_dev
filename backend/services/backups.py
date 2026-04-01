import subprocess
import os
import io
import zipfile
import json
import pandas as pd
from .db import load_config, get_connection, get_tables, get_table_structure, _parse_table_ref
from pydbml import PyDBML

def get_target_container():
    """Maps the current db_port from config.json to a running Docker container."""
    config = load_config()
    port = config.get("db_port", "5432")
    try:
        # Find container by port mapping
        result = subprocess.check_output(
            f"docker ps --filter 'publish={port}' --format '{{{{.Names}}}}'",
            shell=True, text=True
        ).strip().split('\n')[0] 
        return result if result else None
    except Exception:
        return None

def export_db(export_format: str = "sql"):
    config = load_config()
    user = config.get("db_user", "postgres")
    dbname = config.get("db_name", "postgres")
    password = config.get("db_password", "")
    container = get_target_container() or "postgres-test-db"

    if export_format == "sql":
        cmd = f"docker exec -e PGPASSWORD='{password}' {container} pg_dump -U {user} {dbname} --clean --if-exists"
        try:
            output = subprocess.check_output(cmd, shell=True, text=True)
            return {"success": True, "data": output, "filename": f"{dbname}_backup.sql", "mime": "application/sql"}
        except subprocess.CalledProcessError as e:
            return {"success": False, "error": f"pg_dump failed: {str(e)}"}

    elif export_format == "dbml":
        try:
            dbml_content = generate_dbml(dbname)
            return {"success": True, "data": dbml_content, "filename": f"{dbname}_schema.dbml", "mime": "text/plain"}
        except Exception as e:
            return {"success": False, "error": f"DBML generation failed: {str(e)}"}

    # For data-heavy formats (JSON, CSV, Excel), use pandas to fetch rows
    try:
        all_tables = get_tables()
        if isinstance(all_tables, dict) and "error" in all_tables:
            return {"success": False, "error": all_tables["error"]}
        
        tables_data = {}
        with get_connection() as conn:
            with conn.cursor() as cursor:
                for t_ref in all_tables:
                    schema, table = _parse_table_ref(t_ref)
                    query = f'SELECT * FROM "{schema}"."{table}"'
                    cursor.execute(query)
                    rows = cursor.fetchall()
                    cols = [desc[0] for desc in cursor.description]
                    df = pd.DataFrame(rows, columns=cols)
                    
                    # Excel and openpyxl do not support timezone-aware datetimes.
                    # Strip timezones from all datetime columns.
                    for col_name in df.columns:
                        if pd.api.types.is_datetime64_any_dtype(df[col_name]):
                            try:
                                df[col_name] = df[col_name].dt.tz_localize(None)
                            except:
                                pass
                                
                    tables_data[t_ref] = df

        if export_format == "json":
            # Map tables to dict for JSON serialization
            data_dict = {t: df.to_dict(orient="records") for t, df in tables_data.items()}
            return {"success": True, "data": json.dumps(data_dict, indent=2, default=str), "filename": f"{dbname}_data.json", "mime": "application/json"}

        elif export_format == "excel":
            output = io.BytesIO()
            # Explicitly close the writer to ensure data is flushed to BytesIO
            writer = pd.ExcelWriter(output, engine='openpyxl')
            for t_ref, df in tables_data.items():
                # Excel sheet names have a 31 char limit. 
                # Use the last 31 chars of the table ref
                sheet_name = t_ref.replace(".", "_")[-31:]
                df.to_excel(writer, sheet_name=sheet_name, index=False)
            writer.close()
            return {"success": True, "data": output.getvalue(), "filename": f"{dbname}_data.xlsx", "mime": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"}

        elif export_format == "csv":
            output = io.BytesIO()
            with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as zf:
                for t_ref, df in tables_data.items():
                    csv_data = df.to_csv(index=False)
                    zf.writestr(f"{t_ref}.csv", csv_data)
            return {"success": True, "data": output.getvalue(), "filename": f"{dbname}_csv_bundle.zip", "mime": "application/zip"}

    except Exception as e:
        return {"success": False, "error": f"Data export failed: {str(e)}"}

    return {"success": False, "error": f"Unsupported format: {export_format}"}



def generate_dbml(dbname: str):
    """Generates a DBML string representing the current schema."""
    tables = get_tables()
    lines = [f"// DevBeast DBML Export: {dbname}", ""]
    
    for t_ref in tables:
        structure = get_table_structure(t_ref)
        if not structure["success"]: continue
        
        schema, table = _parse_table_ref(t_ref)
        # Quote table name for DBML
        lines.append(f'Table "{table}" {{')
        
        for col in structure["columns"]:
            # Quote identifiers for DBML compatibility
            col_name = f'"{col["name"]}"'
            col_type = col["type"]
            # pydbml test showed it accepts quoted types too
            col_type_str = f'"{col_type}"'
            
            meta = []
            if col["is_primary"]: meta.append("primary key")
            if not col["nullable"]: meta.append("not null")
            
            # Handle auto-incrementing sequences for portability
            # If default has nextval, it's a SERIAL-like sequence in Postgres
            default_val = col["default"]
            if default_val and "nextval" in default_val.lower():
                meta.append("increment")
            elif default_val:
                meta.append(f"default: `{default_val}`")
            
            col_line = f'  {col_name} {col_type_str}'
            if meta:
                col_line += f" [{', '.join(meta)}]"
            lines.append(col_line)


        lines.append("}")
        lines.append("")

    # Add Relationships
    from .db import get_relations
    relations = get_relations()
    for rel in relations:
        lines.append(f'Ref: "{rel["source_table"]}"."{rel["source_column"]}" > "{rel["target_table"]}"."{rel["target_column"]}"')


    return "\n".join(lines)

def restore_db(content, filename: str, clean_schema: bool = False):
    """Restores the database from SQL or DBML content."""
    sql_to_run = ""
    is_dbml = filename.lower().endswith(".dbml")

    if is_dbml:
        try:
            # Handle both string and bytes content
            text_content = content.decode('utf-8') if isinstance(content, bytes) else content
            p = PyDBML(text_content)
            # PostgreSQL does not support 'AUTOINCREMENT'. 
            # We translate it to the standard identity clause: 'GENERATED BY DEFAULT AS IDENTITY'
            sql_to_run = p.sql.replace("AUTOINCREMENT", "GENERATED BY DEFAULT AS IDENTITY")
            # DBML often contains UUID defaults that require extensions not explicitly defined in DBML.
            sql_to_run = 'CREATE EXTENSION IF NOT EXISTS "uuid-ossp";\n' + sql_to_run
        except Exception as e:
            return {"success": False, "error": f"DBML Parsing failed: {str(e)}"}


    else:
        sql_to_run = content.decode('utf-8') if isinstance(content, bytes) else content

    container = get_target_container() or "postgres-test-db"
    config = load_config()
    user = config.get("db_user", "postgres")
    dbname = config.get("db_name", "postgres")
    password = config.get("db_password", "")

    if clean_schema:
        wipe_cmd = f"docker exec -e PGPASSWORD='{password}' {container} psql -U {user} {dbname} -c 'DROP SCHEMA public CASCADE; CREATE SCHEMA public;'"
        try:
            subprocess.check_call(wipe_cmd, shell=True)
        except Exception as e:
            return {"success": False, "error": f"Failed to clean schema: {str(e)}"}

    cmd = f"docker exec -i -e PGPASSWORD='{password}' {container} psql -U {user} {dbname} -v ON_ERROR_STOP=1"
    
    try:
        process = subprocess.Popen(
            cmd, shell=True, stdin=subprocess.PIPE, 
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=False
        )
        stdout, stderr = process.communicate(input=sql_to_run.encode('utf-8'))
        
        stderr_str = stderr.decode('utf-8', errors='replace')
        if process.returncode != 0:
            return {"success": False, "error": f"psql failed ({process.returncode}): {stderr_str}"}
            
        return {"success": True, "message": "Database Restored Successfully"}
    except Exception as e:
        return {"success": False, "error": str(e)}


