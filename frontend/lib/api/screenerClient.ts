import type { ScreeningCriteria, ScreenResponse, WatchlistResponse } from "@/lib/types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export class ScreenerApiError extends Error {
  status?: number;

  constructor(message: string, status?: number) {
    super(message);
    this.name = "ScreenerApiError";
    this.status = status;
  }
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

export async function postScreen(criteria: ScreeningCriteria): Promise<ScreenResponse> {
  return postJson<ScreenResponse>("/api/v1/screener", criteria);
}

export async function getWatchlist(): Promise<WatchlistResponse> {
  const response = await fetch(`${API_BASE_URL}/api/v1/watchlist`);
  if (!response.ok) {
    throw new ScreenerApiError(`Failed to load watchlist (${response.status})`, response.status);
  }
  return response.json() as Promise<WatchlistResponse>;
}

export async function addToWatchlist(symbol: string): Promise<WatchlistResponse> {
  return postJson<WatchlistResponse>("/api/v1/watchlist", { symbol });
}

export async function removeFromWatchlist(symbol: string): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/api/v1/watchlist/${encodeURIComponent(symbol)}`, {
    method: "DELETE",
  });
  if (!response.ok) {
    throw new ScreenerApiError(`Failed to remove ${symbol} (${response.status})`, response.status);
  }
}
