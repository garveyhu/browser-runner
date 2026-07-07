import { PosterHeader } from '@/components/PosterHeader';
import { SecretsBar } from '@/components/SecretsBar';
import { useFlows } from '@/hooks/useFlows';
import type { Flow } from '@/types/api.types';
import { EmptyState } from './components/EmptyState';
import { FlowCard } from './components/FlowCard';

export default function ConsolePage() {
  const { data: flows, isLoading, isError, error } = useFlows();
  return (
    <div className="min-h-full pb-28">
      <PosterHeader />
      <SecretsBar />
      <main className="mx-auto max-w-[1120px] px-8 pt-10">
        {isLoading && <div className="font-mono text-sm font-semibold text-sub">加载流程清单…</div>}
        {isError && (
          <div className="rounded-2xl border-[2.5px] border-ink bg-coral p-5 font-semibold text-white shadow-pop">
            加载失败：{(error as Error).message} —— 确认后端在跑（./scripts/dev.sh）。
          </div>
        )}
        {flows && flows.length === 0 && <EmptyState />}
        {flows && flows.length > 0 && <FlowGroups flows={flows} />}
      </main>
      <footer className="mx-auto mt-20 max-w-[1120px] px-8 text-center font-mono text-xs font-semibold text-sub">
        一个流程一个目录 · 加流程不改内核 · 写操作停在提交前
      </footer>
    </div>
  );
}

function FlowGroups({ flows }: { flows: Flow[] }) {
  const groups = new Map<string, Flow[]>();
  for (const f of flows) {
    const g = f.group || '未分组';
    if (!groups.has(g)) groups.set(g, []);
    groups.get(g)!.push(f);
  }
  let idx = 0;
  return (
    <div className="flex flex-col gap-12">
      {[...groups.entries()].map(([name, items]) => (
        <section key={name}>
          <h2 className="mb-6 flex items-center gap-3 font-grot text-[15px] font-extrabold uppercase tracking-wide">
            <span>{name}</span>
            <span className="rounded-md bg-ink px-2 py-0.5 font-mono text-[11px] font-bold text-white">
              {items.length}
            </span>
            <span className="h-[2.5px] flex-1 bg-ink" />
          </h2>
          <div className="grid grid-cols-[repeat(auto-fill,minmax(330px,1fr))] items-start gap-x-6 gap-y-8">
            {items.map((f) => (
              <FlowCard key={f.name} flow={f} index={idx++} />
            ))}
          </div>
        </section>
      ))}
    </div>
  );
}
