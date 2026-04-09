# LogiFlow AI: Smart PDF Logbook Editor

An AI-powered web application for viewing, editing, and generating PDF logbooks. The platform allows users to manually interact with PDF logbooks using a rich canvas interface or automatically generate detailed logbook entries over a date range using Google's Gemini AI.

## 🚀 Tech Stack

### Frontend
- **Framework:** React 19 with Vite
- **Canvas UI & PDF Rendering:** Konva (`react-konva`), `pdfjs-dist`
- **Text Editing:** Tiptap (Rich text editor)
- **HTTP Client:** Axios

### Backend
- **Framework:** FastAPI (Python)
- **PDF Manipulation:** PyMuPDF (`pymupdf`)
- **AI & Orchestration:** Google Gemini, LangChain, LangGraph
- **Server:** Uvicorn (`uvicorn[standard]`)

## 🛠️ Project Setup

### Prerequisites
- Node.js (v18+)
- Python (v3.9+)
- Google Gemini API Key

### Backend Setup

1. Navigate to the `backend` directory:
   ```bash
   cd backend
   ```
2. Create and activate a Python virtual environment:
   ```bash
   python -m venv venv
   
   # On Windows:
   venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   ```
3. Install the required dependencies: 
   ```bash
    uvicorn main:app --reload
   ```
   *The FastAPI backend will run on `http://localhost:8000`.*

### Frontend Setup

1. Navigate to the `frontend` directory:
   ```bash
   cd frontend
   ```
2. Install the Node dependencies:
   ```bash
   npm install
   ```
3. Start the Vite development server:
   ```bash
   npm run dev
   ```
   *The frontend application will be served at `http://localhost:5173`.*

## 📁 Project Architecture

- `/backend`: Houses the FastAPI application. Key components include Pydantic schemas, PDF routing/upload logic, PyMuPDF business logic (`services/pdf_service.py`), and LangGraph/Gemini AI agents (`services/ai_service.py`).
- `/frontend`: Contains the React UI. It features a canvas interface constructed with Konva for annotating PDFs, as well as forms for specifying date ranges to generate logbooks.

## ✨ Features
- **Interactive PDF Viewer:** Renders PDF pages as images on a canvas using `pdf.js` and Konva.
- **AI-Powered Generation:** Formulate logbook entries utilizing LangGraph and Google's Gemini model.
- **Rich Text Annotations:** Add and format text directly onto PDF representations using Tiptap.
