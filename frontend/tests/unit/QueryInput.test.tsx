import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryInput } from "@/components/screener/QueryInput";

describe("QueryInput", () => {
  it("submits the entered query text", async () => {
    const user = userEvent.setup();
    const onSubmit = vi.fn();
    render(<QueryInput onSubmit={onSubmit} isLoading={false} parseError={null} />);

    await user.type(screen.getByLabelText(/query/i), 'pe < 20 AND sector = "Technology"');
    await user.click(screen.getByRole("button", { name: /run query/i }));

    expect(onSubmit).toHaveBeenCalledWith('pe < 20 AND sector = "Technology"');
  });

  it("does not submit a blank query", async () => {
    const user = userEvent.setup();
    const onSubmit = vi.fn();
    render(<QueryInput onSubmit={onSubmit} isLoading={false} parseError={null} />);

    await user.click(screen.getByRole("button", { name: /run query/i }));

    expect(onSubmit).not.toHaveBeenCalled();
  });

  it("shows a parse error message and position when given", () => {
    render(
      <QueryInput
        onSubmit={vi.fn()}
        isLoading={false}
        parseError={{ error: "unknown field 'foo'", position: 0 }}
      />
    );

    expect(screen.getByRole("alert")).toHaveTextContent(/unknown field/i);
    expect(screen.getByRole("alert")).toHaveTextContent(/position 0/i);
  });

  it("disables the button while loading", () => {
    render(<QueryInput onSubmit={vi.fn()} isLoading={true} parseError={null} />);

    expect(screen.getByRole("button", { name: /running/i })).toBeDisabled();
  });
});
