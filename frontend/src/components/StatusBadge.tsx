import type { RunStatus } from '@/types/api.types';

const MAP: Record<string, [string, string]> = {
  pending: ['bg-sun text-ink', '排队'],
  running: ['bg-blue text-white', '运行中'],
  succeeded: ['bg-lime text-ink', '完成'],
  failed: ['bg-coral text-white', '失败'],
  cancelled: ['bg-sub text-white', '已取消'],
  error: ['bg-coral text-white', '出错'],
  interrupted: ['bg-sub text-white', '中断'],
};

export function StatusBadge({ status, label }: { status: RunStatus; label?: string }) {
  const [cls, text] = MAP[status] ?? ['bg-sub text-white', status];
  return (
    <span className={`border border-ink px-2 py-0.5 font-mono text-xs font-bold ${cls}`}>
      {label ?? text}
    </span>
  );
}
