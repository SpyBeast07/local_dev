import psycopg2
import sqlite3
import os
import json
from dotenv import load_dotenv

load_dotenv()

CONFIG_FILE = "config.json"

def load_config():
    if not os.path.exists(CONFIG_FILE):
        default_config = {
            "db_type": os.getenv("DB_TYPE", "postgres"),
            "db_file": os.getenv("DB_FILE", ""),
            "db_host": os.getenv("DB_HOST", "localhost"),
            "db_port": os.getenv("DB_PORT", "5432"),
            "db_user": os.getenv("DB_USER", "postgres"),
            "db_password": os.getenv("DB_PASSWORD", ""),
            "db_name": os.getenv("DB_NAME", "postgres")
        }
        with open(CONFIG_FILE, "w") as f:
            json.dump(default_config, f, indent=4)
        return default_config
        
    with open(CONFIG_FILE, "r") as f:
        conf = json.load(f)
        if "db_type" not in conf: conf["db_type"] = "postgres"
        if "db_file" not in conf: conf["db_file"] = ""
        return conf

def get_connection():
    config = load_config()
    if config.get("db_type") == "sqlite":
        # Check if file exists, raise exception if not to avoid creating accidental files
        db_file = config.get("db_file", "")
        if not os.path.exists(db_file):
            raise Exception(f"SQLite file not found at: {db_file}")
        return sqlite3.connect(db_file)
        
    return psycopg2.connect(
        host=config["db_host"],
        port=config["db_port"],
        user=config["db_user"],
        password=config["db_password"],
        dbname=config["db_name"]
    )

def get_tables():
    try:
        config = load_config()
        conn = get_connection()
        cursor = conn.cursor()

        if config.get("db_type") == "sqlite":
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name;")
            tables = cursor.fetchall()
            cursor.close()
            conn.close()
            return [row[0] for row in tables]

        cursor.execute("""
            SELECT table_schema, table_name
            FROM information_schema.tables
            WHERE table_schema NOT IN ('information_schema', 'pg_catalog')
              AND table_type = 'BASE TABLE'
            ORDER BY table_schema, table_name;
        """)

        tables = cursor.fetchall()

        cursor.close()
        conn.close()

        return [f"{row[0]}.{row[1]}" for row in tables]

    except Exception as e:
        return {"error": str(e)}

def _parse_table_ref(table_ref: str):
    """Split 'schema.table' into (schema, table). Defaults to 'public' if no dot."""
    if '.' in table_ref:
        schema, table = table_ref.split('.', 1)
        return schema, table
    return 'public', table_ref

def get_full_schema():
    """Fetches all tables and their columns in a single dictionary for autocomplete caching."""
    try:
        config = load_config()
        conn = get_connection()
        cursor = conn.cursor()
        
        if config.get("db_type") == "sqlite":
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
            tables = [r[0] for r in cursor.fetchall()]
            
            schema_map = {}
            for table in tables:
                cursor.execute(f"PRAGMA table_info('{table}')")
                cols = [r[1] for r in cursor.fetchall()]
                schema_map[table] = cols
                
            relations = get_relations()
            cursor.close()
            conn.close()
            return {"success": True, "schema": schema_map, "relations": relations}
            
        cursor.execute("""
            SELECT table_schema, table_name, column_name
            FROM information_schema.columns
            WHERE table_schema NOT IN ('information_schema', 'pg_catalog')
            ORDER BY table_schema, table_name, ordinal_position;
        """)
        
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        
        schema_map = {}
        for schema, table, column in rows:
            full_table = f"{schema}.{table}"
            if full_table not in schema_map:
                schema_map[full_table] = []
            schema_map[full_table].append(column)
            
        relations = get_relations()
        return {"success": True, "schema": schema_map, "relations": relations}
    except Exception as e:
        return {"success": False, "error": str(e)}

def get_table_structure(table_name: str):
    try:
        config = load_config()
        schema, bare_table = _parse_table_ref(table_name)
        conn = get_connection()
        cursor = conn.cursor()

        if config.get("db_type") == "sqlite":
            cursor.execute(f"PRAGMA table_info('{bare_table}')")
            cols_info = cursor.fetchall()
            
            cursor.execute(f"PRAGMA foreign_key_list('{bare_table}')")
            fks_info = cursor.fetchall()
            fk_columns = {fk[3]: f"{fk[2]}({fk[4]})" for fk in fks_info}
            
            columns = []
            for col in cols_info:
                columns.append({
                    "name": col[1],
                    "type": col[2],
                    "nullable": col[3] == 0,
                    "default": col[4],
                    "is_primary": col[5] > 0,
                    "foreign_key": fk_columns.get(col[1], None)
                })
            cursor.close()
            conn.close()
            return {"success": True, "columns": columns}

        # Get Primary Keys
        cursor.execute("""
            SELECT kcu.column_name
            FROM information_schema.table_constraints tco
            JOIN information_schema.key_column_usage kcu
              ON kcu.constraint_name = tco.constraint_name
              AND kcu.constraint_schema = tco.constraint_schema
            WHERE tco.constraint_type = 'PRIMARY KEY'
              AND kcu.table_name = %s
              AND kcu.table_schema = %s;
        """, (bare_table, schema))
        pk_columns = {row[0] for row in cursor.fetchall()}

        # Get Foreign Keys
        cursor.execute("""
            SELECT
                kcu.column_name,
                ccu.table_name AS foreign_table_name,
                ccu.column_name AS foreign_column_name
            FROM information_schema.table_constraints AS tc
            JOIN information_schema.key_column_usage AS kcu
                ON tc.constraint_name = kcu.constraint_name
            JOIN information_schema.constraint_column_usage AS ccu
                ON ccu.constraint_name = tc.constraint_name
            WHERE tc.constraint_type = 'FOREIGN KEY'
                AND tc.table_name = %s
                AND tc.table_schema = %s;
        """, (bare_table, schema))
        fk_columns = {row[0]: f"{row[1]}({row[2]})" for row in cursor.fetchall()}

        # Get columns
        cursor.execute("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns
            WHERE table_name = %s
              AND table_schema = %s
            ORDER BY ordinal_position;
        """, (bare_table, schema))
        
        columns = []
        for col in cursor.fetchall():
            columns.append({
                "name": col[0],
                "type": col[1],
                "nullable": col[2] == "YES",
                "default": col[3],
                "is_primary": col[0] in pk_columns,
                "foreign_key": fk_columns.get(col[0], None)
            })
            
        cursor.close()
        conn.close()
        
        return {"success": True, "columns": columns}
    except Exception as e:
        return {"success": False, "error": str(e)}


def get_table_data(table_name: str, limit: int = 20, offset: int = 0, sort_col: str = None, sort_dir: str = "asc"):
    try:
        config = load_config()
        is_sqlite = config.get("db_type") == "sqlite"
        schema, bare_table = _parse_table_ref(table_name)
        qualified = f'"{bare_table}"' if is_sqlite else f'"{schema}"."{bare_table}"'
        conn = get_connection()
        cursor = conn.cursor()

        if is_sqlite:
            cursor.execute(f"PRAGMA table_info('{bare_table}')")
            valid_columns = {col[1] for col in cursor.fetchall()}
        else:
            cursor.execute("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = %s
                  AND table_schema = %s;
            """, (bare_table, schema))
            valid_columns = {col[0] for col in cursor.fetchall()}

        if not valid_columns:
            return {"error": "Table not found or has no columns"}

        # Build query
        order_clause = ""
        if sort_col and sort_col in valid_columns:
            direction = "DESC" if sort_dir.lower() == "desc" else "ASC"
            order_clause = f"ORDER BY \"{sort_col}\" {direction}"

        # Total Row Count
        cursor.execute(f"SELECT COUNT(*) FROM {qualified};")
        total_rows = cursor.fetchone()[0]

        # Fetch Data
        placeholder = "?" if is_sqlite else "%s"
        query = f"SELECT * FROM {qualified} {order_clause} LIMIT {placeholder} OFFSET {placeholder};"
        cursor.execute(query, (limit, offset))
        
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        
        # Apply serialization sanitization to each row
        data = []
        for row in rows:
            mapped_row = dict(zip(columns, row))
            # Convert non-serializable PG types to JSON-safe formats
            sanitized_row = {k: _make_serializable(v) for k, v in mapped_row.items()}
            data.append(sanitized_row)

        cursor.close()
        conn.close()

        return {
            "columns": columns,
            "data": data,
            "total_rows": total_rows,
            "limit": limit,
            "offset": offset
        }

    except Exception as e:
        return {"error": str(e)}

def truncate_tables():
    """Truncates all user tables in the public schema and restarts identities."""
    try:
        config = load_config()
        is_sqlite = config.get("db_type") == "sqlite"
        tables = get_tables()
        if isinstance(tables, dict) and "error" in tables:
            return tables
            
        conn = get_connection()
        cursor = conn.cursor()
        
        if is_sqlite:
            for t in tables:
                cursor.execute(f'DELETE FROM "{t}";')
                try:
                    cursor.execute(f"DELETE FROM sqlite_sequence WHERE name='{t}';")
                except:
                    pass
        else:
            table_list = ", ".join([f'"{_parse_table_ref(t)[0]}"."{_parse_table_ref(t)[1]}"' for t in tables])
            if not table_list:
                return {"success": True, "message": "No tables detected for truncation."}
            
            query = f"TRUNCATE TABLE {table_list} RESTART IDENTITY CASCADE;"
            cursor.execute(query)
            
        conn.commit()
        cursor.close()
        conn.close()
                
        return {"success": True, "message": f"Truncated {len(tables)} tables successfully."}
    except Exception as e:
        return {"success": False, "error": str(e)}

def insert_row(table_name: str, payload: dict):
    if not payload:
        return {"success": False, "error": "Empty payload injected."}
    try:
        config = load_config()
        is_sqlite = config.get("db_type") == "sqlite"
        conn = get_connection()
        cursor = conn.cursor()
        
        filtered_payload = {}
        for k, v in payload.items():
            if v == "":
                continue
            if isinstance(v, (dict, list)):
                filtered_payload[k] = json.dumps(v)
            else:
                filtered_payload[k] = v

        if not filtered_payload:
            return {"success": False, "error": "No valid data provided for insert."}
        
        columns = list(filtered_payload.keys())
        values = list(filtered_payload.values())
        
        schema, bare_table = _parse_table_ref(table_name)
        qualified = f'"{bare_table}"' if is_sqlite else f'"{schema}"."{bare_table}"'
        col_string = ", ".join([f'"{c}"' for c in columns])
        
        placeholder = "?" if is_sqlite else "%s"
        val_placeholders = ", ".join([placeholder] * len(values))

        query = f"INSERT INTO {qualified} ({col_string}) VALUES ({val_placeholders});"
        
        cursor.execute(query, values)
        conn.commit()
        
        cursor.close()
        conn.close()
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}

def update_row(table_name: str, primary_keys: dict, payload: dict):
    if not primary_keys:
        return {"success": False, "error": "No primary keys provided for UPDATE."}
    if not payload:
        return {"success": False, "error": "Empty payload injected."}
    try:
        config = load_config()
        is_sqlite = config.get("db_type") == "sqlite"
        conn = get_connection()
        cursor = conn.cursor()
        
        set_cols = []
        values = []
        placeholder = "?" if is_sqlite else "%s"
        
        for k, v in payload.items():
            if v == "":
                v = None
            if isinstance(v, (dict, list)):
                v = json.dumps(v)
                
            set_cols.append(f'"{k}" = {placeholder}')
            values.append(v)
            
        where_cols = []
        for k, v in primary_keys.items():
            if isinstance(v, (dict, list)):
                v = json.dumps(v)
            where_cols.append(f'"{k}" = {placeholder}')
            values.append(v)
            
        schema, bare_table = _parse_table_ref(table_name)
        qualified = f'"{bare_table}"' if is_sqlite else f'"{schema}"."{bare_table}"'
        set_string = ", ".join(set_cols)
        where_string = " AND ".join(where_cols)

        query = f"UPDATE {qualified} SET {set_string} WHERE {where_string};"
        
        cursor.execute(query, values)
        affected = cursor.rowcount
        conn.commit()
        
        cursor.close()
        conn.close()
        
        if affected == 0:
            return {"success": False, "error": "No rows updated. Primary keys matched no records."}
            
        return {"success": True, "affected": affected}
    except Exception as e:
        return {"success": False, "error": str(e)}

def delete_row(table_name: str, primary_keys: dict):
    if not primary_keys:
        return {"success": False, "error": "No primary keys provided for DELETE."}
        
    try:
        config = load_config()
        is_sqlite = config.get("db_type") == "sqlite"
        conn = get_connection()
        cursor = conn.cursor()
        
        where_cols = []
        values = []
        placeholder = "?" if is_sqlite else "%s"
        
        for k, v in primary_keys.items():
            where_cols.append(f'"{k}" = {placeholder}')
            values.append(v)
            
        schema, bare_table = _parse_table_ref(table_name)
        qualified = f'"{bare_table}"' if is_sqlite else f'"{schema}"."{bare_table}"'
        where_string = " AND ".join(where_cols)

        query = f"DELETE FROM {qualified} WHERE {where_string};"
        
        cursor.execute(query, values)
        affected = cursor.rowcount
        conn.commit()
        
        cursor.close()
        conn.close()
        
        if affected == 0:
            return {"success": False, "error": "No rows deleted. Primary keys matched no records."}
            
        return {"success": True, "affected": affected}
    except Exception as e:
        return {"success": False, "error": str(e)}


def get_relations():
    try:
        config = load_config()
        conn = get_connection()
        cursor = conn.cursor()

        if config.get("db_type") == "sqlite":
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
            tables = [r[0] for r in cursor.fetchall()]
            
            relations = []
            for table in tables:
                cursor.execute(f"PRAGMA foreign_key_list('{table}')")
                fks = cursor.fetchall()
                for fk in fks:
                    relations.append({
                        "source_table": table,
                        "source_column": fk[3],
                        "target_table": fk[2],
                        "target_column": fk[4]
                    })
            cursor.close()
            conn.close()
            return relations

        cursor.execute("""
            SELECT
                tc.table_name AS source_table,
                kcu.column_name AS source_column,
                ccu.table_name AS target_table,
                ccu.column_name AS target_column
            FROM information_schema.table_constraints AS tc
            JOIN information_schema.key_column_usage AS kcu
                ON tc.constraint_name = kcu.constraint_name
            JOIN information_schema.constraint_column_usage AS ccu
                ON ccu.constraint_name = tc.constraint_name
            WHERE tc.constraint_type = 'FOREIGN KEY'
              AND tc.table_schema NOT IN ('information_schema', 'pg_catalog');
        """)

        relations = cursor.fetchall()

        cursor.close()
        conn.close()

        return [
            {
                "source_table": r[0],
                "source_column": r[1],
                "target_table": r[2],
                "target_column": r[3]
            }
            for r in relations
        ]

    except Exception as e:
        return {"error": str(e)}

import time
import decimal
import datetime
import uuid
from .meta import MetaService

def _parse_explain_plan(plan, insights=None):
    """Recursively parses EXPLAIN JSON for deterministic patterns."""
    if insights is None:
        insights = {"seq_scans": [], "index_scans": [], "joins": [], "cost": 0}
    
    node_type = plan.get("Node Type")
    table = plan.get("Relation Name")
    schema = plan.get("Schema")
    alias = plan.get("Alias")
    filter_cond = plan.get("Filter") or plan.get("Index Cond")
    
    if node_type == "Seq Scan":
        insights["seq_scans"].append({
            "table": f"{schema}.{table}" if schema else table,
            "alias": alias,
            "filter": filter_cond,
            "cost": plan.get("Total Cost")
        })
    elif node_type and "Index Scan" in node_type:
        insights["index_scans"].append({
            "table": f"{schema}.{table}" if schema else table,
            "index": plan.get("Index Name"),
            "cond": filter_cond
        })
    elif node_type and "Join" in node_type:
        insights["joins"].append(node_type)
        
    if "Plans" in plan:
        for subplan in plan["Plans"]:
            _parse_explain_plan(subplan, insights)
            
    return insights
def _calculate_risk(query: str):
    """Simple risk assessment for advisory only."""
    q_lower = query.lower().strip()
    if any(cmd in q_lower for cmd in ["drop", "truncate", "delete from", "alter table"]):
        return "HIGH"
    if any(cmd in q_lower for cmd in ["update", "insert into", "create index"]):
        return "MEDIUM"
    return "LOW"

def _generate_optimization_hints(insights):
    """Manual, advisory-only optimization hints (Simplified)."""
    hints = []
    
    for scan in insights["seq_scans"]:
        if scan["filter"]:
            table_name = scan["table"]
            col = scan["filter"].split("=")[0].strip() if "=" in scan["filter"] else "id"
            idx_name = f"idx_{table_name.split('.')[-1]}_{int(time.time()) % 1000}"
            hints.append(f"Sequential Scan on '{table_name}'. Consider index on '{col}': CREATE INDEX CONCURRENTLY {idx_name} ON {table_name} ({col});")
            
    if len(insights["seq_scans"]) > 0 and len(insights["index_scans"]) == 0:
        if any(j for j in insights["joins"]):
            hints.append(f"High Cost Joins on {insights['seq_scans'][0]['table']}. Suggest: ANALYZE {insights['seq_scans'][0]['table']};")

    return hints

def execute_raw_query(query: str):
    if not query.strip():
        return {"success": False, "error": "Query cannot be empty."}
        
    start_time = time.time()
    try:
        config = load_config()
        is_sqlite = config.get("db_type") == "sqlite"
        with get_connection() as conn:
            with conn.cursor() as cursor:
                if not is_sqlite:
                    cursor.execute("SET statement_timeout = '10s';")
                cursor.execute(query)
                
                duration = (time.time() - start_time) * 1000
                performance_tier = "FAST"
                if duration > 200:
                    performance_tier = "SLOW"
                elif duration > 100:
                    performance_tier = "MEDIUM"

                affected_rows = cursor.rowcount
                is_truncated = False
                
                table_name = "Global"
                q_lower = query.lower().strip()
                try:
                    if "from" in q_lower:
                        table_name = q_lower.split("from")[1].strip().split()[0].replace('"', '').replace(";", "")
                    elif "update" in q_lower:
                        table_name = q_lower.split("update")[1].strip().split()[0].replace('"', '')
                    elif "into" in q_lower:
                        table_name = q_lower.split("into")[1].strip().split()[0].replace('"', '')
                except:
                    pass

                explain_summary = None
                optimization_hints = []
                if q_lower.startswith("select") and not is_sqlite:
                    try:
                        # Use a separate cursor to avoid overwriting the main result set
                        with conn.cursor() as assist_cursor:
                            assist_cursor.execute(f"EXPLAIN (FORMAT JSON) {query}")
                            plan_res = assist_cursor.fetchone()[0]
                            if plan_res and len(plan_res) > 0:
                                insights = _parse_explain_plan(plan_res[0]['Plan'])
                                optimization_hints = _generate_optimization_hints(insights)
                                
                                root_node = plan_res[0]['Plan']
                                explain_summary = f"{root_node['Node Type']} (Cost: {root_node['Total Cost']})"
                                if insights["seq_scans"]:
                                    explain_summary += f" | {len(insights['seq_scans'])} Seq Scans"
                    except:
                        pass

                risk_score = _calculate_risk(query)
                
                # Fetch data... (existing logic)
                data = []
                columns = []
                if cursor.description:
                    raw_columns = [desc[0] for desc in cursor.description]
                    seen_counts = {}
                    for col in raw_columns:
                        if col not in seen_counts:
                            seen_counts[col] = 0
                            columns.append(col)
                        else:
                            seen_counts[col] += 1
                            columns.append(f"{col}_{seen_counts[col]}")

                    rows = cursor.fetchmany(1001) 
                    if len(rows) > 1000:
                        is_truncated = True
                        rows = rows[:1000]
                        
                    for row in rows:
                        mapped_row = dict(zip(columns, row))
                        sanitized_row = {k: _make_serializable(v) for k, v in mapped_row.items()}
                        data.append(sanitized_row)

                conn.commit()
                
                MetaService.add_history(
                    query=query, 
                    duration_ms=duration, 
                    affected_rows=affected_rows if affected_rows != -1 else 0,
                    success=True,
                    table_name=table_name,
                    performance_tier=performance_tier,
                    explain_summary=explain_summary,
                    optimization_hints=optimization_hints
                )
                
                return {
                    "success": True,
                    "columns": columns,
                    "data": data,
                    "affected_rows": affected_rows,
                    "is_truncated": is_truncated,
                    "execution_time_ms": round(duration, 2),
                    "performance_tier": performance_tier,
                    "explain_summary": explain_summary,
                    "optimization_hints": optimization_hints,
                    "risk_score": risk_score
                }
    except Exception as e:
        duration = (time.time() - start_time) * 1000
        MetaService.add_history(
            query=query, 
            duration_ms=duration, 
            affected_rows=0, 
            success=False, 
            error=str(e),
            performance_tier="FAST"
        )
        return {"success": False, "error": str(e), "execution_time_ms": round(duration, 2)}

def get_roles_permissions():
    """Fetches database roles and their associated table privileges."""
    try:
        config = load_config()
        if config.get("db_type") == "sqlite":
            return {"success": True, "roles": [], "privileges": []}
            
        conn = get_connection()
        cursor = conn.cursor()
        # Get Roles
        cursor.execute("""
            SELECT rolname, rolsuper, rolinherit, rolcreaterole, rolcreatedb, rolcanlogin 
            FROM pg_roles
            WHERE rolname NOT LIKE 'pg_%'
            ORDER BY rolname;
        """)
        roles_raw = cursor.fetchall()
        roles = []
        for r in roles_raw:
            roles.append({
                "name": r[0],
                "is_superuser": r[1],
                "can_inherit": r[2],
                "can_create_role": r[3],
                "can_create_db": r[4],
                "can_login": r[5]
            })
        
        # Get Table Privileges
        cursor.execute("""
            SELECT grantee, table_schema, table_name, privilege_type
            FROM information_schema.role_table_grants
            WHERE table_schema NOT IN ('information_schema', 'pg_catalog')
            ORDER BY grantee, table_schema, table_name;
        """)
        privs_raw = cursor.fetchall()
        privileges = []
        for p in privs_raw:
            privileges.append({
                "grantee": p[0],
                "schema": p[1],
                "table": p[2],
                "type": p[3]
            })
        cursor.close()
        conn.close()
        
        return {"success": True, "roles": roles, "privileges": privileges}
    except Exception as e:
        return {"success": False, "error": str(e)}

def get_schema_snapshot():
    """Captures a structural snapshot of all user tables for diffing."""
    try:
        config = load_config()
        if config.get("db_type") == "sqlite":
            return {"success": True, "snapshot": {}} # Simplified for SQLite
            
        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT table_schema, table_name, column_name, data_type, is_nullable
                    FROM information_schema.columns
                    WHERE table_schema NOT IN ('information_schema', 'pg_catalog')
                    ORDER BY table_schema, table_name, ordinal_position;
                """)
                rows = cursor.fetchall()
                
                snapshot = {}
                for s, t, c, dt, n in rows:
                    full_table = f"{s}.{t}"
                    if full_table not in snapshot:
                        snapshot[full_table] = []
                    snapshot[full_table].append({
                        "column": c,
                        "type": dt,
                        "nullable": n == "YES"
                    })
                return {"success": True, "snapshot": snapshot}
    except Exception as e:
        return {"success": False, "error": str(e)}


def execute_migration(query: str):
    """Executes a batch of migration statements within a single transaction."""
    try:
        config = load_config()
        is_sqlite = config.get("db_type") == "sqlite"
        with get_connection() as conn:
            with conn.cursor() as cursor:
                # Set a longer timeout for migrations (30s)
                if not is_sqlite:
                    cursor.execute("SET statement_timeout = '30s';")
                # Split by semicolon then execute each
                statements = [s.strip() for s in query.split(";") if s.strip()]
                for stmt in statements:
                    if not stmt.startswith("--"):
                        cursor.execute(stmt)
                conn.commit()
                return {"success": True, "message": f"Successfully executed {len(statements)} migration steps."}
    except Exception as e:
        return {"success": False, "error": str(e)}

def get_active_queries():
    """Monitors currently running queries on the database (Real-Time Awareness)."""
    try:
        config = load_config()
        if config.get("db_type") == "sqlite":
            return {"success": True, "active": []} # SQLite doesn't surface pg_stat_activity
            
        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT 
                        pid, 
                        query, 
                        now() - query_start AS duration, 
                        state, 
                        wait_event_type, 
                        wait_event
                    FROM pg_stat_activity 
                    WHERE state != 'idle' 
                      AND pid != pg_backend_pid()
                      AND query NOT LIKE '%%pg_stat_activity%%'
                    ORDER BY duration DESC;
                """)
                rows = cursor.fetchall()
                active = []
                for r in rows:
                    # Convert duration to seconds for easier frontend handling
                    dur_seconds = r[2].total_seconds() if r[2] else 0
                    active.append({
                        "pid": r[0],
                        "query": r[1],
                        "duration_s": round(dur_seconds, 2),
                        "state": r[3],
                        "wait_event": f"{r[4] or ''}: {r[5] or ''}".strip() or "None"
                    })
                return {"success": True, "active": active}
    except Exception as e:
        return {"success": False, "error": str(e)}

def validate_db_config(config: dict):
    try:
        if config.get("db_type") == "sqlite":
            db_file = config.get("db_file", "")
            if not os.path.exists(db_file):
                raise Exception(f"SQLite file not found at path: {db_file}")
            conn = sqlite3.connect(db_file)
            conn.close()
            return True
            
        conn = psycopg2.connect(
            host=config.get("db_host"),
            port=config.get("db_port"),
            user=config.get("db_user"),
            password=config.get("db_password"),
            dbname=config.get("db_name"),
            connect_timeout=5
        )
        conn.close()
        return True
    except Exception as e:
        raise Exception(f"Database connection failed: {str(e)}")

def _make_serializable(val):
    """
    Converts PostgreSQL specific types (Decimal, UUID, DateTime, Bytes)
    into JSON-serializable formats for the API.
    """
    import decimal
    import datetime
    import uuid

    if val is None:
        return None
    if isinstance(val, (datetime.datetime, datetime.date, datetime.time)):
        return val.isoformat()
    if isinstance(val, decimal.Decimal):
        return float(val)
    if isinstance(val, uuid.UUID):
        return str(val)
    if isinstance(val, (bytes, memoryview)):
        return "<binary data>"
    return val
