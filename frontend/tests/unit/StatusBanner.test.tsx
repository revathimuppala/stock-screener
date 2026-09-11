import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { StatusBanner } from "@/components/screener/StatusBanner";

describe("StatusBanner", () => {
  it("renders nothing when status is ok", () => {
    const { container } = render(
      <StatusBanner status="ok" staleSymbols={[]} excludedSymbols={[]} />
    );
    expect(container).toBeEmptyDOMElement();
  });

  it("shows a degraded banner listing stale and excluded symbols", () => {
    render(
      <StatusBanner status="degraded" staleSymbols={["AAPL"]} excludedSymbols={["BAD"]} />
    );

    const banner = screen.getByRole("status");
    expect(banner).toHaveTextContent(/degraded/i);
    expect(banner).toHaveTextContent("AAPL");
    expect(banner).toHaveTextContent("BAD");
  });
});
