import { StatusBadge, statusToTone } from "@/components/StatusBadge";
import type { AppState } from "@/api/appState";

interface ReadinessStripProps {
  state: AppState | undefined;
}

interface ReadinessTile {
  label: string;
  value: string;
  status: string;
}

/**
 * Build the readiness tiles from the aggregated app state.
 *
 * Note: `runtime.perpetua_tools` / `runtime.perpetua_tools_endpoint` may not be
 * populated by portal_server.py yet — the Perplexity-Tools tile will show
 * "unknown" until the backend wires those fields.
 */
function readinessFromState(state: AppState | undefined): ReadinessTile[] {
  const runtime = (state?.runtime?.data ?? {}) as Record<string, string>;
  const models = (state?.models?.data ?? {}) as Record<string, string>;

  return [
    {
      label: "Ollama (Mac)",
      value: models.mac_primary ?? "—",
      status: runtime.ollama_mac ?? "unknown",
    },
    {
      label: "LM Studio (Win)",
      value: models.win_primary ?? "—",
      status: runtime.lmstudio_win ?? "unknown",
    },
    {
      label: "OpenRouter",
      value: models.openrouter_primary ?? "—",
      status: runtime.openrouter ?? "unknown",
    },
    {
      label: "Perplexity-Tools",
      value: runtime.perpetua_tools_endpoint ?? "—",
      status: runtime.perpetua_tools ?? "unknown",
    },
    {
      label: "Gateway",
      value: state?.portal?.available ? "ok" : "—",
      status: state?.portal?.available ? "online" : "offline",
    },
  ];
}

export function ReadinessStrip({ state }: ReadinessStripProps) {
  const tiles = readinessFromState(state);

  return (
    <section className="mb-4">
      <div className="mb-2 flex items-baseline justify-between">
        <h2 className="text-2xs font-mono uppercase tracking-wider text-ink-subtle">
          Readiness
        </h2>
        <span className="text-2xs text-ink-subtle">
          {tiles.filter((t) => statusToTone(t.status) === "ok").length} / {tiles.length} ready
        </span>
      </div>
      <div className="grid grid-cols-2 gap-2 md:grid-cols-5">
        {tiles.map((tile) => (
          <div
            key={tile.label}
            className="rounded border border-line bg-canvas-surface px-3 py-2"
          >
            <div className="flex items-center justify-between">
              <span className="text-2xs uppercase tracking-wider text-ink-subtle">
                {tile.label}
              </span>
              <StatusBadge tone={statusToTone(tile.status)} dot={false}>
                {tile.status}
              </StatusBadge>
            </div>
            <div className="mt-1 truncate font-mono text-xs text-ink" title={tile.value}>
              {tile.value}
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}
