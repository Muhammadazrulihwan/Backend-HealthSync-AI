from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
import uuid

from app.models.schemas import SymptomRequest, SymptomResponse, SeverityLevel
from app.services.gemini_service import (
    generate_response, check_emergency, get_emergency_response,
    SYMPTOM_SYSTEM_PROMPT, SAFETY_DISCLAIMER
)
from app.database import get_db, ConsultationHistory

router = APIRouter()


# ─── Request model untuk followup ────────────────────────────────────────────
class FollowupRequest(BaseModel):
    question: str
    session_id: str

    class Config:
        json_schema_extra = {
            "example": {
                "question": "Apakah saya perlu ke dokter segera?",
                "session_id": "uuid-session-id"
            }
        }


def determine_severity(response_text: str) -> SeverityLevel:
    """
    Deteksi severity dari section '## Tingkat Urgensi' di respons Gemini.
    Fallback ke LOW jika section tidak ditemukan.
    """
    text_lower = response_text.lower()

    if "tingkat urgensi" in text_lower:
        idx = text_lower.find("tingkat urgensi")
        section = text_lower[idx:idx + 150]

        if "darurat" in section:
            return SeverityLevel.EMERGENCY
        elif "tinggi" in section:
            return SeverityLevel.HIGH
        elif "sedang" in section:
            return SeverityLevel.MEDIUM
        else:
            return SeverityLevel.LOW

    if "segera ke igd" in text_lower or "hubungi 119" in text_lower:
        return SeverityLevel.EMERGENCY
    elif "segera konsultasi dokter dalam 24 jam" in text_lower:
        return SeverityLevel.HIGH
    elif "perlu diperhatikan" in text_lower:
        return SeverityLevel.MEDIUM

    return SeverityLevel.LOW


@router.post("/check", response_model=SymptomResponse, summary="Analisis gejala yang dialami")
async def check_symptoms(request: SymptomRequest, db: Session = Depends(get_db)):
    """
    Menerima deskripsi gejala dan memberikan analisis awal beserta panduan tindakan.

    - **symptoms**: Deskripsi gejala secara detail
    - **duration**: Lama gejala berlangsung (opsional)
    - **age**: Usia pasien (opsional)
    - **gender**: Jenis kelamin (opsional)
    """
    if check_emergency(request.symptoms):
        emergency_resp = get_emergency_response()
        session_id = request.session_id or str(uuid.uuid4())
        db.add(ConsultationHistory(
            session_id=session_id,
            consultation_type="symptom",
            user_input=request.symptoms,
            ai_response=emergency_resp["message"],
            severity_level="emergency"
        ))
        db.commit()
        return SymptomResponse(
            is_emergency=True,
            severity_level=SeverityLevel.EMERGENCY,
            analysis=emergency_resp["message"],
            disclaimer=SAFETY_DISCLAIMER,
            session_id=session_id
        )

    context_parts = [f"Gejala: {request.symptoms}"]
    if request.duration:
        context_parts.append(f"Durasi: {request.duration}")
    if request.age:
        context_parts.append(f"Usia: {request.age} tahun")
    if request.gender:
        context_parts.append(f"Jenis kelamin: {request.gender.value}")
    if request.existing_conditions:
        context_parts.append(f"Kondisi yang sudah ada: {request.existing_conditions}")

    user_prompt = "\n".join(context_parts)

    try:
        ai_response = await generate_response(user_prompt, SYMPTOM_SYSTEM_PROMPT)
        severity = determine_severity(ai_response)
        session_id = request.session_id or str(uuid.uuid4())

        db.add(ConsultationHistory(
            session_id=session_id,
            consultation_type="symptom",
            user_input=user_prompt,
            ai_response=ai_response,
            severity_level=severity.value
        ))
        db.commit()

        return SymptomResponse(
            is_emergency=False,
            severity_level=severity,
            analysis=ai_response,
            disclaimer=SAFETY_DISCLAIMER,
            session_id=session_id
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gagal memproses permintaan: {str(e)}")


@router.post("/followup", summary="Tindak lanjut pertanyaan tentang gejala")
async def symptom_followup(request: FollowupRequest, db: Session = Depends(get_db)):
    """
    Ajukan pertanyaan lanjutan tentang gejala dalam sesi yang sama.

    - **question**: Pertanyaan lanjutan
    - **session_id**: ID sesi dari response /check sebelumnya
    """
    history = db.query(ConsultationHistory).filter(
        ConsultationHistory.session_id == request.session_id,
        ConsultationHistory.consultation_type == "symptom"
    ).order_by(ConsultationHistory.created_at.desc()).limit(3).all()

    conversation_history = []
    for h in reversed(history):
        conversation_history.append({"role": "user", "content": h.user_input})
        conversation_history.append({"role": "assistant", "content": h.ai_response})

    try:
        ai_response = await generate_response(
            request.question, SYMPTOM_SYSTEM_PROMPT, conversation_history
        )

        db.add(ConsultationHistory(
            session_id=request.session_id,
            consultation_type="symptom",
            user_input=request.question,
            ai_response=ai_response,
            severity_level="low"
        ))
        db.commit()

        return {
            "response": ai_response,
            "disclaimer": SAFETY_DISCLAIMER,
            "session_id": request.session_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))