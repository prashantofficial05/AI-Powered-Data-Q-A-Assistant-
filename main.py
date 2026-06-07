
import os
import re
import uuid
import json
import shutil
from pathlib import Path
from datetime import datetime
from typing import Optional

import pandas as pd
from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from dotenv import load_dotenv

load_dotenv()

from database       import create_tables, get_db, ChatSession, ChatMessage, UploadedFile
from data_processor_ import dataframe_to_context, run_pandas_query, load_csv, UPLOAD_DIR
from llm_provider   import ask_llm
from prompts        import (
    SYSTEM_DATA_QA, SYSTEM_SUMMARY, SYSTEM_GENERAL,
    build_data_prompt, build_summary_prompt, build_history_prompt,s
)

# ── App setup ──────────────────────────────────────────────────────────────────
app = FastAPI(title="AI Data Q&A Assistant", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

create_tables()

FRONTEND_DIR = Path(__file__).parent.parent / "frontend"


# ── Global error handler ───────────────────────────────────────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail": f"Internal server error: {str(exc)}"},
    )


# ── Pydantic schemas ───────────────────────────────────────────────────────────
class ChatRequest(BaseModel):
    question:    str
    session_id:  Optional[str] = None
    file_path:   Optional[str] = None   # path of an uploaded CSV
    use_history: bool = True


class SummarizeRequest(BaseModel):
    file_path: str


# ── Routes ─────────────────────────────────────────────────────────────────────

@app.get("/api/health")
def health():
    return {
        "status":   "ok",
        "provider": os.getenv("LLM_PROVIDER", "groq"),
        "db":       "sqlite" if os.getenv("USE_SQLITE", "true").lower() == "true" else "mysql",
    }


@app.get("/api/provider")
def provider_info():
    """Return current LLM provider and model for the frontend status bar."""
    p = os.getenv("LLM_PROVIDER", "groq").lower()
    models = {
        "groq":   os.getenv("GROQ_MODEL",   "llama-3.1-8b-instant"),
        "claude": os.getenv("CLAUDE_MODEL",  "claude-haiku-4-5-20251001"),
        "openai": os.getenv("OPENAI_MODEL",  "gpt-3.5-turbo"),
    }
    return {"provider": p, "model": models.get(p, "unknown")}


# ── File upload ────────────────────────────────────────────────────────────────
@app.post("/api/upload")
async def upload_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(400, "Only CSV files are supported.")

    # FIX: avoid overwriting existing uploads with same name
    dest = UPLOAD_DIR / file.filename
    if dest.exists():
        stem   = Path(file.filename).stem
        suffix = Path(file.filename).suffix
        ts     = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        dest   = UPLOAD_DIR / f"{stem}_{ts}{suffix}"

    with open(dest, "wb") as f:
        shutil.copyfileobj(file.file, f)

    try:
        df      = pd.read_csv(dest, encoding="utf-8-sig")
        rows    = len(df)
        columns = json.dumps(df.columns.tolist())
    except Exception as e:
        dest.unlink(missing_ok=True)
        raise HTTPException(400, f"Could not parse CSV: {e}")

    record = UploadedFile(
        filename   = dest.name,
        file_path  = str(dest),
        rows       = rows,
        columns    = columns,
        size_bytes = dest.stat().st_size,
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    return {
        "id":       record.id,
        "filename": record.filename,
        "rows":     rows,
        "columns":  df.columns.tolist(),
        "path":     str(dest),
    }


@app.get("/api/files")
def list_files(db: Session = Depends(get_db)):
    records = db.query(UploadedFile).order_by(UploadedFile.uploaded_at.desc()).all()
    result  = []
    for r in records:
        # Skip records whose files were manually deleted
        if not Path(r.file_path).exists():
            continue
        cols = json.loads(r.columns) if r.columns else []
        result.append({
            "id":          r.id,
            "filename":    r.filename,
            "rows":        r.rows,
            "columns":     cols,
            "size_bytes":  r.size_bytes,
            "uploaded_at": r.uploaded_at.isoformat(),
            "path":        r.file_path,
        })
    return result


# ── Chat ───────────────────────────────────────────────────────────────────────
@app.post("/api/chat")
def chat(req: ChatRequest, db: Session = Depends(get_db)):
    # ── Session management ─────────────────────────────────────────────────────
    session_id = req.session_id or str(uuid.uuid4())
    session    = db.query(ChatSession).filter_by(session_id=session_id).first()
    if not session:
        title   = req.question[:60] + ("…" if len(req.question) > 60 else "")
        session = ChatSession(session_id=session_id, title=title)
        db.add(session)
        db.commit()

    # ── Load data context ──────────────────────────────────────────────────────
    context    = None
    file_label = None
    df         = None   # FIX: always initialise so it's never unbound

    if req.file_path:
        fp = Path(req.file_path)
        if not fp.exists():
            raise HTTPException(404, f"File not found: {req.file_path}")
        try:
            df         = load_csv(str(fp))
            context    = dataframe_to_context(df, req.question)
            file_label = fp.name
        except Exception as e:
            raise HTTPException(400, f"Error reading file: {e}")

    # ── Build history ──────────────────────────────────────────────────────────
    history: list[dict] = []
    if req.use_history:
        past = (
            db.query(ChatMessage)
            .filter_by(session_id=session_id)
            .order_by(ChatMessage.created_at)
            .limit(20)
            .all()
        )
        history = [{"role": m.role, "content": m.content} for m in past]

    # ── Build messages for LLM ────────────────────────────────────────────────
    if context:
        messages = build_history_prompt(history, context, req.question)
        system   = SYSTEM_DATA_QA
    elif history:
        messages = [*history, {"role": "user", "content": req.question}]
        system   = SYSTEM_GENERAL
    else:
        messages = [{"role": "user", "content": req.question}]
        system   = SYSTEM_GENERAL

    # ── Call LLM ───────────────────────────────────────────────────────────────
    try:
        result = ask_llm(messages, system)
    except RuntimeError as e:
        raise HTTPException(502, str(e))

    answer      = result["answer"]
    exec_result = None

    # FIX: only try to execute code if we actually loaded a dataframe
    if context and df is not None and "```python" in answer:
        code_blocks = re.findall(r"```python\n(.*?)```", answer, re.DOTALL)
        if code_blocks:
            exec_result = run_pandas_query(df, code_blocks[0].strip())

    # ── Persist messages ────────────────────────────────────────────────────────
    db.add(ChatMessage(
        session_id  = session_id,
        role        = "user",
        content     = req.question,
        data_source = file_label,
    ))
    db.add(ChatMessage(
        session_id  = session_id,
        role        = "assistant",
        content     = answer,
        data_source = file_label,
        provider    = result["provider"],
        tokens_used = result["tokens"],
        latency_ms  = result["latency_ms"],
    ))
    db.commit()

    return {
        "session_id":  session_id,
        "answer":      answer,
        "exec_result": exec_result,
        "provider":    result["provider"],
        "tokens":      result["tokens"],
        "latency_ms":  result["latency_ms"],
    }


# ── Summarize ──────────────────────────────────────────────────────────────────
@app.post("/api/summarize")
def summarize(req: SummarizeRequest):
    fp = Path(req.file_path)
    if not fp.exists():
        raise HTTPException(404, "File not found.")
    try:
        df      = load_csv(str(fp))
        context = dataframe_to_context(df, "summary")
    except Exception as e:
        raise HTTPException(400, str(e))

    messages = build_summary_prompt(context)
    try:
        result = ask_llm(messages, SYSTEM_SUMMARY)
    except RuntimeError as e:
        raise HTTPException(502, str(e))

    return {
        "summary":  result["answer"],
        "provider": result["provider"],
        "tokens":   result["tokens"],
    }


# ── Sessions ───────────────────────────────────────────────────────────────────
@app.get("/api/sessions")
def list_sessions(db: Session = Depends(get_db)):
    sessions = db.query(ChatSession).order_by(ChatSession.created_at.desc()).all()
    return [
        {
            "session_id": s.session_id,
            "title":      s.title,
            "created_at": s.created_at.isoformat(),
        }
        for s in sessions
    ]


@app.get("/api/sessions/{session_id}")
def get_session(session_id: str, db: Session = Depends(get_db)):
    messages = (
        db.query(ChatMessage)
        .filter_by(session_id=session_id)
        .order_by(ChatMessage.created_at)
        .all()
    )
    return [
        {
            "role":       m.role,
            "content":    m.content,
            "provider":   m.provider,
            "tokens":     m.tokens_used,
            "latency_ms": m.latency_ms,
            "created_at": m.created_at.isoformat(),
        }
        for m in messages
    ]


@app.delete("/api/sessions/{session_id}")
def delete_session(session_id: str, db: Session = Depends(get_db)):
    db.query(ChatMessage).filter_by(session_id=session_id).delete()
    db.query(ChatSession).filter_by(session_id=session_id).delete()
    db.commit()
    return {"deleted": True}


# ── Serve frontend (must be last) ──────────────────────────────────────────────
if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")

    @app.get("/")
    def root():
        return FileResponse(str(FRONTEND_DIR / "index.html"))
