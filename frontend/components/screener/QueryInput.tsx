"use client";

import { FormEvent, useState } from "react";
import type { QueryParseErrorDetail } from "@/lib/api/screenerClient";

interface QueryInputProps {
  onSubmit: (query: string) => void;
  isLoading: boolean;
  parseError: QueryParseErrorDetail | null;
}

export function QueryInput({ onSubmit, isLoading, parseError }: QueryInputProps) {
  const [query, setQuery] = useState("");

  function handleSubmit(event: FormEvent) {
    event.preventDefault();
    const trimmed = query.trim();
    if (!trimmed) return;
    onSubmit(trimmed);
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-2">
      <label htmlFor="dsl-query" className="text-sm">
        Query
      </label>
      <textarea
        id="dsl-query"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        rows={3}
        placeholder='pe < 20 AND sector = "Technology" AND (roe > 0.15 OR dividend_yield > 0.02)'
        className="rounded border px-2 py-1 font-mono text-sm"
      />

      {parseError && (
        <p role="alert" className="text-sm text-red-600">
          {parseError.error} (position {parseError.position})
        </p>
      )}

      <button
        type="submit"
        disabled={isLoading}
        className="w-fit rounded bg-zinc-900 px-4 py-2 text-sm text-white disabled:opacity-50 dark:bg-zinc-100 dark:text-zinc-900"
      >
        {isLoading ? "Running..." : "Run query"}
      </button>
    </form>
  );
}
