"use client";

import { useEffect, useState } from "react";
import { CompanyDetailContent } from "@/components/company/CompanyDetailContent";

interface CompanyDetailDrawerProps {
  symbol: string | null;
  onClose: () => void;
}

/** A slide-over panel showing one company's detail, opened from the
 * results table instead of navigating away to /company/[symbol] (that
 * route still exists for direct/bookmarkable links). */
export function CompanyDetailDrawer({ symbol, onClose }: CompanyDetailDrawerProps) {
  // Starts false so the panel renders off-screen on mount, then flips true
  // on the next frame so the transform transition actually animates in
  // instead of snapping into place. The component is remounted per symbol
  // (see the `key` at the call site) so this resets for every open.
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    if (symbol == null) return;
    const frame = requestAnimationFrame(() => setIsVisible(true));
    return () => cancelAnimationFrame(frame);
  }, [symbol]);

  useEffect(() => {
    if (symbol == null) return;
    function handleKeyDown(e: KeyboardEvent) {
      if (e.key === "Escape") onClose();
    }
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [symbol, onClose]);

  if (symbol == null) return null;

  return (
    <div className="fixed inset-0 z-50">
      <div
        className={`absolute inset-0 bg-black/30 transition-opacity ${isVisible ? "opacity-100" : "opacity-0"}`}
        onClick={onClose}
        aria-hidden="true"
      />
      <div
        role="dialog"
        aria-modal="true"
        aria-label={`${symbol} details`}
        className={`absolute inset-y-0 right-0 flex w-full max-w-2xl flex-col bg-white shadow-xl transition-transform dark:bg-zinc-900 ${
          isVisible ? "translate-x-0" : "translate-x-full"
        }`}
      >
        <div className="flex items-center justify-between border-b px-6 py-4">
          <h1 className="text-xl font-semibold">{symbol}</h1>
          <button
            type="button"
            onClick={onClose}
            aria-label="Close"
            className="rounded px-2 py-1 text-zinc-500 hover:bg-zinc-100 hover:text-zinc-900 dark:hover:bg-zinc-800 dark:hover:text-zinc-100"
          >
            ✕
          </button>
        </div>
        <div className="overflow-y-auto px-6 py-6">
          <CompanyDetailContent key={symbol} symbol={symbol} />
        </div>
      </div>
    </div>
  );
}
