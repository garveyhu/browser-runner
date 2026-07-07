import { useQuery } from '@tanstack/react-query';

import { doctorApi } from '@/services/doctorApi';

export function useDoctor() {
  return useQuery({ queryKey: ['doctor'], queryFn: doctorApi.get, refetchInterval: 8000 });
}
