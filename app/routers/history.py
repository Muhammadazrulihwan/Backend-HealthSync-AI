from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid

from app.models.schemas import HistoryResponse, UserProfileCreate, UserProfileResponse
from app.database import get_db, ConsultationHistory, UserProfile
import json

router = APIRouter()


@router.get("/session/{session_id}", response_model=List[HistoryResponse], summary="Riwayat konsultasi per sesi")
async def get_session_history(
    session_id: str,
    db: Session = Depends(get_db),
    limit: int = Query(default=20, le=100)
):
    """Mendapatkan semua riwayat konsultasi dalam satu sesi."""
    records = db.query(ConsultationHistory).filter(
        ConsultationHistory.session_id == session_id
    ).order_by(ConsultationHistory.created_at.asc()).limit(limit).all()

    if not records:
        raise HTTPException(status_code=404, detail="Sesi tidak ditemukan")
    return records


@router.get("/user/{user_id}", response_model=List[HistoryResponse], summary="Riwayat konsultasi per pengguna")
async def get_user_history(
    user_id: str,
    db: Session = Depends(get_db),
    consultation_type: Optional[str] = None,
    limit: int = Query(default=20, le=100)
):
    """Mendapatkan riwayat konsultasi pengguna dengan filter opsional."""
    query = db.query(ConsultationHistory).filter(
        ConsultationHistory.user_id == user_id
    )
    if consultation_type:
        query = query.filter(ConsultationHistory.consultation_type == consultation_type)

    records = query.order_by(ConsultationHistory.created_at.desc()).limit(limit).all()
    return records


@router.delete("/session/{session_id}", summary="Hapus riwayat sesi")
async def delete_session(session_id: str, db: Session = Depends(get_db)):
    """Menghapus semua riwayat dalam satu sesi."""
    deleted = db.query(ConsultationHistory).filter(
        ConsultationHistory.session_id == session_id
    ).delete()
    db.commit()

    if deleted == 0:
        raise HTTPException(status_code=404, detail="Sesi tidak ditemukan")
    return {"message": f"Berhasil menghapus {deleted} record dari sesi {session_id}"}


@router.get("/stats/summary", summary="Statistik penggunaan")
async def get_usage_stats(db: Session = Depends(get_db)):
    """Mendapatkan statistik penggunaan keseluruhan."""
    total = db.query(ConsultationHistory).count()

    type_counts = {}
    for ctype in ["symptom", "medication", "chatbot", "preventive", "terminology"]:
        count = db.query(ConsultationHistory).filter(
            ConsultationHistory.consultation_type.like(f"{ctype}%")
        ).count()
        type_counts[ctype] = count

    emergency_count = db.query(ConsultationHistory).filter(
        ConsultationHistory.severity_level == "emergency"
    ).count()

    return {
        "total_consultations": total,
        "by_type": type_counts,
        "emergency_cases": emergency_count
    }


# ─── USER PROFILE ─────────────────────────────────────────────────────────────

@router.post("/profile", response_model=UserProfileResponse, summary="Buat atau update profil pengguna")
async def create_or_update_profile(profile: UserProfileCreate, db: Session = Depends(get_db)):
    """Membuat atau memperbarui profil pengguna untuk personalisasi."""
    existing = db.query(UserProfile).filter(UserProfile.user_id == profile.user_id).first()

    conditions_json = json.dumps(profile.existing_conditions) if profile.existing_conditions else None
    allergies_json = json.dumps(profile.allergies) if profile.allergies else None

    if existing:
        existing.age = profile.age
        existing.gender = profile.gender.value if profile.gender else None
        existing.existing_conditions = conditions_json
        existing.allergies = allergies_json
        db.commit()
        db.refresh(existing)
        return existing
    else:
        new_profile = UserProfile(
            user_id=profile.user_id,
            age=profile.age,
            gender=profile.gender.value if profile.gender else None,
            existing_conditions=conditions_json,
            allergies=allergies_json
        )
        db.add(new_profile)
        db.commit()
        db.refresh(new_profile)
        return new_profile


@router.get("/profile/{user_id}", response_model=UserProfileResponse, summary="Ambil profil pengguna")
async def get_profile(user_id: str, db: Session = Depends(get_db)):
    """Mendapatkan profil pengguna berdasarkan user ID."""
    profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profil tidak ditemukan")
    return profile
