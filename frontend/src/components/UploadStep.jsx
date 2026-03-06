import { useRef } from 'react';

/**
 * Step 0 — Upload screen with dropzone and AI quick-start button.
 */
export default function UploadStep({
    file, setFile,
    loading,
    onUpload,
    aiPanelOpen, setAiPanelOpen,
    children,  // AiPanel passed as children when open
}) {
    const fileInputRef = useRef(null);

    return (
        <>
            <div className="card upload-card">
                <div className="card-header">
                    <h2>Upload PDF</h2>
                    <p>Select a PDF from your device to get started</p>
                </div>

                <div
                    className={`dropzone ${file ? 'has-file' : ''}`}
                    onClick={() => fileInputRef.current?.click()}
                    onDragOver={e => { e.preventDefault(); e.currentTarget.classList.add('dragover'); }}
                    onDragLeave={e => e.currentTarget.classList.remove('dragover')}
                    onDrop={e => {
                        e.preventDefault();
                        e.currentTarget.classList.remove('dragover');
                        const f = e.dataTransfer.files[0];
                        if (f && f.name.endsWith('.pdf')) setFile(f);
                    }}
                >
                    <input
                        ref={fileInputRef}
                        type="file" accept=".pdf" hidden
                        onChange={e => setFile(e.target.files[0])}
                    />
                    {file ? (
                        <div className="file-info">
                            <span className="file-icon">📑</span>
                            <div><strong>{file.name}</strong><small>{(file.size / 1024).toFixed(1)} KB</small></div>
                        </div>
                    ) : (
                        <>
                            <span className="upload-icon">⬆️</span>
                            <p><strong>Click or drag PDF here</strong></p>
                            <small>Only .pdf files accepted</small>
                        </>
                    )}
                </div>

                <button className="btn primary" onClick={onUpload} disabled={loading}>
                    {loading ? <span className="spinner" /> : null}
                    {loading ? 'Uploading…' : 'Upload & Continue'}
                </button>

                <div className="ai-divider"><span>or</span></div>

                <button className="btn ai-btn" onClick={() => setAiPanelOpen(true)}>
                    ✨ Make OJL Logbook with AI
                </button>
            </div>

            {aiPanelOpen && children}
        </>
    );
}
