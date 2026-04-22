import axios from 'axios';

// Use environment variable if set; otherwise, use Render URL in production, or localhost locally
const isProd = import.meta.env.PROD;
const rawBaseUrl = import.meta.env.VITE_API_URL || (isProd ? 'https://logiflow-cw5a.onrender.com' : 'http://localhost:8000');
const BASE_URL = rawBaseUrl.endsWith('/') ? rawBaseUrl.slice(0, -1) : rawBaseUrl;

const API = axios.create({
  baseURL: BASE_URL,
});

export async function uploadPdf(file) {
  const form = new FormData();
  form.append('file', file);
  const { data } = await API.post('/upload', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return data;
}

export async function editPdf(filename, edits) {
  const { data } = await API.post('/edit', { filename, edits });
  return data;
}

export async function extractText(filename) {
  const { data } = await API.get(`/extract-text/${encodeURIComponent(filename)}`);
  return data.blocks;
}

export const generateMonthLogbook = async (requestData, signal, taskId) => {
    const url = new URL(`${API.defaults.baseURL}/generate-month-logbook`);
    if (taskId) url.searchParams.append('task_id', taskId);

    // Attach user-supplied API keys from sessionStorage
    const gemini_api_key = sessionStorage.getItem('gemini_api_key') || undefined;
    const groq_api_key = sessionStorage.getItem('groq_api_key') || undefined;

    const response = await fetch(url.toString(), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ...requestData, gemini_api_key, groq_api_key }),
        signal: signal
    });
    
    if (!response.ok) {
        const errData = await response.json().catch(() => ({}));
        throw { response: { data: errData } };
    }
    
    const data = await response.json();
    return data;
};

export const cancelGeneration = async (taskId) => {
    try {
        await API.post(`/cancel-generation/${encodeURIComponent(taskId)}`);
    } catch (err) {
        console.error("Failed to call cancel endpoint:", err);
    }
};

export function getDownloadUrl(filename) {
  return `${BASE_URL}/download/${encodeURIComponent(filename)}`;
}
