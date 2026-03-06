import fitz  # PyMuPDF
import os
from typing import List, Optional
from pydantic import BaseModel


class EditItem(BaseModel):
    page: int
    x: float
    y: float
    text: str
    font_size: Optional[float] = 12.0
    # For replacing existing text: cover original area first
    orig_x: Optional[float] = None
    orig_y: Optional[float] = None
    orig_w: Optional[float] = None
    orig_h: Optional[float] = None
    orig_text: Optional[str] = None


class TextBlock(BaseModel):
    page: int
    x: float
    y: float
    w: float
    h: float
    text: str
    font_size: float
    font_name: str = ""
    color: List[float] = [0, 0, 0]


UPLOADS_DIR = "uploads"
OUTPUTS_DIR = "outputs"


def ensure_dirs():
    os.makedirs(UPLOADS_DIR, exist_ok=True)
    os.makedirs(OUTPUTS_DIR, exist_ok=True)


def extract_text_blocks(filename: str) -> List[dict]:
    """
    Extract all text spans from the PDF with their bounding boxes,
    font info, and color.
    """
    input_path = os.path.join(UPLOADS_DIR, filename)

    if not os.path.exists(input_path):
        raise FileNotFoundError(f"File '{filename}' not found in uploads folder.")

    try:
        doc = fitz.open(input_path)
    except Exception as e:
        raise ValueError(f"Failed to load PDF '{filename}': {str(e)}")

    blocks = []
    for page_num in range(len(doc)):
        page = doc[page_num]
        text_dict = page.get_text("dict", flags=fitz.TEXT_PRESERVE_WHITESPACE)

        for block in text_dict.get("blocks", []):
            if block.get("type") != 0:
                continue
            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    text = span.get("text", "").strip()
                    if not text:
                        continue
                    bbox = span.get("bbox", [0, 0, 0, 0])
                    # Extract color (int → RGB floats)
                    color_int = span.get("color", 0)
                    r = ((color_int >> 16) & 0xFF) / 255.0
                    g = ((color_int >> 8) & 0xFF) / 255.0
                    b = (color_int & 0xFF) / 255.0

                    blocks.append({
                        "page": page_num + 1,
                        "x": round(bbox[0], 2),
                        "y": round(bbox[1], 2),
                        "w": round(bbox[2] - bbox[0], 2),
                        "h": round(bbox[3] - bbox[1], 2),
                        "text": text,
                        "font_size": round(span.get("size", 12), 2),
                        "font_name": span.get("font", ""),
                        "color": [round(r, 3), round(g, 3), round(b, 3)],
                    })

    doc.close()
    return blocks


def apply_edits(filename: str, edits: List[EditItem]) -> str:
    """
    Open the uploaded PDF, apply edits (insert or replace text),
    save the result to outputs/ and return the output filename.
    """
    input_path = os.path.join(UPLOADS_DIR, filename)

    if not os.path.exists(input_path):
        raise FileNotFoundError(f"File '{filename}' not found in uploads folder.")

    try:
        doc = fitz.open(input_path)
    except Exception as e:
        raise ValueError(f"Failed to load PDF '{filename}': {str(e)}")

    total_pages = len(doc)

    # First pass: collect redactions
    redactions_by_page = {}
    for edit in edits:
        page_index = edit.page - 1
        if page_index < 0 or page_index >= total_pages:
            doc.close()
            raise IndexError(
                f"Invalid page number {edit.page}. "
                f"PDF has {total_pages} page(s) (1-indexed)."
            )
        if (edit.orig_x is not None and edit.orig_y is not None
                and edit.orig_w is not None and edit.orig_h is not None):
            if page_index not in redactions_by_page:
                redactions_by_page[page_index] = []
            redactions_by_page[page_index].append(edit)

    # Apply redactions: use search_for() for precise text bounds
    for page_index, redact_edits in redactions_by_page.items():
        page = doc[page_index]
        for edit in redact_edits:
            # Try to find exact text bounds using search_for
            rect = None
            if edit.orig_text:
                found = page.search_for(edit.orig_text)
                if found:
                    # Pick the match closest to our expected position
                    best = None
                    best_dist = float('inf')
                    for r in found:
                        dist = abs(r.x0 - edit.orig_x) + abs(r.y0 - edit.orig_y)
                        if dist < best_dist:
                            best_dist = dist
                            best = r
                    if best and best_dist < 50:
                        rect = best

            # Fallback to bbox from extract
            if rect is None:
                rect = fitz.Rect(
                    edit.orig_x,
                    edit.orig_y,
                    edit.orig_x + edit.orig_w + 1,
                    edit.orig_y + edit.orig_h + 1,
                )

            page.add_redact_annot(rect)

        # graphics=0: preserve ALL vector line art (form lines, underscores, borders)
        page.apply_redactions(images=fitz.PDF_REDACT_IMAGE_NONE, graphics=0)

    # Second pass: insert replacement text with matching font
    for edit in edits:
        page_index = edit.page - 1
        page = doc[page_index]
        fs = edit.font_size if edit.font_size else 12.0

        if edit.orig_text and edit.orig_x is not None:
            # For replacements: position at the original text location
            # Use orig coords — baseline is near the bottom of the bbox
            insert_x = edit.orig_x
            insert_y = edit.orig_y + (edit.orig_h * 0.85) if edit.orig_h else edit.y
        else:
            # For new inserts: use the click position
            insert_x = edit.x
            insert_y = edit.y

        lines = edit.text.split('\n')
        line_height = fs * 1.4  # standard leading: ~140% of font size
        for i, line in enumerate(lines):
            if not line.strip():
                continue
            page.insert_text(
                point=fitz.Point(insert_x, insert_y + i * line_height),
                text=line,
                fontsize=fs,
                color=(0, 0, 0),
            )

    output_filename = f"edited_{filename}"
    output_path = os.path.join(OUTPUTS_DIR, output_filename)

    try:
        doc.save(output_path)
    finally:
        doc.close()

    return output_filename
