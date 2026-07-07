"""把抓来的评论 + 大模型分析渲染成一张自包含 HTML 报告。

单文件、无外链、可离线可分享。视觉走 browser-runner 看板的扁平风 DNA：
纸底、粗描边、硬投影；只留一个 signature —— 3 个选题卡（页面视觉重心）。
其余（痛点 / 缺口 / 热评榜 / 评论表 / 追问框）安静让位。亮暗双主题、零 emoji。
"""
from __future__ import annotations

import html
import json
from pathlib import Path


def _esc(s) -> str:
    return html.escape(str(s if s is not None else ""), quote=True)


def build_report(data: dict, analysis: dict, out_path: Path) -> None:
    topic = data.get("topic", "")
    stats = data.get("stats", {})
    nv, nc = stats.get("videos", 0), stats.get("comments", 0)

    # ── 选题卡（signature）──
    ideas = analysis.get("video_ideas") or []
    idea_cards = []
    for i, it in enumerate(ideas[:3], 1):
        idea_cards.append(
            f'<article class="idea" data-reveal style="--i:{i}">'
            f'<span class="idea__tag">选题 {i:02d}</span>'
            f'<h3 class="idea__title">{_esc(it.get("title"))}</h3>'
            f'<p class="idea__hook">「{_esc(it.get("hook"))}」</p>'
            f'<p class="idea__why">{_esc(it.get("why"))}</p>'
            "</article>"
        )
    ideas_html = "\n".join(idea_cards) or '<p class="empty">大模型没给出选题（分析可能失败，看下面原文）。</p>'

    # ── 痛点 ──
    pain_items = []
    for p in analysis.get("pain_points") or []:
        pt = p.get("point") if isinstance(p, dict) else str(p)
        ev = p.get("evidence") if isinstance(p, dict) else ""
        pain_items.append(
            f'<li class="pain" data-reveal><p class="pain__point">{_esc(pt)}</p>'
            + (f'<p class="pain__ev">“{_esc(ev)}”</p>' if ev else "")
            + "</li>"
        )
    pains_html = "\n".join(pain_items) or '<li class="empty">—</li>'

    # ── 内容缺口 ──
    gaps = analysis.get("content_gaps") or []
    gaps_html = "\n".join(f'<span class="gap">{_esc(g)}</span>' for g in gaps) or '<span class="empty">—</span>'

    # ── 总览 / 原文兜底 ──
    summary = analysis.get("summary") or ""
    if analysis.get("_error") and not summary:
        summary = f"（大模型分析未成功：{analysis['_error']}）"
    raw_html = f'<details class="rawbox"><summary>大模型原始输出（未能解析成结构）</summary><pre class="raw">{_esc(analysis.get("_raw"))}</pre></details>' if analysis.get("_raw") else ""

    # ── 追问框预填的提示词 ──
    pool = sorted(
        ((c.get("likes", 0), c.get("text", "")) for v in data.get("videos", []) for c in v.get("comments", [])),
        key=lambda x: x[0], reverse=True,
    )
    sample_lines = "\n".join(f"- {t[:60]}" for _, t in pool[:30])
    digest = (
        f"这是抖音「{topic}」话题下 {nv} 条视频、{nc} 条评论的分析。\n"
        f"总览：{summary}\n部分高赞评论：\n{sample_lines}\n\n我的问题："
    )

    data_json = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    digest_json = json.dumps(digest, ensure_ascii=False).replace("</", "<\\/")

    html_out = (
        _TEMPLATE
        .replace("__TOPIC__", _esc(topic))
        .replace("__GENERATED__", _esc(data.get("generated", "")))
        .replace("__STAT_V__", str(nv))
        .replace("__STAT_C__", str(nc))
        .replace("__SUMMARY__", _esc(summary) or "—")
        .replace("__IDEAS__", ideas_html)
        .replace("__PAINS__", pains_html)
        .replace("__GAPS__", gaps_html)
        .replace("__RAW__", raw_html)
        .replace("__DATA__", data_json)
        .replace("__DIGEST__", digest_json)
    )
    out_path.write_text(html_out, encoding="utf-8")


_TEMPLATE = r"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>抖音评论选题雷达 · __TOPIC__</title>
<style>
:root{
  --paper:#f4f1ea; --card:#fffdf7; --ink:#141414; --sub:#6b6459; --line:#e4e0d3; --edge:#141414;
  --hot:#ff4d3d; --blue:#2450e6; --lime:#c9f24a;
  --shadow:6px 6px 0 var(--edge); --shadow-sm:3px 3px 0 var(--edge);
  --sans:"PingFang SC","Hiragino Sans GB","Microsoft YaHei",-apple-system,BlinkMacSystemFont,sans-serif;
  --mono:"SF Mono","JetBrains Mono",ui-monospace,Menlo,monospace;
  --ease:cubic-bezier(0.34,1.56,0.64,1);
}
@media (prefers-color-scheme:dark){
  :root{ --paper:#16140d; --card:#211d13; --ink:#f2ece0; --sub:#a89e88; --line:#332d1f; --edge:#f2ece0; }
}
:root[data-theme="light"]{ --paper:#f4f1ea; --card:#fffdf7; --ink:#141414; --sub:#6b6459; --line:#e4e0d3; --edge:#141414; }
:root[data-theme="dark"]{ --paper:#16140d; --card:#211d13; --ink:#f2ece0; --sub:#a89e88; --line:#332d1f; --edge:#f2ece0; }

*{ box-sizing:border-box; margin:0; padding:0; }
[hidden]{ display:none !important; }
body{ background:var(--paper); color:var(--ink); font-family:var(--sans); line-height:1.55; -webkit-font-smoothing:antialiased; }
.wrap{ max-width:1080px; margin:0 auto; padding:32px 22px 80px; }
a{ color:inherit; }

/* ── 抬头 ── */
.mast{ display:flex; flex-wrap:wrap; align-items:flex-end; gap:16px 20px; padding-bottom:22px; border-bottom:3px solid var(--edge); }
.mast__tag{ font-family:var(--mono); font-size:12px; letter-spacing:.14em; text-transform:uppercase;
  background:var(--ink); color:var(--paper); padding:5px 10px; align-self:flex-start; }
.mast__topic{ font-size:clamp(34px,7vw,62px); font-weight:900; letter-spacing:-.01em; line-height:.98; flex:1 1 320px; }
.mast__topic b{ color:var(--hot); }
.chips{ display:flex; gap:10px; flex-wrap:wrap; }
.chip{ font-family:var(--mono); font-size:12px; border:2px solid var(--edge); padding:6px 11px; display:flex; gap:7px; align-items:baseline; }
.chip b{ font-size:16px; font-weight:800; }
.toggle{ font-family:var(--mono); font-size:12px; border:2px solid var(--edge); background:transparent; color:var(--ink);
  padding:6px 11px; cursor:pointer; transition:transform .15s var(--ease); }
.toggle:hover{ transform:translate(-1px,-1px); box-shadow:var(--shadow-sm); }

/* ── 区块 ── */
.sec{ margin-top:46px; }
.sec__h{ font-family:var(--mono); font-size:12px; letter-spacing:.16em; text-transform:uppercase; color:var(--sub);
  display:flex; align-items:center; gap:12px; margin-bottom:18px; }
.sec__h::after{ content:""; flex:1; height:2px; background:var(--line); }
.lead{ font-size:clamp(17px,2.2vw,21px); font-weight:500; max-width:60ch; }

/* ── signature：选题卡 ── */
.ideas{ display:grid; grid-template-columns:repeat(3,1fr); gap:18px; margin-top:22px; }
.idea{ background:var(--card); border:2.5px solid var(--edge); box-shadow:var(--shadow); padding:20px 18px 22px;
  display:flex; flex-direction:column; gap:10px; transition:transform .2s var(--ease), box-shadow .2s var(--ease); }
.idea:hover{ transform:translate(-3px,-3px); box-shadow:9px 9px 0 var(--edge); }
.idea__tag{ font-family:var(--mono); font-size:11px; letter-spacing:.12em; font-weight:700;
  background:var(--lime); color:#141414; padding:3px 8px; align-self:flex-start; border:1.5px solid #141414; }
.idea__title{ font-size:21px; font-weight:900; line-height:1.15; letter-spacing:-.01em; }
.idea__hook{ font-size:14px; color:var(--blue); font-weight:600; }
.idea__why{ font-size:13.5px; color:var(--sub); line-height:1.6; }

/* ── 痛点 + 缺口 ── */
.grid2{ display:grid; grid-template-columns:1.15fr .85fr; gap:34px; margin-top:22px; }
.pains{ list-style:none; display:flex; flex-direction:column; gap:14px; }
.pain{ border-left:3px solid var(--hot); padding:2px 0 2px 14px; }
.pain__point{ font-weight:700; font-size:15.5px; }
.pain__ev{ font-size:13px; color:var(--sub); margin-top:3px; font-style:italic; }
.gaps{ display:flex; flex-wrap:wrap; gap:9px; }
.gap{ font-size:13.5px; border:2px solid var(--edge); border-radius:999px; padding:6px 13px; background:var(--card); }
.empty{ color:var(--sub); font-size:14px; }

/* ── 热评榜 ── */
.bars{ display:flex; flex-direction:column; gap:9px; }
.bar{ display:grid; grid-template-columns:26px 1fr auto; gap:12px; align-items:center; }
.bar__rank{ font-family:var(--mono); font-size:13px; color:var(--sub); text-align:right; }
.bar__body{ position:relative; background:var(--line); height:34px; display:flex; align-items:center; overflow:hidden; }
.bar__fill{ position:absolute; inset:0 auto 0 0; background:color-mix(in srgb,var(--hot) 22%, transparent); }
.bar__txt{ position:relative; padding:0 12px; font-size:13.5px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
.bar__num{ font-family:var(--mono); font-size:13px; font-variant-numeric:tabular-nums; color:var(--hot); font-weight:700; }
.note{ font-size:12.5px; color:var(--sub); margin-top:8px; font-family:var(--mono); }

/* ── 每视频评论量 ── */
.vol{ display:flex; flex-direction:column; gap:7px; margin-top:8px; }
.volrow{ display:grid; grid-template-columns:1fr 46px; gap:12px; align-items:center; font-size:13px; }
.voltrack{ height:10px; background:var(--line); position:relative; }
.volfill{ position:absolute; inset:0 auto 0 0; background:var(--blue); }
.volrow a{ overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
.volrow span{ font-family:var(--mono); font-variant-numeric:tabular-nums; text-align:right; color:var(--sub); }

/* ── 评论表 ── */
.tbar{ display:flex; gap:10px; flex-wrap:wrap; margin-bottom:12px; }
.tbar input{ flex:1 1 220px; font-family:var(--sans); font-size:14px; padding:9px 12px; background:var(--card);
  border:2px solid var(--edge); color:var(--ink); }
.tbar input::placeholder{ color:var(--sub); }
.tbar button{ font-family:var(--mono); font-size:12px; border:2px solid var(--edge); background:transparent; color:var(--ink);
  padding:0 14px; cursor:pointer; transition:transform .15s var(--ease); }
.tbar button:hover{ transform:translate(-1px,-1px); box-shadow:var(--shadow-sm); }
.tbar button.on{ background:var(--ink); color:var(--paper); }
.tscroll{ max-height:440px; overflow:auto; border:2px solid var(--edge); }
table{ width:100%; border-collapse:collapse; font-size:13.5px; }
thead th{ position:sticky; top:0; background:var(--card); text-align:left; font-family:var(--mono); font-size:11px;
  letter-spacing:.1em; text-transform:uppercase; color:var(--sub); padding:10px 12px; border-bottom:2px solid var(--edge); }
tbody td{ padding:10px 12px; border-bottom:1px solid var(--line); vertical-align:top; }
tbody tr:hover{ background:color-mix(in srgb,var(--lime) 14%, transparent); }
td.tnum{ font-family:var(--mono); font-variant-numeric:tabular-nums; color:var(--hot); font-weight:700; text-align:right; white-space:nowrap; }
td.tvid a{ color:var(--sub); font-size:12px; }

/* ── 追问框 ── */
.ask{ background:var(--card); border:2.5px solid var(--edge); box-shadow:var(--shadow); padding:22px; margin-top:22px; }
.ask textarea{ width:100%; min-height:120px; font-family:var(--sans); font-size:14px; line-height:1.6; padding:12px;
  background:var(--paper); border:2px solid var(--edge); color:var(--ink); resize:vertical; }
.ask__row{ display:flex; gap:10px; flex-wrap:wrap; margin-top:12px; }
.ask__row button{ font-family:var(--mono); font-size:13px; font-weight:700; border:2px solid var(--edge); padding:9px 16px; cursor:pointer;
  transition:transform .15s var(--ease); background:var(--lime); color:#141414; }
.ask__row button.ghost{ background:transparent; color:var(--ink); }
.ask__row button:hover{ transform:translate(-2px,-2px); box-shadow:var(--shadow-sm); }
.ask details{ margin-top:14px; font-size:13px; }
.ask summary{ cursor:pointer; color:var(--sub); font-family:var(--mono); }
.ask__api{ display:flex; gap:8px; flex-wrap:wrap; margin-top:10px; }
.ask__api input{ flex:1 1 160px; font-family:var(--mono); font-size:12.5px; padding:8px 10px; background:var(--paper);
  border:2px solid var(--line); color:var(--ink); }
.ask__ans{ margin-top:14px; font-size:14px; line-height:1.7; white-space:pre-wrap; }
.ask__ans:empty{ display:none; }

.rawbox{ margin-top:24px; font-size:13px; }
.rawbox summary{ cursor:pointer; color:var(--sub); font-family:var(--mono); }
.raw{ white-space:pre-wrap; font-family:var(--mono); font-size:12px; margin-top:10px; padding:14px; background:var(--card); border:2px solid var(--line); overflow:auto; }

.foot{ margin-top:60px; padding-top:22px; border-top:2px solid var(--line); font-family:var(--mono); font-size:12px; color:var(--sub); text-align:center; }

.toast{ position:fixed; left:50%; bottom:28px; transform:translateX(-50%) translateY(20px); opacity:0;
  background:var(--ink); color:var(--paper); font-size:13px; padding:11px 18px; border-radius:2px; pointer-events:none;
  transition:opacity .25s, transform .25s var(--ease); z-index:9; }
.toast.show{ opacity:1; transform:translateX(-50%) translateY(0); }

[data-reveal]{ opacity:0; transform:translateY(14px); transition:opacity .5s var(--ease), transform .5s var(--ease); transition-delay:calc(var(--i,0)*70ms); }
[data-reveal].in{ opacity:1; transform:none; }

@media (max-width:820px){ .ideas{ grid-template-columns:1fr; } .grid2{ grid-template-columns:1fr; gap:26px; } }
@media (prefers-reduced-motion:reduce){ *{ transition:none !important; } [data-reveal]{ opacity:1; transform:none; } }
</style>
</head>
<body>
<div class="wrap">

  <header class="mast">
    <span class="mast__tag">抖音 · 评论选题雷达</span>
    <h1 class="mast__topic"><b>#</b>__TOPIC__</h1>
    <div class="chips">
      <span class="chip">视频 <b>__STAT_V__</b></span>
      <span class="chip">评论 <b>__STAT_C__</b></span>
      <span class="chip">__GENERATED__</span>
      <button class="toggle" id="themeBtn" type="button">明 / 暗</button>
    </div>
  </header>

  <section class="sec">
    <div class="sec__h">观众整体 · Overview</div>
    <p class="lead" data-reveal>__SUMMARY__</p>
  </section>

  <section class="sec">
    <div class="sec__h">该做哪期视频 · Video Ideas</div>
    <div class="ideas">__IDEAS__</div>
  </section>

  <section class="sec">
    <div class="grid2">
      <div>
        <div class="sec__h">观众在痛什么 · Pain Points</div>
        <ul class="pains">__PAINS__</ul>
      </div>
      <div>
        <div class="sec__h">没人好好答的 · Content Gaps</div>
        <div class="gaps">__GAPS__</div>
      </div>
    </div>
  </section>

  <section class="sec">
    <div class="sec__h">最戳人的评论 · Top by Likes</div>
    <div class="bars" id="topBars"></div>
    <p class="note" id="topNote" hidden></p>
  </section>

  <section class="sec">
    <div class="sec__h">各视频评论量 · Volume</div>
    <div class="vol" id="vol"></div>
  </section>

  <section class="sec">
    <div class="sec__h">全部评论 · Raw · <span id="tcount"></span></div>
    <div class="tbar">
      <input id="q" type="search" placeholder="搜评论内容 / 作者…" autocomplete="off">
      <button id="sortBtn" type="button">按点赞排序</button>
    </div>
    <div class="tscroll">
      <table>
        <thead><tr><th>#</th><th>评论</th><th>视频</th><th style="text-align:right">赞</th></tr></thead>
        <tbody id="tbody"></tbody>
      </table>
    </div>
  </section>

  <section class="sec">
    <div class="sec__h">再追问一句 · Ask More</div>
    <div class="ask">
      <textarea id="ask" spellcheck="false"></textarea>
      <div class="ask__row">
        <button id="copyBtn" type="button">复制提示词</button>
        <button id="callBtn" class="ghost" type="button">直接问（填了 key）</button>
      </div>
      <details>
        <summary>直接调用需填 key（本地页面，不上传；接口需支持跨域，不行会自动降级成复制）</summary>
        <div class="ask__api">
          <input id="k" type="password" placeholder="api_key">
          <input id="u" type="text" placeholder="base_url（默认 https://api.deepseek.com）">
          <input id="m" type="text" placeholder="model（默认 deepseek-chat）">
        </div>
      </details>
      <div class="ask__ans" id="ans"></div>
    </div>
  </section>

  __RAW__

  <footer class="foot">browser-runner · douyin-comment-radar · 数据源自你登录的抖音 · 本地生成</footer>
</div>

<div class="toast" id="toast"></div>

<script id="payload" type="application/json">__DATA__</script>
<script>
const DATA = JSON.parse(document.getElementById('payload').textContent);
const DIGEST = __DIGEST__;

// 主题切换
const root = document.documentElement;
document.getElementById('themeBtn').addEventListener('click', () => {
  const cur = root.getAttribute('data-theme')
    || (matchMedia('(prefers-color-scheme:dark)').matches ? 'dark' : 'light');
  root.setAttribute('data-theme', cur === 'dark' ? 'light' : 'dark');
});

// 展开评论
const ALL = [];
DATA.videos.forEach((v, vi) => (v.comments || []).forEach(c =>
  ALL.push({ t: c.text || '', l: c.likes || 0, a: c.author || '', vt: v.title || ('视频 ' + (vi + 1)), vu: v.url })));

const esc = s => (s || '').replace(/[&<>"]/g, m => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[m]));

// 热评榜
(() => {
  const top = [...ALL].sort((a, b) => b.l - a.l).slice(0, 12);
  const max = Math.max(1, ...top.map(c => c.l));
  const hasLikes = top.some(c => c.l > 0);
  document.getElementById('topBars').innerHTML = top.map((c, i) => `
    <div class="bar">
      <span class="bar__rank">${i + 1}</span>
      <div class="bar__body"><span class="bar__fill" style="width:${hasLikes ? (c.l / max * 100) : 0}%"></span>
        <span class="bar__txt">${esc(c.t)}</span></div>
      <span class="bar__num">${hasLikes ? fmt(c.l) : '·'}</span>
    </div>`).join('');
  if (!hasLikes) { const n = document.getElementById('topNote'); n.hidden = false; n.textContent = '点赞数没抓到，这里按抓取顺序排列。'; }
})();

// 各视频评论量
(() => {
  const rows = DATA.videos.map((v, i) => ({ t: v.title || ('视频 ' + (i + 1)), n: (v.comments || []).length, u: v.url }));
  const max = Math.max(1, ...rows.map(r => r.n));
  document.getElementById('vol').innerHTML = rows.map(r => `
    <div class="volrow">
      <a href="${r.u}" target="_blank" rel="noopener" title="${esc(r.t)}">
        <div class="voltrack"><span class="volfill" style="width:${r.n / max * 100}%"></span></div>
      </a>
      <span>${r.n}</span>
    </div>`).join('');
})();

// 评论表 + 搜索 + 排序
let sortByLike = false;
const tbody = document.getElementById('tbody');
const qEl = document.getElementById('q');
function fmt(n) { return n >= 10000 ? (n / 10000).toFixed(1) + 'w' : String(n); }
function draw() {
  const kw = qEl.value.trim().toLowerCase();
  let rows = kw ? ALL.filter(c => (c.t + c.a).toLowerCase().includes(kw)) : ALL.slice();
  if (sortByLike) rows.sort((a, b) => b.l - a.l);
  document.getElementById('tcount').textContent = rows.length + ' 条';
  tbody.innerHTML = rows.slice(0, 600).map((c, i) => `
    <tr><td class="tnum" style="color:var(--sub);font-weight:400">${i + 1}</td>
      <td>${esc(c.t)}${c.a ? ` <span style="color:var(--sub)">— ${esc(c.a)}</span>` : ''}</td>
      <td class="tvid"><a href="${c.vu}" target="_blank" rel="noopener" title="${esc(c.vt)}">${esc(c.vt.slice(0, 14))}</a></td>
      <td class="tnum">${c.l ? fmt(c.l) : '·'}</td></tr>`).join('');
}
qEl.addEventListener('input', draw);
document.getElementById('sortBtn').addEventListener('click', e => {
  sortByLike = !sortByLike; e.target.classList.toggle('on', sortByLike); draw();
});
draw();

// 追问框
const askEl = document.getElementById('ask');
askEl.value = DIGEST;
function toast(m) { const t = document.getElementById('toast'); t.textContent = m; t.classList.add('show'); setTimeout(() => t.classList.remove('show'), 2200); }
async function copyPrompt() { try { await navigator.clipboard.writeText(askEl.value); return true; } catch (e) { return false; } }
document.getElementById('copyBtn').addEventListener('click', async () => {
  toast(await copyPrompt() ? '已复制，去任意大模型对话框粘贴' : '复制失败，请手动全选复制');
});
document.getElementById('callBtn').addEventListener('click', async () => {
  const key = document.getElementById('k').value.trim();
  if (!key) { await copyPrompt(); toast('没填 key，已复制提示词'); return; }
  const base = (document.getElementById('u').value.trim() || 'https://api.deepseek.com').replace(/\/$/, '');
  const model = document.getElementById('m').value.trim() || 'deepseek-chat';
  const ans = document.getElementById('ans');
  ans.textContent = '问询中…';
  try {
    const r = await fetch(base + '/chat/completions', {
      method: 'POST', headers: { 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + key },
      body: JSON.stringify({ model, messages: [{ role: 'user', content: askEl.value }] })
    });
    const j = await r.json();
    ans.textContent = j.choices?.[0]?.message?.content || ('接口返回异常：' + JSON.stringify(j).slice(0, 300));
  } catch (e) { ans.textContent = ''; await copyPrompt(); toast('接口不通（多半跨域），已复制提示词'); }
});

// reveal
const io = new IntersectionObserver(es => es.forEach(e => { if (e.isIntersecting) { e.target.classList.add('in'); io.unobserve(e.target); } }), { threshold: .12 });
document.querySelectorAll('[data-reveal]').forEach(el => io.observe(el));
</script>
</body>
</html>
"""
