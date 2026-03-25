import axios from 'axios';

const API = axios.create({
  baseURL: 'http://localhost:8000',
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

export const generateMonthLogbook = async (requestData) => {
    const response = await fetch(`${API.defaults.baseURL}/generate-month-logbook`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(requestData)
    });
    const data = await response.json();
    // Returns: { days: [{my_space, ...}], next_week_context: '' }
    return data;
};

export function getDownloadUrl(filename) {
  return `http://localhost:8000/download/${encodeURIComponent(filename)}`;
}
