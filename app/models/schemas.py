from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class SeverityLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    EMERGENCY = "emergency"


class GenderEnum(str, Enum):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"


# ─── SYMPTOM CHECKER ──────────────────────────────────────────────────────────

class SymptomRequest(BaseModel):
    symptoms: str = Field(..., description="Deskripsi gejala yang dialami", min_length=5)
    duration: Optional[str] = Field(None, description="Berapa lama gejala berlangsung")
    age: Optional[int] = Field(None, description="Usia pasien", ge=0, le=120)
    gender: Optional[GenderEnum] = None
    existing_conditions: Optional[str] = Field(None, description="Kondisi kesehatan yang sudah ada")
    session_id: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "symptoms": "kepala pusing, mual, dan demam sejak kemarin",
                "duration": "1 hari",
                "age": 30,
                "gender": "male"
            }
        }


class SymptomResponse(BaseModel):
    is_emergency: bool
    severity_level: SeverityLevel
    analysis: str
    disclaimer: str
    session_id: Optional[str] = None


# ─── MEDICATION INFO ──────────────────────────────────────────────────────────

class MedicationRequest(BaseModel):
    medication_name: str = Field(..., description="Nama obat yang ingin dicari", min_length=2)
    query_type: Optional[str] = Field(
        "general",
        description="Jenis pertanyaan: general, interaction, dosage, side_effects"
    )
    other_medications: Optional[str] = Field(None, description="Obat lain yang sedang dikonsumsi (untuk cek interaksi)")
    session_id: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "medication_name": "Paracetamol",
                "query_type": "general"
            }
        }


class MedicationResponse(BaseModel):
    medication_name: str
    information: str
    disclaimer: str
    session_id: Optional[str] = None


# ─── EDUCATIONAL CHATBOT ──────────────────────────────────────────────────────

class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str


class ChatbotRequest(BaseModel):
    message: str = Field(..., description="Pertanyaan atau pesan pengguna", min_length=2)
    conversation_history: Optional[List[ChatMessage]] = Field(default=[], description="Riwayat percakapan")
    session_id: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "message": "Apa itu diabetes dan bagaimana cara mencegahnya?",
                "conversation_history": []
            }
        }


class ChatbotResponse(BaseModel):
    response: str
    disclaimer: str
    session_id: Optional[str] = None


# ─── PREVENTIVE CARE ──────────────────────────────────────────────────────────

class PreventiveRequest(BaseModel):
    topic: str = Field(..., description="Topik kesehatan preventif yang ingin ditanyakan")
    age: Optional[int] = Field(None, ge=0, le=120)
    gender: Optional[GenderEnum] = None
    lifestyle_info: Optional[str] = Field(None, description="Informasi gaya hidup saat ini")
    session_id: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "topic": "pencegahan hipertensi",
                "age": 45,
                "gender": "male",
                "lifestyle_info": "jarang olahraga, sering makan makanan asin"
            }
        }


class PreventiveResponse(BaseModel):
    topic: str
    recommendations: str
    disclaimer: str
    session_id: Optional[str] = None


# ─── TERMINOLOGY ──────────────────────────────────────────────────────────────

class TerminologyRequest(BaseModel):
    term: str = Field(..., description="Istilah medis yang ingin dijelaskan", min_length=2)
    context: Optional[str] = Field(None, description="Konteks di mana istilah ini ditemukan")
    session_id: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "term": "hipertensi",
                "context": "hasil pemeriksaan tekanan darah"
            }
        }


class TerminologyResponse(BaseModel):
    term: str
    explanation: str
    disclaimer: str
    session_id: Optional[str] = None


# ─── HISTORY ──────────────────────────────────────────────────────────────────

class HistoryResponse(BaseModel):
    id: int
    session_id: str
    consultation_type: str
    user_input: str
    ai_response: str
    severity_level: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


# ─── USER PROFILE ─────────────────────────────────────────────────────────────

class UserProfileCreate(BaseModel):
    user_id: str
    age: Optional[int] = Field(None, ge=0, le=120)
    gender: Optional[GenderEnum] = None
    existing_conditions: Optional[List[str]] = None
    allergies: Optional[List[str]] = None


class UserProfileResponse(BaseModel):
    user_id: str
    age: Optional[int]
    gender: Optional[str]
    existing_conditions: Optional[str]
    allergies: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True
