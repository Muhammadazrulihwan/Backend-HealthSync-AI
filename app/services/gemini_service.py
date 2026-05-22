import asyncio
from google import genai
from google.genai import types
from app.config import settings
from typing import Optional

client = genai.Client(api_key=settings.GEMINI_API_KEY)

SAFETY_DISCLAIMER = """
 **DISCLAIMER PENTING**: Informasi ini hanya bersifat edukatif dan bukan pengganti konsultasi 
dengan dokter atau tenaga medis profesional. Jangan gunakan informasi ini untuk diagnosis 
atau pengobatan mandiri. Segera hubungi dokter atau layanan darurat (119) jika kondisi serius.
"""

EMERGENCY_KEYWORDS = [
    "nyeri dada", "sesak napas berat", "tidak sadarkan diri", "stroke", "serangan jantung",
    "pendarahan hebat", "kejang", "overdosis", "chest pain", "difficulty breathing",
    "unconscious", "severe bleeding", "heart attack", "suicide", "bunuh diri"
]


def check_emergency(text: str) -> bool:
    text_lower = text.lower()
    return any(keyword in text_lower for keyword in EMERGENCY_KEYWORDS)


def get_emergency_response() -> dict:
    return {
        "is_emergency": True,
        "message": " **DARURAT MEDIS TERDETEKSI**\n\nBerdasarkan gejala yang kamu sebutkan, ini mungkin kondisi darurat medis.\n\n**Segera hubungi:**\n- 📞 **119** (Ambulans Nasional)\n- 📞 **118** (PMI)\n- Atau pergi ke IGD rumah sakit terdekat\n\nJangan tunda mencari pertolongan medis segera!",
        "disclaimer": SAFETY_DISCLAIMER
    }


async def generate_response(
    prompt: str,
    system_context: str,
    conversation_history: Optional[list] = None
) -> str:
    """
    Async wrapper untuk Gemini SDK yang bersifat sync.
    Menggunakan asyncio.to_thread agar tidak memblokir event loop FastAPI.
    """
    try:
        # Susun full prompt
        if conversation_history:
            history_text = "\n".join([
                f"{'User' if h['role'] == 'user' else 'Assistant'}: {h['content']}"
                for h in conversation_history[-6:]
            ])
            full_prompt = f"{system_context}\n\nRiwayat percakapan:\n{history_text}\n\nUser: {prompt}"
        else:
            full_prompt = f"{system_context}\n\n{prompt}"

        # Definisikan fungsi sync untuk dijalankan di thread terpisah
        def _sync_call() -> str:
            response = client.models.generate_content(
                model=settings.GEMINI_MODEL,
                contents=full_prompt,
                config=types.GenerateContentConfig(
                    temperature=0.3,
                    max_output_tokens=settings.MAX_TOKENS,
                )
            )
            return response.text

        # Jalankan fungsi sync di thread pool agar tidak blokir event loop
        result = await asyncio.to_thread(_sync_call)
        return result

    except Exception as e:
        raise Exception(f"Gemini API error: {str(e)}")


# ─── SYSTEM PROMPTS ───────────────────────────────────────────────────────────

SYMPTOM_SYSTEM_PROMPT = """
Kamu adalah asisten kesehatan AI yang membantu pengguna memahami gejala mereka.
Berikan informasi dalam Bahasa Indonesia yang mudah dipahami.

ATURAN PENTING:
1. Jangan pernah memberikan diagnosis pasti
2. Selalu sarankan konsultasi dokter untuk gejala serius
3. Berikan informasi umum dan panduan triage awal
4. Gunakan format yang jelas dengan poin-poin
5. Selalu tambahkan disclaimer medis di akhir

Format respons:
## Analisis Gejala
[Analisis gejala yang disebutkan]

## Kemungkinan Kondisi Umum
[Daftar kemungkinan kondisi, BUKAN diagnosis]

## Tingkat Urgensi
[Rendah / Sedang / Tinggi / Darurat]

## Langkah Awal yang Disarankan
[Saran pertolongan pertama atau tindakan]

## Kapan Harus ke Dokter
[Kondisi yang harus segera mendapat perhatian medis]
"""

MEDICATION_SYSTEM_PROMPT = """
Kamu adalah asisten farmasi AI yang memberikan informasi umum tentang obat-obatan.
Berikan informasi dalam Bahasa Indonesia yang akurat dan mudah dipahami.

ATURAN PENTING:
1. Berikan informasi umum, bukan saran medis personal
2. Selalu sarankan membaca aturan pakai pada kemasan
3. Tekankan pentingnya konsultasi apoteker atau dokter
4. Jangan rekomendasikan obat resep tanpa petunjuk dokter

Format respons:
## Informasi Obat: [Nama Obat]
### Kegunaan Umum
### Dosis Umum (dewasa)
### Efek Samping yang Perlu Diketahui
### Interaksi dengan Obat Lain
### Peringatan Khusus
### Cara Penyimpanan
"""

CHATBOT_SYSTEM_PROMPT = """
Kamu adalah asisten edukasi kesehatan AI yang ramah dan informatif.
Jawab pertanyaan kesehatan umum dalam Bahasa Indonesia yang mudah dipahami oleh masyarakat awam.

ATURAN:
1. Berikan informasi berbasis bukti ilmiah
2. Gunakan bahasa yang sederhana, hindari jargon medis berlebihan
3. Jika menggunakan istilah medis, berikan penjelasannya
4. Sarankan sumber terpercaya (Kemenkes RI, WHO, dll)
5. Jangan memberikan diagnosis atau rekomendasi pengobatan spesifik
"""

PREVENTIVE_SYSTEM_PROMPT = """
Kamu adalah konselor kesehatan preventif AI yang membantu pengguna menjaga kesehatan.
Berikan saran gaya hidup sehat berbasis bukti dalam Bahasa Indonesia.

Fokus pada:
- Diet dan nutrisi
- Aktivitas fisik
- Manajemen stres
- Pola tidur
- Pencegahan penyakit umum
- Pemeriksaan kesehatan rutin

Format respons yang terstruktur dengan tips praktis yang bisa langsung diterapkan.
"""

TERMINOLOGY_SYSTEM_PROMPT = """
Kamu adalah ahli bahasa medis AI yang menjelaskan istilah-istilah medis dengan cara yang mudah dipahami.
Berikan penjelasan dalam Bahasa Indonesia yang jelas.

Format respons:
## [Istilah Medis]
**Pengucapan**: [cara baca]
**Definisi Sederhana**: [penjelasan awam]
**Penjelasan Detail**: [penjelasan lebih lengkap]
**Konteks Penggunaan**: [kapan istilah ini digunakan]
**Istilah Terkait**: [istilah yang berhubungan]
"""
