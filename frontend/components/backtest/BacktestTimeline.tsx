"use client";

import type { BacktestMatch } from "@/lib/types";

interface BacktestTimelineProps {
  timeline: BacktestMatch[];
  onSelectMatch: (symbol: string, matchDate: string) => void;
}

function groupByDate(timeline: BacktestMatch[]): Map<string, BacktestMatch[]> {
  const groups = new Map<string, BacktestMatch[]>();
  for (const match of timeline) {
    const existing = groups.get(match.match_date) ?? [];
    existing.push(match);
    groups.set(match.match_date, existing);
  }
  return groups;
}

export function BacktestTimeline({ timeline, onSelectMatch }: BacktestTimelineProps) {
  if (timeline.length === 0) {
    return <p className="text-sm text-zinc-500">No matches in this window.</p>;
  }

  const groups = groupByDate(timeline);
  const dates = [...groups.keys()].sort();

  return (
    <ul className="flex flex-col gap-3">
      {dates.map((matchDate) => (
        <li key={matchDate} className="rounded border px-3 py-2 text-sm">
          <div className="font-medium">{matchDate}</div>
          <div className="mt-1 flex flex-wrap gap-2">
            {groups.get(matchDate)!.map((match) => (
              <button
                key={match.symbol}
                type="button"
                onClick={() => onSelectMatch(match.symbol, match.match_date)}
                className="rounded border px-2 py-0.5 text-xs hover:bg-zinc-100 dark:hover:bg-zinc-900"
              >
                {match.symbol} @ ${match.match_price.toFixed(2)}
              </button>
            ))}
          </div>
        </li>
      ))}
    </ul>
  );
}
