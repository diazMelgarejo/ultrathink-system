import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { StatusBadge, statusToTone } from "@/components/StatusBadge";
import type { JobSummary } from "@/api/appState";
import { cancelJob, replayJob } from "@/api/jobs";

interface RunsTableProps {
  jobs: JobSummary[];
}

const PAGE_SIZE = 7;

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

function JobStatusBadge({ status }: { status: string | undefined }) {
  const tone = statusToTone(status);
  const label = status ?? "unknown";
  return <StatusBadge tone={tone} dot>{label}</StatusBadge>;
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
              {pageJobs.map((j, i) => {
                const id = j.job_id ?? j.id ?? `row-${i}`;
                return (
                  <tr
                    key={id}
                    className="group border-b border-line last:border-b-0 hover:bg-canvas-raised/50"
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
                      <JobStatusBadge status={j.status} />
                    </td>
                    {/* Workers — not in schema yet, show placeholder */}
                    <td className="px-3 py-2">
                      <span className="font-mono text-xs text-ink-subtle">
                        {(j as { worker_count?: number }).worker_count ?? "—"}
                      </span>
                    </td>
                    {/* Started */}
                    <td className="px-3 py-2">
                      <span className="font-mono text-xs text-ink-subtle">
                        {j.created_at
                          ? new Date(j.created_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
                          : "—"}
                      </span>
                    </td>
                    {/* Duration — not in schema yet */}
                    <td className="px-3 py-2">
                      <span className="font-mono text-xs text-ink-subtle">—</span>
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
