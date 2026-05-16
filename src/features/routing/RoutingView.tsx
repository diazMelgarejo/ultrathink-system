/**
 * Routing — hardware policy + model routing table viewer.
 * Phase 5 placeholder: shows current routing policy summary from app state.
 */
import { StatusBadge } from "@/components/StatusBadge";
import type { AppState } from "@/api/appState";

interface RoutingViewProps {
  state: AppState | undefined;
}

const ROUTING_PRECEDENCE = [
  { level: "Session", description: "Per-session model_hint override (from /run request body)" },
  { level: "Run", description: "Per-job preferred_device + backend_hint from SwarmRequest" },
  { level: "Policy", description: "Hardware policy JSON schema (agate / perpetua-core)" },
];

const FALLBACK_CHAIN = [
  { model: "ollama/qwen3.5:9b-nvfp4", device: "mac", status: "primary" },
  { model: "lmstudio-win/qwen3.5-27b-*", device: "win-lan", status: "launchable" },
  { model: "openrouter/nvidia/nemotron-3-super-120b-a12b:free", device: "cloud", status: "fallback-1" },
  { model: "openrouter/minimax/minimax-m2.5:free", device: "cloud", status: "fallback-2" },
  { model: "openrouter/deepseek/deepseek-v4-5:free", device: "cloud", status: "fallback-3" },
  { model: "google/gemini-2.5-flash", device: "cloud", status: "fallback-4 (last)" },
];

export function RoutingView({ state }: RoutingViewProps) {
  const runtime = (state?.runtime?.data ?? {}) as Record<string, string>;
  const lmStatus = runtime.lmstudio_win ?? "unknown";
  const lmOnline = lmStatus === "online";
  const fallbackChain = lmOnline
    ? FALLBACK_CHAIN
    : FALLBACK_CHAIN.filter((row) => row.model !== "lmstudio-win/qwen3.5-27b-*");

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-sm font-semibold text-ink">Routing</h1>
        <p className="mt-0.5 text-xs text-ink-muted">
          Hardware policy routing table and model fallback chain.
        </p>
      </div>

      {/* Routing Precedence */}
      <section>
        <h2 className="mb-2 text-2xs font-mono uppercase tracking-wider text-ink-subtle">
          Routing Precedence
        </h2>
        <div className="overflow-hidden rounded border border-line bg-canvas-surface">
          <table className="w-full border-collapse text-sm">
            <thead className="bg-canvas-raised">
              <tr className="border-b border-line">
                <th className="px-3 py-1.5 text-left text-2xs font-mono uppercase tracking-wider text-ink-subtle">Level</th>
                <th className="px-3 py-1.5 text-left text-2xs font-mono uppercase tracking-wider text-ink-subtle">Description</th>
                <th className="px-3 py-1.5 text-left text-2xs font-mono uppercase tracking-wider text-ink-subtle">Priority</th>
              </tr>
            </thead>
            <tbody>
              {ROUTING_PRECEDENCE.map((row, i) => (
                <tr key={row.level} className="border-b border-line last:border-b-0">
                  <td className="px-3 py-2 font-mono text-xs font-semibold text-accent">{row.level}</td>
                  <td className="px-3 py-2 text-xs text-ink-muted">{row.description}</td>
                  <td className="px-3 py-2">
                    <StatusBadge tone={i === 0 ? "ok" : i === 1 ? "info" : "neutral"} dot={false}>
                      {i + 1}
                    </StatusBadge>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* Fallback Chain */}
      <section>
        <h2 className="mb-2 text-2xs font-mono uppercase tracking-wider text-ink-subtle">
          OpenRouter Fallback Chain
        </h2>
        <div className="overflow-hidden rounded border border-line bg-canvas-surface">
          <table className="w-full border-collapse text-sm">
            <thead className="bg-canvas-raised">
              <tr className="border-b border-line">
                <th className="px-3 py-1.5 text-left text-2xs font-mono uppercase tracking-wider text-ink-subtle">Model</th>
                <th className="px-3 py-1.5 text-left text-2xs font-mono uppercase tracking-wider text-ink-subtle">Device</th>
                <th className="px-3 py-1.5 text-left text-2xs font-mono uppercase tracking-wider text-ink-subtle">Role</th>
              </tr>
            </thead>
            <tbody>
              {fallbackChain.map((row) => (
                <tr key={row.model} className="border-b border-line last:border-b-0 hover:bg-canvas-raised/50">
                  <td className="px-3 py-2 font-mono text-xs text-ink">{row.model}</td>
                  <td className="px-3 py-2 font-mono text-xs text-ink-subtle">{row.device}</td>
                  <td className="px-3 py-2">
                    <StatusBadge
                      tone={row.status === "primary" || row.status === "launchable" ? "ok" : "neutral"}
                      dot={false}
                    >
                      {row.status}
                    </StatusBadge>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p className="mt-1.5 text-2xs text-ink-subtle">
          Configured in <span className="font-mono">~/.openclaw/openclaw.json</span> · Primary must be <span className="font-mono">ollama/*</span> or <span className="font-mono">lmstudio/*</span>
        </p>
        <p className="mt-0.5 text-2xs text-ink-subtle">
          Windows LM Studio is <span className="font-mono">{lmStatus}</span> and may be launched when LAN availability is online.
        </p>
      </section>

      {/* Live status */}
      <section>
        <h2 className="mb-2 text-2xs font-mono uppercase tracking-wider text-ink-subtle">
          Live Runtime Status
        </h2>
        <div className="grid grid-cols-2 gap-2 md:grid-cols-3">
          {Object.entries(runtime).map(([k, v]) => (
            <div key={k} className="rounded border border-line bg-canvas-surface px-3 py-2">
              <div className="text-2xs font-mono uppercase tracking-wider text-ink-subtle">{k}</div>
              <div className="mt-1 truncate font-mono text-xs text-ink">{String(v)}</div>
            </div>
          ))}
          {Object.keys(runtime).length === 0 && (
            <div className="col-span-3 text-sm text-ink-muted">
              Runtime data unavailable — portal_server.py offline.
            </div>
          )}
        </div>
      </section>
    </div>
  );
}
