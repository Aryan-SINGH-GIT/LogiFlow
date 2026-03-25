"""
OJL Logbook PDF Editor API — application entry point.

Architecture:
  schemas/        → Pydantic request/response models
  routes/pdf.py   → Upload, extract-text, edit, download endpoints
  routes/logbook.py → AI logbook generation endpoint
  services/pdf_service.py → PyMuPDF business logic
  services/ai_service.py  → Google Gemini AI integration
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from schemas import GenerateLogbookRequest, GenerateMonthLogbookRequest
from services.ai_service import generate_logbook_content
from services.langgraph_service import run_monthly_generation_pipeline
from dotenv import load_dotenv

from routes.pdf import router as pdf_router
from routes.logbook import router as logbook_router
from services.pdf_service import ensure_dirs

# Load environment variables from .env
load_dotenv()

# Ensure upload/output directories exist
ensure_dirs()

app = FastAPI(
    title="OJL Logbook PDF Editor API",
    description="Edit PDF logbooks manually or generate content via AI.",
    version="1.0.0",
)

# Allow React dev server (Vite default port)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(pdf_router)
app.include_router(logbook_router)


@app.get("/", summary="Health check", tags=["Health"])
async def root():
    return {"status": "ok", "message": "OJL Logbook PDF Editor API is running."}
