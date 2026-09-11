import { describe, it, expect, vi } from "vitest";
import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { BacktestTimeline } from "@/components/backtest/BacktestTimeline";
import type { BacktestMatch } from "@/lib/types";

const timeline: BacktestMatch[] = [
  { symbol: "AAPL", match_date: "2026-01-01", match_price: 100 },
  { symbol: "MSFT", match_date: "2026-01-01", match_price: 200 },
  { symbol: "AAPL", match_date: "2026-01-05", match_price: 105 },
];

describe("BacktestTimeline", () => {
  it("groups matches by date", () => {
    render(<BacktestTimeline timeline={timeline} onSelectMatch={vi.fn()} />);

    expect(screen.getByText("2026-01-01")).toBeInTheDocument();
    expect(screen.getByText("2026-01-05")).toBeInTheDocument();
  });

  it("lists every matched symbol under its date", () => {
    render(<BacktestTimeline timeline={timeline} onSelectMatch={vi.fn()} />);

    const jan1Group = screen.getByText("2026-01-01").closest("li") as HTMLElement;
    expect(jan1Group).toHaveTextContent("AAPL");
    expect(jan1Group).toHaveTextContent("MSFT");
  });

  it("calls onSelectMatch with the symbol and date when clicked", async () => {
    const user = userEvent.setup();
    const onSelectMatch = vi.fn();
    render(<BacktestTimeline timeline={timeline} onSelectMatch={onSelectMatch} />);

    const jan5Group = screen.getByText("2026-01-05").closest("li") as HTMLElement;
    const { getByRole } = within(jan5Group);
    await user.click(getByRole("button", { name: /AAPL/i }));

    expect(onSelectMatch).toHaveBeenCalledWith("AAPL", "2026-01-05");
  });

  it("shows an empty state when there are no matches", () => {
    render(<BacktestTimeline timeline={[]} onSelectMatch={vi.fn()} />);

    expect(screen.getByText(/no matches/i)).toBeInTheDocument();
  });
});
