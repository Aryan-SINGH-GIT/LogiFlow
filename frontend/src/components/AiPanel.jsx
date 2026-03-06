/**
 * AI Logbook Generator form — reused in UploadStep and EditSidebar.
 */
export default function AiPanel({
    aiForm, setAiForm,
    onGenerate, onCancel,
    aiLoading, loading,
    compact = false,   // true when used in sidebar (fewer rows)
    showUploadAndGenerate = false,  // true when used on upload step
    onUploadAndGenerate,
}) {
    return (
        <div className="card ai-panel">
            <div className="card-header">
                <h2>✨ {compact ? 'AI Generator' : 'AI OJL Logbook Generator'}</h2>
                {!compact && <p>Describe your project and what you did today — AI will fill in the logbook.</p>}
                {compact && <p>Fill in the logbook with AI</p>}
            </div>

            <div className="ai-form">
                <label>Project Description</label>
                <textarea
                    className="ai-textarea"
                    rows={compact ? 2 : 3}
                    placeholder="e.g. A full-stack expense tracker using Django + React"
                    value={aiForm.projectDesc}
                    onChange={e => setAiForm(f => ({ ...f, projectDesc: e.target.value }))}
                />

                <label>Tech Stack</label>
                <input
                    className="modal-input"
                    placeholder="e.g. Django, React, PostgreSQL, Redis"
                    value={aiForm.techStack}
                    onChange={e => setAiForm(f => ({ ...f, techStack: e.target.value }))}
                />

                <div style={{ display: 'flex', gap: '10px' }}>
                    <div style={{ flex: 1 }}>
                        <label>Start Date</label>
                        <input
                            type="date"
                            className="modal-input"
                            value={aiForm.startDate}
                            onChange={e => setAiForm(f => ({ ...f, startDate: e.target.value }))}
                        />
                    </div>
                    <div style={{ flex: 1 }}>
                        <label>End Date</label>
                        <input
                            type="date"
                            className="modal-input"
                            value={aiForm.endDate}
                            onChange={e => setAiForm(f => ({ ...f, endDate: e.target.value }))}
                        />
                    </div>
                </div>

                <label>Start PDF Day Index (Optional)</label>
                <input
                    type="number" min={1}
                    className="modal-input"
                    placeholder="e.g. 1 (Places the first day on Day 1 of the PDF)"
                    value={aiForm.startPdfDay}
                    onChange={e => setAiForm(f => ({ ...f, startPdfDay: parseInt(e.target.value) || 1 }))}
                />

                <label>What did you do today? (brief notes)</label>
                <textarea
                    className="ai-textarea"
                    rows={compact ? 3 : 4}
                    placeholder="e.g. Set up virtual env, installed DRF, wrote user auth endpoints, tested JWT flow"
                    value={aiForm.dayOverview}
                    onChange={e => setAiForm(f => ({ ...f, dayOverview: e.target.value }))}
                />
            </div>

            <div style={{ display: 'flex', gap: '10px', marginTop: '12px', flexWrap: 'wrap' }}>
                {onCancel && (
                    <button className="btn ghost" onClick={onCancel}>Cancel</button>
                )}
                {showUploadAndGenerate && (
                    <button
                        className="btn ai-btn"
                        onClick={onUploadAndGenerate}
                        disabled={aiLoading || loading}
                    >
                        {(aiLoading || loading) ? <><span className="spinner" /> Generating…</> : '✨ Generate & Apply'}
                    </button>
                )}
                {!showUploadAndGenerate && (
                    <button
                        className="btn ai-btn"
                        style={{ flex: 1 }}
                        onClick={onGenerate}
                        disabled={aiLoading}
                    >
                        {aiLoading ? <><span className="spinner" /> Generating…</> : '✨ Generate'}
                    </button>
                )}
            </div>
        </div>
    );
}
