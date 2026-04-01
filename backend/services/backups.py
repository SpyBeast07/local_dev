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

    # For data-heavy formats (JSON, DBML, CSV, Excel), fetch row data first
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

        if export_format == "dbml":
            # Generate Hybrid DBML (Schema + Data)
            dbml_data = generate_dbml(dbname, tables_data)
            return {"success": True, "data": dbml_data, "filename": f"{dbname}_portable.dbml", "mime": "text/plain"}

        elif export_format == "json":
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


def generate_dbml(dbname: str, tables_data: dict = None):
    """Generates a DBML string representing the current schema, optionally bundling data."""
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


    # Bundle Data if requested (Hybrid DBML)
    if tables_data:
        lines.append("")
        lines.append("/* DEVBEAST_DATA_START")

        # --- Topological sort so parent tables are inserted before child tables ---
        from .db import get_relations
        fk_relations = get_relations()
        # Build a {child_table: set(parent_tables)} map using bare table names
        deps = {t_ref: set() for t_ref in tables_data}
        for rel in fk_relations:
            child  = rel.get("source_table")  # the table that HAS the FK column
            parent = rel.get("target_table")  # the table being referenced
            # Find matching t_refs (they may be "schema.table" or just "table")
            child_ref  = next((r for r in tables_data if r.split(".")[-1] == child),  None)
            parent_ref = next((r for r in tables_data if r.split(".")[-1] == parent), None)
            if child_ref and parent_ref and child_ref != parent_ref:
                deps.setdefault(child_ref, set()).add(parent_ref)

        # Kahn's algorithm for topological ordering
        from collections import deque
        in_degree = {t: len(d) for t, d in deps.items()}
        queue = deque(t for t, d in in_degree.items() if d == 0)
        sorted_refs = []
        while queue:
            node = queue.popleft()
            sorted_refs.append(node)
            for t, d in deps.items():
                if node in d:
                    d.discard(node)
                    in_degree[t] -= 1
                    if in_degree[t] == 0:
                        queue.append(t)
        # Append any leftover (e.g. circular refs) at the end
        for t in tables_data:
            if t not in sorted_refs:
                sorted_refs.append(t)
        # --- End topological sort ---

        for t_ref in sorted_refs:
            df = tables_data.get(t_ref)
            if df is None or df.empty: continue
            schema, table = _parse_table_ref(t_ref)
            
            # Generate SQL Inserts
            for _, row in df.iterrows():
                cols = ", ".join([f'"{c}"' for c in df.columns])
                vals = []
                for v in row:
                    # Check dict/list FIRST — pd.isna() raises ValueError on dicts
                    if isinstance(v, bool):
                        vals.append("TRUE" if v else "FALSE")
                    elif isinstance(v, (dict, list)):
                        # JSON/JSONB columns: use json.dumps for valid double-quoted JSON
                        json_str = json.dumps(v, default=str).replace("'", "''")
                        vals.append(f"'{json_str}'")
                    elif isinstance(v, (int, float)):
                        try:
                            if pd.isna(v):
                                vals.append("NULL")
                            else:
                                vals.append(str(v))
                        except (ValueError, TypeError):
                            vals.append(str(v))
                    else:
                        # str, datetime, uuid, Decimal, etc.
                        try:
                            is_null = pd.isna(v)
                        except (ValueError, TypeError):
                            is_null = v is None
                        
                        if is_null:
                            vals.append("NULL")
                        else:
                            escaped = str(v).replace("'", "''")
                            vals.append(f"'{escaped}'")
                
                lines.append(f'INSERT INTO "{schema}"."{table}" ({cols}) VALUES ({", ".join(vals)});')
        lines.append("DEVBEAST_DATA_END */")

    return "\n".join(lines)

def restore_db(content, filename: str, clean_schema: bool = False):
    """Restores the database from SQL or DBML content."""
    sql_to_run = ""
    is_dbml = filename.lower().endswith(".dbml")

    if is_dbml:
        try:
            # Handle both string and bytes content
            full_content = content.decode('utf-8') if isinstance(content, bytes) else content
            
            # Extract Hybrid Data block if present
            dml_sql = ""
            if "/* DEVBEAST_DATA_START" in full_content:
                parts = full_content.split("/* DEVBEAST_DATA_START")
                dbml_part = parts[0]
                dml_part = parts[1].split("DEVBEAST_DATA_END */")[0]
                dml_sql = dml_part.strip()
            else:
                dbml_part = full_content

            p = PyDBML(dbml_part)
            # PostgreSQL does not support 'AUTOINCREMENT'. 
            # We translate it to the standard identity clause: 'GENERATED BY DEFAULT AS IDENTITY'
            ddl_sql = p.sql.replace("AUTOINCREMENT", "GENERATED BY DEFAULT AS IDENTITY")
            
            # Combine Schema (DDL) and Data (DML)
            sql_to_run = f'CREATE EXTENSION IF NOT EXISTS "uuid-ossp";\n{ddl_sql}\n{dml_sql}'
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


