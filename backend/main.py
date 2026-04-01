from fastapi import FastAPI, Request
from dotenv import load_dotenv
import os
import json
from pydantic import BaseModel
from services.docker import (
    get_containers, get_container_logs, manage_container, get_container_stats,
    get_images, pull_image, delete_image, get_volumes, get_networks, deploy_container
)
from services.ports import get_ports, kill_port_process
from services.db import get_tables, get_table_data, get_relations, load_config, CONFIG_FILE, execute_raw_query, get_table_structure, insert_row, update_row, delete_row

load_dotenv()

app = FastAPI()

@app.get("/")
def root():
    return {"message": "Backend is running 🚀"}

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

class QueryPayload(BaseModel):
    query: str

@app.post("/db/query")
def run_query(payload: QueryPayload):
    return execute_raw_query(payload.query)

@app.get("/config/db")
def get_db_config():
    return load_config()

@app.post("/config/db")
async def update_db_config(request: Request):
    data = await request.json()
    with open(CONFIG_FILE, "w") as f:
        json.dump(data, f, indent=4)
    return {"message": "Config updated"}


from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)