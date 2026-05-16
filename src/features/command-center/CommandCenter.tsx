import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Shell } from "@/components/Shell";
import { fetchAppState } from "@/api/appState";
import type { JobSummary } from "@/api/appState";
import type { SwarmPreview } from "@/api/swarm";
import type { Artifact } from "@/api/artifacts";
import { mockArtifactList, mockState } from "@/data/mockState";
import { ReadinessStrip } from "./ReadinessStrip";
import { SwarmComposer } from "./SwarmComposer";
import { WorkerAssignments } from "./WorkerAssignments";
import { RunsTable } from "./RunsTable";
import { ArtifactsPanel } from "./ArtifactsPanel";

/**
 * Command Center — operator console main view.
 *
 * Polls /api/app/state every 5 seconds while the tab is focused. Falls back
 * to mockState before first response and on error so the UI always renders.
 * Local SwarmComposer state drives WorkerAssignments via the preview prop.
 */
export function CommandCenter() {
  const [preview, setPreview] = useState<SwarmPreview | undefined>(undefined);

  const appStateQuery = useQuery({
    queryKey: ["appState"],
    queryFn: ({ signal }) => fetchAppState(signal),
    refetchInterval: 5_000,
    refetchIntervalInBackground: false,
  });

  // Use API response when available; fall back to mock state for empty/error states
  const state = appStateQuery.data ?? (appStateQuery.isError ? mockState : appStateQuery.data);

  const jobs: JobSummary[] = (state?.jobs?.data?.jobs ?? mockState.jobs.data.jobs) as JobSummary[];

  // Artifacts: in this prototype we use mockArtifactList; live wiring is a Phase 5
  // follow-up (would aggregate /api/jobs/{id}/artifacts for recent completed jobs).
  const artifacts: Artifact[] = mockArtifactList;

  return (
    <Shell state={state} isFetching={appStateQuery.isFetching}>
      <ReadinessStrip state={state} />

      <SwarmComposer
        onPreview={(p) => setPreview(p)}
        onLaunch={() => {
          // After launch, the jobs poll picks up the new job within 5s.
          // No-op here; the RunsTable will refresh from /api/app/state.
        }}
      />

      <WorkerAssignments preview={preview} />

      <RunsTable jobs={jobs} />

      <ArtifactsPanel artifacts={artifacts} />

      {appStateQuery.isError && (
        <div className="mt-2 rounded border border-status-err/40 bg-status-err/5 px-3 py-2 text-2xs text-status-err">
          /api/app/state unreachable — showing mock state. Check that portal_server.py is running on port 8001.
        </div>
      )}
    </Shell>
  );
}
