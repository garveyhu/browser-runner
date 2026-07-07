import { useQuery } from '@tanstack/react-query';

import { presetApi } from '@/services/presetApi';

export function usePresets(flow?: string) {
  return useQuery({ queryKey: ['presets', flow ?? null], queryFn: () => presetApi.list(flow) });
}
