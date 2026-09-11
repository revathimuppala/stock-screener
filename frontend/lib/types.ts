export interface ScreeningCriteria {
  pe_min?: number;
  pe_max?: number;
  market_cap_min?: number;
  market_cap_max?: number;
  sector?: string;
  min_dividend_yield?: number;
  roe_min?: number;
  debt_to_equity_max?: number;
  price_to_book_max?: number;
  earnings_growth_min?: number;
  revenue_growth_min?: number;
  near_52_week_high_pct?: number;
}

export interface StockResult {
  symbol: string;
  name: string;
  sector: string;
  price: number;
  pe_ratio: number | null;
  market_cap: number | null;
  dividend_yield: number | null;
  is_stale: boolean;
  roe: number | null;
  debt_to_equity: number | null;
  price_to_book: number | null;
  earnings_growth: number | null;
  revenue_growth: number | null;
  fifty_two_week_high: number | null;
  fifty_two_week_low: number | null;
}

export type ScreenStatus = "ok" | "degraded";

export interface ScreenResponse {
  status: ScreenStatus;
  results: StockResult[];
  stale_symbols: string[];
  excluded_symbols: string[];
  as_of: string;
}

export interface WatchlistResponse {
  symbols: string[];
}

export interface SavedScreen {
  id: string;
  name: string;
  criteria: ScreeningCriteria | null;
  query: string | null;
  created_at: string;
}

export interface SavedScreenListResponse {
  screens: SavedScreen[];
}

export interface BacktestMatch {
  symbol: string;
  match_date: string;
  match_price: number;
}

export interface BacktestPerformance {
  match: BacktestMatch;
  exit_date: string | null;
  exit_price: number | null;
  return_pct: number | null;
  status: "completed" | "pending";
}

export interface BacktestSummary {
  total_matches: number;
  completed_count: number;
  pending_count: number;
  avg_return_pct: number | null;
  win_rate: number | null;
  best_return_pct: number | null;
  worst_return_pct: number | null;
}

export type BacktestJobStatus = "pending" | "running" | "completed" | "failed";

export interface BacktestJob {
  status: BacktestJobStatus;
  timeline?: BacktestMatch[];
  performances?: BacktestPerformance[];
  summary?: BacktestSummary;
  excluded_symbols?: string[];
  warnings?: string[];
  fundamentals_as_of?: string;
  error?: string;
}
