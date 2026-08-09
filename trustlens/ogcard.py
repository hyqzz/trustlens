"""og:image 分享卡生成器：双语言 1200×630 PNG，数据实时取自评测结果。

- 中文卡 -> site/dist/og-card.png（微信/掘金/公众号等国内分享）
- 英文卡 -> site/dist/og-card-en.png（X/HN/Reddit/LinkedIn 等海外分享）
- 数据（112 / 60% / A 数 / skills 数）每次构建实时计算，周更后自动过期更新
- Pillow 为软依赖：不可用时跳过生成（build-site 不失败，保留旧卡）
"""
from __future__ import annotations

import os
from collections import Counter
from pathlib import Path

try:  # pragma: no cover
    from PIL import Image, ImageDraw, ImageFont

    _HAVE_PIL = True
except Exception:  # pragma: no cover
    _HAVE_PIL = False

W, H = 1200, 630

_FONT_CANDIDATES_BOLD = [
    r"C:\Windows\Fonts\msyhbd.ttc",            # Windows 微软雅黑 Bold
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",  # Linux fonts-noto-cjk
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttf",
    "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",        # 文泉驿（中文兜底）
    r"C:\Windows\Fonts\arialbd.ttf",           # 无中文字体时拉丁兜底
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
]
_FONT_CANDIDATES_REG = [
    r"C:\Windows\Fonts\msyh.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttf",
    "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
    r"C:\Windows\Fonts\arial.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
]

# 品牌色（与 site.css 一致）
_ACCENT = (79, 142, 247)      # #4f8ef7 蓝
_ACCENT2 = (155, 92, 246)     # #9b5cf6 紫
_GREEN = (45, 164, 78)        # #2da44e A 级
_RED = (207, 34, 46)          # #cf222e F 级
_TEXT = (230, 236, 245)       # 主文本
_TEXT_DIM = (148, 160, 178)   # 次级文本
_CARD_BG = (23, 32, 56, 235)  # 数据卡背景
_BG_TOP = (13, 20, 40)
_BG_BOTTOM = (24, 34, 62)


def _font(candidates: list[str], size: int) -> ImageFont.FreeTypeFont:
    for c in candidates:
        p = Path(c)
        if p.exists():
            try:
                return ImageFont.truetype(str(p), size)
            except Exception:
                continue
    return ImageFont.load_default()


def _gradient_bg() -> Image.Image:
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    for y in range(H):
        t = y / (H - 1)
        r = round(_BG_TOP[0] + (_BG_BOTTOM[0] - _BG_TOP[0]) * t)
        g = round(_BG_TOP[1] + (_BG_BOTTOM[1] - _BG_TOP[1]) * t)
        b = round(_BG_TOP[2] + (_BG_BOTTOM[2] - _BG_TOP[2]) * t)
        d.line([(0, y), (W, y)], fill=(r, g, b, 255))
    # 品牌色光晕（两团，营造氛围）
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    for cx, cy, rad, col in [(-60, -80, 540, (*_ACCENT, 88)),
                             (1160, 700, 580, (*_ACCENT2, 78))]:
        gd.ellipse([cx - rad, cy - rad, cx + rad, cy + rad], fill=col)
    img.alpha_composite(glow)
    return img


def _rounded(x0, y0, x1, y1, r, d: ImageDraw.ImageDraw, fill, outline=None, ow=0):
    d.rounded_rectangle([x0, y0, x1, y1], radius=r, fill=fill,
                        outline=outline, width=ow)


def _logo(d: ImageDraw.ImageDraw, x: int, y: int, size: int):
    """品牌渐变方块 + 'T'（左侧 logo，替代 emoji 保证跨环境可渲染）。"""
    half = size // 2
    _rounded(x, y, x + half, y + size, half // 2, d, fill=_ACCENT)
    _rounded(x + half, y, x + size, y + size, half // 2, d, fill=_ACCENT2)
    d.rounded_rectangle([x, y, x + size, y + size], radius=half // 2,
                        outline=(255, 255, 255, 200), width=2)
    fb = _font(_FONT_CANDIDATES_BOLD, size - 4)
    tw = d.textlength("T", font=fb)
    d.text((x + (size - tw) / 2, y - 2), "T", font=fb, fill=(255, 255, 255, 255),
           anchor="la")


def _center_text(d, text, font, fill, cx, y):
    tw = d.textlength(text, font=font)
    d.text((cx - tw / 2, y), text, font=font, fill=fill)


def _data_card(d, x0, y0, w, h, number, label, num_color):
    _rounded(x0, y0, x0 + w, y0 + h, 18, d, fill=_CARD_BG)
    fn = _font(_FONT_CANDIDATES_BOLD, 84)
    fl = _font(_FONT_CANDIDATES_REG, 25)
    cx = x0 + w / 2
    _center_text(d, number, fn, num_color, cx, y0 + 26)
    fl = _font(_FONT_CANDIDATES_REG, 25)
    _center_text(d, label, fl, _TEXT_DIM, cx, y0 + 124)


def _render_card(reports: list, skills: list, en: bool) -> Image.Image:
    counts = Counter(getattr(r, "grade", "") for r in reports)
    n = len(reports)
    n_f = counts.get("F", 0)
    pct_f = (n_f / n * 100) if n else 0.0
    n_a = counts.get("A", 0)
    n_sk = len(skills)

    img = _gradient_bg()
    d = ImageDraw.Draw(img)

    fb = _font(_FONT_CANDIDATES_BOLD, 46)   # 品牌
    fbig = _font(_FONT_CANDIDATES_BOLD, 72 if not en else 60)  # 主标题
    fsub = _font(_FONT_CANDIDATES_REG, 30)  # 副标题
    fhl = _font(_FONT_CANDIDATES_REG, 26)   # 底部高亮
    furl = _font(_FONT_CANDIDATES_BOLD, 38)  # URL

    # 品牌行
    _logo(d, 60, 44, 46)
    d.text((124, 50), "TrustLens", font=fb, fill=_TEXT)
    d.text((340, 58), "· ICodeStar 智码星" if not en else "· ICodeStar", font=fsub, fill=_TEXT_DIM)

    # 主标题 / 副标题
    d.text((60, 128), "Agent 工具质检局" if not en else "The trust benchmark for agents",
           font=fbig, fill=_TEXT)
    d.text((60, 216),
           "112 个真实 MCP 服务器 · 110 个 Agent Skills · 0–100 信任分" if not en
           else "112 real MCP servers · 110 agent skills · 0–100 trust score",
           font=fsub, fill=_TEXT_DIM)

    # 数据卡
    cw, gap, y0, ch = 340, 40, 268, 178
    x0 = 60
    cards = [
        (f"{n}", "个去重真实服务器" if not en else "distinct real servers", _ACCENT),
        (f"{pct_f:.1f}%", "开箱即用无法用（F 级）" if not en else "unusable out of the box (F)", _RED),
        (f"{n_a}", "个真正开箱即用（A 级）" if not en else "grade A out of the box", _GREEN),
    ]
    for i, (num, lab, col) in enumerate(cards):
        _data_card(d, x0 + i * (cw + gap), y0, cw, ch, num, lab, col)

    # 底部高亮
    d.text((60, 476),
           "唯一满分 ifconfig-mcp · 官方 filesystem 仅 C 级 —— 热门 ≠ 靠谱" if not en
           else "Only perfect score: ifconfig-mcp · official filesystem: C — hot ≠ reliable",
           font=fhl, fill=(214, 170, 90))

    # URL 条 + 说明
    d.line([(60, 540), (W - 60, 540)], fill=(255, 255, 255, 34), width=1)
    d.text((60, 556), "trustlens.icodestar.net" + ("/en" if en else ""), font=furl, fill=_TEXT)
    note = _font(_FONT_CANDIDATES_REG, 22)
    d.text((W - 60, 568), "每周自动更新 · 数据公开可审计 · Apache-2.0" if not en
           else "Weekly auto-update · Open data · git history is the audit log",
           font=note, fill=_TEXT_DIM, anchor="rs")
    return img


def render_og_cards(dist: Path, reports: list, skills: list) -> bool:
    """生成两张分享卡到 dist/。PIL 不可用返回 False，build-site 照常成功。"""
    if not _HAVE_PIL:
        return False
    try:
        _render_card(reports, skills, False).convert("RGB").save(dist / "og-card.png")
        _render_card(reports, skills, True).convert("RGB").save(dist / "og-card-en.png")
        return True
    except Exception:
        return False
