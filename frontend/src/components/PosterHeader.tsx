import { useQueryClient } from '@tanstack/react-query';
import { useState, type ReactNode } from 'react';
import { Link, useLocation } from 'react-router-dom';

import { revealDelay } from '@/config/ui';
import { useDoctor } from '@/hooks/useDoctor';
import { chromeApi } from '@/services/chromeApi';

function Chip({ value, label }: { value: ReactNode; label: string }) {
  return (
    <span className="inline-flex items-baseline gap-2 border-2 border-ink px-3 py-1.5 font-mono text-xs">
      <b className="text-base font-extrabold tabular-nums">{value}</b>
      <span className="text-sub">{label}</span>
    </span>
  );
}

const navCls = (active: boolean) =>
  `font-mono text-xs px-3 py-1.5 border-2 border-ink transition-transform ease-back hover:-translate-x-0.5 hover:-translate-y-0.5 hover:shadow-pop-sm ${
    active ? 'bg-ink text-paper' : 'bg-transparent text-ink'
  }`;

export function PosterHeader() {
  const { data: doctor } = useDoctor();
  const qc = useQueryClient();
  const { pathname } = useLocation();
  const [launching, setLaunching] = useState(false);
  const alive = doctor?.chrome_alive ?? false;

  async function launchChrome() {
    setLaunching(true);
    try {
      await chromeApi.launch();
    } catch {
      /* 忽略：连接状态由 doctor 轮询兜底 */
    }
    await qc.invalidateQueries({ queryKey: ['doctor'] });
    setLaunching(false);
  }

  return (
    <header
      className="reveal relative mx-auto max-w-5xl border-b-[3px] border-ink px-6 pb-6 pt-10"
      style={revealDelay(0)}
    >
      <svg
        className="pointer-events-none absolute right-4 top-4 hidden h-16 w-16 md:block"
        viewBox="0 0 100 100"
        aria-hidden
      >
        <path
          d="M50 2l9 20 21-9-9 21 20 9-20 9 9 21-21-9-9 20-9-20-21 9 9-21-20-9 20-9-9-21 21 9z"
          fill="#c7f03a"
          stroke="#141414"
          strokeWidth="3"
          strokeLinejoin="round"
        />
      </svg>

      <div className="mb-4 flex items-center gap-3">
        <span className="bg-ink px-2 py-1 font-mono text-xs font-bold tracking-widest text-paper">01</span>
        <span className="font-mono text-xs uppercase tracking-[0.2em] text-sub">
          Browser Automation · Console
        </span>
      </div>

      <h1 className="text-5xl font-black leading-none tracking-tight md:text-6xl">
        browser<span className="text-coral">·</span>runner
      </h1>
      <p className="mt-4 max-w-2xl text-lg text-sub">
        把重复的浏览器操作，attach 你真实已登录的浏览器，沉淀成秒级可复放的脚本。
      </p>

      <div className="mt-6 flex flex-wrap items-center gap-3">
        <Chip value={doctor?.flows ?? '–'} label="流程" />
        <Chip value={doctor?.port ?? '–'} label="调试端口" />
        <span className="inline-flex items-center gap-2 border-2 border-ink px-3 py-1.5 font-mono text-xs">
          <span
            className={`h-2 w-2 rounded-full ${alive ? 'animate-pulse bg-lime' : 'bg-sub'}`}
            aria-hidden
          />
          {alive ? '已连接' : '未连接'}
        </span>
        {!alive && (
          <button
            type="button"
            onClick={launchChrome}
            disabled={launching}
            className="inline-flex items-center gap-2 border-2 border-ink bg-blue px-3 py-1.5 font-mono text-xs font-bold text-white shadow-pop-sm transition-transform ease-back hover:-translate-x-0.5 hover:-translate-y-0.5 disabled:opacity-60"
          >
            {launching ? '启动中… 首次弹窗登录' : '起调试 Chrome'}
          </button>
        )}

        <span className="mx-1 h-5 w-px bg-line" />
        <Link to="/" className={navCls(pathname === '/')}>
          控制台
        </Link>
        <Link to="/runs" className={navCls(pathname.startsWith('/runs'))}>
          运行历史
        </Link>
      </div>
    </header>
  );
}
