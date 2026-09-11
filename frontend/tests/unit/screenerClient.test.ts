import { describe, it, expect, vi, beforeEach } from "vitest";
import { postScreen, ScreenerApiError } from "@/lib/api/screenerClient";
import type { ScreenResponse } from "@/lib/types";

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
