import { SCALE } from '../constants';

/**
 * Step 1 — Edit canvas with PDF rendering, text overlays, and edit overlays.
 */
export default function EditStep({
    canvasRef, wrapperRef,
    currentPage, totalPages, setCurrentPage,
    currentBlocks, currentEdits,
    dragging, dragPos,
    pdfToOverlay,
    onCanvasClick,
    onBlockClick, onBlockMouseDown,
    onEditMouseDown,
    children,  // EditSidebar passed as children
}) {
    return (
        <div className="editor-layout">
            <div className="editor-canvas-wrap">
                {/* Page navigation */}
                <div className="canvas-toolbar">
                    <button className="btn ghost sm" disabled={currentPage <= 1} onClick={() => setCurrentPage(p => p - 1)}>◀</button>
                    <span className="page-info">Page {currentPage} / {totalPages}</span>
                    <button className="btn ghost sm" disabled={currentPage >= totalPages} onClick={() => setCurrentPage(p => p + 1)}>▶</button>
                </div>

                <div className="canvas-container">
                    <div className="canvas-wrapper" ref={wrapperRef}>
                        <canvas
                            ref={canvasRef}
                            onClick={onCanvasClick}
                            className={`pdf-canvas ${dragging ? 'dragging' : ''}`}
                        />

                        {/* Text block overlays (invisible clickable/draggable areas over existing PDF text) */}
                        {currentBlocks.map((block, i) => {
                            const isDraggingThis = dragging?.type === 'block' && dragging.index === i;
                            const displayX = isDraggingThis ? dragPos.x : block.x;
                            const displayY = isDraggingThis ? dragPos.y : block.y;
                            const style = pdfToOverlay(displayX, displayY, block.w, block.h);
                            return (
                                <div
                                    key={`block-${block.page}-${i}`}
                                    className={`text-overlay ${block._edited ? 'edited' : ''} ${isDraggingThis ? 'is-dragging' : ''}`}
                                    style={style}
                                    title={block._edited
                                        ? `"${block.text}" → "${block._newText}" (drag to move)`
                                        : `"${block.text}" — click to edit, drag to move`
                                    }
                                    onClick={e => !isDraggingThis && onBlockClick(block, e)}
                                    onMouseDown={e => onBlockMouseDown(e, i)}
                                />
                            );
                        })}

                        {/* Edit overlays (visible purple labels for queued edits) */}
                        {currentEdits.map(edit => {
                            const isDraggingThis = dragging?.type === 'edit' && dragging.index === edit._idx;
                            const displayX = isDraggingThis ? dragPos.x : edit.x;
                            const displayY = isDraggingThis ? dragPos.y : edit.y;
                            const isMultiline = edit.text?.includes('\n');
                            const baseStyle = pdfToOverlay(displayX, isMultiline ? displayY : displayY - 12);
                            const style = {
                                ...baseStyle,
                                whiteSpace: 'pre-wrap',
                                maxWidth: isMultiline ? `${400 * SCALE}px` : undefined,
                                lineHeight: 1.4,
                                cursor: 'grab',
                            };
                            return (
                                <div
                                    key={`edit-${edit._idx}`}
                                    className={`edit-overlay ${isDraggingThis ? 'is-dragging' : ''}`}
                                    style={style}
                                    title="Click to edit · drag to move"
                                    onMouseDown={e => onEditMouseDown(e, edit._idx)}
                                >
                                    {edit.text}
                                </div>
                            );
                        })}
                    </div>

                    <div className="canvas-hint">
                        💡 <strong>Click</strong> to add text · <strong>Click existing text</strong> to edit · <strong>Drag</strong> any text to reposition
                    </div>
                </div>
            </div>

            {children}
        </div>
    );
}
