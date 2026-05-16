import { StatusBadge } from "@/components/StatusBadge";
import { Table } from "@/components/Table";
import type { TableColumn } from "@/components/Table";
import type { SwarmAssignment, SwarmPreview } from "@/api/swarm";

interface WorkerAssignmentsProps {
  preview: SwarmPreview | undefined;
}

const COLUMNS: TableColumn<SwarmAssignment>[] = [
  {
    key: "role",
    header: "Role",
    width: "180px",
    render: (a) => (
      <div>
        <div className="font-semibold text-ink">{a.role}</div>
        <div className="text-2xs text-ink-subtle">{a.specialization}</div>
      </div>
    ),
  },
  {
    key: "intent",
    header: "Intent",
    width: "180px",
    render: (a) => <span className="font-mono text-xs text-ink-muted">{a.intent}</span>,
  },
  {
    key: "backend",
    header: "Backend hint",
    render: (a) => (
      <span className="break-all font-mono text-xs text-ink" title={a.backend_hint}>
        {a.backend_hint}
      </span>
    ),
  },
  {
    key: "rubric",
    header: "Verification",
    width: "200px",
    render: (a) => (
      <span className="font-mono text-2xs text-ink-muted">{a.verification_rubric}</span>
    ),
  },
  {
    key: "routing",
    header: "Routed by",
    width: "160px",
    render: (a) => (
      <span className="font-mono text-2xs text-ink-subtle">{a.routing_source}</span>
    ),
  },
];

export function WorkerAssignments({ preview }: WorkerAssignmentsProps) {
  return (
    <section className="mb-4">
      <header className="mb-2 flex items-baseline justify-between">
        <h2 className="text-2xs font-mono uppercase tracking-wider text-ink-subtle">
          Worker Assignments
        </h2>
        {preview && (
          <div className="flex items-center gap-2 text-2xs">
            <span className="text-ink-subtle">
              {preview.assignments.length} role{preview.assignments.length === 1 ? "" : "s"}
            </span>
            {preview.hardware_policy?.ok ? (
              <StatusBadge tone="ok">policy ok</StatusBadge>
            ) : (
              <StatusBadge tone="err">
                {preview.hardware_policy?.violations?.length ?? 0} violation
                {(preview.hardware_policy?.violations?.length ?? 0) === 1 ? "" : "s"}
              </StatusBadge>
            )}
          </div>
        )}
      </header>

      <Table
        columns={COLUMNS}
        rows={preview?.assignments ?? []}
        rowKey={(a) => a.role}
        empty="Run a preview to see the role-by-role assignment plan."
      />

      {/* Violation detail */}
      {preview && !preview.hardware_policy?.ok && (
        <div className="mt-2 rounded border border-status-err/40 bg-status-err/5 p-2">
          <div className="mb-1 text-2xs font-mono uppercase tracking-wider text-status-err">
            Hardware policy violations
          </div>
          <ul className="space-y-1 text-2xs text-ink-muted">
            {preview.hardware_policy.violations.map((v, i) => (
              <li key={i} className="font-mono">
                {v.role ?? "—"} → {v.model ?? "?"}: {v.reason ?? v.message ?? "rejected"}
              </li>
            ))}
          </ul>
        </div>
      )}
    </section>
  );
}
