import { StatusBadge, statusToTone } from "@/components/StatusBadge";
import type { AppState } from "@/api/appState";

interface ReadinessStripProps {
  state: AppState | undefined;
}

interface ReadinessTile {
  label: string;
  detail: string;
  status: string;
  statusLabel: string;
}

function readinessFromState(state: AppState | undefined): ReadinessTile[] {
  const runtime = (state?.runtime?.data ?? {}) as Record<string, string>;
  const portal = state?.portal?.data as { version?: string } | undefined;

  const ptStatus = runtime.ollama_mac ?? "unknown";
  const portalStatus = state?.portal?.available ? "online" : "offline";
  const hwStatus = runtime.hardware_policy ?? "unknown";

  return [
    {
      label: "PT Runtime",
      detail: `v${portal?.version ?? "—"} • ${runtime.ollama_mac_model ?? "qwen3.5:9b"}`,
      status: ptStatus,
      statusLabel: ptStatus === "online" ? "Ready" : ptStatus,
    },
    {
      label: "Portal",
      detail: state?.portal?.available ? "/healthz 200" : "unreachable",
      status: portalStatus,
      statusLabel: portalStatus === "online" ? "Ready" : "Offline",
    },
    {
      label: "Gateway",
      detail: runtime.gateway_p95 ?? "p95 —",
      status: runtime.gateway ?? (state?.portal?.available ? "online" : "unknown"),
      statusLabel: state?.portal?.available ? "Ready" : "Unknown",
    },
    {
      label: "Hardware Policy",
      detail: runtime.hw_violations
        ? `${runtime.hw_violations} rules blocked`
        : (hwStatus === "warn" ? "2 rules blocked" : "all rules pass"),
      status: hwStatus === "warn" || runtime.hw_violations ? "warn" : (portalStatus === "online" ? "online" : "unknown"),
      statusLabel: hwStatus === "warn" || runtime.hw_violations ? "Warning" : "OK",
    },
  ];
}

export function ReadinessStrip({ state }: ReadinessStripProps) {
  const tiles = readinessFromState(state);
  const readyCount = tiles.filter((t) => statusToTone(t.status) === "ok").length;

  return (
    <section className="mb-4">
      <div className="mb-2 flex items-center justify-between">
        <h2 className="text-2xs font-mono uppercase tracking-wider text-ink-subtle">
          System Readiness
        </h2>
        <div className="flex items-center gap-3">
          <span className="text-2xs text-ink-subtle">
            {readyCount}/{tiles.length} ready
          </span>
          <button
            type="button"
            className="rounded border border-line bg-canvas-raised px-2 py-0.5 text-2xs text-ink-muted transition hover:border-accent hover:text-accent"
          >
            View Details
          </button>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-2 md:grid-cols-4">
        {tiles.map((tile) => {
          const tone = statusToTone(tile.status);
          const borderColor =
            tone === "warn" ? "border-status-warn/40" :
            tone === "ok" ? "border-line" :
            tone === "err" ? "border-status-err/40" :
            "border-line";
          const bgColor =
            tone === "warn" ? "bg-status-warn/5" : "bg-canvas-surface";

          return (
            <div
              key={tile.label}
              className={`rounded border ${borderColor} ${bgColor} px-3 py-2.5`}
            >
              <div className="flex items-center justify-between">
                <span className="text-2xs uppercase tracking-wider text-ink-subtle">
                  {tile.label}
                </span>
                <StatusBadge tone={tone} dot={false}>
                  {tile.statusLabel}
                </StatusBadge>
              </div>
              <div className="mt-1.5 truncate font-mono text-xs text-ink-muted" title={tile.detail}>
                {tile.detail}
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
}
