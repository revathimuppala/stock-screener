import { describe, it, expect, vi, beforeEach } from "vitest";
import {
  getMarkets,
  getScreenJob,
  postScreen,
  QueryParseException,
  ScreenerApiError,
  startScreenJob,
} from "@/lib/api/screenerClient";
import type { Market, ScreenJob, ScreenResponse } from "@/lib/types";

const sampleResponse: ScreenResponse = {
  status: "ok",
  results: [],
  stale_symbols: [],
  excluded_symbols: [],
  as_of: "2026-01-01T00:00:00Z",
};

describe("postScreen", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("posts criteria as JSON to the screener endpoint", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => sampleResponse,
    });
    vi.stubGlobal("fetch", fetchMock);

    const result = await postScreen({ pe_min: 10, pe_max: 20 });

    expect(fetchMock).toHaveBeenCalledTimes(1);
    const [url, options] = fetchMock.mock.calls[0];
    expect(String(url)).toContain("/api/v1/screener");
    expect(options.method).toBe("POST");
    expect(JSON.parse(options.body)).toEqual({ pe_min: 10, pe_max: 20 });
    expect(result).toEqual(sampleResponse);
  });

  it("throws ScreenerApiError on a non-ok response", async () => {
    const fetchMock = vi.fn().mockResolvedValue({ ok: false, status: 503 });
    vi.stubGlobal("fetch", fetchMock);

    await expect(postScreen({})).rejects.toBeInstanceOf(ScreenerApiError);
  });
});

describe("getMarkets", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("fetches the market allowlist", async () => {
    const markets: Market[] = [{ id: "default", label: "US Large Cap (Default)" }];
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({ markets }),
    });
    vi.stubGlobal("fetch", fetchMock);

    const result = await getMarkets();

    expect(String(fetchMock.mock.calls[0][0])).toContain("/api/v1/markets");
    expect(result).toEqual({ markets });
  });
});

describe("startScreenJob", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("posts the job request and returns the screen_id", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 202,
      json: async () => ({ screen_id: "abc-123", status: "pending" }),
    });
    vi.stubGlobal("fetch", fetchMock);

    const result = await startScreenJob({ market_id: "sp500", criteria: { pe_max: 20 } });

    const [url, options] = fetchMock.mock.calls[0];
    expect(String(url)).toContain("/api/v1/screener/jobs");
    expect(JSON.parse(options.body)).toEqual({ market_id: "sp500", criteria: { pe_max: 20 } });
    expect(result).toEqual({ screen_id: "abc-123", status: "pending" });
  });

  it("throws QueryParseException on a malformed-query 400 response", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: false,
      status: 400,
      json: async () => ({ detail: { error: "unknown field 'foo'", position: 0 } }),
    });
    vi.stubGlobal("fetch", fetchMock);

    await expect(startScreenJob({ market_id: "sp500", query: "foo < 1" })).rejects.toBeInstanceOf(
      QueryParseException
    );
  });

  it("throws ScreenerApiError on an unknown-market 400 response", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: false,
      status: 400,
      json: async () => ({ detail: "unknown market_id 'dow30'" }),
    });
    vi.stubGlobal("fetch", fetchMock);

    await expect(
      startScreenJob({ market_id: "dow30", criteria: { pe_max: 20 } })
    ).rejects.toBeInstanceOf(ScreenerApiError);
  });
});

describe("getScreenJob", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("fetches the job record by id", async () => {
    const job: ScreenJob = { status: "completed", screen_status: "ok", results: [] };
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => job,
    });
    vi.stubGlobal("fetch", fetchMock);

    const result = await getScreenJob("abc-123");

    expect(String(fetchMock.mock.calls[0][0])).toContain("/api/v1/screener/jobs/abc-123");
    expect(result).toEqual(job);
  });
});
