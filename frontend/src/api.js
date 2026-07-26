const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000").replace(/\/+$/, "");

class ApiError extends Error {
  constructor(message, status) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

async function parseErrorMessage(res) {
  try {
    const body = await res.json();
    return body.message || body.detail || `Request failed with status ${res.status}`;
  } catch {
    return `Request failed with status ${res.status}`;
  }
}

export async function getHealth() {
  const res = await fetch(`${API_BASE_URL}/health`);
  if (!res.ok) throw new ApiError(await parseErrorMessage(res), res.status);
  return res.json();
}

export async function getStatus() {
  const res = await fetch(`${API_BASE_URL}/status`);
  if (!res.ok) throw new ApiError(await parseErrorMessage(res), res.status);
  return res.json();
}

export async function runInvestigation(file, query) {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("query", query ?? "");

  const res = await fetch(`${API_BASE_URL}/investigate`, {
    method: "POST",
    body: formData,
  });

  if (!res.ok) throw new ApiError(await parseErrorMessage(res), res.status);
  return res.json();
}

export { API_BASE_URL, ApiError };
