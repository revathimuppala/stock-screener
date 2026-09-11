"use client";

import { useMemo, useState, type ReactNode } from "react";
import type { StockResult } from "@/lib/types";

interface ResultsTableProps {
  results: StockResult[];
}

type SortDirection = "asc" | "desc";

interface Column {
  key: string;
  label: string;
  getValue: (stock: StockResult) => number | string | null;
  render: (stock: StockResult) => ReactNode;
}

// `value == null` (not `=== null`) so a field missing entirely from an
// older/partial API response degrades to "—" instead of crashing on
// `undefined.toFixed()`.
function formatNumber(value: number | null | undefined, digits = 2): string {
  return value == null ? "—" : value.toFixed(digits);
}

function formatMarketCap(value: number | null | undefined): string {
  if (value == null) return "—";
  return `$${(value / 1_000_000_000).toFixed(1)}B`;
}

function formatPercent(value: number | null | undefined): string {
  return value == null ? "—" : `${(value * 100).toFixed(2)}%`;
}

const COLUMNS: Column[] = [
  {
    key: "symbol",
    label: "Symbol",
    getValue: (s) => s.symbol,
    render: (s) => (
      <>
        {s.symbol}
        {s.is_stale && (
          <span className="ml-2 rounded bg-amber-100 px-1.5 py-0.5 text-xs text-amber-800 dark:bg-amber-900 dark:text-amber-200">
            stale
          </span>
        )}
      </>
    ),
  },
  { key: "name", label: "Name", getValue: (s) => s.name, render: (s) => s.name },
  { key: "sector", label: "Sector", getValue: (s) => s.sector, render: (s) => s.sector },
  { key: "price", label: "Price", getValue: (s) => s.price, render: (s) => `$${formatNumber(s.price)}` },
  { key: "pe_ratio", label: "P/E", getValue: (s) => s.pe_ratio, render: (s) => formatNumber(s.pe_ratio) },
  {
    key: "market_cap",
    label: "Market Cap",
    getValue: (s) => s.market_cap,
    render: (s) => formatMarketCap(s.market_cap),
  },
  {
    key: "dividend_yield",
    label: "Dividend Yield",
    getValue: (s) => s.dividend_yield,
    render: (s) => formatPercent(s.dividend_yield),
  },
  { key: "roe", label: "ROE", getValue: (s) => s.roe, render: (s) => formatPercent(s.roe) },
  {
    key: "debt_to_equity",
    label: "Debt/Equity",
    getValue: (s) => s.debt_to_equity,
    render: (s) => formatNumber(s.debt_to_equity),
  },
  {
    key: "price_to_book",
    label: "P/B",
    getValue: (s) => s.price_to_book,
    render: (s) => formatNumber(s.price_to_book),
  },
  {
    key: "earnings_growth",
    label: "Earnings Growth",
    getValue: (s) => s.earnings_growth,
    render: (s) => formatPercent(s.earnings_growth),
  },
  {
    key: "revenue_growth",
    label: "Revenue Growth",
    getValue: (s) => s.revenue_growth,
    render: (s) => formatPercent(s.revenue_growth),
  },
  {
    key: "fifty_two_week_high",
    label: "52W High",
    getValue: (s) => s.fifty_two_week_high,
    render: (s) => (s.fifty_two_week_high == null ? "—" : `$${formatNumber(s.fifty_two_week_high)}`),
  },
];

export function ResultsTable({ results }: ResultsTableProps) {
  const [sortKey, setSortKey] = useState<string | null>(null);
  const [sortDirection, setSortDirection] = useState<SortDirection>("asc");

  const sorted = useMemo(() => {
    if (sortKey === null) return results;
    const column = COLUMNS.find((c) => c.key === sortKey);
    if (!column) return results;
    const withValues = results.map((stock) => ({ stock, value: column.getValue(stock) }));
    withValues.sort((a, b) => {
      if (a.value == null) return 1;
      if (b.value == null) return -1;
      if (a.value < b.value) return sortDirection === "asc" ? -1 : 1;
      if (a.value > b.value) return sortDirection === "asc" ? 1 : -1;
      return 0;
    });
    return withValues.map((w) => w.stock);
  }, [results, sortKey, sortDirection]);

  function handleHeaderClick(key: string) {
    if (sortKey === key) {
      setSortDirection((d) => (d === "asc" ? "desc" : "asc"));
    } else {
      setSortKey(key);
      setSortDirection("asc");
    }
  }

  if (results.length === 0) {
    return <p className="text-sm text-zinc-500">No stocks match the current filters.</p>;
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-left text-sm">
        <thead>
          <tr>
            {COLUMNS.map((column) => (
              <th
                key={column.key}
                role="columnheader"
                aria-sort={
                  sortKey === column.key ? (sortDirection === "asc" ? "ascending" : "descending") : "none"
                }
                onClick={() => handleHeaderClick(column.key)}
                className="cursor-pointer select-none whitespace-nowrap py-2 pr-4 hover:text-zinc-900 dark:hover:text-zinc-100"
              >
                {column.label}
                {sortKey === column.key && (sortDirection === "asc" ? " ↑" : " ↓")}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {sorted.map((stock) => (
            <tr key={stock.symbol} className="border-t">
              {COLUMNS.map((column) => (
                <td key={column.key} className="whitespace-nowrap py-2 pr-4">
                  {column.render(stock)}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
