import { StatusBadge } from '@/components/StatusBadge';
import { useRunsStore } from '@/stores/runsStore';

/** 全局浮层：并发运行总览 + 取消。多个流程同时跑时各占一格，互不干扰。 */
export function ActiveRunsDock() {
  const runs = useRunsStore((s) => s.runs);
  const cancel = useRunsStore((s) => s.cancel);
  const active = Object.values(runs).filter((r) => r.status === 'running' || r.status === 'pending');
  if (!active.length) return null;

  return (
    <div className="fixed bottom-4 right-4 z-20 flex w-72 flex-col gap-2">
      {active.map((r) => (
        <div key={r.runId} className="rounded-xl border-[2.5px] border-ink bg-white px-3 py-2.5 shadow-pop">
          <div className="flex items-center justify-between gap-2">
            <span className="truncate text-sm font-bold">{r.flow}</span>
            <StatusBadge status={r.status} label={r.dryRun ? 'dry-run' : undefined} />
          </div>
          <div className="mt-1 truncate font-mono text-[11px] text-sub">
            {r.log[r.log.length - 1] ?? '…'}
          </div>
          <button
            type="button"
            onClick={() => cancel(r.runId)}
            className="mt-2 w-full rounded-lg border-2 border-ink bg-white py-1 font-mono text-[11px] transition-colors hover:bg-coral hover:text-white"
          >
            取消
          </button>
        </div>
      ))}
    </div>
  );
}
