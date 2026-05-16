import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Shell } from "@/components/Shell";
import { fetchAppState } from "@/api/appState";
import type { JobSummary } from "@/api/appState";
import type { SwarmPreview } from "@/api/swarm";
import type { Artifact } from "@/api/artifacts";
import { listJobArtifacts } from "@/api/artifacts";
import { mockArtifactList, mockState, mockSwarmPreview } from "@/data/mockState";
import { ReadinessStrip } from "./ReadinessStrip";
import { SwarmComposer } from "./SwarmComposer";
import { WorkerAssignments } from "./WorkerAssignments";
import { RunsTable } from "./RunsTable";
import { ArtifactsPanel } from "./ArtifactsPanel";
import { RoutingView } from "@/features/routing/RoutingView";

type Page = "command" | "composer" | "runs" | "routing" | "artifacts" | "settings" | "docs";

/**
 * Command Center — operator console root.
 *
 * Layout (mockup-matched):
 *   ┌──────────────────────────────────────────────────┐
 *   │  ReadinessStrip (full width, 4 tiles)            │
 *   ├──────────────────────┬───────────────────────────┤
 *   │  SwarmComposer ~60%  │  WorkerAssignments ~40%   │
 *   ├──────────────────────┴───────────────────────────┤
 *   │  RunsTable (full width)                          │
 *   │  ArtifactsPanel (full width)                     │
 *   └──────────────────────────────────────────────────┘
 */
export function CommandCenter() {
  const [page, setPage] = useState<Page>("command");
  const [preview, setPreview] = useState<SwarmPreview | undefined>(mockSwarmPreview);

  const appStateQuery = useQuery({
    queryKey: ["appState"],
    queryFn: ({ signal }) => fetchAppState(signal),
    refetchInterval: 5_000,
    refetchIntervalInBackground: false,
  });

  const state = appStateQuery.data ?? mockState;
  const jobs: JobSummary[] = (state?.jobs?.data?.jobs ?? mockState.jobs.data.jobs) as JobSummary[];
  const latestJobId = jobs[0]?.job_id ?? jobs[0]?.id;

  const artifactsQuery = useQuery({
    queryKey: ["jobArtifacts", latestJobId],
    queryFn: ({ signal }) => listJobArtifacts(String(latestJobId ?? ""), signal),
    enabled: Boolean(latestJobId),
    refetchInterval: 10_000,
  });

  const artifacts: Artifact[] = artifactsQuery.data?.artifacts ?? mockArtifactList;

  function renderPage() {
    switch (page) {
      case "routing":
        return <RoutingView state={state} />;

      case "runs":
        return <RunsTable jobs={jobs} />;

      case "artifacts":
        return <ArtifactsPanel artifacts={artifacts} />;

      case "composer":
        return (
          <div className="grid grid-cols-1 gap-4 lg:grid-cols-5">
            <div className="lg:col-span-3">
              <SwarmComposer
                onPreview={(p) => setPreview(p)}
                onLaunch={() => { /* jobs poll picks up within 5s */ }}
              />
            </div>
            <div className="lg:col-span-2">
              <WorkerAssignments preview={preview} />
            </div>
          </div>
        );

      case "command":
      default:
        return (
          <>
            {/* Readiness row */}
            <ReadinessStrip state={state} />

            {/* Main 2-column region: Composer + Workers */}
            <div className="mb-4 grid grid-cols-1 gap-4 lg:grid-cols-5">
              <div className="lg:col-span-3">
                <SwarmComposer
                  onPreview={(p) => setPreview(p)}
                  onLaunch={() => { /* jobs poll picks up within 5s */ }}
                />
              </div>
              <div className="lg:col-span-2">
                <WorkerAssignments preview={preview} />
              </div>
            </div>

            {/* Runs table */}
            <RunsTable jobs={jobs} />

            {/* Artifacts */}
            <ArtifactsPanel artifacts={artifacts} />
          </>
        );
    }
  }

  return (
    <Shell
      state={state}
      isFetching={appStateQuery.isFetching}
      activePage={page}
      onNavigate={(p) => setPage(p as Page)}
    >
      {renderPage()}

      {appStateQuery.isError && (
        <div className="mt-2 rounded border border-status-err/40 bg-status-err/5 px-3 py-2 text-2xs text-status-err">
          /api/app/state unreachable — showing mock state. Check that portal_server.py is running on port 8001.
        </div>
      )}
    </Shell>
  );
}
