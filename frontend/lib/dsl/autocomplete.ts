// Pure text-manipulation helpers for the DSL query autocomplete — split out
// from the textarea component so the tricky bit (finding the identifier
// under the caret, splicing in a suggestion) is unit-testable without a DOM.

const IDENTIFIER_CHAR = /[A-Za-z0-9_]/;

export interface WordAtCursor {
  word: string;
  start: number;
  end: number;
}

/** The identifier immediately ending at `cursorPos`, if any (e.g. typing
 * "pe_ra|" with the caret at `|` returns { word: "pe_ra", start: 0, end: 5 }).
 * Empty word when the caret isn't right after an identifier character. */
export function getWordAtCursor(text: string, cursorPos: number): WordAtCursor {
  let start = cursorPos;
  while (start > 0 && IDENTIFIER_CHAR.test(text[start - 1])) {
    start -= 1;
  }
  return { word: text.slice(start, cursorPos), start, end: cursorPos };
}

export interface Suggestion {
  value: string;
}

/** Case-insensitive prefix match against field names and DSL keywords,
 * sorted alphabetically, capped so the dropdown stays short. */
export function matchSuggestions(prefix: string, candidates: string[], limit = 8): string[] {
  if (prefix.length === 0) return [];
  const lowered = prefix.toLowerCase();
  return candidates
    .filter((c) => c.toLowerCase().startsWith(lowered) && c.toLowerCase() !== lowered)
    .sort()
    .slice(0, limit);
}

export interface SpliceResult {
  newText: string;
  newCursorPos: number;
}

/** Replaces the [start, end) span with `suggestion`, placing the caret
 * right after the inserted text. */
export function spliceSuggestion(
  text: string,
  start: number,
  end: number,
  suggestion: string
): SpliceResult {
  const newText = text.slice(0, start) + suggestion + text.slice(end);
  return { newText, newCursorPos: start + suggestion.length };
}
