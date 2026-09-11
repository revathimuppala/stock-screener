import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { FilterForm } from "@/components/screener/FilterForm";

describe("FilterForm", () => {
  it("submits the entered criteria", async () => {
    const user = userEvent.setup();
    const onSubmit = vi.fn();
    render(<FilterForm onSubmit={onSubmit} isLoading={false} />);

    await user.type(screen.getByLabelText(/p\/e min/i), "10");
    await user.type(screen.getByLabelText(/p\/e max/i), "20");
    await user.selectOptions(screen.getByLabelText(/sector/i), "Technology");
    await user.type(screen.getByLabelText(/min dividend yield/i), "1");
    await user.click(screen.getByRole("button", { name: /screen stocks/i }));

    expect(onSubmit).toHaveBeenCalledWith({
      pe_min: 10,
      pe_max: 20,
      sector: "Technology",
      min_dividend_yield: 0.01,
      roe_min: undefined,
      debt_to_equity_max: undefined,
      price_to_book_max: undefined,
      earnings_growth_min: undefined,
      revenue_growth_min: undefined,
      near_52_week_high_pct: undefined,
    });
  });

  it("submits undefined for blank optional fields", async () => {
    const user = userEvent.setup();
    const onSubmit = vi.fn();
    render(<FilterForm onSubmit={onSubmit} isLoading={false} />);

    await user.click(screen.getByRole("button", { name: /screen stocks/i }));

    expect(onSubmit).toHaveBeenCalledWith({
      pe_min: undefined,
      pe_max: undefined,
      sector: undefined,
      min_dividend_yield: undefined,
      roe_min: undefined,
      debt_to_equity_max: undefined,
      price_to_book_max: undefined,
      earnings_growth_min: undefined,
      revenue_growth_min: undefined,
      near_52_week_high_pct: undefined,
    });
  });

  it("submits the new fundamental filter fields when filled in", async () => {
    const user = userEvent.setup();
    const onSubmit = vi.fn();
    render(<FilterForm onSubmit={onSubmit} isLoading={false} />);

    await user.type(screen.getByLabelText(/roe min/i), "15");
    await user.type(screen.getByLabelText(/debt\/equity max/i), "100");
    await user.type(screen.getByLabelText(/p\/b max/i), "5");
    await user.type(screen.getByLabelText(/earnings growth min/i), "10");
    await user.type(screen.getByLabelText(/revenue growth min/i), "5");
    await user.type(screen.getByLabelText(/near 52-week high/i), "10");
    await user.click(screen.getByRole("button", { name: /screen stocks/i }));

    expect(onSubmit).toHaveBeenCalledWith(
      expect.objectContaining({
        roe_min: 0.15,
        debt_to_equity_max: 100,
        price_to_book_max: 5,
        earnings_growth_min: 0.1,
        revenue_growth_min: 0.05,
        near_52_week_high_pct: 0.1,
      })
    );
  });

  it("shows a validation error and does not submit when P/E min exceeds P/E max", async () => {
    const user = userEvent.setup();
    const onSubmit = vi.fn();
    render(<FilterForm onSubmit={onSubmit} isLoading={false} />);

    await user.type(screen.getByLabelText(/p\/e min/i), "30");
    await user.type(screen.getByLabelText(/p\/e max/i), "10");
    await user.click(screen.getByRole("button", { name: /screen stocks/i }));

    expect(onSubmit).not.toHaveBeenCalled();
    expect(screen.getByRole("alert")).toHaveTextContent(/p\/e min must be/i);
  });

  it("disables the submit button while loading", () => {
    render(<FilterForm onSubmit={vi.fn()} isLoading={true} />);

    expect(screen.getByRole("button", { name: /screening/i })).toBeDisabled();
  });
});
