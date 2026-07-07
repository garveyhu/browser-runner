export type ParamType = 'string' | 'int' | 'float' | 'bool';

export interface FlowParam {
  key: string;
  label: string;
  type: ParamType;
  required: boolean;
  default: unknown;
}

export interface Flow {
  name: string;
  title: string;
  description: string;
  icon: string;
  group: string;
  write_ops: boolean;
  landing_url: string;
  params: FlowParam[];
  needs: string[];
  source: string;
  last_params?: Record<string, unknown>;
}

export interface Doctor {
  port: number;
  flows: number;
  missing_secrets: string[];
  chrome_alive: boolean;
  engine_ok: boolean;
  max_concurrent: number;
}

export interface ChromeStatus {
  port: number;
  alive: boolean;
}

export interface ChromeLaunchResult {
  ok: boolean;
  port: number;
  message: string;
}

export type RunStatus =
  | 'pending'
  | 'running'
  | 'succeeded'
  | 'failed'
  | 'cancelled'
  | 'error'
  | 'interrupted';

export interface RunResult {
  ok: boolean;
  error?: string;
  [k: string]: unknown;
}

export interface Artifact {
  name: string;
  size: number;
  kind: string;
  mtime: string;
}

export interface RunSummary {
  run_id: string;
  flow: string;
  status: RunStatus;
  started_at: string;
  artifact_count: number;
}

export interface RunDetail {
  run_id: string;
  flow: string;
  params: Record<string, unknown> | null;
  dry_run: boolean;
  status: RunStatus;
  started_at: string;
  ended_at: string | null;
  exit_code: number | null;
  result: RunResult | null;
  artifacts: Artifact[];
  workdir: string;
}

export interface RunListResult {
  total: number;
  runs: RunSummary[];
}

export interface StartRunResponse {
  run_id: string;
  status: RunStatus;
}

export interface Preset {
  id: string;
  flow: string;
  name: string;
  params: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export interface CsvPreview {
  columns: string[];
  rows: string[][];
  total: number;
  truncated: boolean;
}
