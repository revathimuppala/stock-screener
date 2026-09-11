"use client";

import { useState } from "react";
import { FilterForm } from "@/components/screener/FilterForm";
import { ResultsTable } from "@/components/screener/ResultsTable";
import { StatusBanner } from "@/components/screener/StatusBanner";
import { postScreen, ScreenerApiError } from "@/lib/api/screenerClient";
import type { ScreenResponse, ScreeningCriteria } from "@/lib/types";

export default function ScreenerPage() {
  const [result, setResult] = useState<ScreenResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(criteria: ScreeningCriteria) {
    setIsLoading(true);
    setError(null);
    try {
      const response = await postScreen(criteria);
      setResult(response);
    } catch (err) {
      const message =
        err instanceof ScreenerApiError
          ? "Couldn't reach the screener service. Please try again."
          : "Something went wrong. Please try again.";
      setError(message);
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <main className="mx-auto flex max-w-4xl flex-col gap-6 px-6 py-10">
      <div>
        <h1 className="text-2xl font-semibold">Stock Screener</h1>
        <p className="text-sm text-zinc-500">
          Filter the screening universe by valuation, sector, and dividend yield.
        </p>
      </div>

      <FilterForm onSubmit={handleSubmit} isLoading={isLoading} />

      {error && (
        <div role="alert" className="rounded border border-red-300 bg-red-50 px-4 py-2 text-sm text-red-800">
          {error}{" "}
          <button
            type="button"
            className="underline"
            onClick={() => setError(null)}
          >
            Dismiss
          </button>
        </div>
      )}

      {result && (
        <>
          <StatusBanner
            status={result.status}
            staleSymbols={result.stale_symbols}
            excludedSymbols={result.excluded_symbols}
          />
          <ResultsTable results={result.results} />
        </>
      )}
    </main>
  );
}
