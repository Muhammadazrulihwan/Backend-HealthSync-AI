from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import uuid

from app.models.schemas import TerminologyRequest, TerminologyResponse
from app.services.gemini_service import (
    generate_response, TERMINOLOGY_SYSTEM_PROMPT, SAFETY_DISCLAIMER
)
from app.database import get_db, ConsultationHistory

router = APIRouter()


@router.post("/explain", response_model=TerminologyResponse, summary="Jelaskan istilah medis")
async def explain_terminology(request: TerminologyRequest, db: Session = Depends(get_db)):
    """
    Menjelaskan istilah medis dalam bahasa yang mudah dipahami.
    
    - **term**: Istilah medis yang ingin dijelaskan
    - **context**: Konteks di mana istilah ditemukan (opsional)
    """
    prompt = f"Jelaskan istilah medis: {request.term}"
    if request.context:
        prompt += f"\nKonteks: {request.context}"

    try:
        ai_response = await generate_response(prompt, TERMINOLOGY_SYSTEM_PROMPT)
        session_id = request.session_id or str(uuid.uuid4())

        db.add(ConsultationHistory(
            session_id=session_id,
            consultation_type="terminology",
            user_input=prompt,
            ai_response=ai_response
        ))
        db.commit()

        return TerminologyResponse(
            term=request.term,
            explanation=ai_response,
            disclaimer=SAFETY_DISCLAIMER,
            session_id=session_id
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/explain-report", summary="Jelaskan hasil laporan medis")
async def explain_medical_report(report_text: str, db: Session = Depends(get_db)):
    """
    Menjelaskan isi laporan medis atau hasil lab dalam bahasa awam.
    """
    prompt = f"""
    Berikut adalah teks dari laporan/hasil medis:
    ---
    {report_text}
    ---
    
    Tolong jelaskan:
    1. Setiap nilai atau istilah medis yang ada
    2. Apakah nilai tersebut normal atau tidak
    3. Apa artinya secara umum
    4. Pertanyaan apa yang sebaiknya ditanyakan ke dokter
    
    Gunakan bahasa awam yang mudah dipahami.
    """

    try:
        ai_response = await generate_response(prompt, TERMINOLOGY_SYSTEM_PROMPT)
        session_id = str(uuid.uuid4())

        db.add(ConsultationHistory(
            session_id=session_id,
            consultation_type="terminology_report",
            user_input=report_text[:500],
            ai_response=ai_response
        ))
        db.commit()

        return {
            "original_report": report_text[:200] + "..." if len(report_text) > 200 else report_text,
            "explanation": ai_response,
            "disclaimer": SAFETY_DISCLAIMER,
            "session_id": session_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/common-terms", summary="Istilah medis yang sering ditemui")
async def get_common_terms(category: str = "general"):
    """
    Mendapatkan penjelasan istilah medis yang sering ditemui di kategori tertentu.
    Kategori: general, lab_results, cardiovascular, diabetes
    """
    category_terms = {
        "general": "hipertensi, diabetes, kolesterol, BMI, tekanan darah sistol diastol",
        "lab_results": "hemoglobin, leukosit, trombosit, hematokrit, LED, SGOT, SGPT, kreatinin",
        "cardiovascular": "aritmia, aterosklerosis, infark miokard, ejeksi fraksi, stenosis",
        "diabetes": "HbA1c, gula darah puasa, insulin, hiperglikemia, neuropati diabetik"
    }

    terms = category_terms.get(category, category_terms["general"])
    prompt = f"Jelaskan secara singkat istilah-istilah medis berikut dalam bahasa awam: {terms}"

    try:
        ai_response = await generate_response(prompt, TERMINOLOGY_SYSTEM_PROMPT)
        return {"category": category, "explanations": ai_response, "disclaimer": SAFETY_DISCLAIMER}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
