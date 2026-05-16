import { useState } from "react";
import type { Artifact } from "@/api/artifacts";

interface ArtifactsPanelProps {
  artifacts: Artifact[];
}

function formatBytes(n: number | undefined): string {
  if (n == null) return "—";
  if (n < 1024) return `${n} B`;
  if (n < 1024 * 1024) return `${(n / 1024).toFixed(1)} KB`;
  return `${(n / 1024 / 1024).toFixed(1)} MB`;
}

function CopyButton({ value }: { value: string }) {
  const [copied, setCopied] = useState(false);

  function handleCopy() {
    void navigator.clipboard.writeText(value).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 1200);
    });
  }

  return (
    <button
      type="button"
      onClick={handleCopy}
      title={`Copy ${value}`}
      className="ml-1 rounded px-1 py-0.5 text-2xs text-ink-subtle transition hover:bg-canvas-raised hover:text-ink"
    >
      {copied ? "✓" : "⎘"}
    </button>
  );
}

export function ArtifactsPanel({ artifacts }: ArtifactsPanelProps) {
  return (
    <section className="mb-4">
      <header className="mb-2 flex items-center justify-between">
        <h2 className="text-2xs font-mono uppercase tracking-wider text-ink-subtle">
          Artifacts
        </h2>
        <div className="flex items-center gap-3">
          <span className="text-2xs text-ink-subtle">
            {artifacts.length} item{artifacts.length === 1 ? "" : "s"}
          </span>
          <button
            type="button"
            className="rounded border border-line bg-canvas-raised px-2 py-0.5 text-2xs text-ink-muted transition hover:text-ink"
          >
            View All Artifacts
          </button>
        </div>
      </header>

      {/* Redaction notice */}
      <div className="mb-2 flex items-center justify-between rounded border border-status-warn/30 bg-status-warn/5 px-3 py-2">
        <span className="text-2xs text-status-warn">
          All artifacts pass through the redaction gateway. Sensitive fields marked with{" "}
          <span className="font-mono">[REDACTED]</span>.
        </span>
        <button
          type="button"
          className="ml-4 shrink-0 text-2xs text-accent underline hover:text-accent-hover"
        >
          Manage Redaction Policies
        </button>
      </div>

      {artifacts.length === 0 ? (
        <div className="rounded border border-line bg-canvas-surface px-4 py-6 text-center text-sm text-ink-muted">
          No artifacts yet. Completed jobs produce summaries and refs.
        </div>
      ) : (
        <ul className="space-y-1.5">
          {artifacts.map((a, i) => {
            const refId = a.artifact_id ?? a.id ?? `art-${i}`;
            return (
              <li
                key={refId}
                className="rounded border border-line bg-canvas-surface p-3 transition hover:border-accent/30"
              >
                <div className="flex items-start justify-between gap-2">
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-1">
                      <span className="truncate text-sm font-semibold text-ink" title={a.name}>
                        {a.name ?? "(unnamed)"}
                      </span>
                    </div>
                    {a.summary && (
                      <div className="mt-0.5 line-clamp-1 text-xs text-ink-muted">{a.summary}</div>
                    )}
                  </div>
                  <div className="shrink-0 text-2xs text-ink-subtle">{formatBytes(a.size_bytes)}</div>
                </div>

                <div className="mt-1.5 flex flex-wrap items-center gap-2">
                  <span className="rounded bg-canvas-raised px-1.5 py-0.5 font-mono text-2xs text-ink-subtle">
                    {a.kind ?? "blob"}
                  </span>
                  {a.job_id && (
                    <span className="font-mono text-2xs text-ink-subtle">job {a.job_id}</span>
                  )}
                  {/* Ref ID with copy */}
                  <span className="ml-auto flex items-center font-mono text-2xs text-ink-subtle">
                    {refId}
                    <CopyButton value={refId} />
                  </span>
                  {a.url && (
                    <a
                      href={a.url}
                      target="_blank"
                      rel="noreferrer noopener"
                      className="text-2xs text-accent hover:text-accent-hover"
                    >
                      open ↗
                    </a>
                  )}
                </div>
              </li>
            );
          })}
        </ul>
      )}
    </section>
  );
}
