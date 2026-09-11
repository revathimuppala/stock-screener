"use client";

import { FormEvent, useEffect, useState } from "react";
import { FilterForm } from "@/components/screener/FilterForm";
import { QueryInput } from "@/components/screener/QueryInput";
import { ResultsTable } from "@/components/screener/ResultsTable";
import { SavedScreensPanel } from "@/components/screener/SavedScreensPanel";
import { StatusBanner } from "@/components/screener/StatusBanner";
import {
  buildScreenerExportUrl,
  deleteSavedScreen,
  listSavedScreens,
  postQuery,
  postScreen,
  QueryParseException,
  runSavedScreen,
  saveQueryScreen,
  saveScreen,
  ScreenerApiError,
  type QueryParseErrorDetail,
} from "@/lib/api/screenerClient";
import type { SavedScreen, ScreenResponse, ScreeningCriteria } from "@/lib/types";

type Mode = "filters" | "query";

export default function ScreenerPage() {
  const [mode, setMode] = useState<Mode>("filters");
  const [result, setResult] = useState<ScreenResponse | null>(null);
  const [lastCriteria, setLastCriteria] = useState<ScreeningCriteria | null>(null);
  const [lastQuery, setLastQuery] = useState<string | null>(null);
  const [queryParseError, setQueryParseError] = useState<QueryParseErrorDetail | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [savedScreens, setSavedScreens] = useState<SavedScreen[]>([]);
  const [isPanelOpen, setIsPanelOpen] = useState(false);
  const [showSaveForm, setShowSaveForm] = useState(false);
  const [saveName, setSaveName] = useState("");

  function refreshSavedScreens() {
    listSavedScreens()
      .then((res) => setSavedScreens(res.screens))
      .catch(() => setError("Couldn't load saved screens."));
  }

  useEffect(() => {
    refreshSavedScreens();
  }, []);

  async function handleFilterSubmit(criteria: ScreeningCriteria) {
    setIsLoading(true);
    setError(null);
    try {
      const response = await postScreen(criteria);
      setResult(response);
      setLastCriteria(criteria);
      setLastQuery(null);
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

  async function handleQuerySubmit(query: string) {
    setIsLoading(true);
    setError(null);
    setQueryParseError(null);
    try {
      const response = await postQuery(query);
      setResult(response);
      setLastQuery(query);
      setLastCriteria(null);
    } catch (err) {
      if (err instanceof QueryParseException) {
        setQueryParseError(err.detail);
      } else {
        setError("Couldn't reach the screener service. Please try again.");
      }
    } finally {
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

      <div role="tablist" aria-label="Screening mode" className="flex gap-1 border-b border-zinc-200 dark:border-zinc-800">
        {(["filters", "query"] as const).map((m) => (
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
            {m === "filters" ? "Filters" : "Advanced Query"}
          </button>
        ))}
      </div>

      {mode === "filters" ? (
        <FilterForm onSubmit={handleFilterSubmit} isLoading={isLoading} />
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

      <SavedScreensPanel
        isOpen={isPanelOpen}
        screens={savedScreens}
        onClose={() => setIsPanelOpen(false)}
        onRun={handleRunSavedScreen}
        onDelete={handleDeleteSavedScreen}
      />
    </main>
  );
}
