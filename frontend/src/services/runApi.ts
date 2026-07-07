import { httpGet, httpPost } from '@/services/http';
import type { RunDetail, RunListResult, StartRunResponse } from '@/types/api.types';

export interface StartRunBody {
  flow: string;
  params: Record<string, unknown>;
  dry_run?: boolean;
  yes?: boolean;
}

export interface RunListQuery {
  flow?: string;
  status?: string;
  limit?: number;
  offset?: number;
}

export const runApi = {
  start: (body: StartRunBody) => httpPost<StartRunResponse>('/runs', body),
  cancel: (runId: string) => httpPost<{ run_id: string; status: string }>(`/runs/${runId}/cancel`),
  list: (q?: RunListQuery) => {
    const qs = new URLSearchParams();
    if (q?.flow) qs.set('flow', q.flow);
    if (q?.status) qs.set('status', q.status);
    if (q?.limit != null) qs.set('limit', String(q.limit));
    if (q?.offset != null) qs.set('offset', String(q.offset));
    const s = qs.toString();
    return httpGet<RunListResult>(`/runs${s ? `?${s}` : ''}`);
  },
  detail: (runId: string) => httpGet<RunDetail>(`/runs/${runId}`),
};

// ── SSE 消费 ──
// 端点是 GET /runs/{id}/events，但用 fetch + ReadableStream 手动读，
// 而非 EventSource —— 后者流结束会自动重连、反复触发 done，控制生命周期更麻烦。
export interface StreamHandlers {
  onLog: (line: string) => void;
  onDone: (data: string) => void;
}

function parseBlock(raw: string): { event: string; data: string } {
  let event = 'message';
  const data: string[] = [];
  for (const line of raw.split('\n')) {
    if (line.startsWith('event:')) event = line.slice(6).trim();
    else if (line.startsWith('data:')) data.push(line.slice(5).replace(/^ /, ''));
  }
  return { event, data: data.join('\n') };
}

export async function streamRunEvents(
  runId: string,
  handlers: StreamHandlers,
  signal?: AbortSignal,
): Promise<void> {
  const res = await fetch(`/api/runs/${runId}/events`, {
    signal,
    headers: { Accept: 'text/event-stream' },
  });
  if (!res.ok || !res.body) throw new Error(`HTTP ${res.status}`);
  const reader = res.body.getReader();
  const dec = new TextDecoder();
  let buf = '';
  for (;;) {
    const { done, value } = await reader.read();
    if (done) break;
    buf += dec.decode(value, { stream: true });
    let idx: number;
    while ((idx = buf.indexOf('\n\n')) >= 0) {
      const block = buf.slice(0, idx);
      buf = buf.slice(idx + 2);
      if (!block.trim()) continue;
      const { event, data } = parseBlock(block);
      if (event === 'done') {
        handlers.onDone(data);
        return;
      }
      if (data) handlers.onLog(data);
    }
  }
}
