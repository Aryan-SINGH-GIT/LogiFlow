import { SCALE } from '../constants';

/**
 * Edit sidebar — edits list, AI panel toggle, and apply/reset buttons.
 */
export default function EditSidebar({
    edits, removeEdit,
    loading,
    onApplyEdits, onReset,
    aiPanelOpen, setAiPanelOpen,
    children,   // AiPanel passed as children when open
}) {
    return (
        <div className="editor-sidebar">
            {/* AI toggle */}
            <button
                className="btn ai-btn ai-sidebar-btn"
                onClick={() => setAiPanelOpen(p => !p)}
            >
                {aiPanelOpen ? 'Close AI Generator' : 'Fill with AI'}
            </button>

            {aiPanelOpen && children}

            {/* Edits list */}
            <div className="card">
                <div className="card-header">
                    <h2>Edits</h2>
                    <p>{edits.length} edit{edits.length !== 1 ? 's' : ''} queued</p>
                </div>

                <div className="edits-list">
                    {edits.length === 0 ? (
                        <div className="empty-state">
                            <span>🖊️</span>
                            <p>Click on the PDF to place or edit text</p>
                        </div>
                    ) : (
                        edits.map((e, i) => (
                            <div key={i} className={`edit-item ${e.type === 'replace' ? 'replace-edit' : 'insert-edit'}`}>
                                <div className="edit-info">
                                    {e.type === 'replace' ? (
                                        <>
                                            <div className="edit-type-badge replace">Replace</div>
                                            <small className="orig-text">"{e.orig_text}"</small>
                                            <strong>→ "{e.text}"</strong>
                                            <small>Page {e.page} · ({e.x}, {e.y})</small>
                                        </>
                                    ) : (
                                        <>
                                            <div className="edit-type-badge insert">Insert</div>
                                            <strong>"{e.text}"</strong>
                                            <small>Page {e.page} · ({e.x}, {e.y})</small>
                                        </>
                                    )}
                                </div>
                                <button className="btn icon-btn danger-btn" onClick={() => removeEdit(i)}>✕</button>
                            </div>
                        ))
                    )}
                </div>

                <div className="sidebar-actions">
                    <button className="btn primary" onClick={onApplyEdits} disabled={loading || edits.length === 0}>
                        {loading ? <span className="spinner" /> : null}
                        {loading ? 'Applying…' : 'Apply Edits'}
                    </button>
                    <button className="btn ghost" onClick={onReset}>Start Over</button>
                </div>
            </div>
        </div>
    );
}
