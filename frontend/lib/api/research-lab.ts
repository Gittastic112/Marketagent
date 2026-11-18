import { fetchApi, postApi } from "./transport.ts";
import type { components } from "./generated/adapters.ts";

type Schemas = components["schemas"];
export type ResearchCapabilities = Schemas["ResearchCapabilities"];
export type ResearchDataset = Schemas["ResearchDataset"];
export type AllocationRequest = Schemas["AllocationRequest"];
export type SimulationRequest = Schemas["SimulationRequest"];
export type ReportObservation = Schemas["ReportObservation"];
export type ReportRequest = Schemas["ReportRequest"];
export type PeerDiscoveryRequest = Schemas["PeerDiscoveryRequest"];
export type ResearchRun = Schemas["ResearchRunResult"];
export type ResearchKind = ResearchRun["kind"];
export type ResearchRunSummary = Schemas["ResearchRunSummary"];
export type ResearchRequestByKind = { allocation: AllocationRequest; simulation: SimulationRequest; report: ReportRequest; peers: PeerDiscoveryRequest };

export const getResearchCapabilities = () => fetchApi<ResearchCapabilities>("/api/research-lab/capabilities");
export const listResearchRuns = (beforeRunId?: number) => fetchApi<ResearchRunSummary[]>(`/api/research-lab/runs?limit=25${beforeRunId === undefined ? "" : `&before_run_id=${beforeRunId}`}`);
export const getResearchRun = (runId: number) => fetchApi<ResearchRun>(`/api/research-lab/runs/${runId}`);
export function createResearchRun<K extends ResearchKind>(kind: K, payload: ResearchRequestByKind[K]): Promise<ResearchRun> {
  return postApi<ResearchRun>(`/api/research-lab/${kind}`, payload);
}
