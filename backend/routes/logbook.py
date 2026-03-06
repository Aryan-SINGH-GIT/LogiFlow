"""
Logbook AI generation route.
"""
from fastapi import APIRouter, HTTPException

from schemas import GenerateLogbookRequest, GenerateWeekLogbookRequest, WeekLogbookResponse
from services.ai_service import generate_logbook_content
from services.langgraph_service import run_weekly_generation_pipeline

router = APIRouter(tags=["Logbook"])


@router.post("/generate-logbook", summary="Generate logbook content using AI")
async def generate_logbook(request: GenerateLogbookRequest):
    """
    Call Google Gemini AI to generate structured logbook content
    based on the project description and day's overview.
    Returns wrapped text for each of the 5 logbook sections.
    """
    try:
        content = generate_logbook_content(
            project_description=request.project_description,
            tech_stack=request.tech_stack,
            day_overview=request.day_overview,
            day_number=request.day_number,
        )
        return content
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/generate-week-logbook", response_model=WeekLogbookResponse, summary="Generate 5 days of logbook content using LangGraph")
async def generate_week_logbook(request: GenerateWeekLogbookRequest):
    """
    Call the LangGraph pipeline to generate 5 days of structured logbook content
    based on the week's prompt, project description, and previous context.
    Returns 5 full days of wraps content and a context string for next week.
    """
    try:
        response = run_weekly_generation_pipeline(request)
        return response
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Graph generation error: {str(e)}")

