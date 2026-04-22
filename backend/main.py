"""
OJL Logbook PDF Editor API — application entry point.

Architecture:
  schemas/        → Pydantic request/response models
  routes/pdf.py   → Upload, extract-text, edit, download endpoints
  routes/logbook.py → AI logbook generation endpoint
  services/pdf_service.py → PyMuPDF business logic
  services/ai_service.py  → Google Gemini AI integration
"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from routes.pdf import router as pdf_router
from routes.logbook import router as logbook_router
from services.pdf_service import ensure_dirs
from database import get_db, close_db

logger = logging.getLogger(__name__)

# Load environment variables from .env
load_dotenv()

# Ensure upload/output directories exist
ensure_dirs()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Setup database connection — non-fatal if MongoDB is unavailable
    try:
        get_db()
        logger.info("MongoDB connection established.")
    except Exception as e:
        logger.warning(f"MongoDB connection failed at startup: {e}. Context persistence will be disabled.")
    yield
    # Cleanup
    await close_db()

app = FastAPI(
    title="OJL Logbook PDF Editor API",
    description="Edit PDF logbooks manually or generate content via AI.",
    version="1.0.0",
    lifespan=lifespan,
)

# Allow React dev server and production Vercel deployments
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174",  # fallback if 5173 is taken
        "https://logi-flow-zeta.vercel.app",  # Production frontend
    ],
    allow_origin_regex=r"https://.*\.vercel\.app",  # all Vercel preview/prod URLs
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
