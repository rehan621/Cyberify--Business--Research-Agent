# 🔬 Cyberify Autonomous Research Agent

> An AI-powered autonomous business research agent built for the Cyberify AI Engineer Technical Assessment.

![Python](https://img.shields.io/badge/Python-3.10+-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-green)
![LangGraph](https://img.shields.io/badge/LangGraph-0.2.28-purple)
![Streamlit](https://img.shields.io/badge/Streamlit-1.38-red)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-blue)
![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4o--mini-orange)
![Tavily](https://img.shields.io/badge/Tavily-Web%20Search-teal)
![ChromaDB](https://img.shields.io/badge/ChromaDB-Vector%20DB-green)

---

## 📋 Overview

Cyberify Research Agent is a production-grade, full-stack AI application that autonomously conducts business research using a multi-agent LangGraph workflow. It searches the web in real-time, retrieves information from uploaded documents via RAG, validates findings through a reflection loop, and generates professional research reports — all with a live execution pipeline display.

---

## ✨ Features

| Feature               | Description                                           | Status |
| --------------------- | ----------------------------------------------------- | ------ |
| 🔐 Authentication     | JWT-based signup/login with bcrypt password hashing   | ✅     |
| 🤖 Multi-Agent System | 4 LangGraph agents with conditional routing & handoff | ✅     |
| 🔄 Reflection Loop    | Verifier → Researcher retry on low confidence (<70%)  | ✅     |
| 🛠️ Tool Calling       | Web Search, Calculator, File Retrieval (3 tools)      | ✅     |
| 📚 RAG Pipeline       | PDF/DOCX/TXT upload + ChromaDB vector search          | ✅     |
| 🧠 Stateful Memory    | PostgreSQL-backed memory persistence across sessions  | ✅     |
| 📁 Workspaces         | Organize research into project folders                | ✅     |
| ⚡ Live Pipeline      | Real-time agent progress with tool tracking           | ✅     |
| 💬 AI Chat Mode       | General / Research Report / Document RAG chat         | ✅     |
| 📄 PDF Export         | Professional branded PDF with query-based filename    | ✅     |
| 📝 Markdown Export    | Markdown format with YAML metadata header             | ✅     |
| 🗑️ Delete             | Delete research queries and workspaces from UI + DB   | ✅     |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                  Streamlit Frontend  (Port 8501)                 │
│      Login · Dashboard · Workspaces · Documents · Chat          │
└────────────────────────┬────────────────────────────────────────┘
                         │ HTTP REST API
┌────────────────────────▼────────────────────────────────────────┐
│                  FastAPI Backend  (Port 8000)                    │
│   /auth · /research · /workspaces · /documents · /export        │
│   Swagger UI available at: http://localhost:8000/docs            │
└────────────────────────┬────────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────────┐
│                    LangGraph Workflow                            │
│                                                                 │
│  🧠 Planner ──► 🔍 Researcher ──► ✅ Verifier                  │
│                      │                   │                      │
│               ┌──────┴──────┐     conf ≥ 0.7 ──► 📝 Reporter  │
│               │ 🔍 Web Search│     conf < 0.7 ──► 🔄 Retry     │
│               │ 🔢 Calculator│           │         (max 2x)    │
│               │ 📂 File RAG  │           └─────────────────┘   │
│               └─────────────┘                                   │
└────────────────────────┬────────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────────┐
│                       Data Layer                                │
│   PostgreSQL (6 tables)        ChromaDB (Vector Store)          │
│   users · workspaces           PDF · DOCX · TXT embeddings      │
│   research_history             text-embedding-3-small           │
│   documents · checkpoints                                       │
│   chat_messages                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🛠️ Tech Stack

| Layer          | Technology              | Purpose                   |
| -------------- | ----------------------- | ------------------------- |
| Frontend       | Streamlit               | Interactive web UI        |
| Backend        | FastAPI + Uvicorn       | REST API server           |
| AI Agents      | LangGraph + LangChain   | Multi-agent orchestration |
| Language Model | OpenAI GPT-4o-mini      | Research & analysis       |
| Web Search     | Tavily API              | Real-time web search      |
| Database       | PostgreSQL + SQLAlchemy | Data persistence          |
| Vector Store   | ChromaDB                | RAG document search       |
| Authentication | JWT + bcrypt            | Secure auth               |
| PDF Generation | ReportLab               | Professional reports      |
| Doc Processing | PyPDF + python-docx     | File parsing              |

---

## 📁 Project Structure

```
cyberify-task/
├── README.md
├── .env.example
├── .gitignore
├── .dockerignore
├── Dockerfile.backend
├── Dockerfile.frontend
├── docker-compose.yml
│
├── backend/
│   ├── main.py                    # FastAPI entry point
│   ├── requirements.txt
│   │
│   ├── database/
│   │   ├── models.py              # SQLAlchemy ORM models (6 tables)
│   │   └── connection.py          # DB session management
│   │
│   ├── auth/
│   │   └── jwt_handler.py         # JWT token + bcrypt hashing
│   │
│   ├── agents/
│   │   ├── graph.py               # LangGraph workflow + conditional routing
│   │   ├── state.py               # Shared TypedDict state
│   │   ├── planner.py             # Planner agent
│   │   ├── researcher.py          # Researcher agent + tool calling
│   │   ├── verifier.py            # Verifier agent + reflection loop
│   │   ├── reporter.py            # Reporter agent + Pydantic output
│   │   └── schemas.py             # Pydantic structured models
│   │
│   ├── tools/
│   │   └── research_tools.py      # Web Search, Calculator, File Retrieval
│   │
│   ├── memory/
│   │   ├── checkpointer.py        # PostgreSQL memory persistence
│   │   └── progress_tracker.py    # Live agent progress tracking
│   │
│   ├── rag/
│   │   └── rag_pipeline.py        # ChromaDB + document processing
│   │
│   └── api/
│       ├── auth_routes.py         # /api/auth
│       ├── research_routes.py     # /api/research
│       ├── workspace_routes.py    # /api/workspaces
│       ├── document_routes.py     # /api/documents
│       └── export_routes.py       # /api/export (PDF + Markdown)
│
├── frontend/
│   ├── app.py                     # Login / Signup page
│   ├── api_client.py              # API helper functions
│   ├── requirements.txt
│   └── pages/
│       ├── 1_Dashboard.py         # Research interface + live pipeline
│       ├── 2_Workspaces.py        # Workspace management
│       ├── 3_Documents.py         # Document upload + RAG indexing
│       └── 4_Chat.py              # AI Chat (3 modes + history)
│
└── database/
    └── schema.sql                 # PostgreSQL schema (6 tables)
```

---

## 🚀 Installation & Setup

### Prerequisites

- Python 3.10+
- PostgreSQL 15+
- OpenAI API Key → https://platform.openai.com
- Tavily API Key → https://app.tavily.com (free plan available)

---

### Step 1 — Clone Repository

```bash
git clone https://github.com/yourusername/cyberify-research-agent.git
cd cyberify-research-agent
```

### Step 2 — Create Virtual Environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Mac/Linux
source venv/bin/activate
```

### Step 3 — Install Dependencies

```bash
# Backend dependencies
pip install -r backend/requirements.txt

# Frontend dependencies
pip install -r frontend/requirements.txt
```

### Step 4 — Configure Environment Variables

```bash
cp .env.example .env
```

Edit `.env` with your API keys:

```env
# OpenAI
OPENAI_API_KEY=sk-your-openai-key-here

# Tavily Web Search
TAVILY_API_KEY=tvly-your-tavily-key-here

# PostgreSQL
DATABASE_URL=postgresql://postgres:yourpassword@localhost:5432/cyberify_db

# JWT Authentication
SECRET_KEY=your-random-secret-key-minimum-32-characters
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
```

### Step 5 — Create PostgreSQL Database

```bash
psql -U postgres
```

```sql
CREATE DATABASE cyberify_db;
\q
```

### Step 6 — Start the Application

**Terminal 1 — Backend:**

```bash
uvicorn backend.main:app --reload
```

Expected output:

```
[Graph] ✅ LangGraph compiled with MemorySaver + PostgreSQL persistence
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000
```

**Terminal 2 — Frontend:**

```bash
cd frontend
streamlit run app.py
```

Expected output:

```
You can now view your Streamlit app in your browser.
Local URL: http://localhost:8501
```

---

## 🐳 Docker Setup

Run the entire application with a single command:

```bash
# Build and start all services
docker-compose up --build

# Run in background
docker-compose up --build -d

# Stop all services
docker-compose down
```

Services started automatically:

- PostgreSQL database on port 5432
- FastAPI backend on port 8000
- Streamlit frontend on port 8501

---

## 🌐 Access URLs

| Service        | URL                         | Description              |
| -------------- | --------------------------- | ------------------------ |
| 🎨 Frontend    | http://localhost:8501       | Streamlit web UI         |
| 📡 Backend API | http://localhost:8000       | FastAPI server           |
| 📚 API Docs    | http://localhost:8000/docs  | Swagger UI (interactive) |
| 📘 API Redoc   | http://localhost:8000/redoc | ReDoc documentation      |

---

## 🤖 LangGraph Workflow

### Agent Pipeline

```
User Query
    │
    ▼
🧠 Planner Agent
   └── Decomposes query into 3-5 targeted sub-questions
    │
    ▼
🔍 Researcher Agent (with Tool Calling)
   ├── 🔍 web_search_tool    → Tavily real-time web search
   ├── 🔢 calculator_tool    → Financial calculations & percentages
   └── 📂 file_retrieval_tool → ChromaDB RAG search on uploaded docs
    │
    ▼
✅ Verifier Agent (Conditional Routing)
   ├── confidence ≥ 0.70 → Reporter Agent ✅
   └── confidence < 0.70 → Researcher (retry, max 2x) 🔄
    │
    ▼
📝 Reporter Agent
   └── Generates structured Pydantic report (FinalReport model)
```

### Mandatory Requirements Implemented

| Requirement         | Implementation               | File                     |
| ------------------- | ---------------------------- | ------------------------ |
| Conditional Routing | `route_after_verifier()`     | `agents/graph.py`        |
| Tool Calling        | `bind_tools()` with 3 tools  | `agents/researcher.py`   |
| Agent Handoff       | LangGraph edges              | `agents/graph.py`        |
| Memory Persistence  | MemorySaver + PostgreSQL     | `memory/checkpointer.py` |
| Reflection Loop     | Verifier → Researcher retry  | `agents/verifier.py`     |
| Structured Output   | Pydantic `FinalReport` model | `agents/schemas.py`      |

---

## 🗄️ Database Schema

```sql
users            -- User accounts with JWT auth
workspaces       -- Research project folders
research_history -- All queries, reports, confidence scores
documents        -- Uploaded file metadata + ChromaDB references
checkpoints      -- LangGraph stateful memory (PostgreSQL persistence)
chat_messages    -- AI chat history across all 3 chat modes
```

---

## 📡 API Documentation

Full interactive API documentation available at: **http://localhost:8000/docs**

### Key Endpoints

| Method | Endpoint                      | Description                     |
| ------ | ----------------------------- | ------------------------------- |
| POST   | `/api/auth/signup`            | Register new user               |
| POST   | `/api/auth/login`             | Login → get JWT token           |
| GET    | `/api/auth/me`                | Get current user profile        |
| POST   | `/api/research/start`         | Start autonomous research       |
| GET    | `/api/research/status/{id}`   | Get research status + report    |
| GET    | `/api/research/progress/{id}` | Live agent progress (polling)   |
| GET    | `/api/research/history`       | All past research queries       |
| DELETE | `/api/research/{id}`          | Delete research record          |
| POST   | `/api/research/chat/save`     | Save chat message to DB         |
| GET    | `/api/research/chat/history`  | Load chat history from DB       |
| DELETE | `/api/research/chat/clear`    | Clear all chat history          |
| POST   | `/api/documents/upload`       | Upload PDF/DOCX/TXT for RAG     |
| POST   | `/api/documents/search`       | Vector search in documents      |
| DELETE | `/api/documents/{id}`         | Delete document + ChromaDB data |
| GET    | `/api/export/pdf/{id}`        | Download report as PDF          |
| GET    | `/api/export/markdown/{id}`   | Download report as Markdown     |
| POST   | `/api/workspaces/`            | Create workspace                |
| GET    | `/api/workspaces/`            | List all workspaces             |
| DELETE | `/api/workspaces/{id}`        | Delete workspace                |

---

## 💬 AI Chat Modes

| Mode             | Context Used            | Best For                       |
| ---------------- | ----------------------- | ------------------------------ |
| 💬 General Chat  | No extra context        | General AI questions           |
| 📊 Research Chat | Research report content | Deep dive into report findings |
| 📄 Document Chat | Uploaded files via RAG  | Questions about your PDFs/DOCX |

---

## ✅ Assessment Checklist

### Mandatory Requirements

- [x] Multi-Agent LangGraph Workflow (4 agents)
- [x] Conditional Routing (`route_after_verifier`)
- [x] Tool Calling (3 tools: Web Search, Calculator, File Retrieval)
- [x] Agent Handoff (Planner → Researcher → Verifier → Reporter)
- [x] Memory Persistence (MemorySaver + PostgreSQL checkpoints)
- [x] Reflection Loop (Researcher ↔ Verifier, max 2 retries)
- [x] Pydantic Structured Output (`FinalReport`, `ResearchFinding`)
- [x] RAG Pipeline (ChromaDB + PDF/DOCX/TXT processing)
- [x] JWT Authentication with protected routes
- [x] PostgreSQL Database (6 tables)
- [x] Research History with full report storage
- [x] Workspaces for project organization
- [x] Live Pipeline Display (real-time agent + tool tracking)
- [x] AI Chat Mode (3 modes with PostgreSQL history)
- [x] PDF + Markdown Export with query-based filenames
- [x] Professional Streamlit UI (dark theme)

### Bonus Challenges

- [x] Docker Compose setup
- [ ] Multi-LLM Support (OpenAI / Gemini / Groq)
- [ ] Scheduled Research (Daily / Weekly / Monthly)
- [ ] n8n Email Integration
- [ ] Cloud Deployment

---

## 🔒 Security

- JWT token authentication on all protected routes
- bcrypt password hashing (cost factor 12)
- Environment variables for all API keys and secrets
- `.env` excluded from version control via `.gitignore`
- CORS restricted to frontend origin only

---

## 👨‍💻 Author

**Rehan** — AI Engineer Assessment Submission
Cyberify Technical Assessment 2026

---

_Built with ❤️ using LangGraph · FastAPI · PostgreSQL · ChromaDB · Streamlit · OpenAI_
