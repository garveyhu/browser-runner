import { useDoctor } from '@/hooks/useDoctor';

export function SecretsBar() {
  const { data } = useDoctor();
  const missing = data?.missing_secrets ?? [];
  if (!missing.length) return null;
  return (
    <div className="mx-auto mt-4 max-w-5xl px-6">
      <div className="flex items-center gap-3 border-2 border-ink bg-sun px-4 py-3 shadow-pop-sm">
        <span className="font-mono font-bold">!</span>
        <span className="text-sm">
          缺配置：<b>{missing.join('、')}</b> —— 在 <code className="font-mono text-[13px]">var/secrets.toml</code>{' '}
          补上后重跑对应流程。
        </span>
      </div>
    </div>
  );
}
