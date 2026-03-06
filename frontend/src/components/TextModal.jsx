import { useRef } from 'react';

/**
 * Text-insertion / text-edit modal with auto-growing textarea.
 */
export default function TextModal({ modal, editingBlock, modalText, setModalText, onConfirm, onCancel }) {
    const inputRef = useRef(null);

    if (!modal.open) return null;

    return (
        <div className="modal-overlay" onClick={onCancel}>
            <div className="modal-card" onClick={e => e.stopPropagation()}>
                <h3>{editingBlock ? 'Edit Text' : 'Add Text'}</h3>
                <p className="modal-coords">
                    {editingBlock
                        ? <><em>"{editingBlock.text}"</em></>
                        : <>Page · Position ({modal.x}, {modal.y})</>
                    }
                </p>
                <textarea
                    ref={inputRef}
                    className="modal-input modal-textarea"
                    placeholder={editingBlock ? 'Type replacement text…' : 'Enter text to insert…'}
                    value={modalText}
                    rows={1}
                    onChange={e => setModalText(e.target.value)}
                    onInput={e => {
                        e.target.style.height = 'auto';
                        e.target.style.height = e.target.scrollHeight + 'px';
                    }}
                    onKeyDown={e => {
                        if ((e.ctrlKey || e.shiftKey) && e.key === 'Enter') onConfirm();
                        if (e.key === 'Escape') onCancel();
                    }}
                    autoFocus
                />
                <div className="modal-actions">
                    <button className="btn ghost" onClick={onCancel}>Cancel</button>
                    <button className="btn primary" onClick={onConfirm} disabled={!modalText.trim()}>
                        {editingBlock ? 'Save Changes' : 'Add Text'}
                    </button>
                </div>
            </div>
        </div>
    );
}
