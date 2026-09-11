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
    await user.type(screen.getByLabelText(/min dividend yield/i), "0.01");
    await user.click(screen.getByRole("button", { name: /screen stocks/i }));

    expect(onSubmit).toHaveBeenCalledWith({
      pe_min: 10,
      pe_max: 20,
      sector: "Technology",
      min_dividend_yield: 0.01,
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
    });
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
