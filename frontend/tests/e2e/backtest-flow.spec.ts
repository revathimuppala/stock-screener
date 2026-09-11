import { test, expect } from "@playwright/test";

// Stubs the backend at the network boundary: first POST returns a job id
// with status "pending", then GET polls return "running" once and
// "completed" thereafter — exercising the real poll-until-done UI flow
// without depending on a live backend or real yfinance data.
test("starting a backtest polls until completion and shows the timeline", async ({ page }) => {
  let pollCount = 0;

  await page.route("**/api/v1/backtest", async (route) => {
    if (route.request().method() !== "POST") return route.fallback();
    await route.fulfill({
      status: 202,
      contentType: "application/json",
      body: JSON.stringify({ backtest_id: "job-123", status: "pending" }),
    });
  });

  await page.route("**/api/v1/backtest/job-123", async (route) => {
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
        timeline: [{ symbol: "AAPL", match_date: "2026-01-01", match_price: 100 }],
        performances: [
          {
            match: { symbol: "AAPL", match_date: "2026-01-01", match_price: 100 },
            exit_date: "2026-01-31",
            exit_price: 110,
            return_pct: 10,
            status: "completed",
          },
        ],
        summary: {
          total_matches: 1,
          completed_count: 1,
          pending_count: 0,
          avg_return_pct: 10,
          win_rate: 1,
          best_return_pct: 10,
          worst_return_pct: 10,
        },
        excluded_symbols: [],
        warnings: [],
        fundamentals_as_of: "2026-01-01T00:00:00Z",
      }),
    });
  });

  await page.goto("/backtest");
  await page.getByRole("button", { name: /run backtest/i }).click();

  await expect(page.getByText(/is pending|is running/i)).toBeVisible();

  await expect(page.getByRole("button", { name: /AAPL/i })).toBeVisible({ timeout: 10000 });
  await expect(page.getByText(/^1$/)).toBeVisible(); // total matches stat

  await page.getByRole("button", { name: /AAPL/i }).click();
  await expect(page.getByText(/Return: \+10\.00%/)).toBeVisible();
});
