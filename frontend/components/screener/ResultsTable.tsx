"use client";

import Link from "next/link";
import { useMemo, useState, type ReactNode } from "react";
import type { StockResult } from "@/lib/types";

interface ResultsTableProps {
  results: StockResult[];
  /** When given, clicking a symbol calls this instead of navigating to
   * /company/[symbol] — used to open the detail slide-over in place. Falls
   * back to a normal link when omitted. */
  onSelectSymbol?: (symbol: string) => void;
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

function buildSymbolColumn(onSelectSymbol?: (symbol: string) => void): Column {
  return {
    key: "symbol",
    label: "Symbol",
    getValue: (s) => s.symbol,
    render: (s) => (
      <>
        {onSelectSymbol ? (
          <button
            type="button"
            onClick={() => onSelectSymbol(s.symbol)}
            className="underline hover:no-underline"
          >
            {s.symbol}
          </button>
        ) : (
          <Link href={`/company/${s.symbol}`} className="underline hover:no-underline">
            {s.symbol}
          </Link>
        )}
        {s.is_stale && (
          <span className="ml-2 rounded bg-amber-100 px-1.5 py-0.5 text-xs text-amber-800 dark:bg-amber-900 dark:text-amber-200">
            stale
          </span>
        )}
      </>
    ),
  };
}

const BASE_COLUMNS: Column[] = [
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
  // Valuation Ratios
  { key: "peg_ratio", label: "PEG", getValue: (s) => s.peg_ratio, render: (s) => formatNumber(s.peg_ratio) },
  {
    key: "ev_to_ebitda",
    label: "EV/EBITDA",
    getValue: (s) => s.ev_to_ebitda,
    render: (s) => formatNumber(s.ev_to_ebitda),
  },
  {
    key: "graham_value",
    label: "Graham Value",
    getValue: (s) => s.graham_value,
    render: (s) => (s.graham_value == null ? "—" : `$${formatNumber(s.graham_value)}`),
  },
  {
    key: "dcf_value",
    label: "DCF Value",
    getValue: (s) => s.dcf_value,
    render: (s) => (s.dcf_value == null ? "—" : `$${formatNumber(s.dcf_value)}`),
  },
  // Financial Health & Profitability
  {
    key: "operating_margin",
    label: "Op Margin",
    getValue: (s) => s.operating_margin,
    render: (s) => formatPercent(s.operating_margin),
  },
  {
    key: "debt_to_assets",
    label: "Debt/Assets",
    getValue: (s) => s.debt_to_assets,
    render: (s) => formatPercent(s.debt_to_assets),
  },
  {
    key: "cfo_to_operating_profit",
    label: "CFO/OP",
    getValue: (s) => s.cfo_to_operating_profit,
    render: (s) => formatNumber(s.cfo_to_operating_profit),
  },
  // Technical & Price Metrics
  {
    key: "sma_50",
    label: "SMA 50",
    getValue: (s) => s.sma_50,
    render: (s) => (s.sma_50 == null ? "—" : `$${formatNumber(s.sma_50)}`),
  },
  {
    key: "sma_100",
    label: "SMA 100",
    getValue: (s) => s.sma_100,
    render: (s) => (s.sma_100 == null ? "—" : `$${formatNumber(s.sma_100)}`),
  },
  {
    key: "sma_200",
    label: "SMA 200",
    getValue: (s) => s.sma_200,
    render: (s) => (s.sma_200 == null ? "—" : `$${formatNumber(s.sma_200)}`),
  },
  { key: "rsi_14", label: "RSI (14)", getValue: (s) => s.rsi_14, render: (s) => formatNumber(s.rsi_14, 1) },
];

export function ResultsTable({ results, onSelectSymbol }: ResultsTableProps) {
  const [sortKey, setSortKey] = useState<string | null>(null);
  const [sortDirection, setSortDirection] = useState<SortDirection>("asc");

  const columns = useMemo(
    () => [buildSymbolColumn(onSelectSymbol), ...BASE_COLUMNS],
    [onSelectSymbol]
  );

  const sorted = useMemo(() => {
    if (sortKey === null) return results;
    const column = columns.find((c) => c.key === sortKey);
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
  }, [results, sortKey, sortDirection, columns]);

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
            {columns.map((column) => (
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
              {columns.map((column) => (
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
