import type { Flow, FlowParam } from '@/types/api.types';

export type FormValues = Record<string, string | boolean>;

interface ParamFormProps {
  params: FlowParam[];
  values: FormValues;
  onChange: (key: string, value: string | boolean) => void;
}

/** 按 params schema 通用生成表单 —— 加流程零改前端的关键。 */
export function ParamForm({ params, values, onChange }: ParamFormProps) {
  if (!params.length) {
    return <p className="text-sm text-sub">此流程无需参数，直接运行。</p>;
  }
  return (
    <div className="flex flex-col gap-4">
      {params.map((p) => (
        <label key={p.key} className="flex flex-col gap-1.5">
          <span className="flex items-center gap-2 text-sm font-medium">
            {p.label}
            {p.required && (
              <span className="border border-coral px-1 py-px font-mono text-[10px] text-coral">必填</span>
            )}
          </span>
          {p.type === 'bool' ? (
            <input
              type="checkbox"
              checked={values[p.key] === true}
              onChange={(e) => onChange(p.key, e.target.checked)}
              className="h-5 w-5 accent-blue"
            />
          ) : (
            <input
              type={p.type === 'int' || p.type === 'float' ? 'number' : 'text'}
              step={p.type === 'float' ? 'any' : undefined}
              value={String(values[p.key] ?? '')}
              required={p.required}
              placeholder={placeholderFor(p)}
              onChange={(e) => onChange(p.key, e.target.value)}
              className="border-2 border-ink bg-paper px-3 py-2 text-sm outline-none focus:shadow-pop-sm"
            />
          )}
        </label>
      ))}
    </div>
  );
}

function placeholderFor(p: FlowParam): string {
  if (p.required) return '必填';
  if (p.default != null && p.default !== '') return String(p.default);
  return '可选';
}

/** 表单初值：优先上次参数，其次 default。 */
export function initValues(flow: Flow): FormValues {
  const v: FormValues = {};
  const last = flow.last_params ?? {};
  for (const p of flow.params) {
    const src = p.key in last ? last[p.key] : p.default;
    v[p.key] = p.type === 'bool' ? src === true || src === 'true' : src == null ? '' : String(src);
  }
  return v;
}

/** 从一组已保存参数回填表单值（预设加载用）。 */
export function valuesFromParams(flow: Flow, params: Record<string, unknown>): FormValues {
  const v = initValues(flow);
  for (const p of flow.params) {
    if (p.key in params) {
      const val = params[p.key];
      v[p.key] = p.type === 'bool' ? Boolean(val) : val == null ? '' : String(val);
    }
  }
  return v;
}

/** 收集类型化取值：空的可选项省略（让后端填默认 / 校验必填）。 */
export function collectParams(flow: Flow, values: FormValues): Record<string, unknown> {
  const out: Record<string, unknown> = {};
  for (const p of flow.params) {
    if (p.type === 'bool') {
      out[p.key] = values[p.key] === true;
      continue;
    }
    const s = String(values[p.key] ?? '').trim();
    if (s === '') continue;
    if (p.type === 'int') out[p.key] = parseInt(s, 10);
    else if (p.type === 'float') out[p.key] = parseFloat(s);
    else out[p.key] = s;
  }
  return out;
}
