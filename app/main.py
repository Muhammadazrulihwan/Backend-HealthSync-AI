from app.routers import chatbot, medication, preventive, symptom, terminology
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import history
from app.database import init_db

app = FastAPI(
    title="AI-Powered Healthcare Assistant",
    description="Backend API untuk asisten kesehatan berbasis AI menggunakan Gemini",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    init_db()

app.include_router(symptom.router, prefix="/api/v1/symptom", tags=["Symptom Checker"])
app.include_router(medication.router, prefix="/api/v1/medication", tags=["Medication Info"])
app.include_router(chatbot.router, prefix="/api/v1/chatbot", tags=["Educational Chatbot"])
app.include_router(preventive.router, prefix="/api/v1/preventive", tags=["Preventive Care"])
app.include_router(history.router, prefix="/api/v1/history", tags=["Consultation History"])
app.include_router(terminology.router, prefix="/api/v1/terminology", tags=["Medical Terminology"])

@app.get("/", tags=["Root"])
async def root():
    return {
        "message": "AI-Powered Healthcare Assistant API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs"
    }

@app.get("/health", tags=["Root"])
async def health_check():
    return {"status": "healthy"}
