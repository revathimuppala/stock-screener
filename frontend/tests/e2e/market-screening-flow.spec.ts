import { test, expect } from "@playwright/test";

// Selecting a non-default market (S&P 500 here) is too large to screen
// within one HTTP request, so it goes through the async job pattern
// (mirrors backtest-flow.spec.ts's stubbing approach) instead of the
// synchronous /screener/query endpoint.
test("selecting a market runs the screen as a background job and shows results", async ({ page }) => {
  let pollCount = 0;

  await page.route("**/api/v1/markets", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        markets: [
          { id: "default", label: "US Large Cap (Default)" },
          { id: "sp500", label: "S&P 500" },
        ],
      }),
    });
  });

  await page.route("**/api/v1/screener/jobs", async (route) => {
    if (route.request().method() !== "POST") return route.fallback();
    const body = route.request().postDataJSON();
    expect(body.market_id).toBe("sp500");
    expect(body.query).toContain("pe");
    await route.fulfill({
      status: 202,
      contentType: "application/json",
      body: JSON.stringify({ screen_id: "screen-job-1", status: "pending" }),
    });
  });

  await page.route("**/api/v1/screener/jobs/screen-job-1", async (route) => {
    pollCount += 1;
    if (pollCount === 1) {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ status: "running" }),
      });
      return;
    }
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        status: "completed",
        screen_status: "ok",
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
          },
        ],
        stale_symbols: [],
        excluded_symbols: [],
        as_of: "2026-01-01T00:00:00Z",
      }),
    });
  });

  await page.goto("/");
  await page.getByRole("combobox", { name: "Market" }).selectOption("sp500");

  await expect(page.getByText(/S&P 500 can be 100-500\+ symbols/i)).toBeVisible();

  await page.getByLabel(/query/i).fill("pe < 30");
  await page.getByRole("button", { name: /run query/i }).click();

  await expect(page.getByText(/S&P 500 is pending|S&P 500 is running/i)).toBeVisible();

  await expect(page.getByRole("row", { name: /MSFT/ })).toBeVisible({ timeout: 10000 });
});

test("an explicit symbol list bypasses the async job even with a market selected", async ({ page }) => {
  await page.route("**/api/v1/markets", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        markets: [
          { id: "default", label: "US Large Cap (Default)" },
          { id: "sp500", label: "S&P 500" },
        ],
      }),
    });
  });

  let jobsCalled = false;
  await page.route("**/api/v1/screener/jobs", async () => {
    jobsCalled = true;
  });

  await page.route("**/api/v1/screener/query", async (route) => {
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
            price: 190,
            pe_ratio: 15,
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

  await page.goto("/");
  await page.getByRole("combobox", { name: "Market" }).selectOption("sp500");
  await page.getByLabel(/symbols/i).fill("AAPL");
  await page.getByLabel(/query/i).fill("pe < 30");
  await page.getByRole("button", { name: /run query/i }).click();

  await expect(page.getByRole("row", { name: /AAPL/ })).toBeVisible();
  expect(jobsCalled).toBe(false);
});
