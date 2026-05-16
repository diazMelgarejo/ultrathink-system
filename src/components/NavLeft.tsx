import { useState } from "react";

interface NavItem {
  id: string;
  label: string;
  hotkey?: string;
}

const NAV_ITEMS: NavItem[] = [
  { id: "command", label: "Command Center", hotkey: "C" },
  { id: "jobs", label: "Jobs", hotkey: "J" },
  { id: "models", label: "Models", hotkey: "M" },
  { id: "policy", label: "Hardware Policy", hotkey: "H" },
  { id: "artifacts", label: "Artifacts", hotkey: "A" },
  { id: "activity", label: "Activity Log", hotkey: "L" },
];

interface NavLeftProps {
  active?: string;
  onSelect?: (id: string) => void;
}

export function NavLeft({ active = "command", onSelect }: NavLeftProps) {
  const [current, setCurrent] = useState(active);

  return (
    <nav className="flex h-full w-48 flex-col border-r border-line bg-canvas-surface py-2">
      <div className="px-3 py-1 text-2xs font-mono uppercase tracking-wider text-ink-subtle">
        sections
      </div>
      <ul className="flex flex-col">
        {NAV_ITEMS.map((item) => {
          const selected = current === item.id;
          return (
            <li key={item.id}>
              <button
                type="button"
                onClick={() => {
                  setCurrent(item.id);
                  onSelect?.(item.id);
                }}
                className={`flex w-full items-center justify-between px-3 py-1.5 text-left text-sm transition-colors ${
                  selected
                    ? "bg-accent-mute/30 text-accent"
                    : "text-ink-muted hover:bg-canvas-raised hover:text-ink"
                }`}
              >
                <span>{item.label}</span>
                {item.hotkey && (
                  <kbd className="rounded border border-line bg-canvas-inset px-1 text-2xs text-ink-subtle">
                    {item.hotkey}
                  </kbd>
                )}
              </button>
            </li>
          );
        })}
      </ul>

      <div className="mt-auto border-t border-line px-3 py-2 text-2xs text-ink-subtle">
        <div>orama-system v0.9.9.8</div>
        <div className="mt-1">RC-1 prep</div>
      </div>
    </nav>
  );
}
