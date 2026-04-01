# DevBeast 🚀

**DevBeast is a local-first DevOps control plane that gives developers real-time visibility and control over their entire development stack — containers, databases, and services — without context switching.**

## 😩 The Problem
Modern development requires juggling multiple fragmented tools:
- **Portainer/Docker Desktop** for containers
- **pgAdmin/Adminer** for databases
- **Terminal** for logs and ports
- **Mental mapping** for network dependencies

This leads to constant **context switching**, **slow debugging**, and **zero structural visibility**.

## ⚡ Why DevBeast?
DevBeast eliminates tool fragmentation by acting as a **centralized command center**.
- ⚡ **Unified Visibility**: See your entire infrastructure in a single pane of glass.
- 🧠 **Structural Intelligence**: Understand how a single SQL change impacts your services.
- 🚀 **High-Speed Control**: Kill ports, restart containers, and restore backups in seconds.

---

## 🧠 Structural Intelligence

### 🧬 Topological Dependency Graph
DevBeast builds a live map of your stack. Visualize the relationships between:
- **Containers ↔ Database Connections**
- **Database ↔ Port Mappings**
- **Table ↔ Table Foreign Keys**

### 💥 Impact Analysis (Blast Radius)
Before you `COMMIT`, DevBeast computes the structural fallout of your changes.
- **Dependency Detection**: Identify which tables, containers, and services are downstream of your query.
- **Severity Scoring**: Automatically classifies impact as **LOW**, **MEDIUM**, or **HIGH** based on infrastructure risk.

### 🔍 Query Trace Flow
Execute SQL and watch DevBeast visually highlight the "Blast Radius" in real-time on your dependency graph.

---

## 🚀 Portability Engine

### 📥 SQL Backup & Restore
DevBeast provides high-fidelity, container-native database portability.
- **Idempotent Snapshots**: Exports `.sql` dumps with `--clean` and `--if-exists` flags, ensuring snapshots are "Restore-Ready" for any environment.
- **Force Restore Layer**: Optionally wipe the `public` schema before restoration to resolve structural collisions with a single click.
- **Zero Host Dependencies**: Executes `pg_dump` and `psql` directly inside your containers via `docker exec`.

---

## 🧩 Control Plane Features

- 🔥 **Port Killer**: Surgically terminate active local ports without leaving the dashboard.
- 🛡️ **SQL Guardrails**: Prevents unsafe queries and enforces execution patterns like timeouts and row caps.
- ⚙️ **Smart Validation**: Configurations only commit when connectivity is verified.
- ✏️ **Inline Data Editing**: High-speed, typed manipulation of database records.
- 🧬 **Failure Visualization**: Instant visual feedback on broken connection paths or unhealthy containers.

---

## 🛠️ Tech Stack
- **Frontend**: SvelteKit (Svelte 5 Runes) + Tailwind CSS v4 + Vite + vis-network
- **Backend**: Python + FastAPI + Uvicorn + Psycopg2 + Subprocess Engine

---

## 🚀 Getting Started

### Prerequisites
- Python 3.9+
- Node.js 18+
- Docker Engine (Running locally)
- PostgreSQL Database

### 1. Start the Backend API

**Using `uv` (recommended):**
```bash
cd backend
uv venv venv
source venv/bin/activate
uv pip install -r requirements.txt
uvicorn main:app --reload
```

**Using `pip`:**
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
```
*Note: The backend runs natively on `http://127.0.0.1:8000`.*

### 2. Start the Frontend Application
```bash
cd frontend
npm install
npm run dev
```
*Note: Available at `http://localhost:5173`.*

### 3. Connect Your Environment
Navigate to the **⚙️ Settings** tab, input your database credentials, and commit the configuration to instantly unlock the **Dependency Graph** and **Impact Analysis** workspace.

---

*Built for high-performance developer experience (DX) and structural visibility.*
