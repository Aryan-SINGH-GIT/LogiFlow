"""
LangGraph service for multi-day logbook generation.
"""
import os
import json
from typing import TypedDict, List
from pydantic import BaseModel, Field

from langchain_core.messages import SystemMessage, HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, START, END

from schemas import GenerateWeekLogbookRequest, WeekLogbookResponse, LogbookContent
from services.ai_service import _wrap_section, LOGBOOK_PROMPT_TEMPLATE


# Data structure for the LLM output of daily breakdown
class DailyBreakdown(BaseModel):
    date: str
    day_overview: str

class BreakdownResponse(BaseModel):
    days: list[DailyBreakdown]


# State definition for LangGraph
class WeekLogbookState(TypedDict):
    request: GenerateWeekLogbookRequest
    daily_overviews: list[str]  # Just the text overview for days
    daily_dates: list[str]      # The dates for those overviews
    generated_days: list[LogbookContent]  # The structured day outputs
    next_week_context: str
    current_day_index: int


def _get_llm():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY is not set in .env")
    return ChatGoogleGenerativeAI(model="gemini-2.5-flash", api_key=api_key, temperature=0.7)


def breakdown_prompt_node(state: WeekLogbookState) -> WeekLogbookState:
    """Breakdown the single weekly prompt into distinct daily overviews between start and end dates."""
    llm = _get_llm()
    structured_llm = llm.with_structured_output(schema=BreakdownResponse)
    
    req = state["request"]
    
    sys_msg = SystemMessage(content="You are an expert software engineering intern planner.")
    human_msg = HumanMessage(content=f"""
Please breakdown the following work description into distinct daily accomplishments.
Make sure to distribute the work logically sequentially across the days between the given start date and end date inclusive.
For each day, provide the specific date string.

Start Date: {req.start_date}
End Date: {req.end_date}
Project Description: {req.project_description}
Tech Stack: {req.tech_stack}
Previous Week Context: {req.previous_week_context}

Work Description:
{req.week_prompt}
""")
    
    response: BreakdownResponse = structured_llm.invoke([sys_msg, human_msg])
    
    # Sort and guarantee order
    sorted_days = sorted(response.days, key=lambda d: d.date)
    overviews = [day.day_overview for day in sorted_days]
    dates = [day.date for day in sorted_days]
    
    return {
        **state,
        "daily_overviews": overviews,
        "daily_dates": dates,
        "current_day_index": 0,
        "generated_days": []
    }


def generate_day_node(state: WeekLogbookState) -> WeekLogbookState:
    """Generate the detailed logbook content for the current day."""
    idx = state["current_day_index"]
    req = state["request"]
    day_overview = state["daily_overviews"][idx]
    current_date_str = state["daily_dates"][idx]
    
    llm = _get_llm()
    structured_llm = llm.with_structured_output(schema=LogbookContent)
    
    # Passing the exact date string. (You can still assign day_number statically as 1 to avoid breaking the prompt formatting if it literally expects an integer, or pass the string). To ensure formatting is intact, we will just pass idx + 1 representing Day 1, Day 2 inside the prompt logic while grounding the model in the real date.
    # Actually, modifyLOGBOOK_PROMPT_TEMPLATE or just pass current_date_str. The current prompt accepts `{day_number}`, we'll pass the date string safely by interpolating it.
    prompt = LOGBOOK_PROMPT_TEMPLATE.format(
        day_number=current_date_str,
        project_description=req.project_description,
        tech_stack=req.tech_stack,
        day_overview=day_overview
    )
    
    response: LogbookContent = structured_llm.invoke([HumanMessage(content=prompt)])
    
    # Wrapper function logic from ai_service.py to fit PDF boxes
    wrapped_content = LogbookContent(
        my_space=_wrap_section(response.my_space, "my_space"),
        tasks_carried_out=_wrap_section(response.tasks_carried_out, "tasks_carried_out"),
        key_learnings=_wrap_section(response.key_learnings, "key_learnings"),
        tools_used=_wrap_section(response.tools_used, "tools_used"),
        special_achievements=_wrap_section(response.special_achievements, "special_achievements")
    )
    
    new_generated_days = state["generated_days"] + [wrapped_content]
    
    return {
        **state,
        "generated_days": new_generated_days,
        "current_day_index": idx + 1
    }


def check_if_done(state: WeekLogbookState) -> str:
    """Conditional edge to determine if we should generate another day or finish."""
    if state["current_day_index"] < len(state["daily_overviews"]):
        return "generate_day"
    return "generate_context"


class ContextResponse(BaseModel):
    next_week_context: str


def generate_context_node(state: WeekLogbookState) -> WeekLogbookState:
    """Generate a summary of this week to use for next week's context."""
    llm = _get_llm()
    structured_llm = llm.with_structured_output(schema=ContextResponse)
    
    all_overviews = "\n".join([f"Day {i+1}: {overview}" for i, overview in enumerate(state["daily_overviews"])])
    
    sys_msg = SystemMessage(content="You are organizing the transition points for a multi-week project.")
    human_msg = HumanMessage(content=f"""
Based on the following 5 days of work completed this week, generate a concise summary of the current project state (1-2 sentences max).
This will be used as the 'Previous Week Context' for the prompt generating the following week's logbook.

This Week's Work:
{all_overviews}
""")
    response: ContextResponse = structured_llm.invoke([sys_msg, human_msg])
    
    return {
        **state,
        "next_week_context": response.next_week_context
    }


# Build LangGraph
workflow = StateGraph(WeekLogbookState)

workflow.add_node("breakdown_prompt", breakdown_prompt_node)
workflow.add_node("generate_day", generate_day_node)
workflow.add_node("generate_context", generate_context_node)

workflow.add_edge(START, "breakdown_prompt")
workflow.add_edge("breakdown_prompt", "generate_day")
workflow.add_conditional_edges("generate_day", check_if_done, {
    "generate_day": "generate_day",
    "generate_context": "generate_context"
})
workflow.add_edge("generate_context", END)

# Compile graph
week_logbook_app = workflow.compile()


def run_weekly_generation_pipeline(request: GenerateWeekLogbookRequest) -> WeekLogbookResponse:
    """
    Kicks off the LangGraph pipeline to generate a week of logbook content.
    """
    initial_state = WeekLogbookState(
        request=request,
        daily_overviews=[],
        daily_dates=[],
        generated_days=[],
        next_week_context="",
        current_day_index=0
    )
    
    final_state = week_logbook_app.invoke(initial_state)
    
    return WeekLogbookResponse(
        days=final_state["generated_days"],
        next_week_context=final_state["next_week_context"]
    )
