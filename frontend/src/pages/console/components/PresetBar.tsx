import { useQueryClient } from '@tanstack/react-query';

import { usePresets } from '@/hooks/usePresets';
import { presetApi } from '@/services/presetApi';
import type { Flow } from '@/types/api.types';
import { collectParams, type FormValues } from './ParamForm';

interface PresetBarProps {
  flow: Flow;
  values: FormValues;
  onLoad: (params: Record<string, unknown>) => void;
}

/** 参数预设：存当前参数、一键加载、删除。存 var/state/presets.json（后端）。 */
export function PresetBar({ flow, values, onLoad }: PresetBarProps) {
  const { data: presets } = usePresets(flow.name);
  const qc = useQueryClient();

  async function save() {
    const name = window.prompt('预设名？');
    if (!name) return;
    await presetApi.create({ flow: flow.name, name, params: collectParams(flow, values) });
    await qc.invalidateQueries({ queryKey: ['presets', flow.name] });
  }

  async function remove(id: string) {
    await presetApi.remove(id);
    await qc.invalidateQueries({ queryKey: ['presets', flow.name] });
  }

  return (
    <div className="mb-4 flex flex-wrap items-center gap-2">
      <span className="font-mono text-[10px] uppercase tracking-wider text-sub">预设</span>
      {(presets ?? []).map((p) => (
        <span key={p.id} className="inline-flex items-center gap-1.5 border-2 border-ink bg-white px-2 py-1 text-xs">
          <button type="button" onClick={() => onLoad(p.params)} className="hover:text-blue">
            {p.name}
          </button>
          <button
            type="button"
            onClick={() => remove(p.id)}
            className="text-sub hover:text-coral"
            title="删除预设"
          >
            ×
          </button>
        </span>
      ))}
      <button
        type="button"
        onClick={save}
        className="border-2 border-dashed border-ink px-2 py-1 text-xs text-sub transition-colors hover:bg-lime hover:text-ink"
      >
        + 存为预设
      </button>
    </div>
  );
}
