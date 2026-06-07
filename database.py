
import os
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Float
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

USE_SQLITE = os.getenv("USE_SQLITE", "true").lower() == "true"

if USE_SQLITE:
    DATABASE_URL = "sqlite:///./ai_data_qa.db"
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    host = os.getenv("DB_HOST", "localhost")
    port = os.getenv("DB_PORT", "3306")
    name = os.getenv("DB_NAME", "ai_data_qa")
    user = os.getenv("DB_USER", "root")
    pwd  = os.getenv("DB_PASSWORD", "")
    DATABASE_URL = f"mysql+pymysql://{user}:{pwd}@{host}:{port}/{name}"
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# ─── Models ────────────────────────────────────────────────────────────────────

class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id         = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(64), unique=True, index=True)
    title      = Column(String(255), default="New Chat")
    created_at = Column(DateTime, default=datetime.utcnow)


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id          = Column(Integer, primary_key=True, index=True)
    session_id  = Column(String(64), index=True)
    role        = Column(String(16))        # "user" | "assistant"
    content     = Column(Text)
    data_source = Column(String(255), nullable=True)
    provider    = Column(String(32),  nullable=True)
    tokens_used = Column(Integer,     nullable=True)
    latency_ms  = Column(Float,       nullable=True)
    created_at  = Column(DateTime, default=datetime.utcnow)


class UploadedFile(Base):
    __tablename__ = "uploaded_files"

    id          = Column(Integer, primary_key=True, index=True)
    filename    = Column(String(255))
    file_path   = Column(String(512))
    rows        = Column(Integer, nullable=True)
    columns     = Column(Text,    nullable=True)   # JSON list
    size_bytes  = Column(Integer, nullable=True)
    uploaded_at = Column(DateTime, default=datetime.utcnow)


def create_tables():
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
