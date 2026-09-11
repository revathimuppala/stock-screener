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

// Percent-shaped fields (dividend yield, ROE, growth rates, 52-week
// proximity) are entered as a plain percent (e.g. "15" for 15%) — much more
// natural to type than a raw fraction — and converted here at submit time.
function parseOptionalPercent(value: string): number | undefined {
  const parsed = parseOptionalNumber(value);
  return parsed === undefined ? undefined : parsed / 100;
}

interface NumberFieldProps {
  label: string;
  value: string;
  onChange: (value: string) => void;
}

function NumberField({ label, value, onChange }: NumberFieldProps) {
  return (
    <label className="flex flex-col gap-1 text-sm">
      {label}
      <input
        type="number"
        step="any"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="rounded border px-2 py-1"
      />
    </label>
  );
}

export function FilterForm({ onSubmit, isLoading }: FilterFormProps) {
  const [peMin, setPeMin] = useState("");
  const [peMax, setPeMax] = useState("");
  const [sector, setSector] = useState("");
  const [minDividendYield, setMinDividendYield] = useState("");
  const [roeMin, setRoeMin] = useState("");
  const [debtToEquityMax, setDebtToEquityMax] = useState("");
  const [priceToBookMax, setPriceToBookMax] = useState("");
  const [earningsGrowthMin, setEarningsGrowthMin] = useState("");
  const [revenueGrowthMin, setRevenueGrowthMin] = useState("");
  const [near52WeekHigh, setNear52WeekHigh] = useState("");
  const [validationError, setValidationError] = useState<string | null>(null);

  function handleSubmit(event: FormEvent) {
    event.preventDefault();

    const criteria: ScreeningCriteria = {
      pe_min: parseOptionalNumber(peMin),
      pe_max: parseOptionalNumber(peMax),
      sector: sector || undefined,
      min_dividend_yield: parseOptionalPercent(minDividendYield),
      roe_min: parseOptionalPercent(roeMin),
      debt_to_equity_max: parseOptionalNumber(debtToEquityMax),
      price_to_book_max: parseOptionalNumber(priceToBookMax),
      earnings_growth_min: parseOptionalPercent(earningsGrowthMin),
      revenue_growth_min: parseOptionalPercent(revenueGrowthMin),
      near_52_week_high_pct: parseOptionalPercent(near52WeekHigh),
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
        <NumberField label="P/E min" value={peMin} onChange={setPeMin} />
        <NumberField label="P/E max" value={peMax} onChange={setPeMax} />
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
        <NumberField label="Min dividend yield (%)" value={minDividendYield} onChange={setMinDividendYield} />
      </div>

      <div className="grid grid-cols-2 gap-4 sm:grid-cols-3">
        <NumberField label="ROE min (%)" value={roeMin} onChange={setRoeMin} />
        <NumberField label="Debt/Equity max" value={debtToEquityMax} onChange={setDebtToEquityMax} />
        <NumberField label="P/B max" value={priceToBookMax} onChange={setPriceToBookMax} />
        <NumberField
          label="Earnings growth min (%)"
          value={earningsGrowthMin}
          onChange={setEarningsGrowthMin}
        />
        <NumberField
          label="Revenue growth min (%)"
          value={revenueGrowthMin}
          onChange={setRevenueGrowthMin}
        />
        <NumberField
          label="Near 52-week high (within %)"
          value={near52WeekHigh}
          onChange={setNear52WeekHigh}
        />
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
