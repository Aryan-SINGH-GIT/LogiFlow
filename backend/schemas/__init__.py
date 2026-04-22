"""
Pydantic schemas for the OJL Logbook PDF Editor API.
"""
from pydantic import BaseModel
from typing import Optional
from services.pdf_service import EditItem  # re-export for route use


class EditRequest(BaseModel):
    filename: str
    edits: list[EditItem]


class GenerateLogbookRequest(BaseModel):
    project_description: str
    tech_stack: str
    day_overview: str
    day_number: Optional[int] = 1


class LogbookContent(BaseModel):
    """Structured AI response for logbook generation."""
    my_space: str
    tasks_carried_out: str
    key_learnings: str
    tools_used: str
    special_achievements: str


class BatchLogbookContent(BaseModel):
    """Batch wrapper for generating multiple days at once."""
    days: list[LogbookContent]


class GenerateMonthLogbookRequest(BaseModel):
    project_description: str
    tech_stack: str
    month_prompt: str
    dates: list[str]
    start_pdf_day: int = 1
    previous_month_context: str = ""
    registration_no: Optional[str] = None
    gemini_api_key: Optional[str] = None   # User-supplied key (overrides .env)
    groq_api_key: Optional[str] = None     # User-supplied key (overrides .env)


class MonthLogbookResponse(BaseModel):
    days: list[LogbookContent]
    next_month_context: str = ""
