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
            roe: 0.15,
            debt_to_equity: 50,
            price_to_book: 10,
            earnings_growth: 0.1,
            revenue_growth: 0.08,
            fifty_two_week_high: 200,
            fifty_two_week_low: 150,
          },
        ],
        stale_symbols: [],
        excluded_symbols: [],
        as_of: "2026-01-01T00:00:00Z",
      }),
    });
  });

  await page.goto("/");

  await page.getByRole("tab", { name: /^filters$/i }).click();
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
            roe: 0.15,
            debt_to_equity: 50,
            price_to_book: 10,
            earnings_growth: 0.1,
            revenue_growth: 0.08,
            fifty_two_week_high: 200,
            fifty_two_week_low: 150,
          },
        ],
        stale_symbols: ["AAPL"],
        excluded_symbols: [],
        as_of: "2026-01-01T00:00:00Z",
      }),
    });
  });

  await page.goto("/");

  await page.getByRole("tab", { name: /^filters$/i }).click();
  await page.getByRole("button", { name: /screen stocks/i }).click();

  await expect(page.getByRole("status")).toContainText(/degraded/i);
  await expect(page.getByRole("row", { name: /AAPL/ })).toContainText(/stale/i);
});

test("switching to Query mode and running a query shows results", async ({ page }) => {
  await page.route("**/api/v1/screener/query", async (route) => {
    const body = route.request().postDataJSON();
    expect(body.query).toContain("pe");
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        status: "ok",
        results: [
          {
            symbol: "MSFT",
            name: "Microsoft Corporation",
            sector: "Technology",
            price: 400,
            pe_ratio: 27.4,
            market_cap: 3_000_000_000_000,
            dividend_yield: 0.007,
            is_stale: false,
            roe: 0.3,
            debt_to_equity: 40,
            price_to_book: 12,
            earnings_growth: 0.2,
            revenue_growth: 0.1,
            fifty_two_week_high: 500,
            fifty_two_week_low: 300,
          },
        ],
        stale_symbols: [],
        excluded_symbols: [],
        as_of: "2026-01-01T00:00:00Z",
      }),
    });
  });

  await page.goto("/");
  await page.getByRole("tab", { name: /^query$/i }).click();
  await page.getByLabel(/query/i).fill('pe < 30 AND sector = "Technology"');
  await page.getByRole("button", { name: /run query/i }).click();

  await expect(page.getByRole("row", { name: /MSFT/ })).toBeVisible();
});

test("shows an inline parse error for a malformed query", async ({ page }) => {
  await page.route("**/api/v1/screener/query", async (route) => {
    await route.fulfill({
      status: 400,
      contentType: "application/json",
      body: JSON.stringify({ detail: { error: "unknown field 'foo'", position: 0 } }),
    });
  });

  await page.goto("/");
  await page.getByRole("tab", { name: /^query$/i }).click();
  await page.getByLabel(/query/i).fill("foo < 20");
  await page.getByRole("button", { name: /run query/i }).click();

  await expect(page.getByText(/unknown field/i)).toBeVisible();
});
