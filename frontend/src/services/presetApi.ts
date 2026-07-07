import { httpGet, httpPost } from '@/services/http';
import type { Preset } from '@/types/api.types';

export const presetApi = {
  list: (flow?: string) =>
    httpGet<Preset[]>(`/presets${flow ? `?flow=${encodeURIComponent(flow)}` : ''}`),
  create: (body: { flow: string; name: string; params: Record<string, unknown> }) =>
    httpPost<Preset>('/presets/create', body),
  update: (id: string, body: { name?: string; params?: Record<string, unknown> }) =>
    httpPost<Preset>(`/presets/${id}/update`, body),
  remove: (id: string) => httpPost<{ id: string }>(`/presets/${id}/delete`),
};
