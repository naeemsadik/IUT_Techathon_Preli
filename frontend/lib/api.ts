// =============================================================================
//  Frontend API client — typed wrappers around the FastAPI backend.
//  All requests go through `apiFetch` so the base URL is centralised.
// =============================================================================

import type {
  OfficeStatus,
  Room,
  Usage,
  HistoryResponse,
  RangeKey,
  ApiEnvelope,
} from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";

class ApiError extends Error {
  constructor(public status: number, public detail: string) {
    super(`API ${status}: ${detail}`);
  }
}

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const url = `${API_BASE}${path}`;
  const response = await fetch(url, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
    cache: "no-store",
  });
  if (!response.ok) {
    let detail = response.statusText;
    try {
      const body = await response.json();
      detail = body.detail ?? body.message ?? detail;
    } catch {
      /* ignore */
    }
    throw new ApiError(response.status, detail);
  }
  const envelope = (await response.json()) as ApiEnvelope<T>;
  return envelope.data;
}

// ---------- Status / Rooms / Usage ----------

export async function getStatus(): Promise<OfficeStatus> {
  return apiFetch<OfficeStatus>("/api/status");
}

export async function getRoom(name: string): Promise<Room> {
  return apiFetch<Room>(`/api/room/${encodeURIComponent(name)}`);
}

export async function getUsage(): Promise<Usage> {
  return apiFetch<Usage>("/api/usage");
}

export async function getHealth(): Promise<{ status: string; version: string }> {
  return apiFetch("/api/health");
}

// ---------- History (analytics) ----------

export async function getHistory(range: RangeKey): Promise<HistoryResponse> {
  return apiFetch<HistoryResponse>(`/api/history?range=${range}`);
}

export { ApiError, API_BASE };