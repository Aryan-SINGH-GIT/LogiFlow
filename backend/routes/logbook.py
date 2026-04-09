"""
Logbook AI generation route.
"""
import asyncio
from fastapi import APIRouter, HTTPException

import os
from database import get_db
from schemas import GenerateLogbookRequest, GenerateMonthLogbookRequest, MonthLogbookResponse
from services.ai_service import generate_logbook_content
from services.langgraph_service import run_monthly_generation_pipeline, cancel_task

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

@router.post("/generate-month-logbook", response_model=MonthLogbookResponse, summary="Generate up to 20 days of logbook content using LangGraph")
async def generate_month_logbook(request: GenerateMonthLogbookRequest, task_id: str = None):
    """
    Call the LangGraph pipeline to generate a month of structured logbook content
    based on the month's prompt, project description, and previous context.
    Returns generated content and a context string for next month.
    """
    try:
        db = get_db()
        contexts_collection = db["contexts"]

        # Inject previous context if a registration number is provided
        if request.registration_no:
            doc = await contexts_collection.find_one({"registration_no": request.registration_no})
            if doc and "context" in doc:
                request.previous_month_context = doc["context"]

        # Pass task_id if provided by frontend
        response = await run_monthly_generation_pipeline(request, task_id=task_id)
        
        # Save new context for next month
        if request.registration_no and response.next_month_context:
            await contexts_collection.update_one(
                {"registration_no": request.registration_no},
                {"$set": {"context": response.next_month_context}},
                upsert=True
            )
            
        return response
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except asyncio.CancelledError:
        # Gracefully handle the cancellation signal
        raise HTTPException(status_code=499, detail="Task was cancelled.")
    except Exception as e:
        if "cancelled" in str(e).lower():
            raise HTTPException(status_code=499, detail="Task was cancelled.")
        raise HTTPException(status_code=500, detail=f"Graph generation error: {str(e)}")


@router.post("/cancel-generation/{task_id}", summary="Cancel an ongoing logbook generation")
async def cancel_generation(task_id: str):
    """
    Signal the backend to stop a specific generation task.
    """
    cancel_task(task_id)
    return {"status": "ok", "message": f"Cancellation signal sent for task {task_id}"}

