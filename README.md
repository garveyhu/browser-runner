# browser-runner

把重复的浏览器操作，attach 你**真实、已登录**的 Chrome，沉淀成秒级可复放的流程。全栈本地工具：Python 引擎 + FastAPI 后端 + React 前端，外加一个本机 CLI。

## 为什么是「attach 真实浏览器」
用 Playwright 的 `connect_over_cdp` 连到你用 `--remote-debugging-port` 起的有头 Chrome（专属登录 profile），复用全部登录态与指纹——封控风险最低，不存 cookie、不开无头。

## 结构
```
engine/    引擎 + CLI（browser_runner 包·仅 playwright + 标准库）
backend/   FastAPI（REST + SSE·引擎的外壳）
frontend/  React + Vite + TS + Tailwind（可视化控制台）
flows/     流程（每个 = flow.toml 元信息 + flow.py 实现 run(page, params, ctx)）
config/    config/secrets 模板（*.example.toml）
var/        运行时 home（gitignore：config/secrets/profiles/runs/state）
scripts/    run.sh（起后端）· dev.sh（前后端并行热更）
```

## 上手
```bash
uv sync                                   # 装依赖
cp config/secrets.example.toml var/secrets.toml   # 填大模型 key（可选）
browser-runner list                        # 列出流程
browser-runner doctor                      # 体检：浏览器连通 + 密钥
browser-runner run <flow> -p k=v           # 跑一个流程（--dry-run / --yes）
./scripts/dev.sh                           # 开发模式（前后端热更）
```

一个流程一个目录、加流程不改内核；写操作流程停在提交前。
