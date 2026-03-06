import { useRef, useEffect, useCallback } from 'react';
import { SCALE } from '../constants';

/**
 * Converts pixel (clientX/Y) coordinates to PDF point coordinates.
 */
export function useCoordHelpers(canvasRef) {
    const pixelToPdf = useCallback((clientX, clientY) => {
        if (!canvasRef.current) return { x: 0, y: 0 };
        const canvas = canvasRef.current;
        const rect = canvas.getBoundingClientRect();
        const scaleX = canvas.width / rect.width;
        const scaleY = canvas.height / rect.height;
        return {
            x: ((clientX - rect.left) * scaleX) / SCALE,
            y: ((clientY - rect.top) * scaleY) / SCALE,
        };
    }, [canvasRef]);

    const pdfToOverlay = useCallback((pdfX, pdfY, pdfW, pdfH) => {
        if (!canvasRef.current) return {};
        const canvas = canvasRef.current;
        const rect = canvas.getBoundingClientRect();
        const rx = rect.width / canvas.width;
        const ry = rect.height / canvas.height;
        return {
            left: pdfX * SCALE * rx,
            top: pdfY * SCALE * ry,
            width: pdfW != null ? pdfW * SCALE * rx : undefined,
            height: pdfH != null ? pdfH * SCALE * ry : undefined,
        };
    }, [canvasRef]);

    return { pixelToPdf, pdfToOverlay };
}

/**
 * Renders a PDF page onto the canvas and redraws on page/edit changes.
 */
export function usePdfRenderer(canvasRef, pdfDoc, currentPage, edits) {
    const renderPage = useCallback(async (doc, pageNum) => {
        if (!doc || !canvasRef.current) return;
        const page = await doc.getPage(pageNum);
        const viewport = page.getViewport({ scale: SCALE });
        const canvas = canvasRef.current;
        canvas.width = viewport.width;
        canvas.height = viewport.height;
        const ctx = canvas.getContext('2d');
        await page.render({ canvasContext: ctx, viewport }).promise;

        // White-out replaced text areas
        edits
            .filter(e => e.page === pageNum && e.type === 'replace' && e.orig_x != null)
            .forEach(e => {
                ctx.fillStyle = '#ffffff';
                ctx.fillRect(e.orig_x * SCALE, e.orig_y * SCALE, (e.orig_w + 1) * SCALE, (e.orig_h + 1) * SCALE);
            });
    }, [canvasRef, edits]);

    useEffect(() => {
        if (pdfDoc) renderPage(pdfDoc, currentPage);
    }, [pdfDoc, currentPage, renderPage]);
}
