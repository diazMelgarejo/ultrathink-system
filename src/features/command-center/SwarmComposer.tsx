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

const TASK_TYPES: { value: TaskType; label: string }[] = [
  { value: "reasoning", label: "Analysis" },
  { value: "coding", label: "Coding" },
  { value: "research", label: "Research" },
  { value: "ops", label: "Ops" },
];

const OPTIMIZE_OPTIONS: { value: OptimizeFor; label: string }[] = [
  { value: "quality", label: "Quality" },
  { value: "speed", label: "Speed" },
  { value: "reliability", label: "Reliability" },
];

const DEVICE_OPTIONS: { value: PreferredDevice; label: string }[] = [
  { value: "auto", label: "Auto" },
  { value: "mac", label: "Mac (Ollama)" },
  { value: "windows", label: "Win (LM Studio)" },
  { value: "shared", label: "Shared / Cloud" },
];

const CONTEXT_PROFILES = [
  "Default",
  "Code Review",
  "Research Deep Dive",
  "Rapid Ops",
];

const MAX_OBJECTIVE = 2000;

interface SegmentedControlProps<T extends string> {
  label: string;
  options: { value: T; label: string }[];
  value: T;
  onChange: (v: T) => void;
}

function SegmentedControl<T extends string>({
  label,
  options,
  value,
  onChange,
}: SegmentedControlProps<T>) {
  return (
    <div>
      <span className="mb-1 block text-2xs uppercase tracking-wider text-ink-subtle">{label}</span>
      <div className="flex rounded border border-line bg-canvas-inset p-0.5">
        {options.map((opt) => (
          <button
            key={opt.value}
            type="button"
            onClick={() => onChange(opt.value)}
            className={`flex-1 rounded px-2 py-1 text-xs transition-colors ${
              value === opt.value
                ? "bg-canvas-raised text-ink font-medium shadow-sm"
                : "text-ink-muted hover:text-ink"
            }`}
          >
            {opt.label}
          </button>
        ))}
      </div>
    </div>
  );
}

export function SwarmComposer({ onPreview, onLaunch }: SwarmComposerProps) {
  const [objective, setObjective] = useState(
    "Analyze the attached financial report and produce key risk factors, opportunities, and a 1-page executive summary.",
  );
  const [taskType, setTaskType] = useState<TaskType>("reasoning");
  const [optimize, setOptimize] = useState<OptimizeFor>("quality");
  const [device, setDevice] = useState<PreferredDevice>("auto");
  const [contextProfile, setContextProfile] = useState("Default");
  const [showAdvanced, setShowAdvanced] = useState(false);

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

  const charCount = objective.length;
  const canPreview = charCount >= 6;
  const canLaunch = preview.isSuccess && preview.data?.hardware_policy?.ok;

  return (
    <section className="mb-4 rounded border border-line bg-canvas-surface">
      <header className="flex items-center justify-between border-b border-line px-3 py-2">
        <h2 className="text-2xs font-mono uppercase tracking-wider text-ink-subtle">
          Swarm Composer
        </h2>
        <div className="flex items-center gap-2">
          {preview.isPending && <StatusBadge tone="info" dot>previewing…</StatusBadge>}
          {launch.isPending && <StatusBadge tone="info" dot>launching…</StatusBadge>}
          {launch.isSuccess && (
            <StatusBadge tone="ok" dot={false}>session {launch.data.session_id}</StatusBadge>
          )}
        </div>
      </header>

      <div className="space-y-3 p-3">
        {/* Objective textarea */}
        <div>
          <div className="mb-1 flex items-baseline justify-between">
            <span className="text-2xs uppercase tracking-wider text-ink-subtle">Objective</span>
            <span className={`text-2xs font-mono ${charCount > MAX_OBJECTIVE * 0.9 ? "text-status-warn" : "text-ink-subtle"}`}>
              {charCount}/{MAX_OBJECTIVE}
            </span>
          </div>
          <textarea
            value={objective}
            onChange={(e) => setObjective(e.target.value.slice(0, MAX_OBJECTIVE))}
            rows={3}
            placeholder="Describe what the swarm should accomplish…"
            className="w-full resize-none rounded border border-line bg-canvas-inset px-2.5 py-2 text-sm font-mono text-ink placeholder:text-ink-subtle focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent"
          />
        </div>

        {/* Task Type + Optimize For segmented controls */}
        <div className="grid grid-cols-2 gap-3">
          <SegmentedControl
            label="Task type"
            options={TASK_TYPES}
            value={taskType}
            onChange={setTaskType}
          />
          <SegmentedControl
            label="Optimize for"
            options={OPTIMIZE_OPTIONS}
            value={optimize}
            onChange={setOptimize}
          />
        </div>

        {/* Device + Context Profile row */}
        <div className="grid grid-cols-2 gap-3">
          <div>
            <span className="mb-1 block text-2xs uppercase tracking-wider text-ink-subtle">Preferred Device</span>
            <select
              value={device}
              onChange={(e) => setDevice(e.target.value as PreferredDevice)}
              className="w-full rounded border border-line bg-canvas-inset px-2 py-1.5 text-xs font-mono text-ink focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent"
            >
              {DEVICE_OPTIONS.map((opt) => (
                <option key={opt.value} value={opt.value}>{opt.label}</option>
              ))}
            </select>
          </div>
          <div>
            <span className="mb-1 block text-2xs uppercase tracking-wider text-ink-subtle">Context Profile</span>
            <select
              value={contextProfile}
              onChange={(e) => setContextProfile(e.target.value)}
              className="w-full rounded border border-line bg-canvas-inset px-2 py-1.5 text-xs font-mono text-ink focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent"
            >
              {CONTEXT_PROFILES.map((p) => (
                <option key={p} value={p}>{p}</option>
              ))}
            </select>
          </div>
        </div>

        {/* Advanced Options */}
        <div>
          <button
            type="button"
            onClick={() => setShowAdvanced((v) => !v)}
            className="flex items-center gap-1 text-2xs text-ink-subtle transition hover:text-ink"
          >
            <span className={`transition-transform duration-150 ${showAdvanced ? "rotate-90" : ""}`}>▶</span>
            Advanced Options
          </button>
          {showAdvanced && (
            <div className="mt-2 rounded border border-line bg-canvas-inset p-2.5 text-2xs text-ink-muted">
              <p className="font-mono">
                timeout_sec, max_workers, verifier_rubric, depth, session_id override — coming Phase 5
              </p>
            </div>
          )}
        </div>

        {/* Action buttons */}
        <div className="flex items-center gap-2 pt-1">
          <button
            type="button"
            disabled={!canPreview || preview.isPending}
            onClick={() => preview.mutate()}
            className="rounded border border-line bg-canvas-raised px-3 py-1.5 text-xs text-ink transition hover:border-accent hover:text-accent disabled:opacity-40"
          >
            Preview Plan
          </button>
          <button
            type="button"
            disabled={!canLaunch || launch.isPending}
            onClick={() => launch.mutate()}
            className="rounded border border-accent bg-accent/10 px-4 py-1.5 text-xs font-semibold text-accent transition hover:bg-accent/20 disabled:opacity-40"
          >
            Launch Swarm
          </button>

          {preview.isError && (
            <span className="ml-auto text-2xs text-status-err">
              preview failed
            </span>
          )}
          {launch.isError && (
            <span className="ml-auto text-2xs text-status-err">
              launch failed
            </span>
          )}
        </div>
      </div>
    </section>
  );
}
