import { useQuery } from '@tanstack/react-query';

import { runApi } from '@/services/runApi';

export function useRunDetail(runId: string | undefined) {
  return useQuery({
    queryKey: ['run', runId],
    queryFn: () => runApi.detail(runId as string),
    enabled: !!runId,
    // 运行中每 3s 刷新，落终态后停
    refetchInterval: (query) => {
      const s = query.state.data?.status;
      return s === 'running' || s === 'pending' ? 3000 : false;
    },
  });
}
