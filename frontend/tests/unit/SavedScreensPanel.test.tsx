import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { SavedScreensPanel } from "@/components/screener/SavedScreensPanel";
import type { SavedScreen } from "@/lib/types";

const screens: SavedScreen[] = [
  {
    id: "1",
    name: "Cheap tech",
    criteria: { pe_max: 20 },
    query: null,
    created_at: "2026-01-01T00:00:00Z",
  },
  {
    id: "2",
    name: "High yield",
    criteria: null,
    query: 'dividend_yield > 0.02',
    created_at: "2026-01-02T00:00:00Z",
  },
];

describe("SavedScreensPanel", () => {
  it("renders nothing when closed", () => {
    render(
      <SavedScreensPanel
        isOpen={false}
        screens={screens}
        onClose={vi.fn()}
        onRun={vi.fn()}
        onDelete={vi.fn()}
      />
    );

    expect(screen.queryByText("Cheap tech")).not.toBeInTheDocument();
  });

  it("lists saved screens when open", () => {
    render(
      <SavedScreensPanel
        isOpen={true}
        screens={screens}
        onClose={vi.fn()}
        onRun={vi.fn()}
        onDelete={vi.fn()}
      />
    );

    expect(screen.getByText("Cheap tech")).toBeInTheDocument();
    expect(screen.getByText("High yield")).toBeInTheDocument();
  });

  it("shows an empty state with no saved screens", () => {
    render(
      <SavedScreensPanel isOpen={true} screens={[]} onClose={vi.fn()} onRun={vi.fn()} onDelete={vi.fn()} />
    );

    expect(screen.getByText(/no saved screens/i)).toBeInTheDocument();
  });

  it("calls onRun with the screen id when Run is clicked", async () => {
    const user = userEvent.setup();
    const onRun = vi.fn();
    render(
      <SavedScreensPanel isOpen={true} screens={screens} onClose={vi.fn()} onRun={onRun} onDelete={vi.fn()} />
    );

    await user.click(screen.getAllByRole("button", { name: /run/i })[0]);

    expect(onRun).toHaveBeenCalledWith("1");
  });

  it("calls onDelete with the screen id when Delete is clicked", async () => {
    const user = userEvent.setup();
    const onDelete = vi.fn();
    render(
      <SavedScreensPanel
        isOpen={true}
        screens={screens}
        onClose={vi.fn()}
        onRun={vi.fn()}
        onDelete={onDelete}
      />
    );

    await user.click(screen.getAllByRole("button", { name: /delete/i })[1]);

    expect(onDelete).toHaveBeenCalledWith("2");
  });

  it("calls onClose when the close button is clicked", async () => {
    const user = userEvent.setup();
    const onClose = vi.fn();
    render(
      <SavedScreensPanel isOpen={true} screens={screens} onClose={onClose} onRun={vi.fn()} onDelete={vi.fn()} />
    );

    await user.click(screen.getByRole("button", { name: /close/i }));

    expect(onClose).toHaveBeenCalled();
  });
});
