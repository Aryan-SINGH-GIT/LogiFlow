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


class GenerateWeekLogbookRequest(BaseModel):
    project_description: str
    tech_stack: str
    week_prompt: str
    start_date: str
    end_date: str
    start_pdf_day: Optional[int] = 1
    previous_week_context: Optional[str] = ""


class WeekLogbookResponse(BaseModel):
    days: list[LogbookContent]
    next_week_context: str
