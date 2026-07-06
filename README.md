# CampusGPT — AI Campus Assistant API

> An AI-powered Retrieval-Augmented Generation (RAG) chatbot backend for COMSATS University Islamabad, Sahiwal Campus. Students and faculty get instant, accurate answers to campus questions — fees, scholarships, room locations, faculty offices, announcements, and more.

---

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
- [Environment Variables](#environment-variables)
- [API Endpoints](#api-endpoints)
- [RAG Pipeline](#rag-pipeline)
- [Data Sources](#data-sources)
- [Deployment](#deployment)
- [Connected Applications](#connected-applications)

---

## Overview

CampusGPT is a Final Year Project (FYP) built at COMSATS University Islamabad, Sahiwal Campus. It solves a real problem: students waste time searching through scattered PDFs, notice boards, and word-of-mouth to find basic campus information like semester fees, scholarship eligibility, faculty office locations, and exam announcements.

The system uses **Retrieval-Augmented Generation (RAG)** — instead of relying on a general-purpose LLM that may hallucinate, CampusGPT retrieves verified facts from the university knowledge base and passes them as context to the LLM. The result is accurate, grounded answers that stay up to date with a two-click admin workflow.

---

## Architecture

```
┌─────────────────────────────┐     ┌──────────────────────────┐
│      Flutter Mobile App     │     │     React Admin Panel    │
│  Students/Faculty: Chat     │     │   Manage data, generate  │
│  Faculty: Data submissions  │     │   embed, announcements   │
└────────────┬────────────────┘     └────────────┬─────────────┘
             │                                   │
             └──────────────┬────────────────────┘
                            ▼
             ┌──────────────────────────────┐
             │        FastAPI Backend        │
             │  Auth · RAG · LLM Orchestrate │
             └──────────────┬───────────────┘
                            ▼
        ┌───────────────────────────────────────────┐
        │                RAG Pipeline                │
        │                                           │
        │  Campus data ──► Chunks ──► Embed vectors │
        │                                    │       │
        │  User query ──► Embed ──► VectorDB ┘       │
        │                            │               │
        │                            ▼               │
        │               LLM (Generate Answer)        │
        └───────────────────────────────────────────┘
             │                        │
    ┌────────▼────────┐    ┌──────────▼────────┐
    │  Neon PostgreSQL │    │   Google Sheets    │
    │  Users, chats,   │    │  Source of truth   │
    │  announcements   │    │  for campus data   │
    └─────────────────┘    └───────────────────┘
```

---

## Features

### Student & Faculty
- **Conversational chat** with context-aware follow-up question support
- **Query rewriting** — vague follow-ups like "what about CS?" are automatically resolved before retrieval
- **Chat memory** — recent conversation context is maintained per session
- **Saved answers** — bookmark important responses for quick access
- **GPA calculators** — four built-in calculators for academic planning
- **Clickable links** — reference files shared by faculty are tappable in the app
- **Secure authentication** — university email verification with OTP and JWT sessions
- **Password recovery** — self-service forgot-password via email reset link

### Faculty Only
- **Knowledge base submissions** — faculty contribute department-specific data directly through the app, attributed by name in every answer

### Admin Panel
- **Dashboard** — live chunk counts, semester history, pipeline status
- **Generate & Embed** — one-click pull from Google Sheets and re-embed the knowledge base
- **Search tester** — test any question and inspect which chunks are retrieved with match-quality scores
- **Announcements manager** — full CRUD for holidays, exams, and fee notices, filterable by type and semester
- **Semester history** — browse past semesters' data broken down by source and chunk type

---

## Tech Stack

| Layer | Technology |
|---|---|
| **Backend framework** | FastAPI + Uvicorn |
| **Database ORM** | SQLAlchemy |
| **Database** | Neon PostgreSQL |
| **Authentication** | JWT (python-jose) + bcrypt |
| **Vector store** | ChromaDB |
| **Embeddings** | Sentence-Transformers (`all-MiniLM-L6-v2`) |
| **LLM** | DeepSeek via OpenRouter |
| **Data ingestion** | Google Sheets API (gspread + pandas) |
| **Email** | Brevo transactional email API |
| **Mobile app** | Flutter + GetX |
| **Admin panel** | React + Vite + Tailwind CSS |
| **Backend hosting** | Railway |
| **Admin panel hosting** | Vercel |

---

## Project Structure

```
CampusGPT-APIs/
├── main.py                  # FastAPI app entry point
├── startup.py               # Writes credentials from env vars on deploy
├── Procfile                 # Railway start command
│
├── auth/                    # Registration, login, OTP, password reset
├── admin/                   # Admin-only endpoints (generate, embed, search, announcements)
├── students/                # Student/faculty query, saved chats, feedback
├── core/                    # JWT security, token creation
├── db/                      # SQLAlchemy session and engine
├── models/                  # Database models (UserAuth, ChatMessage, Announcement, etc.)
├── schemas/                 # Pydantic request/response schemas
│
├── rag_pipeline/
│   ├── generator.py         # Pulls Google Sheets data and builds chunk JSON
│   ├── embedder.py          # Embeds chunks into ChromaDB
│   ├── searcher.py          # Searches ChromaDB for relevant chunks
│   ├── llm.py               # LLM answer generation and query rewriting
│   ├── sheets_reader.py     # Google Sheets API wrapper
│   ├── scholarships_chunks.py
│   ├── fees_chunks.py
│   ├── basic_info_chunks.py
│   ├── blocks_chunks.py
│   ├── faculty_chunks.py
│   ├── faculty_kb_chunks.py
│   └── announcements_chunks.py
│
└── UNIdata/
    ├── sheets_config.json   # Google Sheet IDs (gitignored)
    ├── credentials.json     # Google service account key (gitignored)
    ├── chunks/              # Generated chunk JSON files (gitignored)
    └── vectordb/            # ChromaDB persistent storage (gitignored)
```

---

## Getting Started

### Prerequisites

- Python 3.11+
- A [Neon](https://neon.tech) PostgreSQL database
- A [Google Cloud](https://console.cloud.google.com) service account with Sheets API access
- An [OpenRouter](https://openrouter.ai) API key
- A [Brevo](https://www.brevo.com) API key for transactional email

### Local setup

```bash
# 1. Clone the repository
git clone https://github.com/your-username/CampusGPT-APIs.git
cd CampusGPT-APIs

# 2. Create and activate a virtual environment
python -m venv myenv
myenv\Scripts\activate        # Windows
source myenv/bin/activate     # macOS/Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Create a .env file (see Environment Variables section below)
cp .env.example .env

# 5. Add your credentials
# Place credentials.json in UNIdata/
# Place sheets_config.json in UNIdata/

# 6. Run the server
uvicorn main:app --reload
```

The API will be available at `http://127.0.0.1:8000`
Interactive docs at `http://127.0.0.1:8000/docs`

---

## Environment Variables

Create a `.env` file in the project root with the following variables:

```env
# Database
DATABASE_URL=postgresql://user:password@host/dbname

# JWT Authentication
SECRET_KEY=your_secret_key_here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRY=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# LLM
OPENROUTER_API_KEY=sk-or-v1-...

# Email
BREVO_API_KEY=xkeysib-...

# Frontend URLs (for CORS)
FRONTEND_APP_URL=http://localhost:3000
FRONTEND_ADMIN_URL=http://localhost:5173

# Google (for deployment only — local uses files directly)
GOOGLE_CREDENTIALS_JSON={"type":"service_account",...}
SHEETS_CONFIG_JSON={"credentials_file":"credentials.json","sheets":{...}}
```

---

## API Endpoints

### Auth (`/auth`)
| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/auth/register` | Register a new student/faculty account |
| `POST` | `/auth/login` | Login and receive JWT tokens |
| `POST` | `/auth/send-otp` | Send OTP to university email |
| `POST` | `/auth/verify-otp` | Verify OTP code |
| `POST` | `/auth/forgot-password` | Send password reset link |
| `POST` | `/auth/reset-password` | Reset password with token |

### Student (`/student`) — requires auth
| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/student/query` | Send a question, receive a grounded AI answer |
| `GET` | `/student/saved-chats` | Retrieve bookmarked answers |
| `POST` | `/student/saved-chats` | Save an answer |
| `DELETE` | `/student/saved-chats/{id}` | Remove a saved answer |
| `DELETE` | `/student/clear-history` | Clear chat context history |

### Admin (`/admin`) — requires admin JWT
| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/admin/login` | Admin login |
| `GET` | `/admin/status` | Chunk file overview and pipeline status |
| `POST` | `/admin/generate` | Generate chunks from Google Sheets |
| `POST` | `/admin/embed` | Embed chunks into ChromaDB |
| `GET` | `/admin/chunks` | Retrieve chunk JSON for a semester |
| `POST` | `/admin/search` | Test search against ChromaDB |
| `GET` | `/admin/announcements` | List all announcements |
| `POST` | `/admin/announcements` | Create an announcement |
| `PUT` | `/admin/announcements/{id}` | Update an announcement |
| `PATCH` | `/admin/announcements/{id}/toggle` | Toggle active status |
| `DELETE` | `/admin/announcements/{id}` | Delete an announcement |

---

## RAG Pipeline

The RAG pipeline runs in two modes:

### Ingestion (offline, admin-triggered)
```
Google Sheets
    │
    ▼
Chunk generators (one per data source)
    │  Narrative chunks, FAQ chunks, overview chunks
    ▼
chunks_{semester}.json
    │
    ▼
Sentence-Transformers (all-MiniLM-L6-v2)
    │  384-dimensional vectors
    ▼
ChromaDB (persistent vector store)
```

### Query (real-time, per student message)
```
Student question
    │
    ▼
Query rewrite (LLM) — resolves vague follow-ups using chat history
    │
    ▼
Sentence-Transformers — embeds question to vector
    │
    ▼
ChromaDB — top-k cosine similarity search
    │
    ▼
LLM (DeepSeek via OpenRouter)
    │  System prompt + retrieved context + chat history
    ▼
Grounded natural-language answer
```

### Multi-level chunking strategy

Each data source is broken into multiple levels of chunks for precise retrieval:

| Level | Example |
|---|---|
| Per-item | "Where is Dr. Aniqa's office?" |
| Per-group | "Who is on C Block ground floor?" |
| Per-category | "What holidays are coming up?" |
| Overview | "What's in A Block overall?" |

Each level has both **narrative** and **FAQ** formats — over **1,200 chunks** across all sources.

---

## Data Sources

| Source | Contents |
|---|---|
| **Fees & Scholarships** | Program-wise fees, admission fees, 25+ scholarship policies |
| **Campus Basics** | Cafeteria, parking, hostel, transport, electric bus |
| **Rooms & Blocks** | Every room across A, B, C Blocks — floor by floor |
| **Faculty Directory** | Office locations, departments, HODs |
| **Announcements** | Holidays, exams, fee deadlines — tagged by type and semester |
| **Faculty Knowledge Base** | Department-specific info submitted by faculty, attributed by name |

All data is sourced from **Google Sheets** — admins update information without touching code, and changes go live with two clicks from the admin panel.

---

## Deployment

The system is fully deployed and operational:

| Component | Platform | URL |
|---|---|---|
| Backend API | Railway |
| Admin Panel | Vercel | `https://campus-gpt-admin-panel.vercel.app` |
| Mobile App | Signed APK | Available for Android installation |

### Deploying to Railway

1. Push code to GitHub
2. Connect repo in Railway dashboard
3. Add all environment variables from the list above, plus:
   - `GOOGLE_CREDENTIALS_JSON` — contents of your `credentials.json` as a single-line JSON string
   - `SHEETS_CONFIG_JSON` — contents of your `sheets_config.json` as a single-line JSON string
4. Railway uses the `Procfile` to run `startup.py` (writes credential files) then starts Uvicorn
5. After first deploy: hit `/admin/generate` then `/admin/embed` from the admin panel to build the knowledge base

---

## Connected Applications

| Application | Repository | Tech |
|---|---|---|
| Mobile App | `CampusGPT-App` | Flutter + Dart + GetX |
| Admin Panel | `CampusGPT-Admin` | React + Vite + Tailwind CSS |

---

## License

This project was developed as a Final Year Project at COMSATS University Islamabad, Sahiwal Campus — 2026.

---

*Built by Muhammad Zaid — FA22-BCS-089 — BS Computer Science*
