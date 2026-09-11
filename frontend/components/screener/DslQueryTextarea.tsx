"use client";

import { useEffect, useRef, useState } from "react";
import { getDslFields } from "@/lib/api/screenerClient";
import { getWordAtCursor, matchSuggestions, spliceSuggestion } from "@/lib/dsl/autocomplete";

const KEYWORDS = ["AND", "OR", "NOT"];

interface DslQueryTextareaProps {
  id: string;
  value: string;
  onChange: (value: string) => void;
  rows?: number;
  placeholder?: string;
}

/** A DSL query textarea with field-name autocomplete. Fetches the field
 * allowlist from GET /api/v1/screener/fields (so suggestions can never
 * drift from what the parser actually accepts) and suggests matches for
 * the identifier under the caret as the user types. Shared by the
 * Screener's Query tab and the Backtest page. */
export function DslQueryTextarea({ id, value, onChange, rows = 3, placeholder }: DslQueryTextareaProps) {
  const [candidates, setCandidates] = useState<string[]>(KEYWORDS);
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [highlightedIndex, setHighlightedIndex] = useState(0);
  const [wordSpan, setWordSpan] = useState<{ start: number; end: number } | null>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    let cancelled = false;
    getDslFields()
      .then((response) => {
        if (cancelled) return;
        const names = response.fields.map((f) => f.name);
        const aliases = Object.keys(response.aliases);
        setCandidates([...KEYWORDS, ...names, ...aliases]);
      })
      .catch(() => {
        // Autocomplete is a nice-to-have; leave the keyword-only fallback.
      });
    return () => {
      cancelled = true;
    };
  }, []);

  function updateSuggestionsFromCursor(text: string, cursorPos: number) {
    const { word, start, end } = getWordAtCursor(text, cursorPos);
    const matches = matchSuggestions(word, candidates);
    setSuggestions(matches);
    setHighlightedIndex(0);
    setWordSpan(matches.length > 0 ? { start, end } : null);
  }

  function handleChange(e: React.ChangeEvent<HTMLTextAreaElement>) {
    onChange(e.target.value);
    updateSuggestionsFromCursor(e.target.value, e.target.selectionStart);
  }

  function acceptSuggestion(suggestion: string) {
    if (!wordSpan) return;
    const { newText, newCursorPos } = spliceSuggestion(value, wordSpan.start, wordSpan.end, suggestion);
    onChange(newText);
    setSuggestions([]);
    setWordSpan(null);
    requestAnimationFrame(() => {
      textareaRef.current?.focus();
      textareaRef.current?.setSelectionRange(newCursorPos, newCursorPos);
    });
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (suggestions.length === 0) return;
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setHighlightedIndex((i) => (i + 1) % suggestions.length);
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setHighlightedIndex((i) => (i - 1 + suggestions.length) % suggestions.length);
    } else if (e.key === "Enter" || e.key === "Tab") {
      e.preventDefault();
      acceptSuggestion(suggestions[highlightedIndex]);
    } else if (e.key === "Escape") {
      setSuggestions([]);
      setWordSpan(null);
    }
  }

  return (
    <div className="relative">
      <textarea
        id={id}
        ref={textareaRef}
        value={value}
        onChange={handleChange}
        onKeyDown={handleKeyDown}
        onBlur={() => setSuggestions([])}
        rows={rows}
        placeholder={placeholder}
        className="w-full rounded border px-2 py-1 font-mono text-sm"
        role="combobox"
        aria-expanded={suggestions.length > 0}
        aria-autocomplete="list"
        aria-controls={`${id}-suggestions`}
      />
      {suggestions.length > 0 && (
        <ul
          id={`${id}-suggestions`}
          role="listbox"
          className="absolute z-10 mt-1 w-48 rounded border bg-white text-sm shadow dark:bg-zinc-900"
        >
          {suggestions.map((suggestion, index) => (
            <li key={suggestion} role="option" aria-selected={index === highlightedIndex}>
              <button
                type="button"
                // onMouseDown (not onClick) fires before the textarea's onBlur closes the dropdown
                onMouseDown={(e) => {
                  e.preventDefault();
                  acceptSuggestion(suggestion);
                }}
                className={`block w-full px-2 py-1 text-left font-mono ${
                  index === highlightedIndex ? "bg-zinc-100 dark:bg-zinc-800" : ""
                }`}
              >
                {suggestion}
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
