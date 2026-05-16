import { useEffect, useMemo, useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { StatusBadge, statusToTone } from "@/components/StatusBadge";
import type { JobSummary } from "@/api/appState";
import { cancelJob, replayJob } from "@/api/jobs";

interface RunsTableProps {
  jobs: JobSummary[];
}

const PAGE_SIZE = 7;
const STALE_AFTER_MS = 5 * 60 * 1000;

function CopyButton({ value }: { value: string }) {
  const [copied, setCopied] = useState(false);
  return (
    <button
      type="button"
      onClick={() => {
        void navigator.clipboard.writeText(value).then(() => {
          setCopied(true);
          setTimeout(() => setCopied(false), 1200);
        });
      }}
      title={`Copy ${value}`}
      className="ml-1 rounded px-0.5 py-0.5 text-2xs text-ink-subtle opacity-0 transition group-hover:opacity-100 hover:bg-canvas-raised hover:text-ink"
    >
      {copied ? "✓" : "⎘"}
    </button>
  );
}

function parseTimestamp(value: unknown): number | null {
  if (value == null) return null;
  if (value instanceof Date) return value.getTime();
  if (typeof value === "number" && Number.isFinite(value)) {
    return value < 1e12 ? value * 1000 : value;
  }
  const text = String(value).trim();
  if (!text) return null;
  if (/^\d+$/.test(text)) {
    const numeric = Number(text);
    return numeric < 1e12 ? numeric * 1000 : numeric;
  }
  const parsed = Date.parse(text);
  return Number.isNaN(parsed) ? null : parsed;
}

function formatDuration(ms: number): string {
  const totalSeconds = Math.max(0, Math.floor(ms / 1000));
  const hours = Math.floor(totalSeconds / 3600);
  const minutes = Math.floor((totalSeconds % 3600) / 60);
  const seconds = totalSeconds % 60;
  if (hours > 0) {
    return `${hours}h ${minutes.toString().padStart(2, "0")}m`;
  }
  if (minutes > 0) {
    return `${minutes}m ${seconds.toString().padStart(2, "0")}s`;
  }
  return `${seconds}s`;
}

function isActiveStatus(status: string | undefined): boolean {
  const s = String(status || "").toLowerCase();
  return ["queued", "waiting", "running", "in_progress", "active"].includes(s);
}

function getDispatchTime(job: JobSummary): number | null {
  const metadata = (job.metadata ?? {}) as Record<string, unknown>;
  return parseTimestamp(metadata.dispatch_at ?? job.updated_at ?? job.created_at);
}

function estimateWorkerLoad(job: JobSummary): { count: number; scope: "local" | "online" } {
  const metadata = (job.metadata ?? {}) as Record<string, unknown>;
  const explicitCount = Number(metadata.worker_count ?? metadata.workers ?? metadata.agent_count);
  if (Number.isFinite(explicitCount) && explicitCount > 0) {
    return {
      count: Math.min(9, Math.max(1, Math.round(explicitCount))),
      scope: String(metadata.worker_scope ?? "").toLowerCase() === "online" ? "online" : "local",
    };
  }

  const backend = String(job.backend ?? "").toLowerCase();
  const device = String(job.device ?? "").toLowerCase();
  const mode = String(metadata.mode ?? metadata.execution_mode ?? "").toLowerCase();
  const executors = Number(metadata.executors ?? metadata.local_executors ?? metadata.executor_count);

  if (backend.startsWith("openrouter/") || mode.includes("online") || device === "shared") {
    return { count: 9, scope: "online" };
  }
  if (
    mode.includes("mac+windows") ||
    mode.includes("mac_windows") ||
    mode.includes("dual") ||
    (backend.includes("lmstudio-mac") && backend.includes("lmstudio-win"))
  ) {
    return { count: 2, scope: "local" };
  }
  if (Number.isFinite(executors) && executors > 0) {
    return { count: Math.min(5, Math.max(1, Math.round(executors) + 1)), scope: "local" };
  }
  if (backend.startsWith("lmstudio-win/") || backend.startsWith("lmstudio-mac/") || backend.startsWith("ollama/") || device === "mac" || device === "windows") {
    return { count: 1, scope: "local" };
  }
  return { count: 1, scope: "local" };
}

function JobStatusBadge({ status, stale }: { status: string | undefined; stale?: boolean }) {
  const tone = stale ? "err" : statusToTone(status);
  const label = status ?? "unknown";
  return <StatusBadge tone={tone} dot className={stale ? "animate-pulse" : ""}>{label}</StatusBadge>;
}

function ActionMenu({ status, onCancel, onReplay, isPending }: {
  jobId?: string;
  status: string | undefined;
  onCancel: () => void;
  onReplay: () => void;
  isPending: boolean;
}) {
  const [open, setOpen] = useState(false);
  const s = (status ?? "").toLowerCase();
  const canCancel = ["queued", "running", "in_progress", "active"].includes(s);
  const canReplay = ["completed", "failed", "rejected"].includes(s);

  return (
    <div className="relative">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="rounded px-1.5 py-0.5 text-ink-subtle transition hover:bg-canvas-raised hover:text-ink"
        aria-label="Job actions"
      >
        ⋯
      </button>
      {open && (
        <>
          {/* Backdrop */}
          <div
            className="fixed inset-0 z-10"
            onClick={() => setOpen(false)}
          />
          <div className="absolute right-0 z-20 mt-1 w-28 rounded border border-line bg-canvas-raised shadow-raised">
            <button
              type="button"
              disabled={!canCancel || isPending}
              onClick={() => { setOpen(false); onCancel(); }}
              className="flex w-full items-center px-3 py-1.5 text-xs text-ink-muted transition hover:bg-canvas-inset hover:text-status-err disabled:opacity-40"
            >
              Cancel
            </button>
            <button
              type="button"
              disabled={!canReplay || isPending}
              onClick={() => { setOpen(false); onReplay(); }}
              className="flex w-full items-center px-3 py-1.5 text-xs text-ink-muted transition hover:bg-canvas-inset hover:text-accent disabled:opacity-40"
            >
              Replay
            </button>
          </div>
        </>
      )}
    </div>
  );
}

export function RunsTable({ jobs }: RunsTableProps) {
  const queryClient = useQueryClient();
  const [page, setPage] = useState(0);
  const [now, setNow] = useState(() => Date.now());

  useEffect(() => {
    const timer = window.setInterval(() => setNow(Date.now()), 30_000);
    return () => window.clearInterval(timer);
  }, []);

  const cancel = useMutation({
    mutationFn: (jobId: string) => cancelJob(jobId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["appState"] }),
  });
  const replay = useMutation({
    mutationFn: (jobId: string) => replayJob(jobId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["appState"] }),
  });

  const totalPages = Math.max(1, Math.ceil(jobs.length / PAGE_SIZE));
  const safePage = Math.min(page, totalPages - 1);
  const pageJobs = jobs.slice(safePage * PAGE_SIZE, safePage * PAGE_SIZE + PAGE_SIZE);

  const startNum = jobs.length === 0 ? 0 : safePage * PAGE_SIZE + 1;
  const endNum = Math.min(safePage * PAGE_SIZE + PAGE_SIZE, jobs.length);

  const rows = useMemo(
    () =>
      pageJobs.map((job, index) => {
        const id = job.job_id ?? job.id ?? `row-${index}`;
        const dispatchTime = getDispatchTime(job);
        const elapsedMs = dispatchTime == null ? null : Math.max(0, now - dispatchTime);
        const stale = Boolean(elapsedMs != null && elapsedMs > STALE_AFTER_MS && isActiveStatus(job.status));
        const workers = estimateWorkerLoad(job);
        return {
          job,
          id,
          dispatchTime,
          elapsedMs,
          stale,
          workers,
        };
      }),
    [now, pageJobs],
  );

  return (
    <section className="mb-4">
      <header className="mb-2 flex items-center justify-between">
        <h2 className="text-2xs font-mono uppercase tracking-wider text-ink-subtle">
          Runs
        </h2>
        <div className="flex items-center gap-3">
          <span className="text-2xs text-ink-subtle">
            {jobs.length === 0
              ? "0 jobs"
              : `showing ${startNum}–${endNum} of ${jobs.length}`}
          </span>
          <button
            type="button"
            className="rounded border border-line bg-canvas-raised px-2 py-0.5 text-2xs text-ink-muted transition hover:text-ink"
          >
            View All Runs
          </button>
        </div>
      </header>

      <div className="overflow-auto rounded border border-line bg-canvas-surface">
        {pageJobs.length === 0 ? (
          <div className="px-4 py-8 text-center text-sm text-ink-muted">
            No jobs yet. Compose a swarm to launch one.
          </div>
        ) : (
          <table className="w-full border-collapse text-sm">
            <thead className="sticky top-0 bg-canvas-raised">
              <tr className="border-b border-line">
                {["Run ID", "Objective", "Status", "Workers", "Started", "Duration", ""].map((h) => (
                  <th
                    key={h}
                    className="px-3 py-1.5 text-left text-2xs font-mono uppercase tracking-wider text-ink-subtle"
                  >
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {rows.map(({ job: j, id, dispatchTime, elapsedMs, stale, workers }) => {
                return (
                  <tr
                    key={id}
                    className={`group border-b border-line last:border-b-0 hover:bg-canvas-raised/50 ${
                      stale ? "border-status-err/40 bg-status-err/5" : ""
                    }`}
                  >
                    {/* Run ID */}
                    <td className="px-3 py-2">
                      <div className="flex items-center font-mono text-xs text-ink-muted">
                        <span className="truncate max-w-[96px]" title={id}>{id}</span>
                        <CopyButton value={id} />
                      </div>
                    </td>
                    {/* Objective / prompt */}
                    <td className="px-3 py-2">
                      <span
                        className="line-clamp-1 max-w-[240px] text-xs text-ink"
                        title={j.prompt ?? j.intent}
                      >
                        {j.prompt ?? j.intent ?? "—"}
                      </span>
                    </td>
                    {/* Status */}
                    <td className="px-3 py-2">
                      <JobStatusBadge status={j.status} stale={stale} />
                    </td>
                    {/* Workers */}
                    <td className="px-3 py-2">
                      <span className={`font-mono text-xs ${workers.scope === "online" ? "text-status-info" : "text-ink-subtle"}`}>
                        {workers.count} {workers.scope}
                      </span>
                    </td>
                    {/* Started */}
                    <td className="px-3 py-2">
                      <span className="font-mono text-xs text-ink-subtle">
                        {dispatchTime
                          ? new Date(dispatchTime).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
                          : "—"}
                      </span>
                    </td>
                    {/* Duration */}
                    <td className="px-3 py-2">
                      <span className={`font-mono text-xs ${stale ? "text-status-err animate-pulse" : "text-ink-subtle"}`}>
                        {elapsedMs != null ? formatDuration(elapsedMs) : "—"}
                      </span>
                    </td>
                    {/* Action menu */}
                    <td className="px-2 py-2 text-right">
                      <ActionMenu
                        jobId={id}
                        status={j.status}
                        onCancel={() => cancel.mutate(id)}
                        onReplay={() => replay.mutate(id)}
                        isPending={cancel.isPending || replay.isPending}
                      />
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}

        {/* Pagination footer */}
        {jobs.length > PAGE_SIZE && (
          <div className="flex items-center justify-between border-t border-line px-3 py-1.5">
            <button
              type="button"
              disabled={safePage === 0}
              onClick={() => setPage((p) => Math.max(0, p - 1))}
              className="rounded border border-line bg-canvas-raised px-2 py-0.5 text-2xs text-ink-muted transition hover:text-ink disabled:opacity-40"
            >
              ← prev
            </button>
            <span className="text-2xs font-mono text-ink-subtle">
              page {safePage + 1} / {totalPages}
            </span>
            <button
              type="button"
              disabled={safePage >= totalPages - 1}
              onClick={() => setPage((p) => Math.min(totalPages - 1, p + 1))}
              className="rounded border border-line bg-canvas-raised px-2 py-0.5 text-2xs text-ink-muted transition hover:text-ink disabled:opacity-40"
            >
              next →
            </button>
          </div>
        )}
      </div>
    </section>
  );
}
