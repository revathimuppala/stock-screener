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
  above_sma_window?: 50 | 100 | 200;
  peg_ratio_max?: number;
  ev_to_ebitda_max?: number;
  operating_margin_min?: number;
  debt_to_assets_max?: number;
  cfo_to_operating_profit_min?: number;
  rsi_min?: number;
  rsi_max?: number;
  symbols?: string[];
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
  peg_ratio: number | null;
  ev_to_ebitda: number | null;
  operating_margin: number | null;
  debt_to_assets: number | null;
  cfo_to_operating_profit: number | null;
  graham_value: number | null;
  dcf_value: number | null;
  sma_50: number | null;
  sma_100: number | null;
  sma_200: number | null;
  rsi_14: number | null;
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

export interface QuarterlyFinancials {
  period_end: string;
  revenue: number | null;
  ebit: number | null;
  ebitda: number | null;
  net_income: number | null;
  diluted_eps: number | null;
  operating_cash_flow: number | null;
  free_cash_flow: number | null;
}

export interface InstitutionalHolder {
  name: string;
  value: number | null;
  pct_change: number | null;
}

export interface ShareholdingPattern {
  insiders_pct: number | null;
  institutions_pct: number | null;
  top_holders: InstitutionalHolder[];
}

export interface FilingLink {
  form_type: string;
  filed_date: string;
  url: string;
}

export interface CompanyProfile {
  business_summary: string | null;
  sector: string;
  industry: string | null;
  competitors: string[];
  order_backlog_note: string;
}

export interface CompanyDetail {
  symbol: string;
  profile: CompanyProfile;
  quarters: QuarterlyFinancials[];
  shareholding: ShareholdingPattern | null;
  filings: FilingLink[];
}

export interface Market {
  id: string;
  label: string;
}

export type ScreenJobStatus = "pending" | "running" | "completed" | "failed";

// The completed shape flattens ScreenResponse's fields alongside the job's
// own lifecycle "status" — the backend renames ScreenResponse's own
// "ok"/"degraded" status to "screen_status" to avoid colliding with this
// job's "pending"/"running"/"completed"/"failed" status.
export interface ScreenJob {
  status: ScreenJobStatus;
  screen_status?: ScreenStatus;
  results?: StockResult[];
  stale_symbols?: string[];
  excluded_symbols?: string[];
  as_of?: string;
  error?: string;
}
