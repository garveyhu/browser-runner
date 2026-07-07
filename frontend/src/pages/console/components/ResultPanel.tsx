import { useState } from 'react';

import type { RunResult } from '@/types/api.types';

const RESERVED = new Set(['ok', 'error', 'items', 'todo', 'stopped_at']);

// 短标量（数字 / 短字符串）→ 大数字块；长字符串 / 路径 → 小行（防撑爆）
function isMetric(v: unknown): boolean {
  if (typeof v === 'number') return true;
  if (typeof v === 'string') return v.length <= 18 && !v.includes('/');
  return false;
}

function asText(v: unknown): string {
  return typeof v === 'object' && v !== null ? JSON.stringify(v) : String(v);
}

export function ResultPanel({ result }: { result: RunResult; runId: string }) {
  if (!result.ok) {
    return (
      <div className="border-t-2 border-ink bg-coral p-4 text-white">
        <div className="font-mono text-xs font-black uppercase">失败</div>
        {result.error && <div className="mt-1 break-words font-mono text-xs">{result.error}</div>}
      </div>
    );
  }

  const entries = Object.entries(result).filter(([k, v]) => !RESERVED.has(k) && v != null);
  const metrics = entries.filter(([, v]) => isMetric(v));
  const paths = entries.filter(([, v]) => !isMetric(v));
  const items = Array.isArray(result.items) ? (result.items as unknown[]) : null;

  return (
    <div className="border-t-2 border-ink p-4">
      {metrics.length > 0 && (
        <div className="flex flex-wrap gap-x-8 gap-y-4">
          {metrics.map(([k, v]) => (
            <div key={k}>
              <div className="font-mono text-[10px] font-bold uppercase tracking-wider text-sub">{k}</div>
              <div className="mt-0.5 font-mono text-3xl font-black tabular-nums text-blue">{asText(v)}</div>
            </div>
          ))}
        </div>
      )}

      {paths.length > 0 && (
        <div className="mt-4 flex flex-col gap-2">
          {paths.map(([k, v]) => (
            <PathRow key={k} label={k} value={asText(v)} />
          ))}
        </div>
      )}

      {items && items.length > 0 && <ItemsBox items={items} />}

      <details className="mt-4 text-xs">
        <summary className="cursor-pointer font-mono text-sub">原始结果 JSON</summary>
        <pre className="mt-2 max-h-64 overflow-auto border-2 border-line bg-panel p-3 font-mono text-[11px]">
          {JSON.stringify(result, null, 2)}
        </pre>
      </details>
    </div>
  );
}

function PathRow({ label, value }: { label: string; value: string }) {
  const [copied, setCopied] = useState(false);
  function copy() {
    navigator.clipboard?.writeText(value).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    });
  }
  return (
    <div className="rounded-xl border-2 border-ink bg-paper px-3 py-2">
      <div className="flex items-center justify-between gap-3 font-mono text-[10px] font-bold uppercase tracking-wider text-sub">
        <span>{label}</span>
        <button
          type="button"
          onClick={copy}
          className="shrink-0 rounded-md border-2 border-ink bg-white px-2 py-0.5 text-[10px] transition-transform ease-back hover:-translate-x-px hover:-translate-y-px hover:bg-lime"
        >
          {copied ? '已复制' : '复制'}
        </button>
      </div>
      <div className="mt-1 break-all font-mono text-xs">{value}</div>
    </div>
  );
}

function ItemsBox({ items }: { items: unknown[] }) {
  return (
    <div className="mt-4 border-2 border-ink">
      <div className="flex items-center justify-between border-b-2 border-ink bg-panel px-3 py-2">
        <span className="font-mono text-xs font-bold uppercase">采集结果</span>
        <span className="font-mono text-[11px] text-sub">{items.length} 条</span>
      </div>
      <div className="max-h-72 overflow-auto">
        {items.slice(0, 60).map((it, i) => (
          <div key={i} className="break-all border-b border-line px-3 py-2 font-mono text-xs">
            {typeof it === 'object' && it !== null ? JSON.stringify(it) : String(it)}
          </div>
        ))}
      </div>
    </div>
  );
}
