import { useState, useRef, useCallback } from 'react';
import { pdfjsLib, STEPS, LOGBOOK_ZONES, DAY_1_PAGE_INDEX } from './constants';
import { uploadPdf, editPdf, extractText, generateWeekLogbook, getDownloadUrl } from './api';
import { useCoordHelpers, usePdfRenderer } from './hooks/usePdf';
import { useDrag } from './hooks/useDrag';
import UploadStep from './components/UploadStep';
import AiPanel from './components/AiPanel';
import EditStep from './components/EditStep';
import EditSidebar from './components/EditSidebar';
import DownloadStep from './components/DownloadStep';
import TextModal from './components/TextModal';
import './App.css';

export default function App() {
  // ── Core state ──────────────────────────────────────────────────────────
  const [step, setStep] = useState(0);
  const [file, setFile] = useState(null);
  const [filename, setFilename] = useState('');
  const [pdfDoc, setPdfDoc] = useState(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(0);
  const [edits, setEdits] = useState([]);
  const [textBlocks, setTextBlocks] = useState([]);
  const [outputFilename, setOutputFilename] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [toast, setToast] = useState('');

  // ── Modal state ──────────────────────────────────────────────────────────
  const [modal, setModal] = useState({ open: false, x: 0, y: 0 });
  const [modalText, setModalText] = useState('');
  const [editingBlock, setEditingBlock] = useState(null);

  // ── Drag state ───────────────────────────────────────────────────────────
  const [dragging, setDragging] = useState(null);
  const [dragPos, setDragPos] = useState(null);

  // ── AI form state ────────────────────────────────────────────────────────
  const [aiPanelOpen, setAiPanelOpen] = useState(false);
  const [aiLoading, setAiLoading] = useState(false);
  const [aiForm, setAiForm] = useState({ projectDesc: '', techStack: '', dayOverview: '', startDate: '', endDate: '', startPdfDay: 1 });

  // ── Refs ─────────────────────────────────────────────────────────────────
  const canvasRef = useRef(null);
  const wrapperRef = useRef(null);

  // ── Helpers & hooks ───────────────────────────────────────────────────────
  const showToast = useCallback((msg) => {
    setToast(msg);
    setTimeout(() => setToast(''), 3000);
  }, []);

  const { pixelToPdf, pdfToOverlay } = useCoordHelpers(canvasRef);

  usePdfRenderer(canvasRef, pdfDoc, currentPage, edits);

  // Derived per-page data
  const currentBlocks = textBlocks.filter(b => b.page === currentPage);
  const currentEdits = edits.map((e, i) => ({ ...e, _idx: i })).filter(e => e.page === currentPage);

  const { onEditMouseDown, onEditMouseUp, onBlockMouseDown } = useDrag({
    dragging, setDragging, dragPos, setDragPos,
    edits, setEdits,
    setEditingBlock, setModalText, setModal,
    currentBlocks, currentPage,
    textBlocks, setTextBlocks,
    pixelToPdf, showToast,
  });

  // ── Upload ────────────────────────────────────────────────────────────────
  const doUpload = async (f = file) => {
    const data = await uploadPdf(f);
    setFilename(data.filename);
    const buf = await f.arrayBuffer();
    const doc = await pdfjsLib.getDocument({ data: buf }).promise;
    setPdfDoc(doc);
    setTotalPages(doc.numPages);
    setCurrentPage(1);
    try { setTextBlocks(await extractText(data.filename)); } catch { setTextBlocks([]); }
    return data;
  };

  const handleUpload = async () => {
    if (!file) { setError('Please choose a PDF file.'); return; }
    setLoading(true); setError('');
    try {
      await doUpload();
      setStep(1);
      showToast('PDF uploaded — click text to edit, drag to move, or click empty area to add.');
    } catch (err) {
      setError(err.response?.data?.detail || 'Upload failed.');
    } finally { setLoading(false); }
  };

  const handleUploadAndGenerate = async () => {
    if (!file) { setError('Please select a PDF first.'); return; }
    setLoading(true); setError('');
    try {
      await doUpload();
      setStep(1);
      await handleGenerateLogbook();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed.');
    } finally { setLoading(false); }
  };

  // ── Modal ─────────────────────────────────────────────────────────────────
  const openModal = (x, y, block = null) => {
    setEditingBlock(block);
    setModal({ open: true, x, y });
    setModalText(block ? block.text : '');
  };

  const handleCanvasClick = (e) => {
    if (dragging) return;
    const { x, y } = pixelToPdf(e.clientX, e.clientY);
    openModal(Math.round(x), Math.round(y));
  };

  const handleBlockClick = (block, e) => {
    e.stopPropagation();
    if (dragging) return;
    openModal(Math.round(block.x), Math.round(block.y + block.h), block);
  };

  const handleModalConfirm = () => {
    const text = modalText.trim();
    if (text) {
      if (editingBlock?._editIndex !== undefined) {
        const idx = editingBlock._editIndex;
        setEdits(prev => prev.map((e, i) => i === idx ? { ...e, text } : e));
      } else if (editingBlock) {
        setEdits(prev => [...prev, {
          page: editingBlock.page, x: editingBlock.x, y: editingBlock.y + editingBlock.h,
          text, font_size: editingBlock.font_size || 12, type: 'replace',
          orig_x: editingBlock.x, orig_y: editingBlock.y, orig_w: editingBlock.w, orig_h: editingBlock.h,
          orig_text: editingBlock.text,
        }]);
        setTextBlocks(prev => prev.map(b => b === editingBlock ? { ...b, _edited: true, _newText: text } : b));
      } else {
        setEdits(prev => [...prev, { page: currentPage, x: modal.x, y: modal.y, text, type: 'insert' }]);
      }
    }
    setModal({ open: false, x: 0, y: 0 });
    setModalText('');
    setEditingBlock(null);
  };

  const handleModalCancel = () => {
    setModal({ open: false, x: 0, y: 0 });
    setModalText('');
    setEditingBlock(null);
  };

  // ── Edits ─────────────────────────────────────────────────────────────────
  const removeEdit = (idx) => {
    const removed = edits[idx];
    if (removed.type === 'replace') {
      setTextBlocks(prev => prev.map(b =>
        b.x === removed.orig_x && b.y === removed.orig_y && b.page === removed.page
          ? { ...b, _edited: false, _newText: undefined }
          : b
      ));
    }
    setEdits(prev => prev.filter((_, i) => i !== idx));
  };

  // ── AI generation ─────────────────────────────────────────────────────────
  const handleGenerateLogbook = async () => {
    if (!aiForm.projectDesc.trim() || !aiForm.dayOverview.trim() || !aiForm.startDate || !aiForm.endDate) {
      setError("Please fill in project desc, today's notes, start date, and end date.");
      return;
    }
    setAiLoading(true); setError('');
    try {
      const result = await generateWeekLogbook({
        project_description: aiForm.projectDesc,
        tech_stack: aiForm.techStack,
        week_prompt: aiForm.dayOverview,
        start_date: aiForm.startDate,
        end_date: aiForm.endDate,
        start_pdf_day: aiForm.startPdfDay || 1,
        previous_week_context: ""
      });

      let allNewEdits = [];
      const startPdfDayIdx = aiForm.startPdfDay || 1;

      // result.days is an array of LogbookContent representing each day
      result.days.forEach((dayContent, i) => {
        const pageNum = DAY_1_PAGE_INDEX + startPdfDayIdx + i; // i offsets each generated day onto a new page
        const dayEdits = LOGBOOK_ZONES
          .map(zone => ({ page: pageNum, x: zone.x, y: zone.y, text: dayContent[zone.key] || '', type: 'insert', font_size: 9 }))
          .filter(e => e.text);
        allNewEdits.push(...dayEdits);
      });

      setEdits(prev => [...prev, ...allNewEdits]);
      setCurrentPage(DAY_1_PAGE_INDEX + startPdfDayIdx); // Go to the first generated page
      setAiPanelOpen(false);
      showToast(`✨ AI generated ${result.days.length} days of logbook sections!`);
    } catch (err) {
      setError(err.response?.data?.detail || 'AI generation failed. Check your API key.');
    } finally { setAiLoading(false); }
  };

  // ── Apply edits ───────────────────────────────────────────────────────────
  const handleApplyEdits = async () => {
    if (!edits.length) { setError('No edits to apply.'); return; }
    setLoading(true); setError('');
    try {
      const backendEdits = edits.map(e => {
        const base = { page: e.page, x: e.x, y: e.y, text: e.text, font_size: e.font_size || 12 };
        if (e.type === 'replace') Object.assign(base, { orig_x: e.orig_x, orig_y: e.orig_y, orig_w: e.orig_w, orig_h: e.orig_h, orig_text: e.orig_text });
        return base;
      });
      const data = await editPdf(filename, backendEdits);
      setOutputFilename(data.output_filename);
      setStep(2);
      showToast('Edits applied! Ready to download.');
    } catch (err) {
      setError(err.response?.data?.detail || 'Edit failed.');
    } finally { setLoading(false); }
  };

  // ── Reset ─────────────────────────────────────────────────────────────────
  const handleReset = () => {
    setStep(0); setFile(null); setFilename(''); setPdfDoc(null);
    setCurrentPage(1); setTotalPages(0); setEdits([]); setTextBlocks([]);
    setOutputFilename(''); setError(''); setEditingBlock(null);
    setDragging(null); setDragPos(null);
  };

  // ── Render ────────────────────────────────────────────────────────────────
  const aiPanelNode = (
    <AiPanel
      aiForm={aiForm} setAiForm={setAiForm}
      onGenerate={handleGenerateLogbook}
      onCancel={() => setAiPanelOpen(false)}
      aiLoading={aiLoading} loading={loading}
      compact={step === 1}
      showUploadAndGenerate={step === 0}
      onUploadAndGenerate={handleUploadAndGenerate}
    />
  );

  return (
    <div className="app">
      <header className="header">
        <div className="logo">
          <span className="logo-icon">📄</span>
          <h1>OJL Logbook</h1>
          <span className="badge">PDF Editor</span>
        </div>
      </header>

      <div className="stepper">
        {STEPS.map((label, i) => (
          <div key={label} className={`step-item ${i === step ? 'active' : ''} ${i < step ? 'done' : ''}`}>
            <div className="step-circle">{i < step ? '✓' : i + 1}</div>
            <span className="step-label">{label}</span>
            {i < STEPS.length - 1 && <div className="step-line" />}
          </div>
        ))}
      </div>

      {toast && <div className="toast">{toast}</div>}
      {error && <div className="error-bar">{error}<button onClick={() => setError('')}>✕</button></div>}

      <main className="main">
        {step === 0 && (
          <UploadStep
            file={file} setFile={setFile}
            loading={loading}
            onUpload={handleUpload}
            aiPanelOpen={aiPanelOpen} setAiPanelOpen={setAiPanelOpen}
          >
            {aiPanelNode}
          </UploadStep>
        )}

        {step === 1 && (
          <EditStep
            canvasRef={canvasRef} wrapperRef={wrapperRef}
            currentPage={currentPage} totalPages={totalPages} setCurrentPage={setCurrentPage}
            currentBlocks={currentBlocks} currentEdits={currentEdits}
            dragging={dragging} dragPos={dragPos}
            pdfToOverlay={pdfToOverlay}
            onCanvasClick={handleCanvasClick}
            onBlockClick={handleBlockClick} onBlockMouseDown={onBlockMouseDown}
            onEditMouseDown={onEditMouseDown} onEditMouseUp={onEditMouseUp}
          >
            <EditSidebar
              edits={edits} removeEdit={removeEdit}
              loading={loading}
              onApplyEdits={handleApplyEdits} onReset={handleReset}
              aiPanelOpen={aiPanelOpen} setAiPanelOpen={setAiPanelOpen}
            >
              {aiPanelNode}
            </EditSidebar>
          </EditStep>
        )}

        {step === 2 && (
          <DownloadStep
            outputFilename={outputFilename}
            downloadUrl={getDownloadUrl(outputFilename)}
            onReset={handleReset}
          />
        )}
      </main>

      <TextModal
        modal={modal}
        editingBlock={editingBlock}
        modalText={modalText}
        setModalText={setModalText}
        onConfirm={handleModalConfirm}
        onCancel={handleModalCancel}
      />
    </div>
  );
}
