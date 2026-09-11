"use client";

import { useEffect, useState } from "react";
import { CompanyNotFoundError, getCompanyDetail } from "@/lib/api/screenerClient";
import type { CompanyDetail } from "@/lib/types";

function formatMoney(value: number | null): string {
  if (value == null) return "—";
  const abs = Math.abs(value);
  if (abs >= 1_000_000_000) return `$${(value / 1_000_000_000).toFixed(2)}B`;
  if (abs >= 1_000_000) return `$${(value / 1_000_000).toFixed(2)}M`;
  return `$${value.toFixed(2)}`;
}

function formatPercent(value: number | null): string {
  return value == null ? "—" : `${(value * 100).toFixed(2)}%`;
}

interface CompanyDetailContentProps {
  symbol: string;
}

/** Fetches and renders one company's detail sections (business overview,
 * quarterly financials, shareholding, SEC filings) — no page chrome of its
 * own, so it can be dropped into either the full-page route
 * (app/company/[symbol]/page.tsx) or the results-table slide-over
 * (CompanyDetailDrawer). */
export function CompanyDetailContent({ symbol }: CompanyDetailContentProps) {
  const [detail, setDetail] = useState<CompanyDetail | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [notFound, setNotFound] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    getCompanyDetail(symbol)
      .then((response) => {
        if (cancelled) return;
        setDetail(response);
      })
      .catch((err) => {
        if (cancelled) return;
        if (err instanceof CompanyNotFoundError) {
          setNotFound(true);
        } else {
          setError("Couldn't load company details. Please try again.");
        }
      })
      .finally(() => {
        if (!cancelled) setIsLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [symbol]);

  return (
    <div className="flex flex-col gap-6">
      {isLoading && <p className="text-sm text-zinc-500">Loading…</p>}

      {notFound && (
        <p role="alert" className="text-sm text-red-600">
          No data available for {symbol}.
        </p>
      )}

      {error && (
        <p role="alert" className="text-sm text-red-600">
          {error}
        </p>
      )}

      {detail && (
        <>
          <section className="flex flex-col gap-2">
            <h2 className="text-lg font-medium">Business overview</h2>
            <p className="text-sm text-zinc-500">
              {detail.profile.sector}
              {detail.profile.industry ? ` · ${detail.profile.industry}` : ""}
            </p>
            <p className="text-sm">{detail.profile.business_summary ?? "No business summary available."}</p>
            <p className="text-sm">
              <span className="font-medium">Competitors: </span>
              {detail.profile.competitors.length > 0
                ? detail.profile.competitors.join(", ")
                : "None found in the current screening universe."}
            </p>
            <p className="text-sm text-zinc-500">{detail.profile.order_backlog_note}</p>
          </section>

          <section className="flex flex-col gap-2">
            <h2 className="text-lg font-medium">Quarterly financial highlights</h2>
            {detail.quarters.length === 0 ? (
              <p className="text-sm text-zinc-500">No quarterly data available.</p>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-sm">
                  <thead>
                    <tr>
                      <th className="whitespace-nowrap py-2 pr-4">Quarter end</th>
                      <th className="whitespace-nowrap py-2 pr-4">Revenue</th>
                      <th className="whitespace-nowrap py-2 pr-4">EBIT</th>
                      <th className="whitespace-nowrap py-2 pr-4">EBITDA</th>
                      <th className="whitespace-nowrap py-2 pr-4">Net Income</th>
                      <th className="whitespace-nowrap py-2 pr-4">Diluted EPS</th>
                      <th className="whitespace-nowrap py-2 pr-4">CFO</th>
                      <th className="whitespace-nowrap py-2 pr-4">FCF</th>
                    </tr>
                  </thead>
                  <tbody>
                    {detail.quarters.map((q) => (
                      <tr key={q.period_end} className="border-t">
                        <td className="whitespace-nowrap py-2 pr-4">{q.period_end}</td>
                        <td className="whitespace-nowrap py-2 pr-4">{formatMoney(q.revenue)}</td>
                        <td className="whitespace-nowrap py-2 pr-4">{formatMoney(q.ebit)}</td>
                        <td className="whitespace-nowrap py-2 pr-4">{formatMoney(q.ebitda)}</td>
                        <td className="whitespace-nowrap py-2 pr-4">{formatMoney(q.net_income)}</td>
                        <td className="whitespace-nowrap py-2 pr-4">
                          {q.diluted_eps == null ? "—" : `$${q.diluted_eps.toFixed(2)}`}
                        </td>
                        <td className="whitespace-nowrap py-2 pr-4">{formatMoney(q.operating_cash_flow)}</td>
                        <td className="whitespace-nowrap py-2 pr-4">{formatMoney(q.free_cash_flow)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </section>

          <section className="flex flex-col gap-2">
            <h2 className="text-lg font-medium">Shareholding pattern</h2>
            {detail.shareholding == null ? (
              <p className="text-sm text-zinc-500">No shareholding data available.</p>
            ) : (
              <>
                <div className="grid grid-cols-2 gap-3 rounded border p-4 text-sm sm:grid-cols-2">
                  <div>
                    <div className="text-zinc-500">Insiders</div>
                    <div className="text-lg font-semibold">{formatPercent(detail.shareholding.insiders_pct)}</div>
                  </div>
                  <div>
                    <div className="text-zinc-500">Institutions</div>
                    <div className="text-lg font-semibold">
                      {formatPercent(detail.shareholding.institutions_pct)}
                    </div>
                  </div>
                </div>
                {detail.shareholding.top_holders.length > 0 && (
                  <table className="w-full text-left text-sm">
                    <thead>
                      <tr>
                        <th className="whitespace-nowrap py-2 pr-4">Holder</th>
                        <th className="whitespace-nowrap py-2 pr-4">Value</th>
                        <th className="whitespace-nowrap py-2 pr-4">% Change</th>
                      </tr>
                    </thead>
                    <tbody>
                      {detail.shareholding.top_holders.map((holder) => (
                        <tr key={holder.name} className="border-t">
                          <td className="whitespace-nowrap py-2 pr-4">{holder.name}</td>
                          <td className="whitespace-nowrap py-2 pr-4">{formatMoney(holder.value)}</td>
                          <td className="whitespace-nowrap py-2 pr-4">{formatPercent(holder.pct_change)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                )}
              </>
            )}
          </section>

          <section className="flex flex-col gap-2">
            <h2 className="text-lg font-medium">SEC filings</h2>
            {detail.filings.length === 0 ? (
              <p className="text-sm text-zinc-500">No filings found.</p>
            ) : (
              <ul className="flex flex-col gap-1">
                {detail.filings.map((filing) => (
                  <li key={filing.form_type}>
                    <a
                      href={filing.url}
                      target="_blank"
                      rel="noreferrer"
                      className="text-sm underline hover:no-underline"
                    >
                      {filing.form_type} — filed {filing.filed_date}
                    </a>
                  </li>
                ))}
              </ul>
            )}
          </section>
        </>
      )}
    </div>
  );
}
