interface NavLeftProps {
  active?: string;
  onSelect?: (id: string) => void;
}

// Simple inline SVG icons — no external dep
function IconCommand() {
  return (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden>
      <rect x="2" y="2" width="5" height="5" rx="1" stroke="currentColor" strokeWidth="1.4"/>
      <rect x="9" y="2" width="5" height="5" rx="1" stroke="currentColor" strokeWidth="1.4"/>
      <rect x="2" y="9" width="5" height="5" rx="1" stroke="currentColor" strokeWidth="1.4"/>
      <rect x="9" y="9" width="5" height="5" rx="1" stroke="currentColor" strokeWidth="1.4"/>
    </svg>
  );
}
function IconComposer() {
  return (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden>
      <path d="M2 11L5 8l3 3 4-5" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round"/>
      <circle cx="13" cy="3" r="1.5" stroke="currentColor" strokeWidth="1.4"/>
    </svg>
  );
}
function IconRuns() {
  return (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden>
      <path d="M2 4h12M2 8h8M2 12h10" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round"/>
    </svg>
  );
}
function IconRouting() {
  return (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden>
      <circle cx="3" cy="4" r="1.5" stroke="currentColor" strokeWidth="1.4"/>
      <circle cx="13" cy="4" r="1.5" stroke="currentColor" strokeWidth="1.4"/>
      <circle cx="8" cy="12" r="1.5" stroke="currentColor" strokeWidth="1.4"/>
      <path d="M4.4 4h7.2M3 5.2L7.2 11M13 5.2L8.8 11" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round"/>
    </svg>
  );
}
function IconArtifacts() {
  return (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden>
      <path d="M3 2h7l3 3v9a1 1 0 01-1 1H3a1 1 0 01-1-1V3a1 1 0 011-1z" stroke="currentColor" strokeWidth="1.4" strokeLinejoin="round"/>
      <path d="M10 2v4h4" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" strokeLinejoin="round"/>
      <path d="M5 9h6M5 12h4" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round"/>
    </svg>
  );
}
function IconSettings() {
  return (
    <svg width="14" height="14" viewBox="0 0 16 16" fill="none" aria-hidden>
      <circle cx="8" cy="8" r="2.5" stroke="currentColor" strokeWidth="1.4"/>
      <path d="M8 1v2M8 13v2M1 8h2M13 8h2M3.1 3.1l1.4 1.4M11.5 11.5l1.4 1.4M12.9 3.1l-1.4 1.4M4.5 11.5l-1.4 1.4" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round"/>
    </svg>
  );
}
function IconDocs() {
  return (
    <svg width="14" height="14" viewBox="0 0 16 16" fill="none" aria-hidden>
      <path d="M3 2h7l3 3v9a1 1 0 01-1 1H3a1 1 0 01-1-1V3a1 1 0 011-1z" stroke="currentColor" strokeWidth="1.4" strokeLinejoin="round"/>
      <path d="M10 2v4h4" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" strokeLinejoin="round"/>
      <path d="M5 8h6M5 11h4" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round"/>
    </svg>
  );
}

const NAV_ITEMS = [
  { id: "command", label: "Command", Icon: IconCommand },
  { id: "composer", label: "Composer", Icon: IconComposer },
  { id: "runs", label: "Runs", Icon: IconRuns },
  { id: "routing", label: "Routing", Icon: IconRouting },
  { id: "artifacts", label: "Artifacts", Icon: IconArtifacts },
];

const FOOTER_ITEMS = [
  { id: "settings", label: "Settings", Icon: IconSettings },
  { id: "docs", label: "Docs", Icon: IconDocs },
];

export function NavLeft({ active = "command", onSelect }: NavLeftProps) {
  return (
    <nav className="flex h-full w-44 flex-col border-r border-line bg-canvas-surface">
      {/* Main nav */}
      <ul className="flex flex-1 flex-col pt-2">
        {NAV_ITEMS.map(({ id, label, Icon }) => {
          const selected = active === id;
          return (
            <li key={id}>
              <button
                type="button"
                onClick={() => onSelect?.(id)}
                className={`flex w-full items-center gap-2.5 px-3 py-2 text-left text-sm transition-colors ${
                  selected
                    ? "border-l-2 border-accent bg-accent/8 text-accent"
                    : "border-l-2 border-transparent text-ink-muted hover:bg-canvas-raised hover:text-ink"
                }`}
              >
                <Icon />
                <span className={selected ? "font-medium" : ""}>{label}</span>
              </button>
            </li>
          );
        })}
      </ul>

      {/* Footer: settings + docs + version */}
      <div className="border-t border-line">
        {FOOTER_ITEMS.map(({ id, label, Icon }) => (
          <button
            key={id}
            type="button"
            onClick={() => onSelect?.(id)}
            className="flex w-full items-center gap-2.5 px-3 py-2 text-left text-xs text-ink-subtle transition-colors hover:text-ink-muted"
          >
            <Icon />
            <span>{label}</span>
          </button>
        ))}
        <div className="px-3 py-2 text-2xs font-mono text-ink-subtle">v0.9.9.8</div>
      </div>
    </nav>
  );
}
