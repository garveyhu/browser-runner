import react from '@vitejs/plugin-react';
import path from 'node:path';
import { defineConfig } from 'vite';

// 前端同源访问后端：/api 代理到 FastAPI（含 SSE）。生产 build 产物由 FastAPI 托管。
export default defineConfig({
  plugins: [react()],
  resolve: { alias: { '@': path.resolve(__dirname, 'src') } },
  server: {
    port: 5173,
    proxy: {
      '/api': { target: 'http://127.0.0.1:8760', changeOrigin: true },
    },
  },
  build: { outDir: 'dist' },
});
