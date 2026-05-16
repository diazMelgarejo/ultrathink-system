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

export function ArtifactsPanel({ artifacts }: ArtifactsPanelProps) {
  return (
    <section className="mb-4">
      <header className="mb-2 flex items-baseline justify-between">
        <h2 className="text-2xs font-mono uppercase tracking-wider text-ink-subtle">
          Latest Artifacts
        </h2>
        <span className="text-2xs text-ink-subtle">
          {artifacts.length} item{artifacts.length === 1 ? "" : "s"}
        </span>
      </header>

      {artifacts.length === 0 ? (
        <div className="rounded border border-line bg-canvas-surface px-4 py-6 text-center text-sm text-ink-muted">
          No artifacts yet. Completed jobs produce summaries and refs.
        </div>
      ) : (
        <ul className="grid grid-cols-1 gap-2 md:grid-cols-2">
          {artifacts.map((a, i) => (
            <li
              key={a.artifact_id ?? a.id ?? i}
              className="rounded border border-line bg-canvas-surface p-3 transition hover:border-accent/40"
            >
              <div className="flex items-center justify-between">
                <span className="truncate text-sm font-semibold text-ink" title={a.name}>
                  {a.name ?? "(unnamed)"}
                </span>
                <span className="text-2xs text-ink-subtle">{formatBytes(a.size_bytes)}</span>
              </div>
              <div className="mt-1 flex flex-wrap items-center gap-2 text-2xs text-ink-muted">
                <span className="font-mono">{a.kind ?? "blob"}</span>
                {a.job_id && (
                  <span className="font-mono text-ink-subtle">job {a.job_id}</span>
                )}
                {a.url && (
                  <a
                    href={a.url}
                    target="_blank"
                    rel="noreferrer noopener"
                    className="ml-auto text-accent hover:text-accent-hover"
                  >
                    open ↗
                  </a>
                )}
              </div>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
