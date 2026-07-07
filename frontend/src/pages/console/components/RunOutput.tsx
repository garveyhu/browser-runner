import { useEffect, useRef } from 'react';

import { StatusBadge } from '@/components/StatusBadge';
import { useRunsStore, type ActiveRun } from '@/stores/runsStore';
import { ResultPanel } from './ResultPanel';

export function RunOutput({ run }: { run: ActiveRun }) {
  const cancel = useRunsStore((s) => s.cancel);
  const logRef = useRef<HTMLPreElement>(null);

  useEffect(() => {
    const el = logRef.current;
    if (el) el.scrollTop = el.scrollHeight;
  }, [run.log.length]);

  const badgeLabel =
    run.status === 'running' && run.dryRun ? '运行中 · dry-run' : undefined;

  return (
    <section className="mt-6 overflow-hidden rounded-xl border-[2.5px] border-ink shadow-pop-sm">
      <div className="flex items-center justify-between border-b-[2.5px] border-ink bg-paper px-3 py-2">
        <span className="font-mono text-xs font-bold uppercase tracking-wider">运行输出</span>
        <div className="flex items-center gap-2">
          <StatusBadge status={run.status} label={badgeLabel} />
          {run.status === 'running' && (
            <button
              type="button"
              onClick={() => cancel(run.runId)}
              className="border border-ink bg-white px-2 py-0.5 font-mono text-[11px] transition-transform ease-back hover:-translate-x-px hover:-translate-y-px hover:bg-coral hover:text-white"
            >
              取消
            </button>
          )}
        </div>
      </div>
      <pre
        ref={logRef}
        tabIndex={0}
        className="max-h-72 overflow-auto whitespace-pre-wrap break-words bg-ink p-3 font-mono text-xs leading-relaxed text-paper"
      >
        {run.log.join('\n') || '…'}
      </pre>
      {run.result && <ResultPanel result={run.result} runId={run.runId} />}
    </section>
  );
}
