import { useQuery } from '@tanstack/react-query';

import { runApi, type RunListQuery } from '@/services/runApi';

export function useRuns(query?: RunListQuery) {
  return useQuery({
    queryKey: ['runs', query ?? {}],
    queryFn: () => runApi.list(query),
    refetchInterval: 5000,
  });
}
