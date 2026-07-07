import { useState } from 'react';
import { Link } from 'react-router-dom';

import { PosterHeader } from '@/components/PosterHeader';
import { StatusBadge } from '@/components/StatusBadge';
import { useFlows } from '@/hooks/useFlows';
import { useRuns } from '@/hooks/useRuns';

export default function RunsPage() {
  const [flow, setFlow] = useState('');
  const { data: flows } = useFlows();
  const { data, isLoading } = useRuns({ flow: flow || undefined, limit: 100 });

  return (
    <div className="min-h-full pb-24">
      <PosterHeader />
      <main className="mx-auto max-w-5xl px-6 pt-10">
        <div className="mb-6 flex flex-wrap items-center justify-between gap-3">
          <h2 className="font-mono text-xs uppercase tracking-[0.16em] text-sub">
            运行历史 · {data?.total ?? 0}
          </h2>
          <select
            value={flow}
            onChange={(e) => setFlow(e.target.value)}
            className="rounded-lg border-[2.5px] border-ink bg-white px-3 py-1.5 font-mono text-xs outline-none"
          >
            <option value="">全部流程</option>
            {(flows ?? []).map((f) => (
              <option key={f.name} value={f.name}>
                {f.title}
              </option>
            ))}
          </select>
        </div>

        {isLoading && <div className="font-mono text-sub">加载…</div>}
        {data && data.runs.length === 0 && (
          <div className="rounded-2xl border-[2.5px] border-dashed border-ink bg-white p-10 text-center text-sub">
            还没有运行记录。去控制台跑一个。
          </div>
        )}

        <div className="flex flex-col gap-2">
          {(data?.runs ?? []).map((r) => (
            <Link
              key={r.run_id}
              to={`/runs/${r.run_id}`}
              className="flex items-center gap-4 rounded-xl border-[2.5px] border-ink bg-white px-4 py-3 shadow-pop-sm transition-transform ease-back hover:-translate-x-0.5 hover:-translate-y-0.5 hover:shadow-pop"
            >
              <StatusBadge status={r.status} />
              <span className="font-bold">{r.flow}</span>
              <span className="font-mono text-xs text-sub">{r.started_at}</span>
              <span className="ml-auto font-mono text-xs text-sub">{r.artifact_count} 产物</span>
              <span className="font-mono text-sub">›</span>
            </Link>
          ))}
        </div>
      </main>
    </div>
  );
}
