import psycopg2
import os
import json
from dotenv import load_dotenv

load_dotenv()

CONFIG_FILE = "config.json"

def load_config():
    if not os.path.exists(CONFIG_FILE):
        default_config = {
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
        return json.load(f)

def get_connection():
    config = load_config()
    return psycopg2.connect(
        host=config["db_host"],
        port=config["db_port"],
        user=config["db_user"],
        password=config["db_password"],
        dbname=config["db_name"]
    )

def get_tables():
    try:
        conn = get_connection()
        cursor = conn.cursor()

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

def get_table_structure(table_name: str):
    try:
        schema, bare_table = _parse_table_ref(table_name)
        conn = get_connection()
        cursor = conn.cursor()

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
        schema, bare_table = _parse_table_ref(table_name)
        qualified = f'"{schema}"."{bare_table}"'
        conn = get_connection()
        cursor = conn.cursor()

        # Safely query column names to prevent SQL injection in sort_col
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
        query = f"SELECT * FROM {qualified} {order_clause} LIMIT %s OFFSET %s;"
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

def insert_row(table_name: str, payload: dict):
    if not payload:
        return {"success": False, "error": "Empty payload injected."}
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Filter out empty strings to allow Postgres defaults (like SERIAL) to trigger
        # Also stringify dicts/lists for psycopg2 adaptation
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
        qualified = f'"{schema}"."{bare_table}"'
        col_string = ", ".join([f'"{c}"' for c in columns])
        val_placeholders = ", ".join(["%s"] * len(values))

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
        conn = get_connection()
        cursor = conn.cursor()
        
        set_cols = []
        values = []
        for k, v in payload.items():
            # If front-end passes empty string for an existing row edit, assume they meant NULL
            if v == "":
                v = None
            
            # Stringify dicts/lists for psycopg2 adaptation
            if isinstance(v, (dict, list)):
                v = json.dumps(v)
                
            set_cols.append(f'"{k}" = %s')
            values.append(v)
            
        where_cols = []
        for k, v in primary_keys.items():
            # Stringify dicts/lists for psycopg2 adaptation if PK is JSON
            if isinstance(v, (dict, list)):
                v = json.dumps(v)
            where_cols.append(f'"{k}" = %s')
            values.append(v)
            
        schema, bare_table = _parse_table_ref(table_name)
        qualified = f'"{schema}"."{bare_table}"'
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
        conn = get_connection()
        cursor = conn.cursor()
        
        where_cols = []
        values = []
        for k, v in primary_keys.items():
            where_cols.append(f'"{k}" = %s')
            values.append(v)
            
        schema, bare_table = _parse_table_ref(table_name)
        qualified = f'"{schema}"."{bare_table}"'
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
        conn = get_connection()
        cursor = conn.cursor()

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

def execute_raw_query(query: str):
    if not query.strip():
        return {"success": False, "error": "Query cannot be empty."}
        
    try:
        # Use with context managers to ensure connection and cursor are always closed
        with get_connection() as conn:
            with conn.cursor() as cursor:
                # 1. Set a statement timeout for the session (10 seconds)
                cursor.execute("SET statement_timeout = '10s';")
                
                # 2. Execute the user's query
                cursor.execute(query)
                
                data = None
                columns = None
                affected_rows = cursor.rowcount
                is_truncated = False
                
                if cursor.description:
                    raw_columns = [desc[0] for desc in cursor.description]
                    
                    # De-duplicate column names to prevent key collisions in JSON/dicts
                    columns = []
                    seen_counts = {}
                    for col in raw_columns:
                        if col not in seen_counts:
                            seen_counts[col] = 0
                            columns.append(col)
                        else:
                            seen_counts[col] += 1
                            columns.append(f"{col}_{seen_counts[col]}")

                    # 3. Limit to 1000 rows to prevent memory exhaustion
                    rows = cursor.fetchmany(1001) 
                    
                    if len(rows) > 1000:
                        is_truncated = True
                        rows = rows[:1000]
                        
                    data = []
                    for row in rows:
                        # Use our de-duplicated 'columns' for the dictionary keys
                        mapped_row = dict(zip(columns, row))
                        sanitized_row = {k: _make_serializable(v) for k, v in mapped_row.items()}
                        data.append(sanitized_row)

                
                # Commit any data mutations
                conn.commit()
                
                return {
                    "success": True,
                    "columns": columns,
                    "data": data,
                    "affected_rows": affected_rows,
                    "is_truncated": is_truncated
                }
    except Exception as e:
        return {"success": False, "error": str(e)}


def validate_db_config(config: dict):
    try:
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
