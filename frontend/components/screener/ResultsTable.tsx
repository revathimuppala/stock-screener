import type { StockResult } from "@/lib/types";

interface ResultsTableProps {
  results: StockResult[];
}

function formatNumber(value: number | null, digits = 2): string {
  return value === null ? "—" : value.toFixed(digits);
}

function formatMarketCap(value: number | null): string {
  if (value === null) return "—";
  return `$${(value / 1_000_000_000).toFixed(1)}B`;
}

function formatPercent(value: number | null): string {
  return value === null ? "—" : `${(value * 100).toFixed(2)}%`;
}

export function ResultsTable({ results }: ResultsTableProps) {
  if (results.length === 0) {
    return <p className="text-sm text-zinc-500">No stocks match the current filters.</p>;
  }

  return (
    <table className="w-full text-left text-sm">
      <thead>
        <tr>
          <th className="py-2 pr-4">Symbol</th>
          <th className="py-2 pr-4">Name</th>
          <th className="py-2 pr-4">Sector</th>
          <th className="py-2 pr-4">Price</th>
          <th className="py-2 pr-4">P/E</th>
          <th className="py-2 pr-4">Market Cap</th>
          <th className="py-2 pr-4">Dividend Yield</th>
        </tr>
      </thead>
      <tbody>
        {results.map((stock) => (
          <tr key={stock.symbol} className="border-t">
            <td className="py-2 pr-4 font-medium">
              {stock.symbol}
              {stock.is_stale && (
                <span className="ml-2 rounded bg-amber-100 px-1.5 py-0.5 text-xs text-amber-800 dark:bg-amber-900 dark:text-amber-200">
                  stale
                </span>
              )}
            </td>
            <td className="py-2 pr-4">{stock.name}</td>
            <td className="py-2 pr-4">{stock.sector}</td>
            <td className="py-2 pr-4">${formatNumber(stock.price)}</td>
            <td className="py-2 pr-4">{formatNumber(stock.pe_ratio)}</td>
            <td className="py-2 pr-4">{formatMarketCap(stock.market_cap)}</td>
            <td className="py-2 pr-4">{formatPercent(stock.dividend_yield)}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
