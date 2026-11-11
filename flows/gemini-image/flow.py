"""Gemini 网页出图 —— 发一句提示词，把出来的图落到磁盘。

各处踩出来的规矩都写在它自己旁边了，这里先说取图那条，因为它决定产物质量：

  **取图优先在页面里 `fetch` 原 blob 再转 data URL，而不是画到 canvas 再 `toDataURL`。**
  canvas 那条会把图重新编码一遍（PNG 无损但体积翻几倍、JPEG 直接掉一代），而且跨源图会把
  canvas 污染掉、`toDataURL` 当场抛。fetch 拿的是原始字节，拿不到时才退 `page.request`
  （它带着这个浏览器上下文的 cookie，所以受保护的 CDN 链接也取得下），最后才退 canvas。

  实测 Gemini 会在 `<img>` 装上之后就 `revokeObjectURL`，所以那条 `blob:` 多半已经 fetch
  不动，最终多是走到 canvas —— 拿到的是**页面里显示的那张**（当前 1024²），不是「下载完整
  尺寸」按钮背后那张更大的。要更大的图走 cookie 那条通道（它经 RPC 取全尺寸）。
  取法记在结果的 `fetched_by` 里，别靠猜。
"""
from __future__ import annotations

import base64
import time
from pathlib import Path

from primitives import upload_file, wait_idle

#: 判定「这是生成出来的图」的最小边长。头像、图标、按钮里的小图都在这条线以下。
MIN_IMAGE_SIDE = 200

#: 页面明说这次不行了的话术。命中就别再等——等下去只会走到超时，把真正的原因盖掉。
FAILURE_MARKERS = (
    "limit reset", "check your usage", "can't create", "cannot create",
    "something went wrong", "出了点问题", "无法创建", "已达上限",
)

# 页面里已有的大图（发送前的快照）。用它把「这次出的图」和「上一轮留在页面里的图」分开——
# 只按「最后一张大图」认，重开对话失败时就会把上一次的图当成这一次的产物交出去。
_EXISTING_JS = """
(minSide) => [...document.querySelectorAll('img')]
  .filter(i => i.naturalWidth >= minSide && i.naturalHeight >= minSide)
  .map(i => i.currentSrc || i.src)
"""

_POLL_JS = """
([minSide, known]) => {
  const seen = new Set(known);
  const fresh = [...document.querySelectorAll('img')]
    .filter(i => i.naturalWidth >= minSide && i.naturalHeight >= minSide)
    .filter(i => !seen.has(i.currentSrc || i.src));
  if (fresh.length) {
    const i = fresh[fresh.length - 1];
    return { state: 'ready', src: i.currentSrc || i.src,
             width: i.naturalWidth, height: i.naturalHeight };
  }
  return { state: 'wait', text: (document.body.innerText || '').slice(-1200) };
}
"""

# 取原字节：同源的 blob: 直接 fetch 得到；跨源被 CORS 拦下时返回 null，交给 Python 侧兜底。
_FETCH_JS = """
async (src) => {
  try {
    const blob = await (await fetch(src)).blob();
    return await new Promise(done => {
      const reader = new FileReader();
      reader.onload = () => done(reader.result);
      reader.onerror = () => done(null);
      reader.readAsDataURL(blob);
    });
  } catch (e) { return null; }
}
"""

_CANVAS_JS = """
(src) => {
  const img = [...document.querySelectorAll('img')].find(i => (i.currentSrc || i.src) === src);
  if (!img) return null;
  const canvas = document.createElement('canvas');
  canvas.width = img.naturalWidth; canvas.height = img.naturalHeight;
  canvas.getContext('2d').drawImage(img, 0, 0);
  try { return canvas.toDataURL('image/png'); } catch (e) { return null; }
}
"""


#: 输入框。Gemini 用 contenteditable 富文本（Quill），不是 textarea；同一页里还有一个隐藏的
#: `ql-clipboard` 也带 contenteditable，所以要按 role 认，不能随手取第一个 contenteditable。
COMPOSER = 'div[contenteditable="true"][role="textbox"], div.ql-editor[contenteditable="true"]'


def _composer(page, timeout: int = 45000):
    """等输入框出现——**必须等，不能立刻数**。这个页面是先出壳子再水合的，
    导航后两三秒里 DOM 里一个输入框都没有，当场数会把「还没渲染完」判成「没登录」。
    """
    box = page.locator(COMPOSER).first
    box.wait_for(state="visible", timeout=timeout)
    return box


def _fill_prompt(page, box, prompt: str) -> None:
    """先 insert_text（一次到位、长提示词不慢），落空了再退回逐字敲。

    不用 JS 直接改 innerText：Angular 的富文本框不认那种赋值，表现是框里有字、发出去是空的。
    """
    box.click()
    page.keyboard.insert_text(prompt)
    wait_idle(page, 300)
    if not (box.inner_text() or "").strip():
        page.keyboard.type(prompt, delay=8)
        wait_idle(page, 300)


def _send(page) -> None:
    """优先点发送键；找不到才回车——多行提示词里回车可能只是换行，点键才是确定的送出。"""
    for selector in ('button[aria-label*="发送"]', 'button[aria-label*="Send"]',
                     'button[aria-label*="Submit"]'):
        button = page.locator(selector).first
        if button.count() and button.is_enabled():
            button.click()
            return
    page.keyboard.press("Enter")


def _attach_reference(page, ref: str, ctx) -> bool:
    """参考图走隐藏的 file input（CDP 直接喂路径），不去点会弹原生文件框的按钮——
    那个原生框在 automation 里够不到，点开就卡死。

    input 可能要先展开「上传和工具」菜单才挂进 DOM，所以找不到时先点一下那个按钮再找。
    """
    try:
        if page.locator('input[type="file"]').count() == 0:
            for label in ("上传和工具", "Upload", "打开上传菜单"):
                button = page.locator(f'button[aria-label*="{label}"]').first
                if button.count():
                    button.click()
                    wait_idle(page, 1200)
                    break
        upload_file(page, 'input[type="file"]', str(Path(ref).expanduser()))
        wait_idle(page, 3000)
        page.keyboard.press("Escape")  # 收掉可能还开着的菜单，免得它挡住输入框
        return True
    except Exception as error:  # noqa: BLE001 —— 带不上参考图仍能出图，别让整条流程崩掉
        ctx.log(f"参考图没带上（{type(error).__name__}: {str(error)[:120]}），本次按纯文生图出")
        return False


def _wait_for_image(page, known: list, budget: int, ctx) -> dict:
    deadline = time.time() + budget
    while time.time() < deadline:
        state = page.evaluate(_POLL_JS, [MIN_IMAGE_SIDE, known])
        if state.get("state") == "ready":
            return state
        tail = (state.get("text") or "").lower()
        hit = next((m for m in FAILURE_MARKERS if m in tail), None)
        if hit:
            raise RuntimeError(f"页面说这次出不了图（命中「{hit}」）：额度满 / 被限流 / 提示词被拒")
        page.wait_for_timeout(3000)
    raise RuntimeError(f"等了 {budget} 秒也没出图，页面上也没说为什么（改大 timeout_s 再试）")


def _save(page, src: str, out: Path, ctx) -> str:
    out.parent.mkdir(parents=True, exist_ok=True)
    data_url = page.evaluate(_FETCH_JS, src)
    if isinstance(data_url, str) and data_url.startswith("data:"):
        out.write_bytes(base64.b64decode(data_url.split(",", 1)[1]))
        return "fetch"
    if src.startswith("http"):
        # 带着这个浏览器上下文的 cookie 去取，所以要登录才给看的 CDN 链接也拿得下来。
        # **必须接住异常**：它连不上时是抛，不是返回一个 not-ok 的响应——不接就直接从这里
        # 崩出去，后面那条本来能兜住的 canvas 一次都轮不到。
        try:
            response = page.request.get(src)
            if response.ok:
                out.write_bytes(response.body())
                return "request"
            ctx.log(f"CDN 取图 HTTP {response.status}，改走页面内取")
        except Exception as error:  # noqa: BLE001
            ctx.log(f"CDN 取图失败（{type(error).__name__}: {str(error)[:100]}），改走页面内取")
    fallback = page.evaluate(_CANVAS_JS, src)
    if isinstance(fallback, str) and fallback.startswith("data:"):
        ctx.log("原字节取不到，退回 canvas 重编码（体积会变大）")
        out.write_bytes(base64.b64decode(fallback.split(",", 1)[1]))
        return "canvas"
    raise RuntimeError("图在页面上，但三条取法都没拿到字节（跨源污染？）")


def run(page, params, ctx):
    out = Path(params["out"]).expanduser()
    prompt = params["prompt"]
    if params.get("aspect"):
        prompt = f"{prompt}\n(aspect ratio: {params['aspect']})"

    # 每次开一个干净的对话：页面里只留这一轮的图，认图才不会认到上一轮的。
    url = f"https://gemini.google.com/u/{params.get('user_index') or 0}/app"
    page.goto(url, wait_until="domcontentloaded")
    try:
        box = _composer(page)
    except Exception as error:  # noqa: BLE001
        raise RuntimeError(
            f"{url} 上等不到输入框（{type(error).__name__}）。多半是这个 profile 没登录 Gemini——"
            "这条流程复用的是调试 Chrome 那个专属 profile 的登录态，在它的窗口里登录一次即可"
            "（登录持久，只此一次）"
        ) from error

    if ctx.dry_run:
        return {"stopped_at": "只定位不发送（dry-run）", "signed_in": True, "url": url}

    reference_used = bool(params.get("ref")) and _attach_reference(page, params["ref"], ctx)
    known = page.evaluate(_EXISTING_JS, MIN_IMAGE_SIDE)
    _fill_prompt(page, box, prompt)
    _send(page)
    ctx.log("已发送，等出图…")

    found = _wait_for_image(page, known, int(params.get("timeout_s") or 300), ctx)
    how = _save(page, found["src"], out, ctx)
    ctx.log(f"出图 {found['width']}x{found['height']} → {out}（取法 {how}）")
    return {
        "path": str(out.resolve()),
        "width": found["width"],
        "height": found["height"],
        "reference_used": reference_used,
        "fetched_by": how,
    }
