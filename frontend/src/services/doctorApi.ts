import { httpGet } from '@/services/http';
import type { Doctor } from '@/types/api.types';

export const doctorApi = {
  get: () => httpGet<Doctor>('/doctor'),
};
