"use client";

import { FormEvent, useEffect, useRef, useState } from "react";
import { BacktestTimeline } from "@/components/backtest/BacktestTimeline";
import { DslQueryTextarea } from "@/components/screener/DslQueryTextarea";
import { parseOptionalSymbols } from "@/components/screener/FilterForm";
import { getBacktest, startBacktest } from "@/lib/api/screenerClient";
import type { BacktestJob, BacktestPerformance } from "@/lib/types";

const POLL_INTERVAL_MS = 2000;

function todayIso(): string {
  return new Date().toISOString().slice(0, 10);
}

function monthsAgoIso(months: number): string {
  const d = new Date();
  d.setMonth(d.getMonth() - months);
  return d.toISOString().slice(0, 10);
}

function formatReturn(pct: number | null): string {
  if (pct === null) return "—";
  const sign = pct >= 0 ? "+" : "";
  return `${sign}${pct.toFixed(2)}%`;
}

export default function BacktestPage() {
  const [query, setQuery] = useState('pe < 20 AND sector = "Technology"');
  const [startDate, setStartDate] = useState(monthsAgoIso(6));
  const [endDate, setEndDate] = useState(todayIso());
  const [holdingPeriodDays, setHoldingPeriodDays] = useState(30);
  const [symbolsInput, setSymbolsInput] = useState("");

  const [backtestId, setBacktestId] = useState<string | null>(null);
  const [job, setJob] = useState<BacktestJob | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [selected, setSelected] = useState<{ symbol: string; matchDate: string } | null>(null);

  const pollHandle = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    return () => {
      if (pollHandle.current) clearTimeout(pollHandle.current);
    };
  }, []);

  function schedulePoll(id: string) {
    pollHandle.current = setTimeout(async () => {
      try {
        const record = await getBacktest(id);
        setJob(record);
        if (record.status === "pending" || record.status === "running") {
          schedulePoll(id);
        }
      } catch {
        setError("Lost track of the running backtest. Please try again.");
      }
    }, POLL_INTERVAL_MS);
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    setJob(null);
    setSelected(null);
    try {
      const response = await startBacktest({
        query,
        start_date: startDate,
        end_date: endDate,
        holding_period_days: holdingPeriodDays,
        symbols: parseOptionalSymbols(symbolsInput),
      });
      setBacktestId(response.backtest_id);
      setJob({ status: "pending" });
      schedulePoll(response.backtest_id);
    } catch {
      setError("Couldn't start the backtest. Check your query and try again.");
    }
  }

  const selectedPerformance: BacktestPerformance | undefined = selected
    ? job?.performances?.find(
        (p) => p.match.symbol === selected.symbol && p.match.match_date === selected.matchDate
      )
    : undefined;

  const isRunning = job?.status === "pending" || job?.status === "running";

  return (
    <main className="mx-auto flex max-w-4xl flex-col gap-6 px-6 py-10">
      <div>
        <h1 className="text-2xl font-semibold">Backtest</h1>
        <p className="text-sm text-zinc-500">
          Replay a query against real historical prices. Fundamental fields (P/E, ROE, ...) are
          evaluated at today&rsquo;s values for the whole window — yfinance has no historical
          point-in-time fundamentals, so this measures &ldquo;if this price condition had held
          with today&rsquo;s fundamentals,&rdquo; not a true fundamentals-through-time backtest.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="flex flex-col gap-3">
        <label htmlFor="backtest-query" className="text-sm">
          Query
        </label>
        <DslQueryTextarea id="backtest-query" value={query} onChange={setQuery} rows={2} />

        <label htmlFor="backtest-symbols" className="flex flex-col gap-1 text-sm">
          Symbols (optional, comma-separated — overrides the default universe)
          <input
            id="backtest-symbols"
            type="text"
            value={symbolsInput}
            onChange={(e) => setSymbolsInput(e.target.value)}
            placeholder="e.g. AAPL, MSFT, GOOGL"
            className="rounded border px-2 py-1"
          />
        </label>

        <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
          <label className="flex flex-col gap-1 text-sm">
            Start date
            <input
              type="date"
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
              className="rounded border px-2 py-1"
            />
          </label>
          <label className="flex flex-col gap-1 text-sm">
            End date
            <input
              type="date"
              value={endDate}
              onChange={(e) => setEndDate(e.target.value)}
              className="rounded border px-2 py-1"
            />
          </label>
          <label className="flex flex-col gap-1 text-sm">
            Holding period (days)
            <input
              type="number"
              min={1}
              value={holdingPeriodDays}
              onChange={(e) => setHoldingPeriodDays(Number(e.target.value))}
              className="rounded border px-2 py-1"
            />
          </label>
        </div>

        <button
          type="submit"
          disabled={isRunning}
          className="w-fit rounded bg-zinc-900 px-4 py-2 text-sm text-white disabled:opacity-50 dark:bg-zinc-100 dark:text-zinc-900"
        >
          {isRunning ? "Running..." : "Run backtest"}
        </button>
      </form>

      {error && (
        <p role="alert" className="text-sm text-red-600">
          {error}
        </p>
      )}

      {job && (job.status === "pending" || job.status === "running") && (
        <p className="text-sm text-zinc-500">
          Backtest {backtestId} is {job.status}... this can take a while over a wide date range.
        </p>
      )}

      {job?.status === "failed" && (
        <p role="alert" className="text-sm text-red-600">
          Backtest failed: {job.error}
        </p>
      )}

      {job?.status === "completed" && job.summary && (
        <>
          <div className="grid grid-cols-2 gap-3 rounded border p-4 text-sm sm:grid-cols-4">
            <div>
              <div className="text-zinc-500">Matches</div>
              <div className="text-lg font-semibold">{job.summary.total_matches}</div>
            </div>
            <div>
              <div className="text-zinc-500">Avg return</div>
              <div className="text-lg font-semibold">{formatReturn(job.summary.avg_return_pct)}</div>
            </div>
            <div>
              <div className="text-zinc-500">Win rate</div>
              <div className="text-lg font-semibold">
                {job.summary.win_rate === null ? "—" : `${(job.summary.win_rate * 100).toFixed(0)}%`}
              </div>
            </div>
            <div>
              <div className="text-zinc-500">Best / Worst</div>
              <div className="text-lg font-semibold">
                {formatReturn(job.summary.best_return_pct)} / {formatReturn(job.summary.worst_return_pct)}
              </div>
            </div>
          </div>

          {job.excluded_symbols && job.excluded_symbols.length > 0 && (
            <p className="text-sm text-amber-700 dark:text-amber-400">
              Excluded (no data in window): {job.excluded_symbols.join(", ")}
            </p>
          )}

          <BacktestTimeline
            timeline={job.timeline ?? []}
            onSelectMatch={(symbol, matchDate) => setSelected({ symbol, matchDate })}
          />

          {selectedPerformance && (
            <div className="rounded border p-4 text-sm">
              <h2 className="font-medium">
                {selectedPerformance.match.symbol} — matched {selectedPerformance.match.match_date}
              </h2>
              <p>Entry price: ${selectedPerformance.match.match_price.toFixed(2)}</p>
              {selectedPerformance.status === "completed" ? (
                <>
                  <p>
                    Exit: {selectedPerformance.exit_date} at $
                    {selectedPerformance.exit_price?.toFixed(2)}
                  </p>
                  <p>Return: {formatReturn(selectedPerformance.return_pct)}</p>
                </>
              ) : (
                <p className="text-zinc-500">
                  Holding period hasn&rsquo;t completed within the available data yet.
                </p>
              )}
            </div>
          )}
        </>
      )}
    </main>
  );
}
