/**
 * ApiKeysModal — Prompts user for Gemini and Groq API keys before AI generation.
 * Keys are saved to sessionStorage so the modal only appears once per session.
 */
import { useState, useEffect } from 'react';

export default function ApiKeysModal({ open, onSave, onClose }) {
    const [geminiKey, setGeminiKey] = useState('');
    const [groqKey, setGroqKey] = useState('');
    const [showGemini, setShowGemini] = useState(false);
    const [showGroq, setShowGroq] = useState(false);
    const [error, setError] = useState('');

    // Pre-fill from sessionStorage if already set
    useEffect(() => {
        if (open) {
            setGeminiKey(sessionStorage.getItem('gemini_api_key') || '');
            setGroqKey(sessionStorage.getItem('groq_api_key') || '');
            setError('');
        }
    }, [open]);

    if (!open) return null;

    const handleSave = () => {
        if (!geminiKey.trim()) {
            setError('Gemini API key is required.');
            return;
        }
        sessionStorage.setItem('gemini_api_key', geminiKey.trim());
        sessionStorage.setItem('groq_api_key', groqKey.trim());
        onSave({ geminiKey: geminiKey.trim(), groqKey: groqKey.trim() });
    };

    const handleClear = () => {
        sessionStorage.removeItem('gemini_api_key');
        sessionStorage.removeItem('groq_api_key');
        setGeminiKey('');
        setGroqKey('');
    };

    return (
        <div className="api-modal-overlay" onClick={(e) => e.target === e.currentTarget && onClose()}>
            <div className="api-modal">
                {/* Header */}
                <div className="api-modal-header">
                    <div className="api-modal-icon">🔑</div>
                    <div>
                        <h2 className="api-modal-title">API Keys Required</h2>
                        <p className="api-modal-subtitle">
                            Your keys are stored only in this browser session — never sent anywhere else.
                        </p>
                    </div>
                    <button className="api-modal-close" onClick={onClose}>✕</button>
                </div>

                {/* Body */}
                <div className="api-modal-body">
                    {/* Gemini Key */}
                    <div className="api-key-group">
                        <label className="api-key-label">
                            <span className="api-key-badge gemini-badge">Gemini</span>
                            Gemini API Key
                            <span className="api-key-required">Required</span>
                        </label>
                        <p className="api-key-hint">
                            Used for planning and context generation.
                            Get yours at <a href="https://aistudio.google.com/app/apikey" target="_blank" rel="noreferrer">aistudio.google.com</a>
                        </p>
                        <div className="api-key-input-wrapper">
                            <input
                                type={showGemini ? 'text' : 'password'}
                                className="api-key-input"
                                placeholder="AIza..."
                                value={geminiKey}
                                onChange={e => { setGeminiKey(e.target.value); setError(''); }}
                                autoComplete="off"
                                spellCheck={false}
                            />
                            <button
                                type="button"
                                className="api-key-toggle"
                                onClick={() => setShowGemini(v => !v)}
                                title={showGemini ? 'Hide' : 'Show'}
                            >
                                {showGemini ? '🙈' : '👁️'}
                            </button>
                        </div>
                    </div>

                    {/* Groq Key */}
                    <div className="api-key-group">
                        <label className="api-key-label">
                            <span className="api-key-badge groq-badge">Groq</span>
                            Groq API Key
                            <span className="api-key-optional">Optional</span>
                        </label>
                        <p className="api-key-hint">
                            Used for fast logbook writing (Llama 3.3).
                            Get yours at <a href="https://console.groq.com/keys" target="_blank" rel="noreferrer">console.groq.com</a>
                        </p>
                        <div className="api-key-input-wrapper">
                            <input
                                type={showGroq ? 'text' : 'password'}
                                className="api-key-input"
                                placeholder="gsk_..."
                                value={groqKey}
                                onChange={e => setGroqKey(e.target.value)}
                                autoComplete="off"
                                spellCheck={false}
                            />
                            <button
                                type="button"
                                className="api-key-toggle"
                                onClick={() => setShowGroq(v => !v)}
                                title={showGroq ? 'Hide' : 'Show'}
                            >
                                {showGroq ? '🙈' : '👁️'}
                            </button>
                        </div>
                    </div>

                    {error && <div className="api-key-error">⚠️ {error}</div>}

                    <div className="api-modal-info">
                        <span>🔒</span>
                        <span>Keys are stored in <strong>sessionStorage</strong> — they're cleared when you close the browser tab and are never sent to our servers.</span>
                    </div>
                </div>

                {/* Footer */}
                <div className="api-modal-footer">
                    <button className="btn ghost" onClick={handleClear}>Clear Keys</button>
                    <div style={{ display: 'flex', gap: '10px' }}>
                        <button className="btn ghost" onClick={onClose}>Cancel</button>
                        <button className="btn ai-btn" onClick={handleSave}>
                            Save & Continue →
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
}
