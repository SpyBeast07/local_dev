# DevBeast 🚀

**DevBeast is a local-first DevOps control plane that gives developers structural visibility and high-speed control over their entire development stack — containers, databases, and services — in a single pane of glass.**

![DevBeast Dashboard Mockup](docs/images/dashboard_mockup.png)

## 😩 The Problem
Modern development requires juggling multiple fragmented tools:
- **Portainer/Docker Desktop** for containers
- **pgAdmin/Adminer** for databases
- **Terminal** for logs and ports
- **Mental mapping** for network dependencies

This leads to constant **context switching**, **slow debugging**, and **zero structural visibility**.

## 🧬 Why DevBeast? (The Developer-Trust-First Approach)
DevBeast eliminates tool fragmentation by acting as a **centralized command center** designed for developers who demand full control and transparency.
- ⚡ **Unified Visibility**: See your entire infrastructure in a single pane of glass.
- 🧠 **Architectural Intelligence**: Identify performance hotspots and structural volatility through manual, advisory-only insights.
- 🛡️ **Transparent Execution**: No background "smart" loops. All schema migrations and optimizations are manual, explicit, and developer-verified.
- 🚀 **High-Speed Control**: Kill ports, restart containers, and restore backups in seconds.

---

## 🏗️ The Four Diagnostic Pillars

DevBeast organizes infrastructure management into four distinct, human-in-the-loop pillars:

### 📡 Architecture (Performance Insights)
View aggregated performance patterns and structural volatility. Identify the slowest queries and most-impacted tables across your last 100 executions without background telemetry.

### 🌓 Auditor (Audit & Migrations)
Manual structural comparative analysis. Review schema diffs and preview migration SQL with explicit risk indicators before applying changes.

### 📜 History (Audit Logs)
A transparent, searchable record of every segment executed. Audit execution times, affected rows, and table-level impact to debug regressions fast.

### 📝 Library (Snippets)
A collection of SQL utility assets and favorites. Quickly re-use complex queries or structural templates without leaving the workspace.

---

## 🧬 Real-World Workflows

### 🔍 Debug a Broken API
Click a failed service → instantly see:
- Connected database and specific schemas
- Dependent tables and record flow
- Failing query paths via visual trace context

### 🛡️ Safe Schema Changes
Before you `ALTER TABLE` or `DROP`:
- View the **Impact Radius** of your change
- Identify affected services and downstream containers
- Review **Optimization Insights**: Manual SQL suggestions (Add Index, Analyze) that you can copy or send directly to the editor for validation.

### ♻️ Reset & Recover Fast
- **Backup → Experiment → Restore**: Create idempotent snapshots with a single click before risky refactoring.
- **Reset & Reseed**: Instantly wipe the database and reseed with clean test data for rapid development cycles.

---

## 🥊 Why Not Existing Tools?

| Problem | Existing Tools | **DevBeast** |
| :--- | :--- | :--- |
| **Full Stack Visibility** | Fragmented (Portainer + pgAdmin) | **Unified Pane of Glass** |
| **Dependency Mapping** | Manual / Mental | **Live Topological Graph** |
| **Optimization** | Advisory but Clunky | **Manual-Action Advisory (Copy/Send)** |
| **Recovery** | Complex manual dumps | **One-Click Snapshots** |
| **Context Switching** | Highly required | **Completely Eliminated** |

---

## 🧠 Structural Intelligence

### 🗺️ Live Dependency Mesh
DevBeast builds a live map of your stack. Visualize the relationships between:
- **Containers ↔ Database Connections**
- **Database ↔ Port Mappings**
- **Table ↔ Table Foreign Keys**

### ⌨️ Schema-Aware SQL Autocomplete
A professional-grade, high-performance SQL editor integrated into the core dashboard.
- **Context-Aware Suggestions**: Ranks completions based on cursor position (Tables after `FROM`, Columns after `alias.`).
- **Alias Resolution**: Dynamically parses queries to resolve table aliases and multi-table JOINs.
- **Live Metadata Caching**: powered by an in-memory schema store.

### 💥 Impact Analysis (Blast Radius)
Before you `COMMIT`, DevBeast computes the structural fallout of your changes.
- **Dependency Detection**: Identify which tables, containers, and services are downstream of your query.
- **Severity Scoring**: Automatically classifies impact as **LOW**, **MEDIUM**, or **HIGH** based on infrastructure risk.

---

## 🛡️ Data Safety & Recovery

### 📥 Idempotent Backup & Restore
- **Snapshot Logic**: Exports `.sql` dumps with `--clean` and `--if-exists` flags, ensuring snapshots are "Restore-Ready".
- **Force Restore Layer**: Optionally wipe the `public` schema before restoration to resolve structural collisions.
- **Zero Host Dependencies**: Executes directly inside your containers via `docker exec`.

### 🧪 Reset & Reseed Engine
- Instantly reset your database to a verified baseline.
- Automate the seeding of test data for high-speed debugging workflows.

---

## 🛠️ Tech Stack
- **Frontend**: SvelteKit (Svelte 5 Runes) + Tailwind CSS v4 + CodeMirror 6 + Vis-Network
- **Backend**: Python + FastAPI + Psycopg2 + Pandas + PyDBML
- **Execution Engine**: Local Docker Engine + Subprocess Wrapper

---

## 🚀 Getting Started

### Prerequisites
- Python 3.12+
- Node.js 20+
- Docker Engine (Running locally)
- PostgreSQL Database

### 1. Start the Backend API
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
```
*Note: Available at `http://127.0.0.1:8000`.*

### 2. Start the Frontend Application
```bash
cd frontend
npm install
npm run dev
```
*Note: Available at `http://localhost:5173`.*

### 3. Connect Your Environment
Navigate to the **⚙️ Settings** tab, input your database credentials, and commit to instantly unlock the **Dependency Graph** workspace.

---

> [!IMPORTANT]
> **Developer Control**: DevBeast is an **advisory** platform. It provides high-speed structural data and optimization suggestions, but the final decision to execute and verify remains entirely with the developer.

## 🚀 Try It Out

Spin up your local stack and see your system like never before. 

If you’ve ever struggled with understanding database relationships, debugging across services, or safely modifying schemas — **DevBeast will change how you work.**

---
*Built for high-performance developer experience (DX) and structural visibility.*
