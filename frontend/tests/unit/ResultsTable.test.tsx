import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { ResultsTable } from "@/components/screener/ResultsTable";
import type { StockResult } from "@/lib/types";

const results: StockResult[] = [
  {
    symbol: "AAPL",
    name: "Apple Inc.",
    sector: "Technology",
    price: 190.12,
    pe_ratio: 15.4,
    market_cap: 3_000_000_000_000,
    dividend_yield: 0.005,
    is_stale: false,
  },
  {
    symbol: "STALE",
    name: "Stale Co.",
    sector: "Energy",
    price: 50,
    pe_ratio: 10,
    market_cap: 1_000_000_000,
    dividend_yield: 0.03,
    is_stale: true,
  },
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
});
