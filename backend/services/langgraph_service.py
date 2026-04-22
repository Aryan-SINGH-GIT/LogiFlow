"""
LangGraph service for multi-day logbook generation.
"""
import os
import json
import asyncio
import time
import logging
from typing import TypedDict, List, Set, Dict, Any, Optional

logger = logging.getLogger(__name__)
if not logger.handlers:
    # Setup basic logging to stdout if not done
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
logger.setLevel(logging.INFO)

from typing import TypedDict, List, Set, Dict, Any, Optional
from pydantic import BaseModel, Field

from langchain_core.messages import SystemMessage, HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, START, END

from schemas import GenerateMonthLogbookRequest, MonthLogbookResponse, LogbookContent, BatchLogbookContent
from services.ai_service import _wrap_section, LOGBOOK_PROMPT_TEMPLATE


class DailyBreakdown(BaseModel):
    date: str
    day_overview: str

class BreakdownResponse(BaseModel):
    days: list[DailyBreakdown]


class MonthLogbookState(TypedDict):
    request: GenerateMonthLogbookRequest
    daily_overviews: list[str]  # Just the text overview for days
    daily_dates: list[str]      # The dates for those overviews
    generated_days: list[LogbookContent]  # The structured day outputs
    next_month_context: str
    task_id: Optional[str]
    user_gemini_key: Optional[str]  # Per-request user-supplied Gemini API key
    user_groq_key: Optional[str]    # Per-request user-supplied Groq API key


# Global set to track cancelled task IDs
CANCELLED_TASKS: Set[str] = set()

def cancel_task(task_id: Optional[str]):
    """Marks a task as cancelled."""
    if task_id:
        CANCELLED_TASKS.add(task_id)

def is_cancelled(task_id: Optional[str]) -> bool:
    """Checks if a task has been cancelled."""
    if not task_id:
        return False
    return task_id in CANCELLED_TASKS

def clear_task(task_id: Optional[str]):
    """Cleans up a task ID after completion or cancellation."""
    if task_id and task_id in CANCELLED_TASKS:
        CANCELLED_TASKS.remove(task_id)


DEFAULT_FALLBACK = [
    "gemini-2.5-flash",
    "gemini-2.0-flash",
    "gemini-3.1-pro-preview",
    "gemini-3-flash-preview",
    "gemini-3.1-flash-lite-preview",
    "gemma-3-27b-it",
    "gemma-3-12b-it",
    "gemma-3-4b-it",
    "gemma-3-1b-it"
]

async def invoke_with_fallback(
    schema: Any,
    messages: List[Any],
    task_id: Optional[str] = None,
    preferred_models: Optional[List[str]] = None,
    max_retries_per_model: int = 2,
    user_gemini_key: Optional[str] = None,
    user_groq_key: Optional[str] = None,
) -> Any:
    """Robust fallback: cycle through models, waiting short durations on 429 errors before trying next attempt/model.
    User-supplied keys take priority over .env values.
    """
    if task_id and is_cancelled(task_id):
        raise asyncio.CancelledError(f"Task {task_id} was cancelled.")

    models_to_try = preferred_models if preferred_models else DEFAULT_FALLBACK
        
    last_err = None
    for model_name in models_to_try:
        is_groq = model_name.startswith("llama") or model_name.startswith("mixtral")
        
        if is_groq:
            api_key = user_groq_key or os.environ.get("GROQ_API_KEY")
            if not api_key:
                logger.warning(f"[{model_name}] No Groq API key available — skipping.")
                continue
            llm = ChatGroq(model=model_name, api_key=api_key, temperature=0.7)
        else:
            api_key = user_gemini_key or os.environ.get("GEMINI_API_KEY")
            if not api_key:
                raise ValueError("No Gemini API key provided. Please supply your Gemini API key.")
            llm = ChatGoogleGenerativeAI(model=model_name, api_key=api_key, temperature=0.7)
            
        structured_llm = llm.with_structured_output(schema=schema)
        
        for attempt in range(max_retries_per_model):
            if task_id and is_cancelled(task_id):
                raise asyncio.CancelledError(f"Task {task_id} was cancelled.")
            try:
                # Gemma models do not support System Messages (Developer Instructions). Merge them.
                if "gemma" in model_name:
                    merged_messages = []
                    sys_text = ""
                    for msg in messages:
                        if isinstance(msg, SystemMessage):
                            sys_text += msg.content + "\n\n"
                        elif isinstance(msg, HumanMessage):
                            merged_messages.append(HumanMessage(content=sys_text + msg.content))
                            sys_text = ""
                        else:
                            merged_messages.append(msg)
                    invoke_messages = merged_messages
                else:
                    invoke_messages = messages
                
                logger.info(f"[{model_name}] Attempting invocation (attempt {attempt+1}/{max_retries_per_model})...")
                start_time = time.time()
                res = await structured_llm.ainvoke(invoke_messages)
                elapsed = time.time() - start_time
                logger.info(f"[{model_name}] Invocation successful in {elapsed:.2f}s")
                return res
            except Exception as e:
                last_err = e
                err_str = str(e).lower()
                if "429" in err_str or "resource_exhausted" in err_str or "quota" in err_str:
                    logger.warning(f"[{model_name}] 429 quota hit. Waiting 30s... (Attempt {attempt+1}/{max_retries_per_model})")
                    # Check cancellation during sleep
                    for _ in range(30):
                        if task_id and is_cancelled(task_id):
                            raise asyncio.CancelledError(f"Task {task_id} was cancelled during wait.")
                        await asyncio.sleep(1)
                else:
                    logger.error(f"[{model_name}] Error: {e}. Falling back to next model...")
                    break  # Break inner loop to try next model immediately
                    
    if isinstance(last_err, BaseException):
        logger.error(f"Exhausted all fallback models. Last error: {last_err}")
        raise last_err
    raise Exception("Max retries and all fallback models exhausted without success.")


async def breakdown_prompt_node(state: MonthLogbookState) -> MonthLogbookState:
    """Breakdown the single monthly prompt into distinct daily overviews between start and end dates."""
    req = state["request"]
    task_id = state["task_id"]
    user_gemini_key = state.get("user_gemini_key")
    user_groq_key = state.get("user_groq_key")
    
    if task_id and is_cancelled(task_id):
        raise asyncio.CancelledError(f"Task {task_id} was cancelled before breakdown.")

    logger.info(f"[NODE START] breakdown_prompt_node started for task {task_id}")
    start_time = time.time()
    
    sys_msg = SystemMessage(content="You are an expert software engineering intern planner.")
    human_msg = HumanMessage(content=f"""
Please breakdown the overarching monthly work description into distinct daily accomplishments.
Make sure to distribute the work logically sequentially across the {len(req.dates)} dates provided below:
Dates to distribute over: {', '.join(req.dates)}

For each day, provide the specific date string exactly as given in the list above.
Project Description: {req.project_description}
Tech Stack: {req.tech_stack}
Previous Month Context: {req.previous_month_context}

Work Description:
{req.month_prompt}
""")
    planner_models = [
        "gemini-2.5-flash",
        "gemini-2.0-flash",
        "gemini-3.1-pro-preview", 
        "gemini-3-flash-preview",
        "gemma-3-27b-it",
        "gemma-3-12b-it"
    ]
    response: BreakdownResponse = await invoke_with_fallback(
        BreakdownResponse, [sys_msg, human_msg], task_id, planner_models,
        user_gemini_key=user_gemini_key, user_groq_key=user_groq_key
    )
    
    sorted_days = sorted(response.days, key=lambda d: d.date)
    overviews = [day.day_overview for day in sorted_days]
    dates = [day.date for day in sorted_days]
    
    elapsed = time.time() - start_time
    logger.info(f"[NODE END] breakdown_prompt_node completed in {elapsed:.2f}s. Generated {len(overviews)} daily overviews.")
    
    return {
        **state,
        "daily_overviews": overviews,
        "daily_dates": dates,
        "daily_dates": dates,
        "generated_days": []
    }


async def generate_all_days_node(state: MonthLogbookState) -> MonthLogbookState:
    """Generate the detailed logbook content for all days in parallel to drastically optimize time."""
    req = state["request"]
    task_id = state.get("task_id")
    user_gemini_key = state.get("user_gemini_key")
    user_groq_key = state.get("user_groq_key")
    
    if task_id and is_cancelled(task_id):
        raise asyncio.CancelledError(f"Task {task_id} was cancelled before generating days.")

    logger.info(f"[NODE START] generate_all_days_node for {len(state['daily_overviews'])} days")
    start_time = time.time()
    
    writer_models = [
        "llama-3.3-70b-versatile",
        "llama-3.1-8b-instant",
        "gemini-2.5-flash",
        "gemini-2.0-flash",
        "gemini-3-flash-preview", 
        "gemini-3.1-pro-preview",
        "gemma-3-12b-it",
        "gemma-3-4b-it",
        "gemini-3.1-flash-lite-preview"
    ]
    
    BATCH_LOGBOOK_PROMPT = """You are an expert software engineering intern writing daily logbook entries.
Generate professional, first-person content for the logbook sections for multiple days based on:

Project Description: {project_description}
Tech Stack: {tech_stack}

Days to generate:
{days_text}

Rules:
- my_space: Write 4-5 lines of detailed text.
- tasks_carried_out: Write 2-3 lines of text.
- key_learnings: Write 1-2 lines of text.
- tools_used: Limit to 1 line or a few words.
- special_achievements: Only use keywords. Say "Steady progress." if nothing notable.
- Write in first person ("I").

Return a list of generated days in the exact order requested.
"""
    
    chunk_size = 2
    chunks = []
    for i in range(0, len(state["daily_overviews"]), chunk_size):
        chunk_overviews = state["daily_overviews"][i:i+chunk_size]
        chunk_dates = state["daily_dates"][i:i+chunk_size]
        chunks.append((i, chunk_overviews, chunk_dates))
        
    async def process_chunk(start_idx, overviews, dates):
        if task_id and is_cancelled(task_id):
            raise asyncio.CancelledError()
            
        days_text = ""
        for dt, ov in zip(dates, overviews):
            days_text += f"\nDate: {dt}\nToday's work: {ov}\n---"
            
        prompt = BATCH_LOGBOOK_PROMPT.format(
            project_description=req.project_description,
            tech_stack=req.tech_stack,
            days_text=days_text
        )
        
        await asyncio.sleep((start_idx / chunk_size) * 0.5)
        
        response: BatchLogbookContent = await invoke_with_fallback(
            BatchLogbookContent, [HumanMessage(content=prompt)], task_id, writer_models,
            max_retries_per_model=3,
            user_gemini_key=user_gemini_key, user_groq_key=user_groq_key
        )
        
        processed_days = []
        for day_content in response.days[:len(dates)]: # Ensure we don't process more than requested if model hallucinates
            processed_days.append(LogbookContent(
                my_space=_wrap_section(day_content.my_space, "my_space"),
                tasks_carried_out=_wrap_section(day_content.tasks_carried_out, "tasks_carried_out"),
                key_learnings=_wrap_section(day_content.key_learnings, "key_learnings"),
                tools_used=_wrap_section(day_content.tools_used, "tools_used"),
                special_achievements=_wrap_section(day_content.special_achievements, "special_achievements")
            ))
            
        # Pad with empty if model returned too few
        while len(processed_days) < len(dates):
            processed_days.append(LogbookContent(
                my_space="Data generation failed.",
                tasks_carried_out="Error",
                key_learnings="Error",
                tools_used="Error",
                special_achievements="Error"
            ))
            
        return start_idx, processed_days

    tasks = []
    for chunk in chunks:
        tasks.append(process_chunk(*chunk))
        
    results = await asyncio.gather(*tasks)
    
    results.sort(key=lambda x: x[0])
    
    generated_days = []
    for r in results:
        generated_days.extend(r[1])
    
    elapsed = time.time() - start_time
    logger.info(f"[NODE END] generate_all_days_node completed all {len(generated_days)} days (in chunks of {chunk_size}) in {elapsed:.2f}s")
    
    return {
        **state,
        "generated_days": generated_days
    }


class ContextResponse(BaseModel):
    next_month_context: str


async def generate_context_node(state: MonthLogbookState) -> MonthLogbookState:
    """Generate a summary of this month to use for next month's context."""
    task_id = state.get("task_id")
    user_gemini_key = state.get("user_gemini_key")
    user_groq_key = state.get("user_groq_key")
    
    if task_id and is_cancelled(task_id):
        raise asyncio.CancelledError(f"Task {task_id} was cancelled before generating context.")

    logger.info("[NODE START] generate_context_node started")
    start_time = time.time()
    all_overviews = "\n".join([f"Day {i+1}: {overview}" for i, overview in enumerate(state["daily_overviews"])])
    
    sys_msg = SystemMessage(content="You are organizing the transition points for a multi-month project.")
    human_msg = HumanMessage(content=f"""
Based on the following {len(state["daily_overviews"])} days of work completed this month, generate a concise summary of the current project state (1-2 sentences max).
This will be used as the 'Previous Month Context' for the prompt generating the following month's logbook.

This Month's Work:
{all_overviews}
""")
    summary_models = [
        "gemini-2.5-flash",
        "gemini-2.0-flash",
        "gemini-3.1-flash-lite-preview",
        "gemini-3-flash-preview",
        "gemma-3-4b-it",
        "gemma-3-1b-it"
    ]
    response: ContextResponse = await invoke_with_fallback(
        ContextResponse, [sys_msg, human_msg], task_id, summary_models,
        user_gemini_key=user_gemini_key, user_groq_key=user_groq_key
    )
    
    elapsed = time.time() - start_time
    logger.info(f"[NODE END] generate_context_node completed in {elapsed:.2f}s")
    
    return {
        **state,
        "next_month_context": response.next_month_context
    }


workflow = StateGraph(MonthLogbookState)

workflow.add_node("breakdown_prompt", breakdown_prompt_node)
workflow.add_node("generate_all_days", generate_all_days_node)
workflow.add_node("generate_context", generate_context_node)

workflow.add_edge(START, "breakdown_prompt")
workflow.add_edge("breakdown_prompt", "generate_all_days")
workflow.add_edge("generate_all_days", "generate_context")
workflow.add_edge("generate_context", END)

month_logbook_app = workflow.compile()


async def run_monthly_generation_pipeline(request: GenerateMonthLogbookRequest, task_id: Optional[str] = None) -> MonthLogbookResponse:
    """
    Kicks off the LangGraph pipeline to generate a month of logbook content.
    User-supplied API keys from the request take priority over environment variables.
    """
    initial_state = MonthLogbookState(
        request=request,
        daily_overviews=[],
        daily_dates=[],
        generated_days=[],
        next_month_context="",
        task_id=task_id,
        user_gemini_key=request.gemini_api_key or None,
        user_groq_key=request.groq_api_key or None,
    )
    
    logger.info(f"==== START PIPELINE run_monthly_generation_pipeline (task: {task_id}) ====")
    start_time = time.time()
    
    try:
        final_state = await month_logbook_app.ainvoke(initial_state)
        elapsed = time.time() - start_time
        logger.info(f"==== END PIPELINE run_monthly_generation_pipeline in {elapsed:.2f}s ====")
        return MonthLogbookResponse(
            days=final_state["generated_days"],
            next_month_context=final_state["next_month_context"]
        )
    except asyncio.CancelledError:
        logger.warning(f"==== PIPELINE CANCELLED for task: {task_id} after {time.time()-start_time:.2f}s ====")
        raise
    finally:
        if task_id:
            clear_task(task_id)
