import { useState, type ReactNode } from 'react';

import { Icon } from '@/components/Icon';
import { TILE_BG, tileColor, tileGlyphIsInk } from '@/config/palette';
import { revealDelay } from '@/config/ui';
import { useRunsStore } from '@/stores/runsStore';
import type { Flow } from '@/types/api.types';
import { collectParams, initValues, ParamForm, valuesFromParams, type FormValues } from './ParamForm';
import { PresetBar } from './PresetBar';
import { RunOutput } from './RunOutput';

function Badge({ children, className }: { children: ReactNode; className: string }) {
  return (
    <span className={`shrink-0 border border-ink px-1.5 py-px font-mono text-[10px] font-bold ${className}`}>
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
    <article className="reveal border-[2.5px] border-ink bg-panel shadow-pop" style={revealDelay(index)}>
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        className="flex w-full items-center gap-4 p-5 text-left"
        aria-expanded={open}
      >
        <span
          className={`grid h-11 w-11 shrink-0 place-items-center border-2 border-ink ${TILE_BG[color]} ${
            tileGlyphIsInk(color) ? 'text-ink' : 'text-white'
          }`}
        >
          <Icon name={flow.icon} size={22} />
        </span>
        <span className="min-w-0 flex-1">
          <span className="flex items-center gap-2">
            <span className="truncate font-extrabold">{flow.title}</span>
            {flow.write_ops && <Badge className="bg-coral text-white">写操作</Badge>}
            {flow.source === 'private' && <Badge className="bg-lime text-ink">私有</Badge>}
          </span>
          <span className="mt-0.5 block truncate text-sm text-sub">{flow.description}</span>
        </span>
        <span className={`shrink-0 font-mono text-xl transition-transform ease-back ${open ? 'rotate-90' : ''}`}>
          ›
        </span>
      </button>

      {open && (
        <div className="border-t-2 border-line p-5">
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
          <label className="mt-4 flex cursor-pointer items-center gap-2 text-sm">
            <input
              type="checkbox"
              checked={dryRun}
              onChange={(e) => setDryRun(e.target.checked)}
              className="h-4 w-4 accent-blue"
            />
            <span>
              Dry-run <span className="text-sub">· 只连接 + 定位，不执行动作</span>
            </span>
          </label>
          <div className="mt-4 flex flex-wrap items-center gap-3">
            <button
              type="button"
              onClick={onRun}
              disabled={running}
              className="border-2 border-ink bg-lime px-5 py-2 font-bold text-ink shadow-pop-sm transition-transform ease-back hover:-translate-x-0.5 hover:-translate-y-0.5 disabled:opacity-60"
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
