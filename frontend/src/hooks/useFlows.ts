import { useQuery } from '@tanstack/react-query';

import { flowApi } from '@/services/flowApi';

export function useFlows() {
  return useQuery({ queryKey: ['flows'], queryFn: flowApi.list });
}
