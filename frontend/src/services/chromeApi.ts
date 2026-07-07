import { httpGet, httpPost } from '@/services/http';
import type { ChromeLaunchResult, ChromeStatus } from '@/types/api.types';

export const chromeApi = {
  status: () => httpGet<ChromeStatus>('/chrome/status'),
  launch: () => httpPost<ChromeLaunchResult>('/chrome/launch'),
};
