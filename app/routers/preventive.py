from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import uuid

from app.models.schemas import PreventiveRequest, PreventiveResponse
from app.services.gemini_service import (
    generate_response, PREVENTIVE_SYSTEM_PROMPT, SAFETY_DISCLAIMER
)
from app.database import get_db, ConsultationHistory

router = APIRouter()


@router.post("/suggest", response_model=PreventiveResponse, summary="Saran pencegahan penyakit & gaya hidup sehat")
async def get_preventive_suggestions(request: PreventiveRequest, db: Session = Depends(get_db)):
    """
    Mendapatkan saran kesehatan preventif yang dipersonalisasi.
    
    - **topic**: Topik kesehatan preventif yang ingin ditanyakan
    - **age**: Usia untuk saran yang lebih tepat
    - **gender**: Jenis kelamin
    - **lifestyle_info**: Gambaran gaya hidup saat ini
    """
    context_parts = [f"Topik: {request.topic}"]
    if request.age:
        context_parts.append(f"Usia: {request.age} tahun")
    if request.gender:
        context_parts.append(f"Jenis kelamin: {request.gender.value}")
    if request.lifestyle_info:
        context_parts.append(f"Gaya hidup saat ini: {request.lifestyle_info}")

    prompt = "\n".join(context_parts) + "\n\nBerikan saran kesehatan preventif yang praktis dan spesifik."

    try:
        ai_response = await generate_response(prompt, PREVENTIVE_SYSTEM_PROMPT)
        session_id = request.session_id or str(uuid.uuid4())

        db.add(ConsultationHistory(
            session_id=session_id,
            consultation_type="preventive",
            user_input=prompt,
            ai_response=ai_response
        ))
        db.commit()

        return PreventiveResponse(
            topic=request.topic,
            recommendations=ai_response,
            disclaimer=SAFETY_DISCLAIMER,
            session_id=session_id
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/screening-schedule", summary="Jadwal pemeriksaan kesehatan rutin")
async def get_screening_schedule(age: int, gender: str = "general"):
    """
    Mendapatkan rekomendasi jadwal pemeriksaan kesehatan rutin berdasarkan usia.
    """
    prompt = f"""
    Buat jadwal pemeriksaan kesehatan rutin yang direkomendasikan untuk:
    - Usia: {age} tahun
    - Jenis kelamin: {gender}
    
    Sertakan: jenis pemeriksaan, frekuensi, dan alasan pentingnya.
    Format dengan tabel atau daftar yang mudah dibaca.
    """
    try:
        ai_response = await generate_response(prompt, PREVENTIVE_SYSTEM_PROMPT)
        return {
            "age": age,
            "gender": gender,
            "schedule": ai_response,
            "disclaimer": SAFETY_DISCLAIMER
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health-tips/daily", summary="Tips kesehatan harian")
async def get_daily_health_tips(category: str = "general"):
    """
    Mendapatkan tips kesehatan harian berdasarkan kategori.
    Kategori: general, nutrition, exercise, mental_health, sleep
    """
    category_prompts = {
        "general": "Berikan 5 tips kesehatan umum yang praktis untuk diterapkan hari ini",
        "nutrition": "Berikan 5 tips nutrisi dan pola makan sehat untuk hari ini",
        "exercise": "Berikan 5 tips olahraga atau aktivitas fisik yang bisa dilakukan hari ini",
        "mental_health": "Berikan 5 tips menjaga kesehatan mental dan mengelola stres hari ini",
        "sleep": "Berikan 5 tips meningkatkan kualitas tidur untuk malam ini"
    }

    prompt = category_prompts.get(category, category_prompts["general"])

    try:
        ai_response = await generate_response(prompt, PREVENTIVE_SYSTEM_PROMPT)
        return {"category": category, "tips": ai_response, "disclaimer": SAFETY_DISCLAIMER}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
