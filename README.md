# DevBeast 🚀 

**DevBeast is a local-first DevOps control plane that gives developers real-time visibility and control over their entire development stack — containers, databases, and services — without context switching.**

## 😩 The Problem
Modern development requires juggling multiple tools:
- Docker containers in Portainer
- Databases in pgAdmin
- Logs in terminal
- Ports and services manually tracked

This leads to constant **context switching**, **slow debugging**, and **fragmented visibility** across your stack.

## ⚡ Why DevBeast?
DevBeast eliminates tool fragmentation by acting as a **local DevOps control plane**.
- ⚡ **Faster debugging** with unified logs and services in one view.
- 🧠 **Visual understanding** of complex database relationships.
- 🚀 **Real-time visibility** without ever switching tools.

## 💡 The Control Plane Objective
DevBeast isn't just a dashboard; it's a centralized command center that eliminates the clunky, slow experience of legacy tools. 

One of the primary drivers for building DevBeast was the frustration with **PgAdmin** and **Adminer**—which often feel sluggish and outdated. DevBeast is engineered for high-performance, real-time interaction:

- 🐳 **Docker Engine**: Direct control over containers, images, and volumes with live-streaming logs and telemetry.
- 🗄️ **Postgres Explorer**: High-speed schema exploration and data manipulation, designed to be significantly faster than traditional web-based DB managers.
- 🧠 **Relations Graph**: Instant visualization of complex SQL Foreign Key relationships through an interactive, topological map.
- 🌐 **Network Gates**: Real-time monitoring and surgical termination of active local ports and services.

## 🧩 Advanced Features
- 🔥 **Port Killer**  
  Instantly free blocked ports without leaving the dashboard.
- 🛡️ **SQL Guardrails**  
  Prevent unsafe queries and enforce safe execution patterns (timeouts & row caps).
- ⚙️ **Smart Connection Validation**  
  Settings only confirm when database connectivity is verified.
- 🧬 **Typed Data Rendering**  
  Automatically formats fields (JSON, date, UUID, etc.) for clarity.
- ✏️ **Inline Data Editing**  
  Double-click cells to edit database records directly.

## 🎯 Who is this for?
- **Full-stack developers** managing local environments.
- **Backend engineers** working with Docker + PostgreSQL.
- **Startup teams** needing lightweight DevOps visibility.

## 🛠️ Tech Stack
- **Frontend**: SvelteKit (Svelte 5 Runes) + Tailwind CSS v4 + Vite + Axios + vis-network
- **Backend**: Python + FastAPI + Uvicorn + Psycopg2 + Local Subprocess execution

## 🚀 Getting Started

### Prerequisites
- Python 3.9+
- Node.js 18+
- Docker Engine (Running locally in the background)
- PostgreSQL Database (Locally or remotely accessible)

### 1. Start the Backend API

**Using `uv` (recommended):**
```bash
cd backend

# Create and activate a virtual environment
uv venv venv
source venv/bin/activate

# Install dependencies
uv pip install -r requirements.txt

# Start the FastAPI server
uvicorn main:app --reload
```

**Using `pip`:**
```bash
cd backend

# Create and activate a virtual environment (optional but recommended)
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start the FastAPI server
uvicorn main:app --reload
```
*Note: The backend runs natively on `http://127.0.0.1:8000`. Upon startup, it will auto-generate a `config.json` state file to handle your dynamic database credentials based on your environment.*

### 2. Start the Frontend Application
```bash
cd frontend

# Install node dependencies
npm install

# Start the SvelteKit development server
npm run dev
```
*Note: The frontend will be available at `http://localhost:5173`. Open this URL in your browser to access the DevBeast interface.*

### 3. Connect Your Environment
Once the dashboard opens, navigate to the **⚙️ Settings** tab. Input your target PostgreSQL credentials and commit the configuration to instantly unlock the Database Schema tables and the Relations architecture graph!

---

*Built with a focus on developer experience (DX) and premium UI/UX workflow efficiency.*
