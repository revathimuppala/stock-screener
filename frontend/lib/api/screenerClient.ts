import type {
  BacktestJob,
  CompanyDetail,
  Market,
  SavedScreen,
  SavedScreenListResponse,
  ScreeningCriteria,
  ScreenJob,
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

export async function postQuery(query: string, symbols?: string[]): Promise<ScreenResponse> {
  const response = await fetch(`${API_BASE_URL}/api/v1/screener/query`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query, symbols }),
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

export interface DslField {
  name: string;
  type: "string" | "number";
}

export interface DslFieldsResponse {
  fields: DslField[];
  aliases: Record<string, string>;
}

export async function getDslFields(): Promise<DslFieldsResponse> {
  return getJson<DslFieldsResponse>("/api/v1/screener/fields");
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
  symbols?: string[];
}

export async function startBacktest(
  params: StartBacktestParams
): Promise<{ backtest_id: string; status: string }> {
  return postJson("/api/v1/backtest", params);
}

export async function getBacktest(backtestId: string): Promise<BacktestJob> {
  return getJson<BacktestJob>(`/api/v1/backtest/${encodeURIComponent(backtestId)}`);
}

export class CompanyNotFoundError extends Error {
  constructor(symbol: string) {
    super(`No data available for ${symbol}`);
    this.name = "CompanyNotFoundError";
  }
}

export async function getCompanyDetail(symbol: string): Promise<CompanyDetail> {
  const response = await fetch(`${API_BASE_URL}/api/v1/companies/${encodeURIComponent(symbol)}`);
  if (response.status === 404) {
    throw new CompanyNotFoundError(symbol);
  }
  if (!response.ok) {
    throw new ScreenerApiError(`Request for ${symbol} failed with status ${response.status}`, response.status);
  }
  return response.json() as Promise<CompanyDetail>;
}

export async function getMarkets(): Promise<{ markets: Market[] }> {
  return getJson<{ markets: Market[] }>("/api/v1/markets");
}

export interface StartScreenJobParams {
  market_id: string;
  criteria?: ScreeningCriteria;
  query?: string;
  symbols?: string[];
}

export async function startScreenJob(
  params: StartScreenJobParams
): Promise<{ screen_id: string; status: string }> {
  const response = await fetch(`${API_BASE_URL}/api/v1/screener/jobs`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(params),
  });
  if (response.status === 400) {
    const body = await response.json();
    if (body.detail && typeof body.detail === "object" && "error" in body.detail) {
      throw new QueryParseException(body.detail);
    }
    throw new ScreenerApiError(
      typeof body.detail === "string" ? body.detail : "Couldn't start the screen.",
      400
    );
  }
  if (!response.ok) {
    throw new ScreenerApiError(
      `Request to start a screen job failed with status ${response.status}`,
      response.status
    );
  }
  return response.json();
}

export async function getScreenJob(screenId: string): Promise<ScreenJob> {
  return getJson<ScreenJob>(`/api/v1/screener/jobs/${encodeURIComponent(screenId)}`);
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
