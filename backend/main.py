from fastapi import FastAPI, Request, UploadFile, File, Query, Form
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os
import json
import io
from pydantic import BaseModel
from typing import Optional, Annotated
from services.docker import (
    get_containers, get_container_logs, manage_container, get_container_stats,
    get_images, pull_image, delete_image, get_volumes, get_networks, deploy_container,
    get_dependency_graph, get_impact_analysis, trace_query
)
from services.ports import get_ports, kill_port_process
from services.db import get_tables, get_table_data, get_relations, load_config, CONFIG_FILE, execute_raw_query, get_table_structure, insert_row, update_row, delete_row, validate_db_config, truncate_tables, get_full_schema, get_roles_permissions, get_schema_snapshot
from services.backups import export_db, restore_db, export_table
from services.seeding import run_seed_script
from services.meta import MetaService

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"message": "Backend is running 🚀"}

@app.get("/system/dependency-graph")
def dependency_graph():
    return get_dependency_graph()

class QueryRequest(BaseModel):
    query: str

@app.post("/system/trace-query")
async def register_trace_query(request: QueryRequest):
    return trace_query(request.query)

@app.get("/system/impact-analysis")

def impact_analysis(table: str):
    return get_impact_analysis(table)

@app.get("/containers")
def containers():
    return get_containers()

@app.get("/containers/{container_id}/logs")
def container_logs(container_id: str):
    return get_container_logs(container_id)

@app.post("/containers/{container_id}/action")
async def container_action(container_id: str, request: Request):
    data = await request.json()
    action = data.get("action")
    return manage_container(container_id, action)

@app.get("/containers/{container_id}/stats")
def container_stats(container_id: str):
    return get_container_stats(container_id)

@app.get("/images")
def images():
    return get_images()

class PullPayload(BaseModel):
    image: str

@app.post("/images/pull")
def image_pull(payload: PullPayload):
    return pull_image(payload.image)

@app.delete("/images/{image_id}")
def image_delete(image_id: str):
    return delete_image(image_id)

@app.get("/volumes")
def volumes():
    return get_volumes()

@app.get("/networks")
def networks():
    return get_networks()

class DeployPayload(BaseModel):
    image: str
    name: str = ""
    ports: list[str] = []
    envs: list[str] = []

@app.post("/containers/deploy")
def container_deploy(payload: DeployPayload):
    return deploy_container(payload.image, payload.name, payload.ports, payload.envs)

@app.get("/ports")
def ports():
    return get_ports()

class KillPortPayload(BaseModel):
    pid: str

@app.post("/ports/kill")
def kill_port(payload: KillPortPayload):
    return kill_port_process(payload.pid)

@app.get("/db/tables")
def tables():
    return get_tables()

@app.get("/db/schema")
def db_schema():
    return get_full_schema()

@app.get("/db/table/{table_name}")
def table_data(table_name: str, limit: int = 20, offset: int = 0, sort_col: str = None, sort_dir: str = "asc"):
    return get_table_data(table_name, limit, offset, sort_col, sort_dir)

@app.get("/db/table/{table_name}/structure")
def table_structure(table_name: str):
    return get_table_structure(table_name)

class RowInsertPayload(BaseModel):
    payload: dict

class RowUpdatePayload(BaseModel):
    primary_keys: dict
    payload: dict

@app.post("/db/table/{table_name}/row")
def insert_table_row(table_name: str, data: RowInsertPayload):
    return insert_row(table_name, data.payload)

@app.put("/db/table/{table_name}/row")
def update_table_row(table_name: str, data: RowUpdatePayload):
    return update_row(table_name, data.primary_keys, data.payload)

@app.delete("/db/table/{table_name}/row")
async def delete_table_row(table_name: str, request: Request):
    data = await request.json()
    return delete_row(table_name, data.get("primary_keys", {}))

@app.get("/db/relations")
def relations():
    return get_relations()

@app.get("/db/table/{table_name}/export")
def export_table_data(table_name: str, format: str = "json", columns: str = None):
    """Export a single table in the specified format.
    - format: json | csv | excel | dbml
    - columns: optional comma-separated list of column names to include
    """
    col_list = [c.strip() for c in columns.split(",") if c.strip()] if columns else None
    result = export_table(table_name, format, col_list)
    if not result["success"]:
        return JSONResponse(status_code=500, content=result)
    data = result["data"]
    if isinstance(data, str):
        data = data.encode("utf-8")
    return StreamingResponse(
        io.BytesIO(data),
        media_type=result["mime"],
        headers={"Content-Disposition": f"attachment; filename={result['filename']}"}
    )

class QueryPayload(BaseModel):
    query: str

@app.post("/db/query")
def run_query(payload: QueryPayload):
    return execute_raw_query(payload.query)

@app.get("/db/history")
def get_query_history():
    return {"success": True, "history": MetaService.get_history()}

@app.get("/db/snippets")
def get_snippets():
    return {"success": True, "snippets": MetaService.get_snippets()}

class SnippetPayload(BaseModel):
    name: str
    query: str
    tags: list[str] = []

@app.post("/db/snippets")
def save_snippet(payload: SnippetPayload):
    MetaService.save_snippet(payload.name, payload.query, payload.tags)
    return {"success": True}

@app.delete("/db/snippets/{snippet_id}")
def delete_snippet(snippet_id: str):
    MetaService.delete_snippet(snippet_id)
    return {"success": True}

@app.get("/db/roles-permissions")
def db_roles_permissions():
    return get_roles_permissions()

class SnapshotPayload(BaseModel):
    name: str

@app.post("/db/schema/snapshot")
def capture_snapshot(payload: SnapshotPayload):
    res = get_schema_snapshot()
    if res["success"]:
        MetaService.save_snapshot(payload.name, res["snapshot"])
    return res

@app.get("/db/schema/snapshots")
def get_snapshots():
    return {"success": True, "snapshots": MetaService.get_snapshots()}

@app.get("/db/backup")
def get_db_backup(format: str = "sql"):
    result = export_db(format)
    if not result["success"]:
        return JSONResponse(status_code=500, content=result)
    
    data = result["data"]
    if isinstance(data, str):
        data = data.encode("utf-8")
        
    return StreamingResponse(
        io.BytesIO(data),
        media_type=result["mime"],
        headers={"Content-Disposition": f"attachment; filename={result['filename']}"}
    )


@app.post("/db/restore")
async def post_db_restore(file: UploadFile = File(...), clean: bool = Query(False)):
    content = await file.read()
    # Let the service handle format detection via filename
    return restore_db(content, file.filename, clean_schema=clean)

@app.post("/db/reset-reseed")
async def reset_reseed(
    mode: str = Form(...),
    backup: bool = Form(True),
    should_seed: bool = Form(True),
    seed_file: Optional[UploadFile] = File(None)
):
    """Unified action to reset and reseed the database."""
    results = {}
    
    # 1. Backup if requested
    if backup:
        backup_res = export_db("sql")
        results["backup"] = backup_res
        if not backup_res["success"]:
            return JSONResponse(status_code=500, content={"success": False, "error": f"Auto-backup failed: {backup_res['error']}"})
    
    # 2. Reset
    if mode == "full":
        reset_res = restore_db(b"", "empty_reset.sql", clean_schema=True)
        results["reset"] = reset_res
    elif mode == "data-only":
        reset_res = truncate_tables()
        results["reset"] = reset_res
    else:
        return JSONResponse(status_code=400, content={"success": False, "error": "Invalid reset mode."})
    
    if not reset_res["success"]:
        return JSONResponse(status_code=500, content={"success": False, "error": f"Reset failed: {reset_res['error']}"})
        
    # 3. Reseed (Optional)
    if should_seed:
        sql_content = await seed_file.read() if seed_file else None
        seed_res = run_seed_script(sql_content)
        results["seed"] = seed_res
    else:
        results["seed"] = {"success": True, "message": "Seeding skipped by user."}
        
    return {"success": True, "details": results}

@app.get("/config/db")
def get_db_config():
    return load_config()

@app.post("/config/db")
async def update_db_config(request: Request):
    data = await request.json()
    try:
        # Validate before saving
        validate_db_config(data)
        
        with open(CONFIG_FILE, "w") as f:
            json.dump(data, f, indent=4)
        return {"success": True, "message": "Config updated"}
    except Exception as e:
        return JSONResponse(
            status_code=400,
            content={"success": False, "error": str(e)}
        )