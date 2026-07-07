import { useDoctor } from '@/hooks/useDoctor';

export function SecretsBar() {
  const { data } = useDoctor();
  const missing = data?.missing_secrets ?? [];
  if (!missing.length) return null;
  return (
    <div className="mx-auto mt-4 max-w-[1120px] px-8">
      <div className="flex items-center gap-3 rounded-2xl border-[2.5px] border-ink bg-yellow px-4 py-3 shadow-pop">
        <span className="grid h-[22px] w-[22px] flex-none place-items-center rounded-full border-2 border-ink bg-coral font-black text-white">
          !
        </span>
        <span className="text-sm font-semibold">
          缺配置：<b className="text-coral">{missing.join('、')}</b> —— 在{' '}
          <code className="rounded border-2 border-ink bg-white px-1.5 py-0.5 font-mono text-[12px]">
            var/secrets.toml
          </code>{' '}
          补上后重跑对应流程。
        </span>
      </div>
    </div>
  );
}
