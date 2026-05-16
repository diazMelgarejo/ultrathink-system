import { StatusBadge } from "@/components/StatusBadge";
import type { SwarmAssignment, SwarmPreview } from "@/api/swarm";

interface WorkerAssignmentsProps {
  preview: SwarmPreview | undefined;
}

const WORKER_LETTERS: Record<string, string> = {
  "context-builder": "C",
  architect: "A",
  executor: "E",
  verifier: "V",
  crystallizer: "X",
};

function roleColor(role: string): string {
  const colors = [
    "bg-accent/20 text-accent",
    "bg-status-ok/20 text-status-ok",
    "bg-status-gpu/20 text-status-gpu",
    "bg-status-warn/20 text-status-warn",
    "bg-status-info/20 text-status-info",
  ];
  const idx = role.charCodeAt(0) % colors.length;
  return colors[idx];
}

function workerLetter(role: string): string {
  return WORKER_LETTERS[role] ?? role[0]?.toUpperCase() ?? "?";
}

function RoutingSourceBadge({ source }: { source: string }) {
  const [scope] = source.split(".");
  const tone =
    scope === "session" ? "info" :
    scope === "run" ? "ok" :
    scope === "policy" ? "neutral" : "neutral";
  return (
    <StatusBadge tone={tone} dot={false}>
      {source}
    </StatusBadge>
  );
}

function WorkerRow({ assignment }: { assignment: SwarmAssignment }) {
  const letter = workerLetter(assignment.role);
  const colorClass = roleColor(assignment.role);

  return (
    <tr className="border-b border-line last:border-b-0 hover:bg-canvas-raised/50">
      <td className="px-3 py-2">
        <div className={`flex h-8 w-8 items-center justify-center rounded-md text-xs font-semibold ${colorClass}`}>
          {letter}
        </div>
      </td>
      <td className="px-3 py-2">
        <div>
          <div className="text-xs font-medium text-ink">{assignment.role}</div>
          <div className="text-2xs text-ink-subtle">{assignment.specialization}</div>
        </div>
      </td>
      {/* Backend hint */}
      <td className="px-3 py-2">
        <span className="font-mono text-2xs text-ink-muted" title={assignment.backend_hint}>
          {assignment.backend_hint}
        </span>
      </td>
      {/* Routing source */}
      <td className="px-3 py-2">
        <RoutingSourceBadge source={assignment.routing_source} />
      </td>
      {/* Status */}
      <td className="px-3 py-2">
        <StatusBadge tone="ok" dot={false}>Ready</StatusBadge>
      </td>
    </tr>
  );
}

export function WorkerAssignments({ preview }: WorkerAssignmentsProps) {
  const assignments = preview?.assignments ?? [];
  const policyOk = preview?.hardware_policy?.ok ?? true;
  const violations = preview?.hardware_policy?.violations ?? [];

  return (
    <section className="mb-4">
      <header className="mb-2 flex items-center justify-between">
        <h2 className="text-2xs font-mono uppercase tracking-wider text-ink-subtle">
          Worker Assignments
        </h2>
        <button
          type="button"
          className="rounded border border-line bg-canvas-raised px-2 py-0.5 text-2xs text-ink-muted transition hover:text-ink"
        >
          Edit Assignments
        </button>
      </header>

      <div className="overflow-auto rounded border border-line bg-canvas-surface">
        {assignments.length === 0 ? (
          <div className="px-4 py-8 text-center text-sm text-ink-muted">
            Run a preview to see the role-by-role assignment plan.
          </div>
        ) : (
          <table className="w-full border-collapse text-sm">
            <thead className="sticky top-0 bg-canvas-raised">
              <tr className="border-b border-line">
                <th className="px-3 py-1.5 text-left text-2xs font-mono uppercase tracking-wider text-ink-subtle">
                  Worker
                </th>
                <th className="px-3 py-1.5 text-left text-2xs font-mono uppercase tracking-wider text-ink-subtle">
                  Role
                </th>
                <th className="px-3 py-1.5 text-left text-2xs font-mono uppercase tracking-wider text-ink-subtle">
                  Backend (HINT)
                </th>
                <th className="px-3 py-1.5 text-left text-2xs font-mono uppercase tracking-wider text-ink-subtle">
                  Routing Source
                </th>
                <th className="px-3 py-1.5 text-left text-2xs font-mono uppercase tracking-wider text-ink-subtle">
                  Status
                </th>
              </tr>
            </thead>
            <tbody>
              {assignments.map((a) => (
                <WorkerRow key={a.role} assignment={a} />
              ))}
            </tbody>
          </table>
        )}

        {/* Footer: routing precedence note */}
        {assignments.length > 0 && (
          <div className="flex items-center justify-between border-t border-line px-3 py-1.5">
            <span className="text-2xs text-ink-subtle">
              Routing precedence:{" "}
              <span className="font-mono text-ink-muted">Session {">"} Run {">"} Policy</span>
            </span>
            <button type="button" className="text-2xs text-accent hover:text-accent-hover">
              View Routing
            </button>
          </div>
        )}
      </div>

      {/* Violation detail */}
      {!policyOk && violations.length > 0 && (
        <div className="mt-2 rounded border border-status-err/40 bg-status-err/5 p-2">
          <div className="mb-1 text-2xs font-mono uppercase tracking-wider text-status-err">
            Hardware policy violations
          </div>
          <ul className="space-y-1 text-2xs text-ink-muted">
            {violations.map((v, i) => (
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
