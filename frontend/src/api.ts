import { API_BASE } from "./constants";

export async function apiCall(
  endpoint: string,
  token: string | null,
  options: RequestInit = {}
): Promise<any> {
  const headers = new Headers(options.headers || {});

  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  const initData = window.Telegram?.WebApp?.initData;
  if (initData) {
    headers.set("X-Telegram-Init-Data", initData);
  }

  const response = await fetch(`${API_BASE}${endpoint}`, { ...options, headers });

  if (!response.ok) {
    const errData = await response.json().catch(() => ({ detail: "Unknown error" }));
    throw new Error(errData.detail || `HTTP Error ${response.status}`);
  }

  return response.json();
}

export async function authenticateTelegram(initData: string) {
  const response = await fetch(`${API_BASE}/auth/telegram`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ init_data: initData }),
  });
  if (!response.ok) throw new Error("Auth failed");
  return response.json();
}

export async function analyzeScreenshot(token: string | null, file: File) {
  const formData = new FormData();
  formData.append("screenshot", file);
  const headers = new Headers();
  if (token) headers.set("Authorization", `Bearer ${token}`);
  const initData = window.Telegram?.WebApp?.initData;
  if (initData) headers.set("X-Telegram-Init-Data", initData);

  const response = await fetch(`${API_BASE}/user/analyze`, {
    method: "POST",
    headers,
    body: formData,
  });

  if (!response.ok) {
    const err = await response.json().catch(() => ({ detail: "Analysis failed" }));
    throw new Error(err.detail || `HTTP ${response.status}`);
  }
  return response.json();
}
