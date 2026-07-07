import { useQueryClient } from '@tanstack/react-query';
import { useState, type ReactNode } from 'react';
import { Link, useLocation } from 'react-router-dom';

import { revealDelay } from '@/config/ui';
import { useDoctor } from '@/hooks/useDoctor';
import { chromeApi } from '@/services/chromeApi';

function CornerMarks() {
  const base = 'pointer-events-none fixed z-40 h-[34px] w-[34px] border-[2.5px] border-blue';
  return (
    <>
      <span className={`${base} left-[18px] top-[18px] border-b-0 border-r-0`} aria-hidden />
      <span className={`${base} right-[18px] top-[18px] border-b-0 border-l-0`} aria-hidden />
      <span className={`${base} bottom-[18px] left-[18px] border-r-0 border-t-0`} aria-hidden />
      <span className={`${base} bottom-[18px] right-[18px] border-l-0 border-t-0`} aria-hidden />
    </>
  );
}

function Chip({
  tone,
  value,
  label,
  dot,
}: {
  tone: string;
  value?: ReactNode;
  label: string;
  dot?: boolean;
}) {
  return (
    <span
      className={`flex items-center gap-2.5 rounded-2xl border-[2.5px] border-ink px-4 py-2.5 shadow-pop ${tone}`}
    >
      {dot !== undefined && (
        <span
          className={`h-[11px] w-[11px] flex-none rounded-full border-2 border-ink ${
            dot ? 'animate-bpulse bg-ink' : 'bg-[#9aa0a6]'
          }`}
          aria-hidden
        />
      )}
      {value != null && (
        <b className="font-grot text-[30px] font-black leading-none tracking-[-0.03em] tabular-nums">
          {value}
        </b>
      )}
      <span className="font-mono text-[10px] font-bold uppercase tracking-[0.12em] opacity-70">
        {label}
      </span>
    </span>
  );
}

const navCls = (active: boolean) =>
  `rounded-xl border-[2.5px] border-ink px-3.5 py-2 font-grot text-sm font-bold transition-transform ease-tap hover:-translate-x-0.5 hover:-translate-y-0.5 hover:shadow-pop-sm ${
    active ? 'bg-ink text-white' : 'bg-white text-ink'
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
    <>
      <CornerMarks />
      <header
        className="reveal relative mx-auto max-w-[1120px] px-8 pb-8 pt-[72px]"
        style={revealDelay(0)}
      >
        {/* 贴纸（破框 · idle 动） */}
        <svg
          className="animate-spinslow pointer-events-none absolute right-[3%] top-[52px] h-[88px] w-[88px]"
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
        <svg
          className="animate-floaty pointer-events-none absolute right-[18%] top-[228px] hidden w-[74px] md:block"
          viewBox="0 0 80 60"
          aria-hidden
        >
          <path d="M6 40 C 26 6, 52 6, 70 26" fill="none" stroke="#ff4d4d" strokeWidth="6" strokeLinecap="round" />
          <path d="M56 20l16 6-8 15z" fill="#ff4d4d" stroke="#141414" strokeWidth="2.5" strokeLinejoin="round" />
        </svg>
        <svg
          className="animate-wobble pointer-events-none absolute bottom-[-14px] left-[26%] hidden w-[116px] md:block"
          viewBox="0 0 120 30"
          aria-hidden
        >
          <path d="M4 15 Q 19 -3, 34 15 T 64 15 T 94 15 T 116 15" fill="none" stroke="#7b3ff2" strokeWidth="6" strokeLinecap="round" />
        </svg>

        <div className="flex items-center gap-3.5">
          <span className="rounded-xl border-[2.5px] border-ink bg-blue px-3 pb-1.5 pt-2 font-grot text-[30px] font-black leading-none tracking-tight text-white shadow-pop">
            01
          </span>
          <span className="font-mono text-[11px] font-bold uppercase tracking-[0.28em]">
            Browser Automation · Console
          </span>
        </div>

        <h1 className="wordmark-stroke mt-4 font-grot text-[clamp(52px,12vw,128px)] font-black leading-[0.9] tracking-[-0.05em] text-blue">
          browser<span className="text-coral">·</span>runner
        </h1>
        <p className="mt-5 max-w-[40ch] text-base font-semibold leading-relaxed">
          把重复的浏览器操作，attach 你真实已登录的浏览器，沉淀成秒级可复放的脚本。
        </p>

        <div className="mt-8 flex flex-wrap items-center gap-4">
          <Chip tone="bg-yellow" value={doctor?.flows ?? '–'} label="流程" />
          <Chip tone="bg-cyan" value={doctor?.port ?? '–'} label="调试端口" />
          <Chip tone={alive ? 'bg-lime' : 'bg-white'} label={alive ? '已连接' : '未连接'} dot={alive} />
          {!alive && (
            <button
              type="button"
              onClick={launchChrome}
              disabled={launching}
              className="rounded-xl border-[2.5px] border-ink bg-ink px-4 py-2.5 font-grot text-sm font-bold text-white shadow-pop transition-transform ease-tap hover:-translate-x-0.5 hover:-translate-y-0.5 hover:shadow-pop-lg active:translate-x-0.5 active:translate-y-0.5 disabled:opacity-70"
            >
              {launching ? '启动中… 首次弹窗登录' : '起调试 Chrome'}
            </button>
          )}

          <span className="mx-1 h-6 w-px bg-ink/20" />
          <Link to="/" className={navCls(pathname === '/')}>
            控制台
          </Link>
          <Link to="/runs" className={navCls(pathname.startsWith('/runs'))}>
            运行历史
          </Link>
        </div>
      </header>
    </>
  );
}
