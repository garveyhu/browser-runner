import { httpGet } from '@/services/http';
import type { Artifact, CsvPreview } from '@/types/api.types';

/** 产物直链（供 iframe src / 下载 / img）。不走 Result 封套。 */
const artifactUrl = (runId: string, name: string, download = false) =>
  `/api/runs/${runId}/artifacts/${encodeURIComponent(name)}${download ? '?download=1' : ''}`;

export const artifactApi = {
  list: (runId: string) => httpGet<Artifact[]>(`/runs/${runId}/artifacts`),
  csvPreview: (runId: string, name: string) =>
    httpGet<CsvPreview>(`/runs/${runId}/artifacts/${encodeURIComponent(name)}?as=json`),
  url: artifactUrl,
  text: async (runId: string, name: string): Promise<string> => {
    const r = await fetch(artifactUrl(runId, name));
    if (!r.ok) throw new Error(`HTTP ${r.status}`);
    return r.text();
  },
};
