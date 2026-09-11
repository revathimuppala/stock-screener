import { test, expect } from "@playwright/test";

// Stubs the backend at the network boundary so this flow is deterministic
// and doesn't depend on a live FastAPI process or real yfinance data. Manual
// verification against the real backend is a separate step (see specs/ and
// the plan's Verification section).
test("filling filters and submitting shows ranked results", async ({ page }) => {
  await page.route("**/api/v1/screener", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        status: "ok",
        results: [
          {
            symbol: "AAPL",
            name: "Apple Inc.",
            sector: "Technology",
            price: 190.12,
            pe_ratio: 15.4,
            market_cap: 3_000_000_000_000,
            dividend_yield: 0.005,
            is_stale: false,
          },
        ],
        stale_symbols: [],
        excluded_symbols: [],
        as_of: "2026-01-01T00:00:00Z",
      }),
    });
  });

  await page.goto("/screener");

  await page.getByLabel(/p\/e min/i).fill("10");
  await page.getByLabel(/p\/e max/i).fill("20");
  await page.getByRole("button", { name: /screen stocks/i }).click();

  await expect(page.getByRole("row", { name: /AAPL/ })).toBeVisible();
  await expect(page.getByRole("status")).toHaveCount(0);
});

test("shows a degraded banner when results include stale data", async ({ page }) => {
  await page.route("**/api/v1/screener", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        status: "degraded",
        results: [
          {
            symbol: "AAPL",
            name: "Apple Inc.",
            sector: "Technology",
            price: 190.12,
            pe_ratio: 15.4,
            market_cap: 3_000_000_000_000,
            dividend_yield: 0.005,
            is_stale: true,
          },
        ],
        stale_symbols: ["AAPL"],
        excluded_symbols: [],
        as_of: "2026-01-01T00:00:00Z",
      }),
    });
  });

  await page.goto("/screener");
  await page.getByRole("button", { name: /screen stocks/i }).click();

  await expect(page.getByRole("status")).toContainText(/degraded/i);
  await expect(page.getByRole("row", { name: /AAPL/ })).toContainText(/stale/i);
});
