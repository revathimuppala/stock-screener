import { describe, it, expect } from "vitest";
import { getWordAtCursor, matchSuggestions, spliceSuggestion } from "@/lib/dsl/autocomplete";

describe("getWordAtCursor", () => {
  it("returns the identifier immediately before the cursor", () => {
    expect(getWordAtCursor("pe_ra", 5)).toEqual({ word: "pe_ra", start: 0, end: 5 });
  });

  it("returns the identifier under the cursor mid-expression", () => {
    const text = 'pe < 20 AND sec = "Technology"';
    // cursor right after "sec"
    const cursor = text.indexOf("sec") + 3;
    expect(getWordAtCursor(text, cursor)).toEqual({ word: "sec", start: 12, end: 15 });
  });

  it("returns an empty word when the cursor follows whitespace or an operator", () => {
    expect(getWordAtCursor("pe < ", 5)).toEqual({ word: "", start: 5, end: 5 });
  });

  it("returns an empty word at the very start of the text", () => {
    expect(getWordAtCursor("pe", 0)).toEqual({ word: "", start: 0, end: 0 });
  });
});

describe("matchSuggestions", () => {
  const candidates = ["pe_ratio", "price", "price_to_book", "AND", "OR", "NOT"];

  it("returns prefix matches, case-insensitively, sorted", () => {
    expect(matchSuggestions("pr", candidates)).toEqual(["price", "price_to_book"]);
  });

  it("excludes an exact match (nothing left to complete)", () => {
    expect(matchSuggestions("price", candidates)).toEqual(["price_to_book"]);
  });

  it("returns an empty list for an empty prefix", () => {
    expect(matchSuggestions("", candidates)).toEqual([]);
  });

  it("caps results at the given limit", () => {
    const many = Array.from({ length: 20 }, (_, i) => `field_${i}`);
    expect(matchSuggestions("field", many, 5)).toHaveLength(5);
  });
});

describe("spliceSuggestion", () => {
  it("replaces the given span with the suggestion and places the cursor after it", () => {
    const result = spliceSuggestion("pe_ra < 20", 0, 5, "pe_ratio");
    expect(result.newText).toBe("pe_ratio < 20");
    expect(result.newCursorPos).toBe(8);
  });

  it("works when the span is empty (pure insertion)", () => {
    const result = spliceSuggestion("pe < 20 AND ", 12, 12, "sector");
    expect(result.newText).toBe("pe < 20 AND sector");
    expect(result.newCursorPos).toBe(18);
  });
});
