from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import uuid

from app.models.schemas import MedicationRequest, MedicationResponse
from app.services.gemini_service import (
    generate_response, MEDICATION_SYSTEM_PROMPT, SAFETY_DISCLAIMER
)
from app.database import get_db, ConsultationHistory

router = APIRouter()

INTERACTION_PROMPT = """
Kamu adalah asisten farmasi AI. Analisis kemungkinan interaksi antara obat-obat berikut.
Berikan informasi dalam Bahasa Indonesia yang jelas.

Format:
## Analisis Interaksi Obat
### Kombinasi yang Diperiksa
### Interaksi yang Diketahui
### Tingkat Risiko
### Rekomendasi
### ⚠️ Peringatan Penting
"""


@router.post("/info", response_model=MedicationResponse, summary="Informasi lengkap tentang obat")
async def get_medication_info(request: MedicationRequest, db: Session = Depends(get_db)):
    """
    Mendapatkan informasi umum tentang obat tertentu.
    
    - **medication_name**: Nama obat (generik atau merk)
    - **query_type**: Jenis informasi yang dibutuhkan
    - **other_medications**: Daftar obat lain untuk cek interaksi
    """
    if request.query_type == "interaction" and request.other_medications:
        prompt = f"Cek interaksi antara {request.medication_name} dengan {request.other_medications}"
        system = INTERACTION_PROMPT
    elif request.query_type == "dosage":
        prompt = f"Berikan informasi detail tentang dosis {request.medication_name}"
        system = MEDICATION_SYSTEM_PROMPT
    elif request.query_type == "side_effects":
        prompt = f"Jelaskan efek samping dari {request.medication_name} secara lengkap"
        system = MEDICATION_SYSTEM_PROMPT
    else:
        prompt = f"Berikan informasi lengkap tentang obat {request.medication_name}"
        system = MEDICATION_SYSTEM_PROMPT

    try:
        ai_response = await generate_response(prompt, system)
        session_id = request.session_id or str(uuid.uuid4())

        db.add(ConsultationHistory(
            session_id=session_id,
            consultation_type="medication",
            user_input=prompt,
            ai_response=ai_response
        ))
        db.commit()

        return MedicationResponse(
            medication_name=request.medication_name,
            information=ai_response,
            disclaimer=SAFETY_DISCLAIMER,
            session_id=session_id
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search/{name}", summary="Cari informasi obat berdasarkan nama")
async def search_medication(name: str, db: Session = Depends(get_db)):
    """Pencarian cepat informasi obat berdasarkan nama."""
    prompt = f"Berikan ringkasan singkat tentang obat {name}: kegunaan utama, dosis umum, dan peringatan utama."
    try:
        ai_response = await generate_response(prompt, MEDICATION_SYSTEM_PROMPT)
        return {"medication_name": name, "summary": ai_response, "disclaimer": SAFETY_DISCLAIMER}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
