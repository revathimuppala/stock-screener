export interface ScreeningCriteria {
  pe_min?: number;
  pe_max?: number;
  market_cap_min?: number;
  market_cap_max?: number;
  sector?: string;
  min_dividend_yield?: number;
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
