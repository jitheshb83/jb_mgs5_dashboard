/**
 * Typed API client for the FastAPI backend, per docs/architecture/api_contract.md.
 *
 * Every hook in hooks/ calls this module directly against the real backend.
 * hooks/mockData.ts is only used by test files now (fixtures for rendering
 * components without a real network call), not by any hook's runtime path.
 */

import type {
  AdvancedResponse,
  BatteryUsageResponse,
  HistoryParams,
  HistoryResponse,
  LatestResponse,
  RefreshResponse,
  Settings,
  ApiErrorBody,
} from "./types";

export const BASE_URL = "http://localhost:8000";

/** Thrown when the backend returns a non-2xx response. Carries the HTTP status and the contract's {error, detail} body. */
export class ApiRequestError extends Error {
  readonly status: number;
  readonly detail: string;

  constructor(status: number, body: ApiErrorBody) {
    super(body.detail || body.error || `Request failed with status ${status}`);
    this.name = "ApiRequestError";
    this.status = status;
    this.detail = body.detail || body.error;
  }
}

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let body: ApiErrorBody;
    try {
      body = (await res.json()) as ApiErrorBody;
    } catch {
      body = { error: "unknown_error", detail: "The server returned an unexpected error." };
    }
    throw new ApiRequestError(res.status, body);
  }
  return (await res.json()) as T;
}

/** POST /api/refresh — triggers a refresh; backend decides live vs. cached per the 30-min floor. */
export async function refresh(): Promise<RefreshResponse> {
  const res = await fetch(`${BASE_URL}/api/refresh`, { method: "POST" });
  return handleResponse<RefreshResponse>(res);
}

/** GET /api/latest — most recent snapshot from SQLite, no external API call. */
export async function getLatest(): Promise<LatestResponse> {
  const res = await fetch(`${BASE_URL}/api/latest`);
  return handleResponse<LatestResponse>(res);
}

/** GET /api/history — snapshot history for trend charts. */
export async function getHistory(params: HistoryParams = {}): Promise<HistoryResponse> {
  const url = new URL(`${BASE_URL}/api/history`);
  if (params.from) url.searchParams.set("from", params.from);
  if (params.to) url.searchParams.set("to", params.to);
  if (params.limit !== undefined) url.searchParams.set("limit", String(params.limit));
  const res = await fetch(url);
  return handleResponse<HistoryResponse>(res);
}

/** GET /api/settings */
export async function getSettings(): Promise<Settings> {
  const res = await fetch(`${BASE_URL}/api/settings`);
  return handleResponse<Settings>(res);
}

/** PUT /api/settings — partial or full settings object; returns the updated full object. */
export async function updateSettings(partial: Partial<Settings>): Promise<Settings> {
  const res = await fetch(`${BASE_URL}/api/settings`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(partial),
  });
  return handleResponse<Settings>(res);
}

/** GET /api/latest/advanced — decoded "everything else" fields from the latest snapshot's raw API response. */
export async function getAdvanced(): Promise<AdvancedResponse> {
  const res = await fetch(`${BASE_URL}/api/latest/advanced`);
  return handleResponse<AdvancedResponse>(res);
}

/** GET /api/latest/battery-usage — vehicle self-reported battery usage statistics. */
export async function getBatteryUsage(): Promise<BatteryUsageResponse> {
  const res = await fetch(`${BASE_URL}/api/latest/battery-usage`);
  return handleResponse<BatteryUsageResponse>(res);
}
