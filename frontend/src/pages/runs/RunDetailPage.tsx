import { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';

import { PosterHeader } from '@/components/PosterHeader';
import { StatusBadge } from '@/components/StatusBadge';
import { useRunDetail } from '@/hooks/useRunDetail';
import { ResultPanel } from '@/pages/console/components/ResultPanel';
import { ArtifactViewer } from './components/ArtifactViewer';

export default function RunDetailPage() {
  const { runId } = useParams<{ runId: string }>();
  const { data: run, isLoading, isError } = useRunDetail(runId);
  const [selected, setSelected] = useState<string | null>(null);

  useEffect(() => {
    if (run && selected === null && run.artifacts.length) {
      const report = run.artifacts.find((a) => a.kind === 'report');
      setSelected((report ?? run.artifacts[0]).name);
    }
  }, [run, selected]);

  const current = run?.artifacts.find((a) => a.name === selected) ?? null;

  return (
    <div className="min-h-full pb-24">
      <PosterHeader />
      <main className="mx-auto max-w-5xl px-6 pt-10">
        <Link to="/runs" className="font-mono text-xs text-sub hover:text-ink">
          ← 运行历史
        </Link>

        {isLoading && <div className="mt-4 font-mono text-sub">加载…</div>}
        {isError && (
          <div className="mt-4 rounded-2xl border-[2.5px] border-ink bg-coral p-4 font-semibold text-white shadow-pop">
            没有该运行。
          </div>
        )}

        {run && (
          <>
            <header className="mt-4 border-b-2 border-line pb-5">
              <div className="flex flex-wrap items-center gap-3">
                <h1 className="text-2xl font-black">{run.flow}</h1>
                <StatusBadge status={run.status} />
                {run.dry_run && (
                  <span className="border border-ink px-1.5 py-px font-mono text-[10px]">dry-run</span>
                )}
              </div>
              <div className="mt-2 font-mono text-xs text-sub">
                {run.run_id} · {run.started_at}
              </div>
              {run.params && Object.keys(run.params).length > 0 && (
                <div className="mt-3 flex flex-wrap gap-2">
                  {Object.entries(run.params).map(([k, v]) => (
                    <span key={k} className="rounded-lg border-2 border-ink bg-white px-2 py-1 font-mono text-xs">
                      <b className="text-sub">{k}</b>={String(v)}
                    </span>
                  ))}
                </div>
              )}
            </header>

            {run.result && (
              <div className="mt-5 overflow-hidden rounded-2xl border-[2.5px] border-ink bg-white shadow-pop-sm">
                <div className="px-4 py-2 font-mono text-xs font-bold uppercase text-sub">结果</div>
                <ResultPanel result={run.result} runId={run.run_id} />
              </div>
            )}

            {run.artifacts.length > 0 && (
              <section className="mt-8">
                <h2 className="mb-3 font-mono text-xs uppercase tracking-[0.16em] text-sub">产物</h2>
                <div className="mb-3 flex flex-wrap gap-2">
                  {run.artifacts.map((a) => (
                    <button
                      key={a.name}
                      type="button"
                      onClick={() => setSelected(a.name)}
                      className={`rounded-lg border-[2.5px] border-ink px-3 py-1.5 font-mono text-xs transition-transform ease-back hover:-translate-x-px hover:-translate-y-px ${
                        selected === a.name ? 'bg-ink text-white' : 'bg-white'
                      }`}
                    >
                      {a.name}
                    </button>
                  ))}
                </div>
                {current && <ArtifactViewer runId={run.run_id} artifact={current} />}
              </section>
            )}
          </>
        )}
      </main>
    </div>
  );
}
