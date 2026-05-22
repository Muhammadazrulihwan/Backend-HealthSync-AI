from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator
from app.config import settings

# ─── Engine & Session ─────────────────────────────────────────────────────────
engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False}  # Diperlukan untuk SQLite
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


# ─── Models ───────────────────────────────────────────────────────────────────

class ConsultationHistory(Base):
    __tablename__ = "consultation_history"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(100), index=True, nullable=False)
    user_id = Column(String(100), nullable=True)
    consultation_type = Column(String(50), nullable=False)  # symptom, medication, chatbot, dll
    user_input = Column(Text, nullable=False)
    ai_response = Column(Text, nullable=False)
    severity_level = Column(String(20), nullable=True)  # low, medium, high, emergency
    created_at = Column(DateTime, server_default=func.now())


class UserProfile(Base):
    __tablename__ = "user_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(100), unique=True, index=True, nullable=False)
    age = Column(Integer, nullable=True)
    gender = Column(String(10), nullable=True)
    existing_conditions = Column(Text, nullable=True)  # disimpan sebagai JSON string
    allergies = Column(Text, nullable=True)             # disimpan sebagai JSON string
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


# ─── Dependency & Init ────────────────────────────────────────────────────────

def get_db() -> Generator[Session, None, None]:
    """Dependency injection untuk database session di setiap request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Buat semua tabel jika belum ada. Dipanggil saat startup."""
    Base.metadata.create_all(bind=engine)
