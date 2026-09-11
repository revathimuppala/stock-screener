"use client";

import type { SavedScreen } from "@/lib/types";

interface SavedScreensPanelProps {
  isOpen: boolean;
  screens: SavedScreen[];
  onClose: () => void;
  onRun: (screenId: string) => void;
  onDelete: (screenId: string) => void;
}

export function SavedScreensPanel({ isOpen, screens, onClose, onRun, onDelete }: SavedScreensPanelProps) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-20 flex justify-end bg-black/20" onClick={onClose}>
      <aside
        aria-label="Saved screens"
        onClick={(e) => e.stopPropagation()}
        className="flex h-full w-80 flex-col gap-3 overflow-y-auto border-l border-zinc-200 bg-white p-4 dark:border-zinc-800 dark:bg-zinc-950"
      >
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-semibold">Saved Screens</h2>
          <button
            type="button"
            aria-label="Close saved screens panel"
            onClick={onClose}
            className="text-sm text-zinc-500 hover:text-zinc-900 dark:hover:text-zinc-100"
          >
            Close
          </button>
        </div>

        {screens.length === 0 ? (
          <p className="text-sm text-zinc-500">No saved screens yet.</p>
        ) : (
          <ul className="flex flex-col gap-2">
            {screens.map((screen) => (
              <li
                key={screen.id}
                className="flex items-center justify-between gap-2 rounded border px-3 py-2 text-sm"
              >
                <span className="truncate">{screen.name}</span>
                <span className="flex shrink-0 gap-2">
                  <button
                    type="button"
                    onClick={() => onRun(screen.id)}
                    className="text-zinc-900 underline dark:text-zinc-100"
                  >
                    Run
                  </button>
                  <button
                    type="button"
                    onClick={() => onDelete(screen.id)}
                    className="text-red-600 underline"
                  >
                    Delete
                  </button>
                </span>
              </li>
            ))}
          </ul>
        )}
      </aside>
    </div>
  );
}
