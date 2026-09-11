"use client";

import { FormEvent, useEffect, useRef, useState } from "react";
import { CompanyDetailDrawer } from "@/components/company/CompanyDetailDrawer";
import { FilterForm, parseOptionalSymbols } from "@/components/screener/FilterForm";
import { QueryInput } from "@/components/screener/QueryInput";
import { ResultsTable } from "@/components/screener/ResultsTable";
import { SavedScreensPanel } from "@/components/screener/SavedScreensPanel";
import { StatusBanner } from "@/components/screener/StatusBanner";
import {
  buildScreenerExportUrl,
  deleteSavedScreen,
  getMarkets,
  getScreenJob,
  listSavedScreens,
  postQuery,
  postScreen,
  QueryParseException,
  runSavedScreen,
  saveQueryScreen,
  saveScreen,
  ScreenerApiError,
  startScreenJob,
  type QueryParseErrorDetail,
} from "@/lib/api/screenerClient";
import type { Market, SavedScreen, ScreenJobStatus, ScreenResponse, ScreeningCriteria } from "@/lib/types";

type Mode = "query" | "filters";

const DEFAULT_MARKET: Market = { id: "default", label: "US Large Cap (Default)" };
const SCREEN_JOB_POLL_INTERVAL_MS = 2000;

export default function ScreenerPage() {
  const [mode, setMode] = useState<Mode>("query");
  const [symbolsInput, setSymbolsInput] = useState("");
  const [markets, setMarkets] = useState<Market[]>([DEFAULT_MARKET]);
  const [marketId, setMarketId] = useState(DEFAULT_MARKET.id);
  const [result, setResult] = useState<ScreenResponse | null>(null);
  const [lastCriteria, setLastCriteria] = useState<ScreeningCriteria | null>(null);
  const [lastQuery, setLastQuery] = useState<string | null>(null);
  const [queryParseError, setQueryParseError] = useState<QueryParseErrorDetail | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [screenJobStatus, setScreenJobStatus] = useState<ScreenJobStatus | null>(null);
  const [error, setError] = useState<string | null>(null);

  const [savedScreens, setSavedScreens] = useState<SavedScreen[]>([]);
  const [isPanelOpen, setIsPanelOpen] = useState(false);
  const [showSaveForm, setShowSaveForm] = useState(false);
  const [saveName, setSaveName] = useState("");
  const [selectedSymbol, setSelectedSymbol] = useState<string | null>(null);

  const pollHandle = useRef<ReturnType<typeof setTimeout> | null>(null);

  function refreshSavedScreens() {
    listSavedScreens()
      .then((res) => setSavedScreens(res.screens))
      .catch(() => setError("Couldn't load saved screens."));
  }

  useEffect(() => {
    refreshSavedScreens();
    getMarkets()
      .then((res) => setMarkets(res.markets))
      .catch(() => {
        // Non-critical — the page still works screening the default universe.
      });
  }, []);

  useEffect(() => {
    return () => {
      if (pollHandle.current) clearTimeout(pollHandle.current);
    };
  }, []);

  // Markets other than "default" are 100-500+ symbols — too large to screen
  // within one HTTP request — so they always go through the async job
  // pattern (mirrors Backtest's job/poll flow), UNLESS the user typed an
  // explicit (small) symbol list, which still wins over the market and can
  // run synchronously just like today.
  function shouldUseAsyncJob(explicitSymbols: string[] | undefined): boolean {
    return marketId !== DEFAULT_MARKET.id && !explicitSymbols;
  }

  function scheduleScreenJobPoll(screenId: string) {
    pollHandle.current = setTimeout(async () => {
      try {
        const job = await getScreenJob(screenId);
        if (job.status === "completed") {
          setResult({
            status: job.screen_status ?? "ok",
            results: job.results ?? [],
            stale_symbols: job.stale_symbols ?? [],
            excluded_symbols: job.excluded_symbols ?? [],
            as_of: job.as_of ?? new Date().toISOString(),
          });
          setScreenJobStatus("completed");
          setIsLoading(false);
        } else if (job.status === "failed") {
          setError(job.error ?? "The screen failed. Please try again.");
          setScreenJobStatus("failed");
          setIsLoading(false);
        } else {
          setScreenJobStatus(job.status);
          scheduleScreenJobPoll(screenId);
        }
      } catch {
        setError("Lost track of the running screen. Please try again.");
        setIsLoading(false);
      }
    }, SCREEN_JOB_POLL_INTERVAL_MS);
  }

  async function handleFilterSubmit(criteria: ScreeningCriteria) {
    setIsLoading(true);
    setError(null);
    setScreenJobStatus(null);
    try {
      if (shouldUseAsyncJob(criteria.symbols)) {
        const { screen_id } = await startScreenJob({ market_id: marketId, criteria });
        setLastCriteria(criteria);
        setLastQuery(null);
        setScreenJobStatus("pending");
        scheduleScreenJobPoll(screen_id);
        return; // isLoading clears once the poll reaches a terminal state
      }
      const response = await postScreen(criteria);
      setResult(response);
      setLastCriteria(criteria);
      setLastQuery(null);
      setIsLoading(false);
    } catch (err) {
      const message =
        err instanceof ScreenerApiError
          ? "Couldn't reach the screener service. Please try again."
          : "Something went wrong. Please try again.";
      setError(message);
      setIsLoading(false);
    }
  }

  async function handleQuerySubmit(query: string) {
    setIsLoading(true);
    setError(null);
    setQueryParseError(null);
    setScreenJobStatus(null);
    const explicitSymbols = parseOptionalSymbols(symbolsInput);
    try {
      if (shouldUseAsyncJob(explicitSymbols)) {
        const { screen_id } = await startScreenJob({ market_id: marketId, query });
        setLastQuery(query);
        setLastCriteria(null);
        setScreenJobStatus("pending");
        scheduleScreenJobPoll(screen_id);
        return;
      }
      const response = await postQuery(query, explicitSymbols);
      setResult(response);
      setLastQuery(query);
      setLastCriteria(null);
      setIsLoading(false);
    } catch (err) {
      if (err instanceof QueryParseException) {
        setQueryParseError(err.detail);
      } else {
        setError("Couldn't reach the screener service. Please try again.");
      }
      setIsLoading(false);
    }
  }

  async function handleSaveSubmit(event: FormEvent) {
    event.preventDefault();
    if (!saveName.trim()) return;
    try {
      if (lastCriteria) {
        await saveScreen(saveName.trim(), lastCriteria);
      } else if (lastQuery) {
        await saveQueryScreen(saveName.trim(), lastQuery);
      } else {
        return;
      }
      setSaveName("");
      setShowSaveForm(false);
      refreshSavedScreens();
    } catch {
      setError("Couldn't save this screen. Please try again.");
    }
  }

  async function handleRunSavedScreen(screenId: string) {
    setIsLoading(true);
    setError(null);
    try {
      const response = await runSavedScreen(screenId);
      setResult(response);
      setIsPanelOpen(false);
    } catch {
      setError("Couldn't run that saved screen.");
    } finally {
      setIsLoading(false);
    }
  }

  async function handleDeleteSavedScreen(screenId: string) {
    try {
      await deleteSavedScreen(screenId);
      setSavedScreens((prev) => prev.filter((s) => s.id !== screenId));
    } catch {
      setError("Couldn't delete that saved screen.");
    }
  }

  const canSave = Boolean(lastCriteria || lastQuery);

  return (
    <main className="mx-auto flex max-w-5xl flex-col gap-6 px-6 py-10">
      <div>
        <h1 className="text-2xl font-semibold">Stock Screener</h1>
        <p className="text-sm text-zinc-500">
          Filter the screening universe by valuation, sector, and dividend yield.
        </p>
      </div>

      <div className="flex flex-wrap gap-4">
        <label className="flex flex-col gap-1 text-sm">
          Market
          <select
            value={marketId}
            onChange={(e) => setMarketId(e.target.value)}
            className="rounded border px-2 py-1"
          >
            {markets.map((m) => (
              <option key={m.id} value={m.id}>
                {m.label}
              </option>
            ))}
          </select>
        </label>

        <label className="flex flex-1 flex-col gap-1 text-sm">
          Symbols (optional, comma-separated — overrides the selected market; applies to both
          modes below and to Backtest)
          <input
            type="text"
            value={symbolsInput}
            onChange={(e) => setSymbolsInput(e.target.value)}
            placeholder="e.g. AAPL, MSFT, GOOGL"
            className="rounded border px-2 py-1"
          />
        </label>
      </div>

      {marketId !== DEFAULT_MARKET.id && !parseOptionalSymbols(symbolsInput) && (
        <p className="text-sm text-zinc-500">
          {markets.find((m) => m.id === marketId)?.label ?? marketId} can be 100-500+ symbols —
          screening it runs as a background job and may take a few minutes.
        </p>
      )}

      <div role="tablist" aria-label="Screening mode" className="flex gap-1 border-b border-zinc-200 dark:border-zinc-800">
        {(["query", "filters"] as const).map((m) => (
          <button
            key={m}
            type="button"
            role="tab"
            aria-selected={mode === m}
            onClick={() => setMode(m)}
            className={`-mb-px border-b-2 px-3 py-2 text-sm ${
              mode === m
                ? "border-zinc-900 font-medium text-zinc-900 dark:border-zinc-100 dark:text-zinc-100"
                : "border-transparent text-zinc-500"
            }`}
          >
            {m === "filters" ? "Filters" : "Query"}
          </button>
        ))}
      </div>

      {mode === "filters" ? (
        <FilterForm
          onSubmit={handleFilterSubmit}
          isLoading={isLoading}
          symbols={parseOptionalSymbols(symbolsInput)}
        />
      ) : (
        <QueryInput onSubmit={handleQuerySubmit} isLoading={isLoading} parseError={queryParseError} />
      )}

      <div className="flex flex-wrap items-center gap-2 border-t border-zinc-200 pt-4 dark:border-zinc-800">
        <button
          type="button"
          disabled={!canSave}
          onClick={() => setShowSaveForm((v) => !v)}
          className="rounded border px-3 py-1.5 text-sm disabled:opacity-40"
        >
          Save this screen
        </button>
        <button
          type="button"
          onClick={() => setIsPanelOpen(true)}
          className="rounded border px-3 py-1.5 text-sm"
        >
          Saved Screens ({savedScreens.length})
        </button>
        {lastCriteria && (
          <a
            href={buildScreenerExportUrl(lastCriteria)}
            className="rounded border px-3 py-1.5 text-sm"
          >
            Export CSV
          </a>
        )}
      </div>

      {showSaveForm && (
        <form onSubmit={handleSaveSubmit} className="flex gap-2">
          <label className="sr-only" htmlFor="save-screen-name">
            Screen name
          </label>
          <input
            id="save-screen-name"
            value={saveName}
            onChange={(e) => setSaveName(e.target.value)}
            placeholder="Screen name"
            className="rounded border px-2 py-1 text-sm"
          />
          <button type="submit" className="rounded bg-zinc-900 px-3 py-1 text-sm text-white dark:bg-zinc-100 dark:text-zinc-900">
            Save
          </button>
        </form>
      )}

      {(screenJobStatus === "pending" || screenJobStatus === "running") && (
        <p className="text-sm text-zinc-500">
          Screening {markets.find((m) => m.id === marketId)?.label ?? marketId} is{" "}
          {screenJobStatus}...
        </p>
      )}

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
          <ResultsTable results={result.results} onSelectSymbol={setSelectedSymbol} />
        </>
      )}

      <SavedScreensPanel
        isOpen={isPanelOpen}
        screens={savedScreens}
        onClose={() => setIsPanelOpen(false)}
        onRun={handleRunSavedScreen}
        onDelete={handleDeleteSavedScreen}
      />

      <CompanyDetailDrawer
        key={selectedSymbol ?? "closed"}
        symbol={selectedSymbol}
        onClose={() => setSelectedSymbol(null)}
      />
    </main>
  );
}
