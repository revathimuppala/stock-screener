import type { ScreenStatus } from "@/lib/types";

interface StatusBannerProps {
  status: ScreenStatus;
  staleSymbols: string[];
  excludedSymbols: string[];
}

export function StatusBanner({ status, staleSymbols, excludedSymbols }: StatusBannerProps) {
  if (status === "ok") {
    return null;
  }

  return (
    <div
      role="status"
      className="rounded border border-amber-300 bg-amber-50 px-4 py-2 text-sm text-amber-900 dark:border-amber-700 dark:bg-amber-950 dark:text-amber-200"
    >
      <p className="font-medium">Results are degraded — the data provider is having trouble.</p>
      {staleSymbols.length > 0 && (
        <p>Showing cached (stale) data for: {staleSymbols.join(", ")}</p>
      )}
      {excludedSymbols.length > 0 && (
        <p>No data available for: {excludedSymbols.join(", ")}</p>
      )}
    </div>
  );
}
