"""
AI service: Google Gemini integration for logbook content generation.
"""
import json
import textwrap
import os
from google import genai
from google.genai import types

from schemas import LogbookContent

# Section-specific text-wrap constraints
# max_chars: box_width_pt / ~5pt_per_char at 9pt font
# max_lines: box_height_pt / (9pt * 1.4 leading ~= 12.6pt per line)
# Box heights measured from PDF drawings:
#   my_space:      341.9 - 173.8 = 168pt  → ~13 lines
#   tasks:         497.1 - 368.3 = 128pt  → ~10 lines
#   key_learnings: 605.6 - 526.3 =  79pt  → ~6  lines
#   tools/achiev:  842   - 650.9 = 191pt  → ~15 lines (half-width column)
SECTION_WRAP = {
    'my_space':             {'width': 78, 'max_lines': 12},
    'tasks_carried_out':    {'width': 78, 'max_lines': 9},
    'key_learnings':        {'width': 78, 'max_lines': 5},
    'tools_used':           {'width': 35, 'max_lines': 12},
    'special_achievements': {'width': 35, 'max_lines': 12},
}

LOGBOOK_PROMPT_TEMPLATE = """
You are an expert software engineering intern writing a daily logbook entry.
Generate professional, first-person content for 5 logbook sections based on:

  Day:                  {day_number}
  Project Description:  {project_description}
  Tech Stack:           {tech_stack}
  Today's work:         {day_overview}

Rules:
- Maximum 1-2 concise sentences per section.
- Write in first person ("I").
- Keep text short to fit within PDF bounding boxes.
- For special_achievements, say "Steady progress." if nothing notable.

Sections to fill:
  1. my_space             – High-level day overview / thoughts / sketches.
  2. tasks_carried_out    – Concrete tasks completed today.
  3. key_learnings        – Technical or soft skills learned.
  4. tools_used           – Tools / frameworks / tech used.
  5. special_achievements – Notable milestone, bug fixed, or delivery.
"""


def _wrap_section(text: str, key: str) -> str:
    """Wrap text to fit within a PDF section box using calibrated constraints."""
    cfg = SECTION_WRAP.get(key, {'width': 78, 'max_lines': 10})
    lines = textwrap.wrap(str(text), width=cfg['width'])
    return '\n'.join(lines[:cfg['max_lines']])


def generate_logbook_content(
    project_description: str,
    tech_stack: str,
    day_overview: str,
    day_number: int = 1,
) -> dict:
    """
    Call Gemini to generate logbook content and return a dict of
    section_key → wrapped text.

    Raises:
        ValueError: if GEMINI_API_KEY is not set.
        RuntimeError: if the API call or JSON parsing fails.
    """
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY is not set in .env")

    client = genai.Client(api_key=api_key)
    prompt = LOGBOOK_PROMPT_TEMPLATE.format(
        day_number=day_number,
        project_description=project_description,
        tech_stack=tech_stack,
        day_overview=day_overview,
    )

    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=LogbookContent,
                temperature=0.7,
            ),
        )
        data: dict = json.loads(response.text)
    except Exception as exc:
        raise RuntimeError(f"Gemini API call failed: {exc}") from exc

    # Apply section-aware word wrapping
    return {key: _wrap_section(val, key) for key, val in data.items()}
