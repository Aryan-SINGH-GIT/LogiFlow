"""
PDF-related routes: upload, extract-text, edit, download.
"""
import shutil
import os

from fastapi import APIRouter, File, UploadFile, HTTPException
from fastapi.responses import FileResponse

from schemas import EditRequest
from services.pdf_service import apply_edits, extract_text_blocks, UPLOADS_DIR, OUTPUTS_DIR

router = APIRouter(tags=["PDF"])


@router.post("/upload", summary="Upload a PDF file")
async def upload_pdf(file: UploadFile = File(...)):
    """
    Upload a PDF file to the uploads/ directory.
    Returns the stored filename.
    """
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted.")

    dest_path = os.path.join(UPLOADS_DIR, file.filename)
    try:
        with open(dest_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {e}")
    finally:
        await file.close()

    return {"message": "File uploaded successfully.", "filename": file.filename}


@router.get("/extract-text/{filename}", summary="Extract text blocks from a PDF")
async def extract_text(filename: str):
    """
    Extract all text spans from the uploaded PDF, returning
    their page, position, size, and content.
    """
    try:
        blocks = extract_text_blocks(filename)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {e}")

    return {"blocks": blocks}


@router.post("/edit", summary="Apply text edits to a PDF")
async def edit_pdf(request: EditRequest):
    """
    Insert or replace text on specified pages.
    For replacements, include orig_x/y/w/h to cover the original text.
    Returns the output filename.
    """
    try:
        output_filename = apply_edits(request.filename, request.edits)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except IndexError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {e}")

    return {"message": "PDF edited successfully.", "output_filename": output_filename}


@router.get("/download/{filename}", summary="Download an edited PDF")
async def download_pdf(filename: str):
    """
    Download a previously edited PDF from the outputs/ directory.
    """
    file_path = os.path.join(OUTPUTS_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(
            status_code=404,
            detail=f"File '{filename}' not found in outputs folder."
        )
    return FileResponse(
        path=file_path,
        media_type="application/pdf",
        filename=filename,
    )
