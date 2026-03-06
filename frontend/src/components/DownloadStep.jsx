/**
 * Step 2 — Download screen shown after edits are applied.
 */
export default function DownloadStep({ outputFilename, downloadUrl, onReset }) {
    return (
        <div className="card download-card">
            <div className="success-icon">✅</div>
            <h2>PDF Ready!</h2>
            <p>Your edited PDF is ready for download.</p>
            <div className="download-filename">{outputFilename}</div>
            <div className="download-actions">
                <a className="btn primary" href={downloadUrl} download>⬇ Download PDF</a>
                <button className="btn ghost" onClick={onReset}>Edit Another PDF</button>
            </div>
        </div>
    );
}
