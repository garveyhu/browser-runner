import { httpGet } from '@/services/http';
import type { Flow } from '@/types/api.types';

export const flowApi = {
  list: () => httpGet<Flow[]>('/flows'),
  get: (name: string) => httpGet<Flow>(`/flows/${encodeURIComponent(name)}`),
};
