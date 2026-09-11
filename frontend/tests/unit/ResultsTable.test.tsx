import { describe, it, expect } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { ResultsTable } from "@/components/screener/ResultsTable";
import type { StockResult } from "@/lib/types";

function makeResult(overrides: Partial<StockResult>): StockResult {
  return {
    symbol: "AAPL",
    name: "Apple Inc.",
    sector: "Technology",
    price: 190.12,
    pe_ratio: 15.4,
    market_cap: 3_000_000_000_000,
    dividend_yield: 0.005,
    is_stale: false,
    roe: 0.15,
    debt_to_equity: 50,
    price_to_book: 10,
    earnings_growth: 0.1,
    revenue_growth: 0.08,
    fifty_two_week_high: 200,
    fifty_two_week_low: 150,
    peg_ratio: 2.0,
    ev_to_ebitda: 18,
    operating_margin: 0.25,
    debt_to_assets: 0.3,
    cfo_to_operating_profit: 1.1,
    graham_value: 210,
    dcf_value: 180,
    sma_50: 185,
    sma_100: 180,
    sma_200: 175,
    rsi_14: 55,
    ...overrides,
  };
}

const results: StockResult[] = [
  makeResult({ symbol: "AAPL", name: "Apple Inc.", sector: "Technology", price: 190.12, pe_ratio: 15.4, market_cap: 3_000_000_000_000, dividend_yield: 0.005, is_stale: false }),
  makeResult({ symbol: "STALE", name: "Stale Co.", sector: "Energy", price: 50, pe_ratio: 10, market_cap: 1_000_000_000, dividend_yield: 0.03, is_stale: true }),
];

describe("ResultsTable", () => {
  it("renders one row per result with the symbol and sector", () => {
    render(<ResultsTable results={results} />);

    expect(screen.getByRole("row", { name: /AAPL/ })).toBeInTheDocument();
    expect(screen.getByRole("row", { name: /STALE/ })).toBeInTheDocument();
    expect(screen.getByText("Technology")).toBeInTheDocument();
  });

  it("flags stale rows", () => {
    render(<ResultsTable results={results} />);

    const staleRow = screen.getByRole("row", { name: /STALE/ });
    expect(staleRow).toHaveTextContent(/stale/i);

    const freshRow = screen.getByRole("row", { name: /AAPL/ });
    expect(freshRow).not.toHaveTextContent(/stale/i);
  });

  it("shows an empty state when there are no results", () => {
    render(<ResultsTable results={[]} />);

    expect(screen.getByText(/no stocks match/i)).toBeInTheDocument();
  });

  it("sorts rows by a numeric column when its header is clicked, toggling direction", async () => {
    const priced = [
      makeResult({ symbol: "LOW", price: 10 }),
      makeResult({ symbol: "HIGH", price: 100 }),
      makeResult({ symbol: "MID", price: 50 }),
    ];
    render(<ResultsTable results={priced} />);

    const priceHeader = screen.getByRole("columnheader", { name: /price/i });

    fireEvent.click(priceHeader);
    let rows = screen.getAllByRole("row").slice(1); // drop header row
    expect(rows.map((r) => r.textContent)).toEqual([
      expect.stringContaining("LOW"),
      expect.stringContaining("MID"),
      expect.stringContaining("HIGH"),
    ]);

    fireEvent.click(priceHeader); // toggle to descending
    rows = screen.getAllByRole("row").slice(1);
    expect(rows.map((r) => r.textContent)).toEqual([
      expect.stringContaining("HIGH"),
      expect.stringContaining("MID"),
      expect.stringContaining("LOW"),
    ]);
  });
});
