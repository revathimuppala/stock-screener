"use client";

import { FormEvent, useState } from "react";
import type { ScreeningCriteria } from "@/lib/types";

// Must match the sector strings yfinance actually returns for our universe
// (backend/domain/universe.py) — not a generic GICS list.
const SECTORS = [
  "Technology",
  "Financial Services",
  "Healthcare",
  "Consumer Cyclical",
  "Consumer Defensive",
  "Energy",
  "Industrials",
  "Utilities",
  "Communication Services",
];

interface FilterFormProps {
  onSubmit: (criteria: ScreeningCriteria) => void;
  isLoading: boolean;
}

function parseOptionalNumber(value: string): number | undefined {
  if (value.trim() === "") return undefined;
  const parsed = Number(value);
  return Number.isNaN(parsed) ? undefined : parsed;
}

export function FilterForm({ onSubmit, isLoading }: FilterFormProps) {
  const [peMin, setPeMin] = useState("");
  const [peMax, setPeMax] = useState("");
  const [sector, setSector] = useState("");
  const [minDividendYield, setMinDividendYield] = useState("");
  const [validationError, setValidationError] = useState<string | null>(null);

  function handleSubmit(event: FormEvent) {
    event.preventDefault();

    const criteria: ScreeningCriteria = {
      pe_min: parseOptionalNumber(peMin),
      pe_max: parseOptionalNumber(peMax),
      sector: sector || undefined,
      min_dividend_yield: parseOptionalNumber(minDividendYield),
    };

    if (
      criteria.pe_min !== undefined &&
      criteria.pe_max !== undefined &&
      criteria.pe_min > criteria.pe_max
    ) {
      setValidationError("P/E min must be less than or equal to P/E max.");
      return;
    }

    setValidationError(null);
    onSubmit(criteria);
  }

  return (
    <form onSubmit={handleSubmit} aria-label="Screening filters" className="flex flex-col gap-4">
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
        <label className="flex flex-col gap-1 text-sm">
          P/E min
          <input
            type="number"
            step="any"
            value={peMin}
            onChange={(e) => setPeMin(e.target.value)}
            className="rounded border px-2 py-1"
          />
        </label>
        <label className="flex flex-col gap-1 text-sm">
          P/E max
          <input
            type="number"
            step="any"
            value={peMax}
            onChange={(e) => setPeMax(e.target.value)}
            className="rounded border px-2 py-1"
          />
        </label>
        <label className="flex flex-col gap-1 text-sm">
          Sector
          <select
            value={sector}
            onChange={(e) => setSector(e.target.value)}
            className="rounded border px-2 py-1"
          >
            <option value="">Any</option>
            {SECTORS.map((s) => (
              <option key={s} value={s}>
                {s}
              </option>
            ))}
          </select>
        </label>
        <label className="flex flex-col gap-1 text-sm">
          Min dividend yield
          <input
            type="number"
            step="any"
            value={minDividendYield}
            onChange={(e) => setMinDividendYield(e.target.value)}
            className="rounded border px-2 py-1"
          />
        </label>
      </div>

      {validationError && (
        <p role="alert" className="text-sm text-red-600">
          {validationError}
        </p>
      )}

      <button
        type="submit"
        disabled={isLoading}
        className="w-fit rounded bg-zinc-900 px-4 py-2 text-sm text-white disabled:opacity-50 dark:bg-zinc-100 dark:text-zinc-900"
      >
        {isLoading ? "Screening..." : "Screen stocks"}
      </button>
    </form>
  );
}
