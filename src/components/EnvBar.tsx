import { StatusBadge, statusToTone } from "./StatusBadge";
import type { AppState } from "@/api/appState";

interface EnvBarProps {
  state: AppState | undefined;
  isFetching?: boolean;
}

function summarizeSection(section: AppState["portal"] | undefined): string {
  if (!section) return "—";
  if (!section.available) return "offline";
  return "online";
}

export function EnvBar({ state, isFetching = false }: EnvBarProps) {
  const portalData = state?.portal?.data as
    | { version?: string; env?: string; region?: string; stage?: string }
    | undefined;

  const portalStatus = summarizeSection(state?.portal);
  const runtimeStatus = summarizeSection(state?.runtime);
  const modelsStatus = summarizeSection(state?.models);

  return (
    <header className="flex items-center gap-4 border-b border-line bg-canvas-surface px-4 py-2 text-xs">
      {/* Brand */}
      <div className="flex items-center gap-2">
        <span className="font-mono text-sm font-semibold tracking-tight text-accent">
          orama
        </span>
        <span className="text-2xs text-ink-subtle">operator console</span>
      </div>

      {/* Env triple */}
      <div className="flex items-center gap-3 border-l border-line pl-4 text-ink-muted">
        <span>
          env <span className="font-mono text-ink">{portalData?.env ?? "—"}</span>
        </span>
        <span>
          region <span className="font-mono text-ink">{portalData?.region ?? "—"}</span>
        </span>
        <span>
          stage <span className="font-mono text-ink">{portalData?.stage ?? "—"}</span>
        </span>
        <span>
          v <span className="font-mono text-ink">{portalData?.version ?? "—"}</span>
        </span>
      </div>

      {/* API status pills */}
      <div className="ml-auto flex items-center gap-2">
        <StatusBadge tone={statusToTone(portalStatus)}>portal {portalStatus}</StatusBadge>
        <StatusBadge tone={statusToTone(runtimeStatus)}>runtime {runtimeStatus}</StatusBadge>
        <StatusBadge tone={statusToTone(modelsStatus)}>models {modelsStatus}</StatusBadge>
        {isFetching && (
          <StatusBadge tone="info" dot={false}>
            <span className="animate-pulse">syncing…</span>
          </StatusBadge>
        )}
      </div>
    </header>
  );
}
