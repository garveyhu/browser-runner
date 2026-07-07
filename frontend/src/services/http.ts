// 统一 HTTP 客户端 —— 解 Result 封套（{success,code,message,data}），非成功走错误流。
// 约束：所有 HTTP 只在 services/，组件/hook 不出现 fetch。

const BASE = '/api';

export class ApiError extends Error {
  code: number;
  constructor(message: string, code: number) {
    super(message);
    this.code = code;
    this.name = 'ApiError';
  }
}

interface Envelope<T> {
  success: boolean;
  code: number;
  message: string;
  data: T;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(BASE + path, {
    headers: { 'Content-Type': 'application/json', ...(init?.headers ?? {}) },
    ...init,
  });
  let json: Envelope<T>;
  try {
    json = (await res.json()) as Envelope<T>;
  } catch {
    throw new ApiError(`HTTP ${res.status}`, res.status);
  }
  if (!json.success) {
    throw new ApiError(json.message || `HTTP ${res.status}`, json.code || res.status);
  }
  return json.data;
}

export const httpGet = <T>(path: string) => request<T>(path);
export const httpPost = <T>(path: string, body?: unknown) =>
  request<T>(path, {
    method: 'POST',
    body: body === undefined ? undefined : JSON.stringify(body),
  });
