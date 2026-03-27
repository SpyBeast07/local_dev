# DevBeast 🚀 

A powerful, unified developer workspace dashboard that aggregates your entire local development environment into a single, beautiful interface. 

## 💡 The Core Idea
DevBeast brings together the functionality of Portainer, pgAdmin/Adminer, and system monitors into one sleek, glassmorphic UI. It provides immediate visibility and control over your stack:

One of the main reasons to build this tool was that existing solutions like PgAdmin and Adminer can often feel slow and clunky; DevBeast is designed to be a high-performance, developer-first alternative.

- 🐳 **Docker Containers**: Monitor active nodes, inspect running state, and view live formatting terminal logs.
- 🗄️ **Postgres Schemas**: Connect dynamically to PostgreSQL to explore schemas, tables, and raw data.
- 🧠 **Relations Graph**: Automatically format and visualize complex SQL Foreign Key relationships through an interactive, draggable network topology map.
- 🌐 **Running Services**: Instant system overview of all active network gateways and open ports running on your machine.

Everything operates together in real-time under a responsive, dark-mode native dashboard.

## ✨ Key Features
- **Centralized Dashboard**: High-level telemetry of your containers, database schemas, and open ports in one glance.
- **Dynamic Connection Configs**: No need to restart the server or modify `.env` files manually. Update your database connection string visually from the **Settings** panel via the frontend.
- **Interactive Schema Visualizer**: High-fidelity architectural graphs capable of auto-sorting complex table relationships into topological trees.
- **Fault-Tolerant Rendering**: Defensive frontend architecture handles Docker daemon or Postgres connection drops gracefully with stylized "Isolated/Void" empty-state UI instead of crashing.
- **Premium Aesthetics**: Fluid animations, glassmorphism overlays, custom scrollbars, and satisfying micro-interactions built with Svelte 5 and Tailwind CSS v4.

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
