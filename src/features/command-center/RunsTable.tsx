import { useMutation, useQueryClient } from "@tanstack/react-query";
import { StatusBadge, statusToTone } from "@/components/StatusBadge";
import { Table } from "@/components/Table";
import type { TableColumn } from "@/components/Table";
import type { JobSummary } from "@/api/appState";
import { cancelJob, replayJob } from "@/api/jobs";

interface RunsTableProps {
  jobs: JobSummary[];
}

export function RunsTable({ jobs }: RunsTableProps) {
  const queryClient = useQueryClient();

  const cancel = useMutation({
    mutationFn: (jobId: string) => cancelJob(jobId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["appState"] }),
  });
  const replay = useMutation({
    mutationFn: (jobId: string) => replayJob(jobId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["appState"] }),
  });

  const COLUMNS: TableColumn<JobSummary>[] = [
    {
      key: "id",
      header: "Job",
      width: "140px",
      mono: true,
      render: (j) => j.job_id ?? j.id ?? "—",
    },
    {
      key: "intent",
      header: "Intent",
      width: "140px",
      render: (j) => (
        <span className="text-xs text-ink">{j.intent ?? "—"}</span>
      ),
    },
    {
      key: "prompt",
      header: "Prompt",
      render: (j) => (
        <span className="line-clamp-1 text-xs text-ink-muted" title={j.prompt}>
          {j.prompt ?? "—"}
        </span>
      ),
    },
    {
      key: "backend",
      header: "Backend",
      width: "180px",
      mono: true,
      render: (j) => (
        <span className="text-ink-muted" title={j.backend}>
          {j.backend ?? "—"}
        </span>
      ),
    },
    {
      key: "device",
      header: "Device",
      width: "90px",
      render: (j) => (
        <span className="font-mono text-2xs uppercase text-ink-subtle">
          {j.device ?? "—"}
        </span>
      ),
    },
    {
      key: "status",
      header: "Status",
      width: "100px",
      render: (j) => (
        <StatusBadge tone={statusToTone(j.status)} dot={false}>
          {j.status ?? "unknown"}
        </StatusBadge>
      ),
    },
    {
      key: "actions",
      header: "",
      width: "150px",
      align: "right",
      render: (j) => {
        const id = j.job_id ?? j.id;
        if (!id) return null;
        const status = (j.status ?? "").toLowerCase();
        const canCancel = ["queued", "running", "in_progress", "active"].includes(status);
        const canReplay = ["completed", "failed", "rejected"].includes(status);
        return (
          <div className="flex justify-end gap-1">
            <button
              type="button"
              disabled={!canCancel || cancel.isPending}
              onClick={() => cancel.mutate(id)}
              className="rounded border border-line bg-canvas-raised px-2 py-0.5 text-2xs text-ink-muted transition hover:border-status-err hover:text-status-err disabled:opacity-30 disabled:hover:border-line disabled:hover:text-ink-muted"
            >
              cancel
            </button>
            <button
              type="button"
              disabled={!canReplay || replay.isPending}
              onClick={() => replay.mutate(id)}
              className="rounded border border-line bg-canvas-raised px-2 py-0.5 text-2xs text-ink-muted transition hover:border-accent hover:text-accent disabled:opacity-30 disabled:hover:border-line disabled:hover:text-ink-muted"
            >
              replay
            </button>
          </div>
        );
      },
    },
  ];

  return (
    <section className="mb-4">
      <header className="mb-2 flex items-baseline justify-between">
        <h2 className="text-2xs font-mono uppercase tracking-wider text-ink-subtle">
          Runs
        </h2>
        <span className="text-2xs text-ink-subtle">
          {jobs.length} job{jobs.length === 1 ? "" : "s"}
        </span>
      </header>

      <Table
        columns={COLUMNS}
        rows={jobs}
        rowKey={(j, i) => j.job_id ?? j.id ?? `row-${i}`}
        empty="No jobs yet. Compose a swarm to launch one."
      />
    </section>
  );
}
