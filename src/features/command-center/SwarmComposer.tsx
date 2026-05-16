import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { previewSwarm, launchSwarm } from "@/api/swarm";
import type {
  SwarmPreview,
  SwarmLaunchResult,
  TaskType,
  OptimizeFor,
  PreferredDevice,
} from "@/api/swarm";
import { StatusBadge } from "@/components/StatusBadge";

interface SwarmComposerProps {
  onPreview?: (preview: SwarmPreview) => void;
  onLaunch?: (result: SwarmLaunchResult) => void;
}

export function SwarmComposer({ onPreview, onLaunch }: SwarmComposerProps) {
  const [objective, setObjective] = useState("");
  const [taskType, setTaskType] = useState<TaskType>("ops");
  const [optimize, setOptimize] = useState<OptimizeFor>("quality");
  const [device, setDevice] = useState<PreferredDevice>("auto");

  const preview = useMutation({
    mutationFn: () =>
      previewSwarm({
        objective,
        task_type: taskType,
        optimize_for: optimize,
        preferred_device: device,
      }),
    onSuccess: (data) => onPreview?.(data),
  });

  const launch = useMutation({
    mutationFn: () =>
      launchSwarm({
        objective,
        task_type: taskType,
        optimize_for: optimize,
        preferred_device: device,
        approved: true,
      }),
    onSuccess: (data) => onLaunch?.(data),
  });

  const canPreview = objective.trim().length >= 6;
  const canLaunch = preview.isSuccess && preview.data?.hardware_policy?.ok;

  return (
    <section className="mb-4 rounded border border-line bg-canvas-surface">
      <header className="flex items-baseline justify-between border-b border-line px-3 py-2">
        <h2 className="text-2xs font-mono uppercase tracking-wider text-ink-subtle">
          Swarm Composer
        </h2>
        {preview.isPending && <StatusBadge tone="info">previewing…</StatusBadge>}
        {launch.isPending && <StatusBadge tone="info">launching…</StatusBadge>}
      </header>

      <div className="space-y-3 p-3">
        <label className="block">
          <span className="block text-2xs uppercase tracking-wider text-ink-subtle">
            Objective
          </span>
          <textarea
            value={objective}
            onChange={(e) => setObjective(e.target.value)}
            rows={2}
            placeholder="Describe what the swarm should accomplish…"
            className="mt-1 w-full resize-none rounded border border-line bg-canvas-inset px-2 py-1.5 text-sm font-mono text-ink placeholder:text-ink-subtle focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent"
          />
        </label>

        <div className="grid grid-cols-3 gap-3">
          <Select
            label="Task type"
            value={taskType}
            options={["coding", "reasoning", "research", "ops"]}
            onChange={(v) => setTaskType(v as TaskType)}
          />
          <Select
            label="Optimize for"
            value={optimize}
            options={["speed", "quality", "reliability"]}
            onChange={(v) => setOptimize(v as OptimizeFor)}
          />
          <Select
            label="Device"
            value={device}
            options={["auto", "mac", "windows", "shared"]}
            onChange={(v) => setDevice(v as PreferredDevice)}
          />
        </div>

        <div className="flex items-center gap-2">
          <button
            type="button"
            disabled={!canPreview || preview.isPending}
            onClick={() => preview.mutate()}
            className="rounded border border-line bg-canvas-raised px-3 py-1.5 text-sm text-ink transition hover:border-accent hover:text-accent disabled:opacity-40 disabled:hover:border-line disabled:hover:text-ink"
          >
            Preview swarm
          </button>
          <button
            type="button"
            disabled={!canLaunch || launch.isPending}
            onClick={() => launch.mutate()}
            className="rounded border border-accent bg-accent/10 px-3 py-1.5 text-sm font-semibold text-accent transition hover:bg-accent/20 disabled:opacity-40 disabled:hover:bg-accent/10"
          >
            Launch (approved)
          </button>

          {preview.isError && (
            <span className="ml-auto text-2xs text-status-err">
              preview failed: {(preview.error as Error).message}
            </span>
          )}
          {launch.isError && (
            <span className="ml-auto text-2xs text-status-err">
              launch failed: {(launch.error as Error).message}
            </span>
          )}
          {launch.isSuccess && (
            <span className="ml-auto text-2xs text-status-ok">
              session {launch.data.session_id}
            </span>
          )}
        </div>
      </div>
    </section>
  );
}

interface SelectProps {
  label: string;
  value: string;
  options: string[];
  onChange: (v: string) => void;
}

function Select({ label, value, options, onChange }: SelectProps) {
  return (
    <label className="block">
      <span className="block text-2xs uppercase tracking-wider text-ink-subtle">
        {label}
      </span>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="mt-1 w-full rounded border border-line bg-canvas-inset px-2 py-1 text-sm font-mono text-ink focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent"
      >
        {options.map((opt) => (
          <option key={opt} value={opt}>
            {opt}
          </option>
        ))}
      </select>
    </label>
  );
}
