import { useState, useRef, useCallback, useEffect } from 'react';
import { Routes, Route, useNavigate, useLocation, Navigate } from 'react-router-dom';
import { pdfjsLib, STEPS, LOGBOOK_ZONES, DAY_1_PAGE_INDEX } from './constants';
import { uploadPdf, editPdf, extractText, generateMonthLogbook, getDownloadUrl, cancelGeneration } from './api';
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
  const navigate = useNavigate();
  const location = useLocation();
  const step = location.pathname === '/' ? 0 : location.pathname === '/edit' ? 1 : 2;
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

  const [modal, setModal] = useState({ open: false, x: 0, y: 0 });
  const [modalText, setModalText] = useState('');
  const [editingBlock, setEditingBlock] = useState(null);

  const [dragging, setDragging] = useState(null);
  const [dragPos, setDragPos] = useState(null);

  const [aiPanelOpen, setAiPanelOpen] = useState(false);
  const [aiLoading, setAiLoading] = useState(false);
  const abortControllerRef = useRef(null);
  const currentTaskIdRef = useRef(null);
  const [aiForm, setAiForm] = useState({ projectDesc: '', techStack: '', dayOverview: '', dates: [], timeFrom: '09:00 AM', timeTo: '7:00 PM', department: 'Engineering Department', designation: 'Backend Developer Trainee', startPdfDay: 1, learnerName: '', registrationNo: '' });

  const canvasRef = useRef(null);
  const wrapperRef = useRef(null);

  const showToast = useCallback((msg) => {
    setToast(msg);
    setTimeout(() => setToast(''), 3000);
  }, []);

  const { pixelToPdf, pdfToOverlay } = useCoordHelpers(canvasRef);

  usePdfRenderer(canvasRef, pdfDoc, currentPage, edits);

  const currentBlocks = textBlocks.filter(b => b.page === currentPage);
  const currentEdits = edits.map((e, i) => ({ ...e, _idx: i })).filter(e => e.page === currentPage);

  const { onEditMouseDown, onBlockMouseDown } = useDrag({
    dragging, setDragging, dragPos, setDragPos,
    edits, setEdits,
    setEditingBlock, setModalText, setModal,
    currentBlocks, currentPage,
    textBlocks, setTextBlocks,
    pixelToPdf, showToast,
  });

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
      navigate('/edit');
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
      navigate('/edit');
      await handleGenerateLogbook();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed.');
    } finally { setLoading(false); }
  };

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

  const handleModalDelete = () => {
    if (editingBlock?._editIndex !== undefined) {
      removeEdit(editingBlock._editIndex);
    } else if (editingBlock) {
      setEdits(prev => [...prev, {
        page: editingBlock.page, x: editingBlock.x, y: editingBlock.y + editingBlock.h,
        text: '', font_size: editingBlock.font_size || 12, type: 'replace',
        orig_x: editingBlock.x, orig_y: editingBlock.y, orig_w: editingBlock.w, orig_h: editingBlock.h,
        orig_text: editingBlock.text,
      }]);
      setTextBlocks(prev => prev.map(b => b === editingBlock ? { ...b, _edited: true, _newText: '' } : b));
    }
    setModal({ open: false, x: 0, y: 0 });
    setModalText('');
    setEditingBlock(null);
  };

  const handleGenerateLogbook = async () => {
    let extractedDates = new Set();
    if (Array.isArray(aiForm.dates)) {
      const isMultipleRanges = aiForm.dates.length > 0 && Array.isArray(aiForm.dates[0]);
      
      if (isMultipleRanges) {
        aiForm.dates.forEach(rangeArray => {
          if (Array.isArray(rangeArray) && rangeArray.length >= 1 && rangeArray[0]?.toDate) {
            const start = new Date(rangeArray[0].toDate());
            const end = rangeArray.length === 2 && rangeArray[1]?.toDate ? new Date(rangeArray[1].toDate()) : start;
            const minD = start < end ? start : end;
            const maxD = start < end ? end : start;
            let curr = new Date(minD);
            curr.setHours(0,0,0,0);
            maxD.setHours(0,0,0,0);
            while (curr <= maxD) {
              const dd = String(curr.getDate()).padStart(2, '0');
              const mm = String(curr.getMonth() + 1).padStart(2, '0');
              const yyyy = curr.getFullYear();
              extractedDates.add(`${dd}/${mm}/${yyyy}`);
              curr.setDate(curr.getDate() + 1);
            }
          }
        });
      } else {
        if (aiForm.dates.length === 2 && aiForm.dates[0]?.toDate && aiForm.dates[1]?.toDate) {
          const start = new Date(aiForm.dates[0].toDate());
          const end = new Date(aiForm.dates[1].toDate());
          const minD = start < end ? start : end;
          const maxD = start < end ? end : start;
          let curr = new Date(minD);
          curr.setHours(0,0,0,0);
          maxD.setHours(0,0,0,0);
          while (curr <= maxD) {
            const dd = String(curr.getDate()).padStart(2, '0');
            const mm = String(curr.getMonth() + 1).padStart(2, '0');
            const yyyy = curr.getFullYear();
            extractedDates.add(`${dd}/${mm}/${yyyy}`);
            curr.setDate(curr.getDate() + 1);
          }
        } else {
          aiForm.dates.forEach(d => {
            if (typeof d === 'object' && d?.format) extractedDates.add(d.format("DD/MM/YYYY"));
            else extractedDates.add(d);
          });
        }
      }
    } else if (typeof aiForm.dates === 'string') {
      aiForm.dates.split(',').forEach(d => {
        const trimmed = d.trim();
        if (trimmed) extractedDates.add(trimmed);
      });
    }
    const dateArray = Array.from(extractedDates);

    dateArray.sort((a, b) => {
      const [dayA, monthA, yearA] = a.split('/');
      const [dayB, monthB, yearB] = b.split('/');
      return new Date(yearA, monthA - 1, dayA) - new Date(yearB, monthB - 1, dayB);
    });

    if (!aiForm.projectDesc.trim() || !aiForm.dayOverview.trim() || dateArray.length === 0) {
      setError("Please fill in project desc, today's notes, and at least one date.");
      return;
    }
    if (dateArray.length > 20) {
      setError("Maximum limit exceeded: You can only select up to 20 days at a time.");
      return;
    }
    setAiLoading(true); setError('');
    
    // Cleanup previous if any
    if (abortControllerRef.current) abortControllerRef.current.abort();
    if (currentTaskIdRef.current) cancelGeneration(currentTaskIdRef.current);

    const taskId = crypto.randomUUID();
    currentTaskIdRef.current = taskId;
    abortControllerRef.current = new AbortController();

    try {
      const result = await generateMonthLogbook({
        project_description: aiForm.projectDesc,
        tech_stack: aiForm.techStack,
        month_prompt: aiForm.dayOverview,
        dates: dateArray,
        start_pdf_day: aiForm.startPdfDay || 1,
        previous_month_context: "",
        registration_no: aiForm.registrationNo || null
      }, abortControllerRef.current.signal, taskId);

      let allNewEdits = [];

      // Add Learner's Details to Page 3
      if (aiForm.learnerName) {
        allNewEdits.push({ page: 3, x: 230, y: 165, text: aiForm.learnerName, type: 'insert', font_size: 14 });
      }
      if (aiForm.registrationNo) {
        allNewEdits.push({ page: 3, x: 230, y: 200, text: aiForm.registrationNo, type: 'insert', font_size: 14 });
      }

      const startPdfDayIdx = aiForm.startPdfDay || 1;

      result.days.forEach((dayContent, i) => {
        const pageNum = DAY_1_PAGE_INDEX + startPdfDayIdx + i; // i offsets each generated day onto a new page
        const dayEdits = LOGBOOK_ZONES
          .map(zone => ({ page: pageNum, x: zone.x, y: zone.y, text: dayContent[zone.key] || '', type: 'insert', font_size: 9 }))
          .filter(e => e.text);
          
        const dateStr = dateArray[i] || dateArray[dateArray.length - 1];
        if (dateStr) dayEdits.push({ page: pageNum, x: 105, y: 95, text: dateStr, type: 'insert', font_size: 11 });
        if (aiForm.timeFrom) dayEdits.push({ page: pageNum, x: 405, y: 95, text: aiForm.timeFrom, type: 'insert', font_size: 11 });
        if (aiForm.timeTo) dayEdits.push({ page: pageNum, x: 485, y: 95, text: aiForm.timeTo, type: 'insert', font_size: 11 });
        
        if (aiForm.department) dayEdits.push({ page: pageNum, x: 155, y: 119, text: aiForm.department, type: 'insert', font_size: 11 });
        if (aiForm.designation) dayEdits.push({ page: pageNum, x: 390, y: 119, text: aiForm.designation, type: 'insert', font_size: 11 });

        allNewEdits.push(...dayEdits);
      });

      setEdits(prev => [...prev, ...allNewEdits]);
      setCurrentPage(DAY_1_PAGE_INDEX + startPdfDayIdx); // Go to the first generated page
      setAiPanelOpen(false);
      showToast(`AI generated ${result.days.length} days of logbook sections!`);
    } catch (err) {
      if (err.name === 'AbortError' || err.name === 'CanceledError' || err.message === 'canceled') {
        showToast('AI generation cancelled.');
        return;
      }
      setError(err.response?.data?.detail || 'AI generation failed. Check your API key.');
    } finally { 
      setAiLoading(false);
      abortControllerRef.current = null;
      currentTaskIdRef.current = null;
    }
  };

  useEffect(() => {
    if (!aiPanelOpen && aiLoading) {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
        abortControllerRef.current = null;
      }
      if (currentTaskIdRef.current) {
        cancelGeneration(currentTaskIdRef.current);
        currentTaskIdRef.current = null;
      }
    }
  }, [aiPanelOpen, aiLoading]);

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
      navigate('/download');
      showToast('Edits applied! Ready to download.');
    } catch (err) {
      setError(err.response?.data?.detail || 'Edit failed.');
    } finally { setLoading(false); }
  };

  const handleReset = () => {
    navigate('/');
    setFile(null); setFilename(''); setPdfDoc(null);
    setCurrentPage(1); setTotalPages(0); setEdits([]); setTextBlocks([]);
    setOutputFilename(''); setError(''); setEditingBlock(null);
    setDragging(null); setDragPos(null);
  };

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
        <Routes>
          <Route path="/" element={
            <UploadStep
              file={file} setFile={setFile}
              loading={loading}
              onUpload={handleUpload}
              aiPanelOpen={aiPanelOpen} setAiPanelOpen={setAiPanelOpen}
            >
              {aiPanelNode}
            </UploadStep>
          } />

          <Route path="/edit" element={
            !file ? <Navigate to="/" replace /> : (
              <EditStep
                canvasRef={canvasRef} wrapperRef={wrapperRef}
                currentPage={currentPage} totalPages={totalPages} setCurrentPage={setCurrentPage}
                currentBlocks={currentBlocks} currentEdits={currentEdits}
                dragging={dragging} dragPos={dragPos}
                pdfToOverlay={pdfToOverlay}
                onCanvasClick={handleCanvasClick}
                onBlockClick={handleBlockClick} onBlockMouseDown={onBlockMouseDown}
                onEditMouseDown={onEditMouseDown}
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
            )
          } />

          <Route path="/download" element={
            !outputFilename ? <Navigate to="/" replace /> : (
              <DownloadStep
                outputFilename={outputFilename}
                downloadUrl={getDownloadUrl(outputFilename)}
                onReset={handleReset}
              />
            )
          } />
        </Routes>
      </main>

      <TextModal
        modal={modal}
        editingBlock={editingBlock}
        modalText={modalText}
        setModalText={setModalText}
        onConfirm={handleModalConfirm}
        onCancel={handleModalCancel}
        onDelete={handleModalDelete}
      />
    </div>
  );
}
