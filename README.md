# Ticket Generator

Web app that turns Fathom meeting transcripts into reviewed tasks, CSV exports, and Jira tickets.

## Features

- Connect Fathom and Jira credentials
- Select a meeting and identify yourself among participants
- AI extracts action items assigned to you
- Review, edit, approve, or reject each task before export
- Export approved tasks to CSV and re-import updates
- Push approved tasks to Jira in bulk

## Stack

- Backend: FastAPI, SQLAlchemy, SQLite
- Frontend: React, TypeScript, Vite
- Integrations: Fathom API, Jira REST API, OpenAI/Anthropic LLM

## Setup

### 1. Backend

```powershell
cd backend
py -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy ..\.env.example ..\.env
```

Edit `.env` in the project root with your LLM, Fathom, and Jira credentials.

Run the API:

```powershell
uvicorn app.main:app --reload --port 8000
```

### 2. Frontend

```powershell
cd frontend
npm install
npm run dev
```

Open [http://localhost:5173](http://localhost:5173)

## Workflow

1. Settings — save Fathom and Jira credentials
2. Meeting — pick a Fathom meeting
3. Identity — choose who you are in the meeting
4. Review — refine and approve tasks
5. Export & Jira — download CSV, re-upload edits, push to Jira

## Notes

- Only approved tasks are exported or synced to Jira
- Jira sync is idempotent: tasks with an existing `jira_key` are skipped
- LLM provider is configured via `LLM_PROVIDER` (`openai` or `anthropic`)
