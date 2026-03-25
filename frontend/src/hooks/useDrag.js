import { useRef, useEffect } from 'react';

/**
 * Handles all drag-and-drop logic for edit overlays and text blocks.
 * Returns handlers to attach to overlay divs, and the global mouseup effect.
 */
export function useDrag({
    dragging, setDragging,
    dragPos, setDragPos,
    edits, setEdits,
    setEditingBlock, setModalText, setModal,
    currentBlocks, currentPage,
    textBlocks, setTextBlocks,
    pixelToPdf,
    showToast,
}) {
    const pointerDownInfoRef = useRef(null);

    // Global mousemove / mouseup listeners while dragging
    useEffect(() => {
        if (!dragging) return;

        const handleMouseMove = (e) => {
            const { x, y } = pixelToPdf(e.clientX, e.clientY);
            const dx = x - dragging.startX;
            const dy = y - dragging.startY;
            setDragPos({ x: dragging.origX + dx, y: dragging.origY + dy });
        };

        const handleMouseUp = () => {
            if (!dragPos) { setDragging(null); return; }

            if (dragging.type === 'edit') {
                const movedX = Math.abs(dragPos.x - dragging.origX);
                const movedY = Math.abs(dragPos.y - dragging.origY);

                if (movedX < 4 && movedY < 4) {
                    // Click: open edit modal
                    const edit = edits[dragging.index];
                    if (edit) {
                        setEditingBlock({ ...edit, _editIndex: dragging.index });
                        setModalText(edit.text);
                        setModal({ open: true, x: edit.x, y: edit.y });
                    }
                } else {
                    // Drag: update position
                    setEdits(prev => prev.map((e, i) =>
                        i !== dragging.index ? e : { ...e, x: Math.round(dragPos.x), y: Math.round(dragPos.y) }
                    ));
                    showToast('Text moved!');
                }
            } else if (dragging.type === 'block') {
                const block = currentBlocks[dragging.index];
                const newX = Math.round(dragPos.x);
                const newY = Math.round(dragPos.y);
                if (Math.abs(newX - block.x) > 2 || Math.abs(newY - block.y) > 2) {
                    setEdits(prev => [...prev, {
                        page: block.page, x: newX, y: newY + block.h,
                        text: block.text, font_size: block.font_size || 12,
                        type: 'replace',
                        orig_x: block.x, orig_y: block.y, orig_w: block.w, orig_h: block.h,
                        orig_text: block.text,
                    }]);
                    setTextBlocks(prev => prev.map(b => {
                        const pageBlocks = prev.filter(bb => bb.page === currentPage);
                        const target = pageBlocks[dragging.index];
                        return b === target ? { ...b, _edited: true, _newText: b.text, x: newX, y: newY } : b;
                    }));
                    showToast('Text moved!');
                }
            }
            setDragging(null);
            setDragPos(null);
        };

        window.addEventListener('mousemove', handleMouseMove);
        window.addEventListener('mouseup', handleMouseUp);
        return () => {
            window.removeEventListener('mousemove', handleMouseMove);
            window.removeEventListener('mouseup', handleMouseUp);
        };
    }, [dragging, dragPos, pixelToPdf, currentPage, showToast]);

    const onEditMouseDown = (e, editIndex) => {
        e.stopPropagation();
        e.preventDefault();
        pointerDownInfoRef.current = { time: Date.now(), clientX: e.clientX, clientY: e.clientY, editIndex };
        const { x, y } = pixelToPdf(e.clientX, e.clientY);
        const edit = edits[editIndex];
        setDragging({ type: 'edit', index: editIndex, startX: x, startY: y, origX: edit.x, origY: edit.y });
        setDragPos({ x: edit.x, y: edit.y });
    };

    const onBlockMouseDown = (e, blockIndex) => {
        e.stopPropagation();
        e.preventDefault();
        const { x, y } = pixelToPdf(e.clientX, e.clientY);
        const block = currentBlocks[blockIndex];
        setDragging({ type: 'block', index: blockIndex, startX: x, startY: y, origX: block.x, origY: block.y });
        setDragPos({ x: block.x, y: block.y });
    };

    return { onEditMouseDown, onBlockMouseDown };
}
