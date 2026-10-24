/* Talks to the clinic server (the same backend as the clinic app).
   The login is kept only for this browser tab (sessionStorage), so closing
   the tab logs the patient out — safer on shared family phones. */

const BASE = (import.meta.env.VITE_API_URL || "https://dental-backend-xojn.onrender.com/api").replace(/\/+$/, "");
const KEY = "ssd_portal";

export function getSession() {
  try { return JSON.parse(sessionStorage.getItem(KEY) || "null"); } catch { return null; }
}
export function setSession(s) {
  try { if (s) sessionStorage.setItem(KEY, JSON.stringify(s)); else sessionStorage.removeItem(KEY); } catch { /* private mode */ }
}

export class ApiError extends Error {
  constructor(message, status) { super(message); this.status = status; }
}

async function request(path, { method = "GET", body, raw = false } = {}) {
  const s = getSession();
  const headers = {};
  if (body !== undefined) headers["Content-Type"] = "application/json";
  if (s?.token) headers.Authorization = `Bearer ${s.token}`;
  let res;
  try {
    res = await fetch(BASE + path, { method, headers, body: body !== undefined ? JSON.stringify(body) : undefined });
  } catch {
    throw new ApiError("Could not reach the clinic server. Check your internet connection and try again.", 0);
  }
  if (res.status === 401 && s?.token) {
    setSession(null);
    window.dispatchEvent(new Event("portal-logout"));
  }
  if (!res.ok) {
    let msg = "Something went wrong. Please try again.";
    try { const j = await res.json(); msg = j.error || j.message || j.msg || msg; } catch { /* not JSON */ }
    if (res.status === 401 && s?.token) msg = "Your login has expired. Please log in again.";
    throw new ApiError(msg, res.status);
  }
  if (raw) return res.blob();
  return res.json();
}

export const portal = {
  requestCode: (mobile) => request("/portal/otp/request", { method: "POST", body: { mobile } }),
  verifyCode: (mobile, code) => request("/portal/otp/verify", { method: "POST", body: { mobile, code } }),
  me: () => request("/portal/me"),
  record: (pid) => request(`/portal/patients/${pid}/record`),
  imageBlob: (id) => request(`/portal/files/image/${id}/data`, { raw: true }),
  imageLink: (id) => request(`/portal/files/image/${id}`),
  receiptBlob: (id) => request(`/portal/files/receipt/${id}`, { raw: true }),
  cbctPreview: (id) => request(`/portal/files/cbct/${id}/preview`, { raw: true }),
  cbctZip: (id) => request(`/portal/files/cbct/${id}/zip`),
};
