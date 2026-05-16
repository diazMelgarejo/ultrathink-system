import { CommandCenter } from "./features/command-center/CommandCenter";

/**
 * App shell — single-route operator console.
 * The visual layout is the "dense dark operator console" target from
 * docs/superpowers/specs/2026-05-14-rc1-orchestration-master-plan.md §3 Stage 4.
 *
 * Layout (top → bottom):
 *   ┌──────────────────────────────────────────────────┐
 *   │  Top env/region/API status bar                   │
 *   ├──────────────────────────────────────────────────┤
 *   │ NavLeft │ ReadinessStrip                         │
 *   │         │ SwarmComposer                          │
 *   │         │ WorkerAssignments                      │
 *   │         │ RunsTable                              │
 *   │         │ ArtifactsPanel                         │
 *   └──────────────────────────────────────────────────┘
 */
export default function App() {
  return <CommandCenter />;
}
