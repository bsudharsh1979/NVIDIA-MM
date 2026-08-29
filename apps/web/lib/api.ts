const BASE = process.env.NEXT_PUBLIC_API_BASE || "";

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

export function apiUrl(path: string): string {
  return path.startsWith("http") ? path : `${BASE}${path}`;
}

async function requestOnce<T>(url: string, init?: RequestInit, timeoutMs = 65000): Promise<T> {
  const ctrl = new AbortController();
  const timer = setTimeout(() => ctrl.abort(), timeoutMs);
  try {
    const res = await fetch(url, {
      ...init,
      headers: {
        ...(init?.body instanceof FormData ? {} : { "Content-Type": "application/json" }),
        ...(init?.headers || {}),
      },
      cache: "no-store",
      signal: ctrl.signal,
    });
    if (!res.ok) {
      let detail = "";
      try {
        const body = await res.json();
        detail = typeof body?.detail === "string" ? body.detail : JSON.stringify(body);
      } catch {
        detail = res.statusText;
      }
      throw new ApiError(res.status, detail || `HTTP ${res.status}`);
    }
    return res.json();
  } finally {
    clearTimeout(timer);
  }
}

/**
 * Fetch JSON with one automatic retry for GETs that hit a cold container
 * (network error, timeout, or 502/503/504). Writes are never retried.
 */
export async function api<T = any>(path: string, init?: RequestInit): Promise<T> {
  const url = apiUrl(path);
  const method = (init?.method || "GET").toUpperCase();
  try {
    return await requestOnce<T>(url, init);
  } catch (e) {
    const gateway = e instanceof ApiError && e.status >= 502;
    const network = !(e instanceof ApiError);
    if (method === "GET" && (gateway || network)) {
      await new Promise((r) => setTimeout(r, 1800));
      return requestOnce<T>(url, init);
    }
    throw e;
  }
}

export function friendlyError(e: unknown): string {
  if (e instanceof ApiError) {
    if (e.status === 404) return e.message;
    if (e.status >= 500) return `The API reported an error (${e.status}). ${e.message}`;
    return `${e.status}: ${e.message}`;
  }
  const msg = String((e as Error)?.message || e);
  if (msg.includes("abort")) {
    return "The API timed out. The first request after idle wakes a Modal container (~10 s) — retry once.";
  }
  if (msg.includes("fetch") || msg.includes("network")) {
    return "Cannot reach the API. Check your connection, then retry — cold starts resolve in seconds.";
  }
  return msg;
}
