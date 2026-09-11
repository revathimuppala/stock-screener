"use client";

import { FormEvent, useState, type ReactNode } from "react";
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

const SMA_WINDOWS = [50, 100, 200] as const;

interface FilterFormProps {
  onSubmit: (criteria: ScreeningCriteria) => void;
  isLoading: boolean;
  /** Already-parsed symbol list from the shared Symbols input in the
   * Screener toolbar (see app/page.tsx) — Filters and Query modes both
   * read from the same field, so it lives one level up. */
  symbols?: string[];
}

export function parseOptionalSymbols(value: string): string[] | undefined {
  const symbols = value
    .split(",")
    .map((s) => s.trim().toUpperCase())
    .filter((s) => s.length > 0);
  return symbols.length > 0 ? symbols : undefined;
}

function parseOptionalNumber(value: string): number | undefined {
  if (value.trim() === "") return undefined;
  const parsed = Number(value);
  return Number.isNaN(parsed) ? undefined : parsed;
}

// Percent-shaped fields (dividend yield, ROE, growth rates, 52-week
// proximity, operating margin, debt/assets) are entered as a plain percent
// (e.g. "15" for 15%) — much more natural to type than a raw fraction —
// and converted here at submit time.
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

function FieldGroup({ title, children }: { title: string; children: ReactNode }) {
  return (
    <fieldset className="flex flex-col gap-2">
      <legend className="mb-1 text-xs font-semibold uppercase tracking-wide text-zinc-500">
        {title}
      </legend>
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-3">{children}</div>
    </fieldset>
  );
}

export function FilterForm({ onSubmit, isLoading, symbols }: FilterFormProps) {
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
  const [pegRatioMax, setPegRatioMax] = useState("");
  const [evToEbitdaMax, setEvToEbitdaMax] = useState("");
  const [operatingMarginMin, setOperatingMarginMin] = useState("");
  const [debtToAssetsMax, setDebtToAssetsMax] = useState("");
  const [cfoToOperatingProfitMin, setCfoToOperatingProfitMin] = useState("");
  const [aboveSmaWindow, setAboveSmaWindow] = useState("");
  const [rsiMin, setRsiMin] = useState("");
  const [rsiMax, setRsiMax] = useState("");
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
      above_sma_window: aboveSmaWindow
        ? (Number(aboveSmaWindow) as 50 | 100 | 200)
        : undefined,
      peg_ratio_max: parseOptionalNumber(pegRatioMax),
      ev_to_ebitda_max: parseOptionalNumber(evToEbitdaMax),
      operating_margin_min: parseOptionalPercent(operatingMarginMin),
      debt_to_assets_max: parseOptionalPercent(debtToAssetsMax),
      cfo_to_operating_profit_min: parseOptionalNumber(cfoToOperatingProfitMin),
      rsi_min: parseOptionalNumber(rsiMin),
      rsi_max: parseOptionalNumber(rsiMax),
      symbols,
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
    <form onSubmit={handleSubmit} aria-label="Screening filters" className="flex flex-col gap-5">
      <FieldGroup title="Core">
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
      </FieldGroup>

      <FieldGroup title="Valuation Ratios">
        <NumberField label="PEG max" value={pegRatioMax} onChange={setPegRatioMax} />
        <NumberField label="EV/EBITDA max" value={evToEbitdaMax} onChange={setEvToEbitdaMax} />
        <NumberField label="P/B max" value={priceToBookMax} onChange={setPriceToBookMax} />
      </FieldGroup>

      <FieldGroup title="Financial Health & Profitability">
        <NumberField label="ROE min (%)" value={roeMin} onChange={setRoeMin} />
        <NumberField label="Debt/Equity max" value={debtToEquityMax} onChange={setDebtToEquityMax} />
        <NumberField label="Debt/Assets max (%)" value={debtToAssetsMax} onChange={setDebtToAssetsMax} />
        <NumberField label="Operating margin min (%)" value={operatingMarginMin} onChange={setOperatingMarginMin} />
        <NumberField label="CFO/OP min" value={cfoToOperatingProfitMin} onChange={setCfoToOperatingProfitMin} />
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
      </FieldGroup>

      <FieldGroup title="Technical & Price Metrics">
        <NumberField
          label="Near 52-week high (within %)"
          value={near52WeekHigh}
          onChange={setNear52WeekHigh}
        />
        <label className="flex flex-col gap-1 text-sm">
          Price above SMA
          <select
            value={aboveSmaWindow}
            onChange={(e) => setAboveSmaWindow(e.target.value)}
            className="rounded border px-2 py-1"
          >
            <option value="">Any</option>
            {SMA_WINDOWS.map((w) => (
              <option key={w} value={w}>
                {w}-day
              </option>
            ))}
          </select>
        </label>
        <NumberField label="RSI min" value={rsiMin} onChange={setRsiMin} />
        <NumberField label="RSI max" value={rsiMax} onChange={setRsiMax} />
      </FieldGroup>

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
