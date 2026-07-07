import { PosterHeader } from '@/components/PosterHeader';
import { SecretsBar } from '@/components/SecretsBar';
import { useFlows } from '@/hooks/useFlows';
import type { Flow } from '@/types/api.types';
import { EmptyState } from './components/EmptyState';
import { FlowCard } from './components/FlowCard';

export default function ConsolePage() {
  const { data: flows, isLoading, isError, error } = useFlows();
  return (
    <div className="min-h-full pb-24">
      <PosterHeader />
      <SecretsBar />
      <main className="mx-auto max-w-5xl px-6 pt-10">
        {isLoading && <div className="font-mono text-sub">加载流程清单…</div>}
        {isError && (
          <div className="border-2 border-ink bg-coral p-4 text-white">
            加载失败：{(error as Error).message} —— 确认后端在跑（./scripts/dev.sh）。
          </div>
        )}
        {flows && flows.length === 0 && <EmptyState />}
        {flows && flows.length > 0 && <FlowGroups flows={flows} />}
      </main>
      <footer className="mx-auto mt-16 max-w-5xl border-t-2 border-line px-6 pt-6 text-center font-mono text-xs text-sub">
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
    <div className="flex flex-col gap-10">
      {[...groups.entries()].map(([name, items]) => (
        <section key={name}>
          <h2 className="mb-4 flex items-center gap-3 font-mono text-xs uppercase tracking-[0.16em] text-sub">
            <span>{name}</span>
            <span className="text-line">·</span>
            <span>{items.length}</span>
            <span className="h-px flex-1 bg-line" />
          </h2>
          <div className="flex flex-col gap-4">
            {items.map((f) => (
              <FlowCard key={f.name} flow={f} index={idx++} />
            ))}
          </div>
        </section>
      ))}
    </div>
  );
}
