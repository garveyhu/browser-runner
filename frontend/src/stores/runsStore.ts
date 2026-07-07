import { create } from 'zustand';

import { runApi, streamRunEvents } from '@/services/runApi';
import type { RunResult, RunStatus } from '@/types/api.types';

export interface ActiveRun {
  runId: string;
  flow: string;
  dryRun: boolean;
  status: RunStatus;
  log: string[];
  result: RunResult | null;
  error?: string;
}

interface RunsState {
  runs: Record<string, ActiveRun>; // runId → run（支持多个并发）
  currentByFlow: Record<string, string>; // flow → 最近一次 runId（卡片显示用）
  controllers: Record<string, AbortController>;
  start: (flow: string, params: Record<string, unknown>, dryRun: boolean, yes: boolean) => Promise<void>;
  cancel: (runId: string) => Promise<void>;
  currentRun: (flow: string) => ActiveRun | undefined;
}

export const useRunsStore = create<RunsState>((set, get) => ({
  runs: {},
  currentByFlow: {},
  controllers: {},

  currentRun: (flow) => {
    const id = get().currentByFlow[flow];
    return id ? get().runs[id] : undefined;
  },

  start: async (flow, params, dryRun, yes) => {
    const { run_id } = await runApi.start({ flow, params, dry_run: dryRun, yes });
    const run: ActiveRun = { runId: run_id, flow, dryRun, status: 'running', log: [], result: null };
    const ac = new AbortController();
    set((s) => ({
      runs: { ...s.runs, [run_id]: run },
      currentByFlow: { ...s.currentByFlow, [flow]: run_id },
      controllers: { ...s.controllers, [run_id]: ac },
    }));

    const patch = (fn: (r: ActiveRun) => ActiveRun) =>
      set((s) => (s.runs[run_id] ? { runs: { ...s.runs, [run_id]: fn(s.runs[run_id]) } } : {}));

    try {
      await streamRunEvents(
        run_id,
        {
          onLog: (line) => patch((r) => ({ ...r, log: [...r.log, line] })),
          onDone: (data) => {
            let result: RunResult;
            try {
              result = JSON.parse(data) as RunResult;
            } catch {
              result = { ok: false, error: '结果解析失败' };
            }
            patch((r) => ({ ...r, result, status: result.ok ? 'succeeded' : 'failed' }));
          },
        },
        ac.signal,
      );
    } catch (e) {
      const err = e as Error;
      if (err.name !== 'AbortError') patch((r) => ({ ...r, status: 'error', error: err.message }));
    }
  },

  cancel: async (runId) => {
    if (!get().runs[runId]) return;
    try {
      await runApi.cancel(runId); // 后端杀子进程
    } catch {
      /* 忽略：可能已结束 */
    }
    get().controllers[runId]?.abort(); // 停本地 SSE 流
    set((s) =>
      s.runs[runId] ? { runs: { ...s.runs, [runId]: { ...s.runs[runId], status: 'cancelled' } } } : {},
    );
  },
}));
