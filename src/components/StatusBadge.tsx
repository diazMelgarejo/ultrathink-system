import type { ReactNode } from "react";

export type StatusTone = "ok" | "warn" | "err" | "info" | "gpu" | "neutral";

const TONE_CLASSES: Record<StatusTone, string> = {
  ok: "bg-status-ok/15 text-status-ok ring-status-ok/30",
  warn: "bg-status-warn/15 text-status-warn ring-status-warn/30",
  err: "bg-status-err/15 text-status-err ring-status-err/30",
  info: "bg-status-info/15 text-status-info ring-status-info/30",
  gpu: "bg-status-gpu/15 text-status-gpu ring-status-gpu/30",
  neutral: "bg-canvas-raised text-ink-muted ring-line",
};

interface StatusBadgeProps {
  tone?: StatusTone;
  children: ReactNode;
  dot?: boolean;
  className?: string;
}

export function StatusBadge({
  tone = "neutral",
  children,
  dot = true,
  className = "",
}: StatusBadgeProps) {
  const ariaLabel = typeof children === "string" || typeof children === "number"
    ? String(children)
    : undefined;
  return (
    <span
      role="status"
      aria-label={ariaLabel}
      className={`inline-flex items-center gap-1.5 rounded-sm px-2 py-0.5 text-2xs font-mono uppercase tracking-wider ring-1 ring-inset ${TONE_CLASSES[tone]} ${className}`}
    >
      {dot && (
        <span
          className="h-1.5 w-1.5 rounded-full"
          style={{ backgroundColor: "currentColor" }}
          aria-hidden
        />
      )}
      {children}
    </span>
  );
}

/** Infer tone from a free-form status string. */
export function statusToTone(status: string | undefined | null): StatusTone {
  if (!status) return "neutral";
  const s = status.toLowerCase();
  if (s.includes("ok") || s.includes("online") || s.includes("ready") || s === "completed" || s === "succeeded") return "ok";
  if (s.includes("warn") || s === "queued" || s === "pending") return "warn";
  if (s.includes("err") || s.includes("fail") || s === "blocked" || s === "rejected") return "err";
  if (s === "running" || s === "in_progress" || s === "active") return "info";
  if (s.includes("gpu") || s.includes("busy")) return "gpu";
  return "neutral";
}
