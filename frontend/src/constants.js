// App-wide constants
import * as pdfjsLib from 'pdfjs-dist';

pdfjsLib.GlobalWorkerOptions.workerSrc = new URL(
    'pdfjs-dist/build/pdf.worker.mjs',
    import.meta.url,
).toString();

export { pdfjsLib };

export const SCALE = 1.5;
export const STEPS = ['Upload', 'Edit', 'Download'];

// First Day 1 page (0-indexed in the PDF). page 8 = index 7.
export const DAY_1_PAGE_INDEX = 7;

/**
 * Coordinate zones for each logbook section (in PDF points at 1.0 scale).
 * Y = section header bottom edge + 12pt padding (measured from actual PDF drawings).
 * Header bottom edges: MY SPACE=173.8, Tasks=368.3, Key Learnings=526.3, Tools=650.9
 * Column divider for Tools/Special Achievements is at x=317.9.
 */
export const LOGBOOK_ZONES = [
    { key: 'my_space', x: 57, y: 186, maxW: 400 },
    { key: 'tasks_carried_out', x: 57, y: 381, maxW: 400 },
    { key: 'key_learnings', x: 57, y: 539, maxW: 400 },
    { key: 'tools_used', x: 57, y: 663, maxW: 190 },
    { key: 'special_achievements', x: 326, y: 663, maxW: 180 },
];
