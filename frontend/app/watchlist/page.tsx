"use client";

import { FormEvent, useEffect, useState } from "react";
import { addToWatchlist, getWatchlist, removeFromWatchlist } from "@/lib/api/screenerClient";

export default function WatchlistPage() {
  const [symbols, setSymbols] = useState<string[]>([]);
  const [newSymbol, setNewSymbol] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    getWatchlist()
      .then((response) => {
        if (cancelled) return;
        setSymbols(response.symbols);
        setError(null);
      })
      .catch(() => {
        if (!cancelled) setError("Couldn't load your watchlist. Please try again.");
      })
      .finally(() => {
        if (!cancelled) setIsLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, []);

  async function handleAdd(event: FormEvent) {
    event.preventDefault();
    if (!newSymbol.trim()) return;
    try {
      const response = await addToWatchlist(newSymbol.trim());
      setSymbols(response.symbols);
      setNewSymbol("");
      setError(null);
    } catch {
      setError(`Couldn't add ${newSymbol}. Please try again.`);
    }
  }

  async function handleRemove(symbol: string) {
    try {
      await removeFromWatchlist(symbol);
      setSymbols((prev) => prev.filter((s) => s !== symbol));
    } catch {
      setError(`Couldn't remove ${symbol}. Please try again.`);
    }
  }

  return (
    <main className="mx-auto flex max-w-2xl flex-col gap-6 px-6 py-10">
      <div>
        <h1 className="text-2xl font-semibold">Watchlist</h1>
        <p className="text-sm text-zinc-500">Track symbols you want to revisit.</p>
      </div>

      <form onSubmit={handleAdd} className="flex gap-2">
        <label className="sr-only" htmlFor="new-symbol">
          Symbol
        </label>
        <input
          id="new-symbol"
          value={newSymbol}
          onChange={(e) => setNewSymbol(e.target.value)}
          placeholder="e.g. AAPL"
          className="rounded border px-2 py-1 text-sm"
        />
        <button type="submit" className="rounded bg-zinc-900 px-4 py-1 text-sm text-white dark:bg-zinc-100 dark:text-zinc-900">
          Add
        </button>
      </form>

      {error && (
        <p role="alert" className="text-sm text-red-600">
          {error}
        </p>
      )}

      {isLoading ? (
        <p className="text-sm text-zinc-500">Loading…</p>
      ) : symbols.length === 0 ? (
        <p className="text-sm text-zinc-500">Your watchlist is empty.</p>
      ) : (
        <ul className="flex flex-col gap-2">
          {symbols.map((symbol) => (
            <li key={symbol} className="flex items-center justify-between rounded border px-3 py-2 text-sm">
              {symbol}
              <button
                type="button"
                onClick={() => handleRemove(symbol)}
                className="text-red-600 underline"
              >
                Remove
              </button>
            </li>
          ))}
        </ul>
      )}
    </main>
  );
}
