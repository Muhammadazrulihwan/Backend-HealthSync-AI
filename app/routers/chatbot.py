from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import uuid

from app.models.schemas import ChatbotRequest, ChatbotResponse
from app.services.gemini_service import (
    generate_response, check_emergency, get_emergency_response,
    CHATBOT_SYSTEM_PROMPT, SAFETY_DISCLAIMER
)
from app.database import get_db, ConsultationHistory

router = APIRouter()


@router.post("/chat", response_model=ChatbotResponse, summary="Chat dengan asisten kesehatan edukatif")
async def chat(request: ChatbotRequest, db: Session = Depends(get_db)):
    """
    Asisten chatbot edukatif untuk menjawab pertanyaan umum seputar kesehatan.
    Mendukung percakapan multi-turn dengan riwayat percakapan.
    
    - **message**: Pertanyaan atau pesan
    - **conversation_history**: Riwayat percakapan sebelumnya
    """
    if check_emergency(request.message):
        emergency = get_emergency_response()
        return ChatbotResponse(
            response=emergency["message"],
            disclaimer=SAFETY_DISCLAIMER,
            session_id=request.session_id or str(uuid.uuid4())
        )

    history = [{"role": m.role, "content": m.content} for m in request.conversation_history]

    try:
        ai_response = await generate_response(request.message, CHATBOT_SYSTEM_PROMPT, history)
        session_id = request.session_id or str(uuid.uuid4())

        db.add(ConsultationHistory(
            session_id=session_id,
            consultation_type="chatbot",
            user_input=request.message,
            ai_response=ai_response
        ))
        db.commit()

        return ChatbotResponse(
            response=ai_response,
            disclaimer=SAFETY_DISCLAIMER,
            session_id=session_id
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/topics", summary="Topik kesehatan yang tersedia")
async def get_health_topics():
    """Mendapatkan daftar topik kesehatan yang bisa ditanyakan."""
    return {
        "topics": [
            {"id": "nutrition", "name": "Gizi & Nutrisi", "description": "Panduan makan sehat dan kebutuhan gizi"},
            {"id": "exercise", "name": "Olahraga & Kebugaran", "description": "Tips aktivitas fisik yang tepat"},
            {"id": "mental_health", "name": "Kesehatan Mental", "description": "Manajemen stres dan kesehatan jiwa"},
            {"id": "chronic_disease", "name": "Penyakit Kronis", "description": "Informasi diabetes, hipertensi, dll"},
            {"id": "child_health", "name": "Kesehatan Anak", "description": "Pertumbuhan dan perkembangan anak"},
            {"id": "womens_health", "name": "Kesehatan Wanita", "description": "Kehamilan, menstruasi, menopause"},
            {"id": "elderly", "name": "Kesehatan Lansia", "description": "Tips hidup sehat di usia lanjut"},
            {"id": "first_aid", "name": "Pertolongan Pertama", "description": "Panduan P3K dasar"},
            {"id": "vaccines", "name": "Vaksinasi", "description": "Informasi imunisasi dan vaksin"},
            {"id": "hygiene", "name": "Kebersihan & Higiene", "description": "Praktik kebersihan yang baik"},
        ]
    }


@router.post("/topic/{topic_id}", summary="Tanya tentang topik kesehatan spesifik")
async def ask_about_topic(topic_id: str, question: str, db: Session = Depends(get_db)):
    """Ajukan pertanyaan tentang topik kesehatan tertentu."""
    topic_context = {
        "nutrition": "Fokus pada topik gizi dan nutrisi.",
        "exercise": "Fokus pada olahraga dan kebugaran fisik.",
        "mental_health": "Fokus pada kesehatan mental dan psikologi.",
        "chronic_disease": "Fokus pada penyakit kronis dan pengelolaannya.",
        "child_health": "Fokus pada kesehatan bayi dan anak.",
        "womens_health": "Fokus pada kesehatan wanita.",
        "elderly": "Fokus pada kesehatan lansia.",
        "first_aid": "Fokus pada pertolongan pertama dan P3K.",
        "vaccines": "Fokus pada vaksinasi dan imunisasi.",
        "hygiene": "Fokus pada kebersihan dan higiene.",
    }

    context = topic_context.get(topic_id, "")
    system = f"{CHATBOT_SYSTEM_PROMPT}\n\nKONTEKS TOPIK: {context}"

    try:
        ai_response = await generate_response(question, system)
        session_id = str(uuid.uuid4())

        db.add(ConsultationHistory(
            session_id=session_id,
            consultation_type=f"chatbot_{topic_id}",
            user_input=question,
            ai_response=ai_response
        ))
        db.commit()

        return {
            "topic": topic_id,
            "question": question,
            "response": ai_response,
            "disclaimer": SAFETY_DISCLAIMER,
            "session_id": session_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
