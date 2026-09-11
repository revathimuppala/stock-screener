import type {
  BacktestJob,
  SavedScreen,
  SavedScreenListResponse,
  ScreeningCriteria,
  ScreenResponse,
  WatchlistResponse,
} from "@/lib/types";

export const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export class ScreenerApiError extends Error {
  status?: number;

  constructor(message: string, status?: number) {
    super(message);
    this.name = "ScreenerApiError";
    this.status = status;
  }
}

async function getJson<T>(path: string): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`);
  if (!response.ok) {
    throw new ScreenerApiError(`Request to ${path} failed with status ${response.status}`, response.status);
  }
  return response.json() as Promise<T>;
}

async function postJson<T>(path: string, body: unknown): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!response.ok) {
    throw new ScreenerApiError(`Request to ${path} failed with status ${response.status}`, response.status);
  }
  return response.json() as Promise<T>;
}

async function deleteRequest(path: string): Promise<void> {
  const response = await fetch(`${API_BASE_URL}${path}`, { method: "DELETE" });
  if (!response.ok) {
    throw new ScreenerApiError(`Request to ${path} failed with status ${response.status}`, response.status);
  }
}

export async function postScreen(criteria: ScreeningCriteria): Promise<ScreenResponse> {
  return postJson<ScreenResponse>("/api/v1/screener", criteria);
}

export interface QueryParseErrorDetail {
  error: string;
  position: number;
}

export class QueryParseException extends Error {
  detail: QueryParseErrorDetail;

  constructor(detail: QueryParseErrorDetail) {
    super(detail.error);
    this.name = "QueryParseException";
    this.detail = detail;
  }
}

export async function postQuery(query: string): Promise<ScreenResponse> {
  const response = await fetch(`${API_BASE_URL}/api/v1/screener/query`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query }),
  });
  if (response.status === 400) {
    const body = await response.json();
    throw new QueryParseException(body.detail);
  }
  if (!response.ok) {
    throw new ScreenerApiError(`Query request failed with status ${response.status}`, response.status);
  }
  return response.json() as Promise<ScreenResponse>;
}

export async function getWatchlist(): Promise<WatchlistResponse> {
  return getJson<WatchlistResponse>("/api/v1/watchlist");
}

export async function addToWatchlist(symbol: string): Promise<WatchlistResponse> {
  return postJson<WatchlistResponse>("/api/v1/watchlist", { symbol });
}

export async function removeFromWatchlist(symbol: string): Promise<void> {
  return deleteRequest(`/api/v1/watchlist/${encodeURIComponent(symbol)}`);
}

export async function listSavedScreens(): Promise<SavedScreenListResponse> {
  return getJson<SavedScreenListResponse>("/api/v1/screens");
}

export async function saveScreen(
  name: string,
  criteria: ScreeningCriteria
): Promise<SavedScreen> {
  return postJson<SavedScreen>("/api/v1/screens", { name, criteria });
}

export async function saveQueryScreen(name: string, query: string): Promise<SavedScreen> {
  return postJson<SavedScreen>("/api/v1/screens", { name, query });
}

export async function deleteSavedScreen(screenId: string): Promise<void> {
  return deleteRequest(`/api/v1/screens/${encodeURIComponent(screenId)}`);
}

export async function runSavedScreen(screenId: string): Promise<ScreenResponse> {
  return getJson<ScreenResponse>(`/api/v1/screens/${encodeURIComponent(screenId)}/run`);
}

export interface StartBacktestParams {
  query: string;
  start_date: string;
  end_date: string;
  holding_period_days: number;
}

export async function startBacktest(
  params: StartBacktestParams
): Promise<{ backtest_id: string; status: string }> {
  return postJson("/api/v1/backtest", params);
}

export async function getBacktest(backtestId: string): Promise<BacktestJob> {
  return getJson<BacktestJob>(`/api/v1/backtest/${encodeURIComponent(backtestId)}`);
}

export function buildScreenerExportUrl(criteria: ScreeningCriteria): string {
  const params = new URLSearchParams();
  for (const [key, value] of Object.entries(criteria)) {
    if (value !== undefined && value !== null) {
      params.set(key, String(value));
    }
  }
  const query = params.toString();
  return `${API_BASE_URL}/api/v1/screener/export${query ? `?${query}` : ""}`;
}
