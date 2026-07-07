"""抖音评论选题雷达 —— 输入主题，把评论区变成选题弹药。

干这么几件事：
  1. 在抖音搜这个主题的视频，取前 N 条
  2. 逐个打开视频、滚动加载评论区，抽评论文本 / 点赞 / 作者
  3. 汇总去重 → comments.csv（带 BOM，Excel 直接开）+ raw.json
  4. 把评论喂大模型，产出：观众痛点 / 内容缺口 / 3 个可直接做的选题
  5. 生成自包含 report.html：选题卡 + 热评榜 + 可搜索评论表 + 追问框

只读流程（不发不点不删），所以 write_ops=false、不需要 --yes。

抖音的 class 名全是混淆的，所以定位一律走 data-e2e 语义钩子 + 启发式兜底。
改版失效时，改下面 JS 里的 data-e2e 名就行；动手前先 `--dry-run` 探一次首条视频。
"""
from __future__ import annotations

import csv
import json
import re
import sys
import webbrowser
from datetime import datetime
from pathlib import Path
from urllib.parse import quote

sys.path.insert(0, str(Path(__file__).resolve().parent))  # 让本目录的 report.py 能 import

from llm import chat  # noqa: E402  (core 已在 sys.path)
from primitives import wait_idle  # noqa: E402
import report as report_mod  # noqa: E402

DOUYIN = "https://www.douyin.com"
SEARCH_SCROLL_ROUNDS = 5     # 搜索页往下滚几屏凑够视频
COMMENT_SCROLL_ROUNDS = 30   # 评论区最多滚几轮（滚不动了会提前停）

# 搜索结果里抽视频链接 + 标题
_VIDEO_JS = r"""
(want) => {
  const seen = new Set(), out = [];
  for (const a of document.querySelectorAll('a[href*="/video/"]')) {
    const m = (a.href || '').match(/\/video\/(\d+)/);
    if (!m) continue;
    const id = m[1];
    if (seen.has(id)) continue;
    seen.add(id);
    let title = (a.getAttribute('title') || '').trim();
    if (!title) { const t = (a.innerText || '').trim(); title = t ? t.split('\n')[0] : ''; }
    out.push({ id, url: 'https://www.douyin.com/video/' + id, title });
    if (out.length >= want) break;
  }
  return out;
}
"""

# 抽评论：抖音一条 comment-item 里 span 顺序固定 ——
#   用户名 → 正文 → 「时间·地点」→ 点赞数 → 分享 → 回复
# 以「时间行」为锚：正文取时间前那段、点赞取时间后第一个数字、用户名取首个非徽章 span；
# 楼中楼是嵌套 comment-item，用 closest 归位，不并进父项（它自己也会被单独抽到）。
_EXTRACT_JS = r"""
() => {
  function pnum(s){ s = (s || '').trim(); if (!s) return 0;
    const m = s.match(/([\d.]+)\s*([wW万kK]?)/); if (!m) return 0;
    let n = parseFloat(m[1]) || 0; const u = (m[2] || '').toLowerCase();
    if (u === 'w' || u === '万') n *= 10000; else if (u === 'k') n *= 1000;
    return Math.round(n); }
  const isNum  = t => /^\d+(\.\d+)?\s*[wW万kK]?$/.test(t);
  const isTime = t => /(\d+\s*(分钟|小时|天|周|个?月|年)前)|(昨天|前天|刚刚)|^\d{4}-\d/.test(t);
  const SKIP = new Set(['回复', '分享', '展开', '收起']);
  const out = [];
  document.querySelectorAll('[data-e2e="comment-item"]').forEach(it => {
    const info = [...it.querySelectorAll('span')]
      .filter(s => s.children.length === 0 && s.closest('[data-e2e="comment-item"]') === it)
      .map(s => ({ t: (s.innerText || '').trim(), tag: /tag/.test((s.className || '').toString()) }))
      .filter(x => x.t);
    if (!info.length) return;
    const author = (info.find(x => !x.tag) || {}).t || '';
    const ti = info.findIndex(x => isTime(x.t));
    const usable = x => !x.tag && x.t !== author && !SKIP.has(x.t);
    let text = '';
    if (ti > 0) text = info.slice(0, ti).filter(usable).map(x => x.t).join(' ');
    if (!text) {
      const cand = info.filter(x => usable(x) && !isNum(x.t) && !isTime(x.t));
      cand.sort((a, b) => b.t.length - a.t.length);
      text = cand.length ? cand[0].t : '';
    }
    if (!text) return;
    let likes = 0;
    if (ti >= 0) for (let j = ti + 1; j < info.length; j++) { if (isNum(info[j].t)) { likes = pnum(info[j].t); break; } }
    out.push({ text, author, likes });
  });
  return out;
}
"""

# 把评论列表所在的可滚动容器滚到底（找不到就滚窗口）
_SCROLL_JS = r"""
() => {
  const item = document.querySelector('[data-e2e="comment-item"]');
  if (!item) { window.scrollBy(0, 1400); return document.body.scrollHeight; }
  let el = item.parentElement;
  while (el && el !== document.body) {
    const oy = getComputedStyle(el).overflowY;
    if ((oy === 'auto' || oy === 'scroll') && el.scrollHeight > el.clientHeight + 20) {
      el.scrollTop = el.scrollHeight; return el.scrollHeight;
    }
    el = el.parentElement;
  }
  window.scrollBy(0, 1400); return document.body.scrollHeight;
}
"""


def _search_videos(page, keyword: str, want: int, ctx) -> list[dict]:
    ctx.log(f"搜索：{keyword}")
    page.goto(f"{DOUYIN}/search/{quote(keyword)}?type=video", wait_until="domcontentloaded")
    wait_idle(page, 2500)
    for _ in range(SEARCH_SCROLL_ROUNDS):
        page.evaluate("() => window.scrollBy(0, 1600)")
        wait_idle(page, 900)
    return (page.evaluate(_VIDEO_JS, want) or [])[:want]


def _video_title(page) -> str:
    """视频页的真实文案标题（document.title 最可靠），去掉「- 抖音」后缀、截断。"""
    try:
        t = (page.title() or "").strip()
    except Exception:  # noqa: BLE001
        return ""
    t = re.sub(r"\s*[-|·]\s*抖音.*$", "", t).strip()
    if not t or "在抖音记录" in t or t in ("抖音", "douyin"):
        return ""
    return t[:48]


def _ensure_comments(page, ctx) -> bool:
    """确认评论区已渲染；没渲染就试着点开评论按钮。"""
    try:
        page.wait_for_selector('[data-e2e="comment-item"]', timeout=6000)
        return True
    except Exception:  # noqa: BLE001
        pass
    for sel in ('[data-e2e="feed-comment-icon"]', '[data-e2e="comment-icon"]'):
        try:
            page.locator(sel).first.click(timeout=1500)
            break
        except Exception:  # noqa: BLE001
            continue
    try:
        page.wait_for_selector('[data-e2e="comment-item"]', timeout=6000)
        return True
    except Exception:  # noqa: BLE001
        return False


def _collect_comments(page, want: int, ctx) -> list[dict]:
    """滚动加载 + 抽取 + 去重，直到够数或滚不动。"""
    seen: dict[str, dict] = {}
    stable = 0
    for _ in range(COMMENT_SCROLL_ROUNDS):
        before = len(seen)
        for c in (page.evaluate(_EXTRACT_JS) or []):
            t = (c.get("text") or "").strip()
            if t and t not in seen:
                seen[t] = {"text": t, "likes": int(c.get("likes") or 0), "author": c.get("author") or ""}
        if len(seen) >= want:
            break
        stable = stable + 1 if len(seen) == before else 0
        if stable >= 3:  # 连滚 3 轮不涨，就是到底了
            break
        page.evaluate(_SCROLL_JS)
        wait_idle(page, 950)
    return sorted(seen.values(), key=lambda c: c["likes"], reverse=True)[:want]


def _parse_json(text: str) -> dict:
    """从大模型输出里抠出 JSON（容忍 ```json 围栏和前后废话）。"""
    s = (text or "").strip()
    if s.startswith("```"):
        s = re.sub(r"^```[a-zA-Z]*\n?", "", s)
        s = re.sub(r"\n?```$", "", s).strip()
    a, b = s.find("{"), s.rfind("}")
    if a != -1 and b > a:
        s = s[a:b + 1]
    try:
        return json.loads(s)
    except Exception:  # noqa: BLE001
        return {"_raw": text}


def _analyze(topic: str, videos: list[dict], provider: str, ctx) -> dict:
    ctx.log("大模型分析中…")
    pool = [(c["likes"], c["text"]) for v in videos for c in v["comments"]]
    pool.sort(key=lambda x: x[0], reverse=True)
    lines = "\n".join(f"{i}. {t[:120]}" for i, (_, t) in enumerate(pool[:250], 1))
    prompt = (
        "你是资深短视频选题策划。下面是抖音上关于「" + topic + "」的多条视频、共 "
        + str(len(pool)) + " 条观众评论（按点赞从高到低）。只依据这些评论，输出严格 JSON，"
        "不要输出 JSON 以外任何文字。结构：\n"
        '{"summary":"一句话总览观众整体情绪与关注点",'
        '"pain_points":[{"point":"痛点或情绪","evidence":"一句代表性评论原话"}],'
        '"content_gaps":["观众反复问、但没人好好答的问题或需求"],'
        '"video_ideas":[{"title":"可直接用的视频标题","hook":"开场一句钩子","why":"为什么会火，结合评论证据"}]}\n'
        "要求：pain_points 3-5 个，content_gaps 3-6 条，video_ideas 正好 3 个。\n\n评论：\n"
        + lines
    )
    text = chat([{"role": "user", "content": prompt}], provider=provider, max_tokens=2200, temperature=0.6)
    return _parse_json(text)


def run(page, params, ctx):
    topic = (params.get("topic") or "").strip()
    if not topic:
        return {"error": "缺主题关键词"}
    want_videos = int(params.get("videos") or 8)
    per_video = int(params.get("per_video") or 40)
    provider = (params.get("provider") or "deepseek").strip()

    vids = _search_videos(page, topic, want_videos, ctx)
    if not vids:
        ctx.log("⚠️ 没搜到视频——多半是抖音要求登录。在这个调试 Chrome 里手动登录抖音后重试。")
        return {"error": "没搜到视频（可能需登录抖音）", "topic": topic}
    ctx.log(f"搜到 {len(vids)} 条视频")

    # dry-run：只探首条视频评论区通不通，快速验证选择器，不跑全量、不调模型
    if ctx.dry_run:
        page.goto(vids[0]["url"], wait_until="domcontentloaded")
        wait_idle(page, 2500)
        ok = _ensure_comments(page, ctx)
        sample = _collect_comments(page, 8, ctx) if ok else []
        ctx.log(f"[dry-run] 首条视频评论区 {'可读' if ok else '未读到'}，抽样 {len(sample)} 条")
        for s in sample[:5]:
            ctx.log(f"  · {s['text'][:40]}")
        return {"dry_run": True, "videos": len(vids), "comment_selector_ok": ok, "sample": sample[:5]}

    videos: list[dict] = []
    total = 0
    for i, v in enumerate(vids, 1):
        v["comments"] = []
        try:
            page.goto(v["url"], wait_until="domcontentloaded")
            wait_idle(page, 2200)
            v["title"] = _video_title(page) or f"视频 {i}"  # 搜索卡标题不可靠，用视频页真实文案
            ctx.log(f"[{i}/{len(vids)}] {v['title'][:26]}")
            if _ensure_comments(page, ctx):
                v["comments"] = _collect_comments(page, per_video, ctx)
                total += len(v["comments"])
                ctx.log(f"  抓到 {len(v['comments'])} 条评论")
            else:
                ctx.log("  ⚠️ 评论区没读到，跳过（可能关评/需登录/改版）")
        except Exception as e:  # noqa: BLE001 — 单条失败不带崩整轮
            v["title"] = v.get("title") or f"视频 {i}"
            ctx.log(f"  ❌ 出错跳过：{e}")
        videos.append(v)

    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    csv_path = ctx.workdir / "comments.csv"
    with csv_path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["视频序号", "视频标题", "视频链接", "评论序号", "评论内容", "点赞", "评论者"])
        for vi, v in enumerate(videos, 1):
            for ci, c in enumerate(v["comments"], 1):
                w.writerow([vi, v["title"], v["url"], ci, c["text"], c["likes"], c["author"]])
    ctx.log(f"CSV 落盘：{csv_path}（共 {total} 条评论）")

    data = {"topic": topic, "generated": ts, "videos": videos,
            "stats": {"videos": len(videos), "comments": total}}
    (ctx.workdir / "raw.json").write_text(json.dumps(data, ensure_ascii=False, indent=2), "utf-8")

    analysis: dict = {}
    if total == 0:
        ctx.log("没抓到任何评论，跳过大模型分析（检查是否已登录抖音 / 选择器是否失效）")
    else:
        try:
            analysis = _analyze(topic, videos, provider, ctx)
        except Exception as e:  # noqa: BLE001 — 分析失败也要出报告
            ctx.log(f"大模型分析失败（报告仍会出，只是少了分析卡）：{e}")
            analysis = {"_error": str(e)}

    report_path = ctx.workdir / "report.html"
    report_mod.build_report(data, analysis, report_path)
    ctx.log(f"报告生成：{report_path}")
    try:
        webbrowser.open(report_path.as_uri())
    except Exception:  # noqa: BLE001
        pass

    return {
        "topic": topic,
        "videos": len(videos),
        "comments": total,
        "csv": str(csv_path),
        "report": str(report_path),
        "ideas": len(analysis.get("video_ideas") or []),
    }
