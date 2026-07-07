import { useState, type ReactNode } from 'react';

import { Icon } from '@/components/Icon';
import { TILE_BG, tileColor, tileGlyphIsInk } from '@/config/palette';
import { useRunsStore } from '@/stores/runsStore';
import type { Flow } from '@/types/api.types';
import { collectParams, initValues, ParamForm, valuesFromParams, type FormValues } from './ParamForm';
import { PresetBar } from './PresetBar';
import { RunOutput } from './RunOutput';

function Badge({ children, className }: { children: ReactNode; className: string }) {
  return (
    <span
      className={`whitespace-nowrap rounded-md border-2 border-ink px-2 py-0.5 font-mono text-[10px] font-bold leading-none ${className}`}
    >
      {children}
    </span>
  );
}

export function FlowCard({ flow, index }: { flow: Flow; index: number }) {
  const [open, setOpen] = useState(false);
  const [values, setValues] = useState<FormValues>(() => initValues(flow));
  const [dryRun, setDryRun] = useState(false);
  const start = useRunsStore((s) => s.start);
  const run = useRunsStore((s) => s.currentRun(flow.name));
  const running = run?.status === 'running';
  const color = tileColor(index);

  async function onRun() {
    let yes = false;
    if (flow.write_ops && !dryRun) {
      const ok = window.confirm(
        `「${flow.title}」是写操作流程。\n\n流程会停在提交按钮前、不会自己点提交，最后一下交回给你。\n\n确认现在运行？`,
      );
      if (!ok) return;
      yes = true;
    }
    await start(flow.name, collectParams(flow, values), dryRun, yes);
  }

  return (
    <article
      className={`relative rounded-[20px] border-[2.5px] border-ink bg-white shadow-pop-lg transition-[transform,box-shadow] duration-200 ease-pop hover:-translate-x-[3px] hover:-translate-y-[3px] hover:shadow-pop-xl ${
        open ? 'col-[1/-1]' : ''
      }`}
    >
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        className="flex w-full items-start gap-3.5 p-5 text-left"
        aria-expanded={open}
      >
        <span
          className={`-ml-2 -mt-[18px] grid h-12 w-12 flex-none place-items-center rounded-[13px] border-[2.5px] border-ink shadow-pop-sm ${TILE_BG[color]} ${
            tileGlyphIsInk(color) ? 'text-ink' : 'text-white'
          }`}
        >
          <Icon name={flow.icon} size={24} />
        </span>
        <span className="min-w-0 flex-1">
          <span className="flex flex-wrap items-center gap-2">
            <span className="font-grot text-xl font-bold tracking-tight">{flow.title}</span>
            {flow.write_ops && <Badge className="bg-coral text-white">写操作</Badge>}
            {flow.source === 'private' && <Badge className="bg-paper text-ink">私有</Badge>}
          </span>
          <span className="mt-1.5 block text-[13px] font-medium leading-relaxed text-sub">
            {flow.description}
          </span>
        </span>
        <span
          className={`mt-2 h-3.5 w-3.5 flex-none rotate-45 border-b-[2.5px] border-r-[2.5px] border-ink transition-transform duration-300 ease-pop ${
            open ? 'rotate-[225deg]' : ''
          }`}
          aria-hidden
        />
      </button>

      {open && (
        <div className="border-t-[2.5px] border-ink p-6">
          <PresetBar
            flow={flow}
            values={values}
            onLoad={(params) => setValues(valuesFromParams(flow, params))}
          />
          <ParamForm
            params={flow.params}
            values={values}
            onChange={(k, v) => setValues((s) => ({ ...s, [k]: v }))}
          />
          <label className="mt-5 flex cursor-pointer items-center gap-2.5 text-sm font-semibold">
            <input
              type="checkbox"
              checked={dryRun}
              onChange={(e) => setDryRun(e.target.checked)}
              className="h-5 w-5 accent-blue"
            />
            <span>
              Dry-run <span className="font-normal text-sub">· 只连接 + 定位，不执行动作</span>
            </span>
          </label>
          <div className="mt-5 flex flex-wrap items-center gap-3">
            <button
              type="button"
              onClick={onRun}
              disabled={running}
              className="rounded-xl border-[2.5px] border-ink bg-coral px-6 py-2.5 font-grot font-bold text-white shadow-pop transition-transform ease-tap hover:-translate-x-0.5 hover:-translate-y-0.5 hover:shadow-pop-lg active:translate-x-0.5 active:translate-y-0.5 disabled:opacity-70"
            >
              {running ? '运行中…' : dryRun ? 'Dry-run' : '运行'}
            </button>
            {flow.write_ops && (
              <span className="font-mono text-xs text-coral">写操作 · 会停在提交前，需二次确认</span>
            )}
          </div>
          {run && <RunOutput run={run} />}
        </div>
      )}
    </article>
  );
}
