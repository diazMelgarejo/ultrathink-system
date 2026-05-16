import { StatusBadge, statusToTone } from "./StatusBadge";
import type { AppState } from "@/api/appState";

interface EnvBarProps {
  state: AppState | undefined;
  isFetching?: boolean;
}

function IconSearch() {
  return (
    <svg width="15" height="15" viewBox="0 0 16 16" fill="none" aria-hidden>
      <circle cx="7" cy="7" r="4.5" stroke="currentColor" strokeWidth="1.4"/>
      <path d="M10.5 10.5L14 14" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round"/>
    </svg>
  );
}
function IconBell() {
  return (
    <svg width="15" height="15" viewBox="0 0 16 16" fill="none" aria-hidden>
      <path d="M8 2a5 5 0 00-5 5v3l-1 1.5h12L13 10V7a5 5 0 00-5-5z" stroke="currentColor" strokeWidth="1.4" strokeLinejoin="round"/>
      <path d="M6.5 13.5a1.5 1.5 0 003 0" stroke="currentColor" strokeWidth="1.4"/>
    </svg>
  );
}

export function EnvBar({ state, isFetching = false }: EnvBarProps) {
  const portalData = state?.portal?.data as
    | { version?: string; env?: string; region?: string; stage?: string }
    | undefined;

  const portalStatus = state?.portal?.available ? "online" : "offline";
  const env = portalData?.env ?? "dev";
  const envLabel = env.toUpperCase();
  const region = portalData?.region ?? "lan";
  const apiHealthy = state?.runtime?.available ?? false;

  return (
    <header className="flex items-center gap-4 border-b border-line bg-canvas-surface px-4 py-2 text-xs">
      {/* Brand */}
      <div className="flex items-center gap-2">
        <span className="font-mono text-sm font-bold tracking-tight text-accent">orama</span>
        <span className="text-2xs text-ink-subtle">Command Center</span>
      </div>

      {/* Divider */}
      <div className="h-4 w-px bg-line" />

      {/* Env pill */}
      <div className="flex items-center gap-3">
        <StatusBadge tone={envLabel === "PRODUCTION" || envLabel === "PROD" ? "ok" : statusToTone(portalStatus)} dot>
          {envLabel}
        </StatusBadge>
        <span className="text-ink-subtle">
          Region <span className="font-mono text-ink">{region}</span>
        </span>
        <span className="text-ink-subtle">
          API{" "}
          <span className={apiHealthy ? "text-status-ok" : "text-status-err"}>
            {apiHealthy ? "Healthy" : "Offline"}
          </span>
        </span>
        {isFetching && (
          <span className="animate-pulse text-2xs text-ink-subtle">syncing…</span>
        )}
      </div>

      {/* Spacer */}
      <div className="flex-1" />

      {/* Action icons + avatar */}
      <div className="flex items-center gap-2 text-ink-subtle">
        <button type="button" className="rounded p-1 hover:bg-canvas-raised hover:text-ink transition-colors" aria-label="Search">
          <IconSearch />
        </button>
        <button type="button" className="rounded p-1 hover:bg-canvas-raised hover:text-ink transition-colors" aria-label="Notifications">
          <IconBell />
        </button>
        <div className="h-4 w-px bg-line mx-1" />
        {/* User avatar */}
        <div className="flex h-6 w-6 items-center justify-center rounded-full bg-accent/20 text-2xs font-semibold text-accent">
          LC
        </div>
      </div>
    </header>
  );
}
