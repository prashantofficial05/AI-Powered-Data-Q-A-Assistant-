# 🤖 AI-Powered Data Q&A Assistant

<div align="center">

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?style=for-the-badge&logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111%2B-009688?style=for-the-badge&logo=fastapi)
![SQLite](https://img.shields.io/badge/SQLite-SQLAlchemy-003B57?style=for-the-badge&logo=sqlite)
![MySQL](https://img.shields.io/badge/MySQL-Supported-4479A1?style=for-the-badge&logo=mysql)
![LLM](https://img.shields.io/badge/LLM-Groq%20%7C%20Claude%20%7C%20OpenAI-FF6B35?style=for-the-badge)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)

**Ask questions about your CSV data in plain English — get instant AI-powered answers, summaries, and auto-executed pandas queries.**

[Features](#-features) • [Tech Stack](#-tech-stack) • [Quick Start](#-quick-start) • [API Reference](#-api-reference) • [Project Structure](#-project-structure) • [Free API Keys](#-getting-free-api-keys)

</div>

---

## 📌 Overview

The **AI-Powered Data Q&A Assistant** is a Python backend application that lets users upload CSV files and ask natural language questions about their data. It uses Large Language Model (LLM) APIs with prompt engineering to generate accurate data analysis, summaries, and pandas code — all served through a REST API built with FastAPI.

**Example interactions:**
> *"What is the average salary by city?"*
> *"Show me the top 5 products by sales."*
> *"Which region had the highest revenue last quarter?"*

The assistant understands the data, writes pandas queries automatically, executes them safely, and returns human-readable answers.

---

## ✨ Features

- 📂 **CSV Upload & Management** — Upload any CSV file; the app stores metadata and gives back column info instantly
- 💬 **Natural Language Q&A** — Ask questions in plain English; the LLM reads your data and answers accurately
- 🧠 **Multi-Turn Chat History** — Conversations are remembered per session so you can ask follow-up questions
- ⚡ **Auto Pandas Execution** — When the LLM suggests a pandas code snippet, the app runs it safely and returns real results
- 📊 **Dataset Summarizer** — One-click AI summary: executive overview + top observations + next steps
- 🔌 **Multi-Provider LLM Support** — Switch between Groq (free), Claude, or OpenAI with a single env variable
- 🗄️ **Dual Database Support** — SQLite for local development, MySQL for production
- 🔒 **Safe Code Execution** — Sandboxed eval blocks dangerous operations (file write, OS access, etc.)
- 🌐 **Full REST API** — All features exposed as clean JSON endpoints, ready to connect to any frontend

---

## 🛠 Tech Stack

| Layer | Technology |
|---|---|
| **Backend Framework** | FastAPI |
| **LLM Providers** | Groq (LLaMA 3.1), Anthropic Claude, OpenAI GPT |
| **Prompt Engineering** | Custom system prompts + multi-turn context injection |
| **Data Processing** | Pandas |
| **ORM / Database** | SQLAlchemy + SQLite (dev) / MySQL (prod) |
| **API Server** | Uvicorn (ASGI) |
| **Validation** | Pydantic v2 |
| **Environment Config** | python-dotenv |

---

## 🚀 Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/prashantofficial05/AI-Powered-Data-Q-A-Assistant-.git
cd AI-Powered-Data-Q-A-Assistant-
```

### 2. Create a Virtual Environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Copy the `.env` file and add your API key:

```bash
# Open .env in any text editor and set your key
```

```env
# Choose your LLM provider: groq | claude | openai
LLM_PROVIDER=groq

# Get a FREE Groq key at https://console.groq.com/keys
GROQ_API_KEY=your_groq_api_key_here

# SQLite (no setup needed for local dev)
USE_SQLITE=true
```

### 5. Run the Server

```bash
uvicorn main:app --reload --port 8000
```

Open your browser at **http://localhost:8000/docs** to see the interactive API docs (Swagger UI).

---

## 🔑 Getting Free API Keys

| Provider | Free Tier | Sign Up |
|---|---|---|
| **Groq** ⭐ Recommended | Very generous free tier, no credit card | [console.groq.com/keys](https://console.groq.com/keys) |
| **Anthropic Claude** | Free trial credits | [console.anthropic.com](https://console.anthropic.com/) |
| **OpenAI** | Free trial credits | [platform.openai.com](https://platform.openai.com/api-keys) |

> 💡 **Groq is recommended** for getting started — it's completely free, requires no credit card, and is extremely fast.

---

## 📁 Project Structure

```
AI-Powered-Data-Q-A-Assistant/
│
├── main.py              # FastAPI app — all REST API endpoints
├── database.py          # SQLAlchemy models (ChatSession, ChatMessage, UploadedFile)
├── llm_provider.py      # Unified LLM interface (Groq / Claude / OpenAI)
├── data_processor.py    # CSV loading, summarization, safe pandas execution
├── prompts.py           # Prompt engineering templates for data Q&A
├── requirements.txt     # Python dependencies
├── .env                 # Environment variables (API keys, DB config)
├── .gitignore
└── README.md
```

---

## 📡 API Reference

### Health Check
```
GET /api/health
```
Returns server status, active LLM provider, and database type.

---

### Upload a CSV File
```
POST /api/upload
Content-Type: multipart/form-data
Body: file=<your_csv_file>
```
**Response:**
```json
{
  "id": 1,
  "filename": "sales.csv",
  "rows": 1500,
  "columns": ["product", "sales", "region", "date"],
  "path": "uploads/sales.csv"
}
```

---

### Ask a Question (Chat)
```
POST /api/chat
Content-Type: application/json
```
**Request Body:**
```json
{
  "question": "What is the total sales by region?",
  "file_path": "uploads/sales.csv",
  "session_id": "optional-session-id",
  "use_history": true
}
```
**Response:**
```json
{
  "session_id": "abc-123",
  "answer": "The total sales by region are: North: **$45,000**, South: **$32,000**...",
  "exec_result": "| region | sales |\n|--------|-------|\n| North | 45000 |",
  "provider": "groq",
  "tokens": 312,
  "latency_ms": 820.5
}
```

---

### Summarize a Dataset
```
POST /api/summarize
Content-Type: application/json

{ "file_path": "uploads/sales.csv" }
```

---

### List Uploaded Files
```
GET /api/files
```

---

### Chat Session Management
```
GET    /api/sessions              # List all sessions
GET    /api/sessions/{session_id} # Get messages for a session
DELETE /api/sessions/{session_id} # Delete a session
```

---

## ⚙️ Configuration Options

All configuration is done via the `.env` file:

| Variable | Default | Description |
|---|---|---|
| `LLM_PROVIDER` | `groq` | Active LLM: `groq`, `claude`, or `openai` |
| `GROQ_API_KEY` | — | Your Groq API key |
| `CLAUDE_API_KEY` | — | Your Anthropic API key |
| `OPENAI_API_KEY` | — | Your OpenAI API key |
| `GROQ_MODEL` | `llama-3.1-8b-instant` | Groq model name |
| `CLAUDE_MODEL` | `claude-haiku-4-5-20251001` | Claude model name |
| `OPENAI_MODEL` | `gpt-3.5-turbo` | OpenAI model name |
| `USE_SQLITE` | `true` | `true` = SQLite, `false` = MySQL |
| `DB_HOST` | `localhost` | MySQL host (if USE_SQLITE=false) |
| `DB_NAME` | `ai_data_qa` | MySQL database name |
| `MAX_ROWS_TO_SEND_LLM` | `100` | Max rows included in LLM context |

---

## 🔄 Switching LLM Providers

Change `LLM_PROVIDER` in `.env` and restart — no code changes needed:

```env
# Use Groq (free)
LLM_PROVIDER=groq
GROQ_API_KEY=gsk_...

# Use Claude
LLM_PROVIDER=claude
CLAUDE_API_KEY=sk-ant-...

# Use OpenAI
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-...
```

---

## 🗄️ Using MySQL (Production)

Set `USE_SQLITE=false` and configure the MySQL connection:

```env
USE_SQLITE=false
DB_HOST=localhost
DB_PORT=3306
DB_NAME=ai_data_qa
DB_USER=root
DB_PASSWORD=yourpassword
```

Create the database first:
```sql
CREATE DATABASE ai_data_qa;
```
Then run the app — SQLAlchemy creates all tables automatically.

---

## 🧩 How It Works

```
User uploads CSV
       ↓
FastAPI stores file + metadata in DB
       ↓
User asks a question via /api/chat
       ↓
data_processor builds a context block
(data summary + sample rows as CSV text)
       ↓
prompts.py injects context + chat history
into a carefully engineered system prompt
       ↓
llm_provider.py calls Groq / Claude / OpenAI
       ↓
LLM returns answer + optional pandas code
       ↓
If pandas code found → sandboxed eval runs it
       ↓
Answer + real query result returned to user
       ↓
Message saved to DB for multi-turn history
```

---

## 🛡️ Security

- **Sandboxed code execution** — LLM-generated pandas code is evaluated with `__builtins__` blocked and a keyword blacklist (`to_csv`, `os.`, `open(`, `exec`, `eval`, `subprocess`, etc.)
- **No API keys in code** — All secrets live in `.env` which is in `.gitignore`
- **Input validation** — Pydantic schemas validate all request bodies
- **File type restriction** — Only `.csv` files accepted for upload

---

## 🤝 Contributing

Contributions are welcome! Feel free to open issues or submit pull requests.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

---

## 👤 Author

**Prashant** — [@prashantofficial05](https://github.com/prashantofficial05)

---

<div align="center">
⭐ If you found this project helpful, please give it a star!
</div>
