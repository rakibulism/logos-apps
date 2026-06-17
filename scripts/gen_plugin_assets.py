#!/usr/bin/env python3
"""Generate Figma Community marketing assets (Pillow-only) for the Brands Logo plugin:
  - assets/og.png                       (1200x630 social card, brandslogo.vercel.app)
  - figma-plugin/marketing/thumbnail.png (1920x1080 cover)
  - figma-plugin/marketing/carousel-1..9.png (1920x1080 each)

Real brand logos come from pre-rasterized PNG tiles in figma-plugin/marketing/tiles/
(rendered once from the SVGs via a headless browser, since no SVG rasterizer is installed).
"""
import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TILES = os.path.join(ROOT, "figma-plugin", "marketing", "tiles")
OUT = os.path.join(ROOT, "figma-plugin", "marketing")
os.makedirs(OUT, exist_ok=True)

# ---------- palette ----------
BG0 = (10, 10, 12)
BG1 = (18, 19, 23)
PANEL = (24, 25, 29)
CARD = (31, 32, 37)
HILITE = (44, 46, 52)      # solid highlight (alpha fills flatten to white on convert)
PBORDER = (58, 59, 66)     # solid panel border
LINE = (255, 255, 255, 20)
TEXT = (245, 245, 247)
MUTED = (150, 153, 162)
FAINT = (110, 113, 122)
ACCENT = (77, 159, 255)
VIOLET = (124, 92, 255)
GREEN = (52, 199, 120)
AMBER = (245, 176, 66)


def _font(*cands):
    for c in cands:
        if os.path.exists(c):
            return c
    raise SystemExit("No font found")

BOLD = _font("/System/Library/Fonts/Supplemental/Arial Bold.ttf", "/Library/Fonts/Arial Bold.ttf",
             "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf")
REG = _font("/System/Library/Fonts/Supplemental/Arial.ttf", "/Library/Fonts/Arial.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")
def fb(s): return ImageFont.truetype(BOLD, s)
def fr(s): return ImageFont.truetype(REG, s)


def new_canvas(w, h):
    """Vertical gradient + dot grid + frame crosshairs."""
    img = Image.new("RGB", (w, h), BG0)
    top = Image.new("RGB", (w, h))
    pt = top.load()
    for y in range(h):
        t = y / h
        r = int(BG1[0] * (1 - t) + BG0[0] * t)
        g = int(BG1[1] * (1 - t) + BG0[1] * t)
        b = int(BG1[2] * (1 - t) + BG0[2] * t)
        for x in range(0, w, 1):
            pt[x, y] = (r, g, b)
    img = top
    ov = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(ov, "RGBA")
    step = 26
    for x in range(0, w, step):
        for y in range(0, h, step):
            d.ellipse([x, y, x + 1.6, y + 1.6], fill=(255, 255, 255, 13))
    m = 70
    for yy in (m, h - m):
        d.line([(0, yy), (w, yy)], fill=LINE, width=1)
    for xx in (m, w - m):
        d.line([(xx, 0), (xx, h)], fill=LINE, width=1)
    for cx in (m, w - m):
        for cy in (m, h - m):
            d.line([(cx - 8, cy), (cx + 8, cy)], fill=(255, 255, 255, 80), width=2)
            d.line([(cx, cy - 8), (cx, cy + 8)], fill=(255, 255, 255, 80), width=2)
    img = Image.alpha_composite(img.convert("RGBA"), ov)
    return img, ImageDraw.Draw(img, "RGBA")


def glow(img, cx, cy, radius, color, alpha=70):
    g = Image.new("RGBA", img.size, (0, 0, 0, 0))
    gd = ImageDraw.Draw(g)
    gd.ellipse([cx - radius, cy - radius, cx + radius, cy + radius], fill=color + (alpha,))
    g = g.filter(ImageFilter.GaussianBlur(radius // 2))
    img.alpha_composite(g)


def rrect(d, box, rad, fill=None, outline=None, width=1):
    d.rounded_rectangle(box, radius=rad, fill=fill, outline=outline, width=width)


def brandmark(d, x, y, s, gap=None, color=TEXT):
    gap = gap if gap else int(s * 0.32)
    w = int(s * 0.28)
    rad = max(2, int(s * 0.07))
    rrect(d, [x, y, x + w, y + w], rad, outline=color, width=max(2, int(s * 0.035)))
    rrect(d, [x + w + gap, y, x + 2 * w + gap, y + w], rad, outline=color, width=max(2, int(s * 0.035)))
    rrect(d, [x, y + w + gap, x + w, y + 2 * w + gap], rad, outline=color, width=max(2, int(s * 0.035)))
    rrect(d, [x + w + gap, y + w + gap, x + 2 * w + gap, y + 2 * w + gap], rad, fill=color)
    return 2 * w + gap


def text(d, xy, s, font, fill=TEXT, anchor="la"):
    d.text(xy, s, font=font, fill=fill, anchor=anchor)


def text_w(d, s, font):
    return d.textlength(s, font=font)


def tile(name):
    p = os.path.join(TILES, name + ".png")
    return Image.open(p).convert("RGBA") if os.path.exists(p) else None


def paste_logo(img, name, box, card=True, card_fill=CARD, contain=0.62):
    x0, y0, x1, y1 = box
    bw, bh = x1 - x0, y1 - y0
    if card:
        d = ImageDraw.Draw(img, "RGBA")
        rrect(d, box, int(min(bw, bh) * 0.18), fill=card_fill, outline=(255, 255, 255, 16), width=1)
    t = tile(name)
    if not t:
        return
    side = int(min(bw, bh) * contain)
    t = t.resize((side, side), Image.LANCZOS)
    img.alpha_composite(t, (int(x0 + (bw - side) / 2), int(y0 + (bh - side) / 2)))


def pill(d, box, label, font, fill, fg, rad=None):
    x0, y0, x1, y1 = box
    rad = rad if rad else (y1 - y0) // 2
    rrect(d, box, rad, fill=fill)
    text(d, ((x0 + x1) / 2, (y0 + y1) / 2 - font.size * 0.62), label, font, fg, anchor="ma")


def eyebrow(d, x, y, label, color=ACCENT):
    f = fb(22)
    d.line([(x, y + 11), (x + 30, y + 11)], fill=color, width=3)
    text(d, (x + 42, y), label.upper(), f, color)


def footer_brand(d, w, h):
    bx, by = 70 + 26, h - 70 - 46
    adv = brandmark(d, bx, by, 70)
    text(d, (bx + adv + 18, by + 6), "logos", fb(30), TEXT)
    text(d, (w - 70 - 26, by + 10), "brandslogo.vercel.app", fr(24), MUTED, anchor="ra")


GRID = ["react", "figma", "vue", "svelte", "tailwindcss", "github", "notion", "slack",
        "spotify", "discord", "stripe", "vercel", "nextjs", "nodejs", "python",
        "typescript", "openai", "claude", "google-chrome", "firebase", "astro",
        "supabase", "prisma", "docker"]


# ---------- mini plugin-panel mockup ----------
def plugin_panel(img, x, y, w, names, active_src=0, mode=0, cols=4, rows=3):
    """Draw a stylized plugin UI panel. Returns its height."""
    d = ImageDraw.Draw(img, "RGBA")
    pad = 22
    head = 56
    tabs_h = 44
    seg_h = 44
    cell = (w - 2 * pad - (cols - 1) * 12) // cols
    grid_h = rows * cell + (rows - 1) * 12
    h = pad + head + tabs_h + seg_h + grid_h + pad + 24
    rrect(d, [x, y, x + w, y + h], 22, fill=PANEL, outline=(255, 255, 255, 26), width=1)
    cx = x + pad
    cy = y + pad
    # search bar
    sb_w = w - 2 * pad - 2 * (head - 8) - 16
    rrect(d, [cx, cy, cx + sb_w, cy + head - 8], 10, fill=(36, 37, 42), outline=(255, 255, 255, 18), width=1)
    d.ellipse([cx + 14, cy + 16, cx + 30, cy + 32], outline=MUTED, width=3)
    d.line([(cx + 29, cy + 31), (cx + 36, cy + 38)], fill=MUTED, width=3)
    text(d, (cx + 50, cy + 13), "Search 15,000+ logos…", fr(22), FAINT)
    # gear + menu squares
    for i in range(2):
        bx = cx + sb_w + 8 + i * ((head - 8) + 8)
        rrect(d, [bx, cy, bx + head - 8, cy + head - 8], 10, fill=(36, 37, 42), outline=(255, 255, 255, 18), width=1)
        if i == 0:
            ccx, ccy = bx + (head - 8) / 2, cy + (head - 8) / 2
            d.ellipse([ccx - 6, ccy - 6, ccx + 6, ccy + 6], outline=MUTED, width=3)
        else:
            for k in range(3):
                d.line([(bx + 12, cy + 12 + k * 8), (bx + head - 20, cy + 12 + k * 8)], fill=MUTED, width=3)
    cy += head + 8
    # source tabs
    tw = (w - 2 * pad - 8) // 2
    for i, lbl in enumerate(["Brands Logo", "svgl"]):
        bx = cx + i * (tw + 8)
        on = (i == active_src)
        pill(d, [bx, cy, bx + tw, cy + tabs_h - 8], lbl, fb(20),
             ACCENT if on else (36, 37, 42), (255, 255, 255) if on else MUTED, rad=8)
    cy += tabs_h
    # segment + size
    seg_w = 150
    for i, lbl in enumerate(["Insert", "Replace"]):
        bx = cx + i * (seg_w / 2)
        on = (i == mode)
        rrect(d, [bx, cy, bx + seg_w / 2, cy + seg_h - 8], 8,
              fill=ACCENT if on else (36, 37, 42), outline=(255, 255, 255, 18) if not on else None, width=1)
        text(d, (bx + seg_w / 4, cy + 6), lbl, fb(18), (255, 255, 255) if on else MUTED, anchor="ma")
    # size box
    rrect(d, [cx + seg_w + 10, cy, cx + seg_w + 110, cy + seg_h - 8], 8, fill=(36, 37, 42), outline=(255, 255, 255, 18), width=1)
    text(d, (cx + seg_w + 24, cy + 6), "128 px", fr(18), MUTED)
    # category
    rrect(d, [cx + seg_w + 120, cy, x + w - pad, cy + seg_h - 8], 8, fill=(36, 37, 42), outline=(255, 255, 255, 18), width=1)
    text(d, (cx + seg_w + 134, cy + 6), "All categories", fr(18), MUTED)
    cy += seg_h
    # grid
    i = 0
    for r in range(rows):
        for c in range(cols):
            bx = cx + c * (cell + 12)
            by = cy + r * (cell + 12)
            paste_logo(img, names[i % len(names)], [bx, by, bx + cell, by + cell], card=True, card_fill=CARD, contain=0.56)
            i += 1
    return h


# =========================================================
#  CAROUSEL SLIDES (1920x1080)
# =========================================================
W, H = 1920, 1080


def save(img, name):
    img.convert("RGB").save(os.path.join(OUT, name), optimize=True)
    print("  ", name, os.path.getsize(os.path.join(OUT, name)) // 1024, "KB")


def headline_block(d, x, y, eb, title_lines, sub, ebcolor=ACCENT):
    eyebrow(d, x, y, eb, ebcolor)
    yy = y + 56
    for ln in title_lines:
        text(d, (x, yy), ln, fb(78), TEXT)
        yy += 90
    yy += 10
    for sl in sub:
        text(d, (x, yy), sl, fr(34), MUTED)
        yy += 48
    return yy


def slide_cover(thumb=False):
    img, d = new_canvas(W, H)
    glow(img, 1500, 250, 520, ACCENT, 46)
    glow(img, 360, 880, 460, VIOLET, 36)
    d = ImageDraw.Draw(img, "RGBA")
    # brand row
    bx, by = 150, 150
    adv = brandmark(d, bx, by, 92)
    text(d, (bx + adv + 26, by + 12), "logos", fb(46), TEXT)
    pill(d, [bx + adv + 200, by + 14, bx + adv + 200 + 230, by + 14 + 46], "FIGMA PLUGIN", fb(22), (10, 10, 12), ACCENT, rad=23)
    # title
    text(d, (150, 330), "15,000+ brand logos", fb(118), TEXT)
    text(d, (150, 452), "& icons, inside Figma.", fb(118), TEXT)
    text(d, (150, 610), "Search · insert · replace in place · resize — without leaving the canvas.", fr(40), MUTED)
    # logo strip
    names = ["react", "figma", "vue", "tailwindcss", "openai", "github", "slack",
             "spotify", "notion", "vercel", "stripe", "discord", "supabase", "claude"]
    n = len(names)
    tilesz = 124
    total = n * tilesz + (n - 1) * 22
    sx = (W - total) // 2 if (W - total) // 2 > 80 else 100
    sy = 770
    # clamp: show as many as fit
    maxn = (W - 200) // (tilesz + 22)
    names = names[:maxn]
    total = len(names) * tilesz + (len(names) - 1) * 22
    sx = (W - total) // 2
    for i, nm in enumerate(names):
        bx = sx + i * (tilesz + 22)
        paste_logo(img, nm, [bx, sy, bx + tilesz, sy + tilesz], card=True, contain=0.6)
    text(d, (W // 2, 950), "brandslogo.vercel.app", fr(28), FAINT, anchor="ma")
    save(img, "thumbnail.png" if thumb else "carousel-1.png")


def slide_feature(idx, eb, title_lines, subs, build_visual, ebcolor=ACCENT):
    img, d = new_canvas(W, H)
    glow(img, 1480, 300, 480, ebcolor, 34)
    d = ImageDraw.Draw(img, "RGBA")
    headline_block(d, 150, 170, eb, title_lines, subs, ebcolor)
    build_visual(img)
    footer_brand(d, W, H)
    save(img, "carousel-%d.png" % idx)


def vis_panel_full(img):
    plugin_panel(img, 1030, 250, 740, GRID, active_src=0, mode=0)


def vis_replace(img):
    d = ImageDraw.Draw(img, "RGBA")
    # before / after frames, same square, logo swapped → no distortion
    base_y = 470
    size = 250
    def frame(cx, label, name, color):
        x0 = cx - size // 2
        rrect(d, [x0, base_y, x0 + size, base_y + size], 18, fill=(20, 21, 25), outline=color, width=3)
        # dashed-ish corner ticks
        paste_logo(img, name, [x0 + 20, base_y + 20, x0 + size - 20, base_y + size - 20], card=False, contain=0.8)
        text(d, (cx, base_y + size + 26), label, fb(26), MUTED, anchor="ma")
        text(d, (cx, base_y + size + 64), "%d × %d" % (size, size), fr(22), FAINT, anchor="ma")
    frame(1180, "before", "stripe", (90, 92, 100))
    frame(1620, "after", "spotify", GREEN)
    # arrow
    ay = base_y + size // 2
    d.line([(1330, ay), (1470, ay)], fill=TEXT, width=5)
    d.polygon([(1470, ay - 14), (1470, ay + 14), (1500, ay)], fill=TEXT)
    text(d, (1400, ay - 64), "same frame", fb(22), GREEN, anchor="ma")


def vis_autosize(img):
    d = ImageDraw.Draw(img, "RGBA")
    # an odd-sized placeholder rectangle → logo fits inside, centered
    x0, y0, w, h = 1080, 430, 640, 300
    # dashed rectangle
    dash = 18
    for xx in range(x0, x0 + w, dash * 2):
        d.line([(xx, y0), (min(xx + dash, x0 + w), y0)], fill=ACCENT, width=3)
        d.line([(xx, y0 + h), (min(xx + dash, x0 + w), y0 + h)], fill=ACCENT, width=3)
    for yy in range(y0, y0 + h, dash * 2):
        d.line([(x0, yy), (x0, min(yy + dash, y0 + h))], fill=ACCENT, width=3)
        d.line([(x0 + w, yy), (x0 + w, min(yy + dash, y0 + h))], fill=ACCENT, width=3)
    text(d, (x0, y0 - 40), "selected frame · 640 × 300", fr(24), MUTED)
    paste_logo(img, "react", [x0, y0, x0 + w, y0 + h], card=False, contain=0.5)
    pill(d, [x0, y0 + h + 30, x0 + 200, y0 + h + 30 + 50], "AUTO SIZE", fb(22), ACCENT, (10, 10, 12), rad=25)
    text(d, (x0 + 224, y0 + h + 40), "fills it exactly — no distortion", fr(26), MUTED)


def vis_sizes(img):
    d = ImageDraw.Draw(img, "RGBA")
    x, y, w = 1140, 300, 440
    rrect(d, [x, y, x + w, y + 60], 12, fill=(36, 37, 42), outline=PBORDER, width=1)
    text(d, (x + 20, y + 14), "128 px", fb(26), TEXT)
    d.polygon([(x + w - 38, y + 26), (x + w - 22, y + 26), (x + w - 30, y + 36)], fill=MUTED)
    opts = [("Auto size", ACCENT), ("64 px", None), ("128 px", None), ("256 px", None), ("512 px", None), ("Custom…", VIOLET)]
    oy = y + 78
    rrect(d, [x, oy, x + w, oy + len(opts) * 64 + 16], 14, fill=PANEL, outline=PBORDER, width=1)
    for i, (lbl, c) in enumerate(opts):
        yy = oy + 12 + i * 64
        if i == 0:
            rrect(d, [x + 8, yy, x + w - 8, yy + 56], 8, fill=HILITE)
        text(d, (x + 26, yy + 12), lbl, fb(26) if c else fr(26), c if c else TEXT)
    text(d, (x + w + 56, y + 6), "→", fb(40), MUTED)
    paste_logo(img, "react", [x + w + 120, y - 20, x + w + 320, y + 180], card=True, contain=0.62)


def vis_sources(img):
    d = ImageDraw.Draw(img, "RGBA")
    x, y, w = 1030, 300, 760
    tw = (w - 16) // 2
    pill(d, [x, y, x + tw, y + 58], "Brands Logo", fb(26), ACCENT, (255, 255, 255), rad=10)
    pill(d, [x + tw + 16, y, x + 2 * tw + 16, y + 58], "svgl", fb(26), (40, 41, 46), MUTED, rad=10)
    repo = ["react", "vue", "svelte", "tailwindcss", "nextjs", "nodejs"]
    sv = ["discord", "stripe", "openai", "vercel", "supabase", "prisma"]
    cell, sp = 104, 116

    def cluster(names, cx, cy):
        for i, nm in enumerate(names):
            r, c = divmod(i, 3)
            bx = cx + c * sp
            by = cy + r * sp
            paste_logo(img, nm, [bx, by, bx + cell, by + cell], card=True, contain=0.6)
    cy = y + 96
    cluster(repo, x + 10, cy)
    cluster(sv, x + 10 + 372, cy)
    ly = cy + 2 * sp + 8
    text(d, (x + 10, ly), "15,000+ repo logos", fr(24), MUTED)
    text(d, (x + 10 + 372, ly), "~660 curated svgl icons", fr(24), MUTED)


def vis_layers(img):
    d = ImageDraw.Draw(img, "RGBA")
    x, y, w, ph = 1120, 290, 580, 300
    rrect(d, [x, y, x + w, y + ph], 16, fill=PANEL, outline=PBORDER, width=1)
    rows = [("bolt", 0, "frame", TEXT, True),
            ("wrap by @rakibulism", 1, "frame", MUTED, False),
            ("Vector", 2, "vec", FAINT, False),
            ("Vector", 2, "vec", FAINT, False)]
    for i, (lbl, ind, kind, col, hi) in enumerate(rows):
        yy = y + 26 + i * 60
        if hi:
            rrect(d, [x + 12, yy - 6, x + w - 12, yy + 44], 8, fill=HILITE)
        ix = x + 30 + ind * 36
        if kind == "frame":
            rrect(d, [ix, yy + 8, ix + 22, yy + 30], 4, outline=col, width=2)
        else:
            d.polygon([(ix + 11, yy + 8), (ix + 22, yy + 19), (ix + 11, yy + 30), (ix, yy + 19)], outline=col, width=2)
        text(d, (ix + 40, yy + 8), lbl, fb(26) if hi else fr(24), col)
    cy = y + ph + 34
    for lbl in ["Square frame", "Clip content", "Lock aspect ratio"]:
        bw = text_w(d, lbl, fb(22)) + 50
        rrect(d, [x, cy, x + bw, cy + 50], 25, fill=(26, 38, 31), outline=(40, 86, 58), width=1)
        text(d, (x + 25, cy + 13), lbl, fb(22), GREEN)
        cy += 66


def _mini(img, x, y, w, h, dark=True):
    d = ImageDraw.Draw(img, "RGBA")
    bg = PANEL if dark else (247, 247, 248)
    bd = PBORDER if dark else (210, 211, 214)
    sub = (36, 37, 42) if dark else (235, 236, 238)
    rrect(d, [x, y, x + w, y + h], 16, fill=bg, outline=bd, width=1)
    rrect(d, [x + 16, y + 16, x + w - 16, y + 56], 8, fill=sub)
    cols = 3
    cell = (w - 32 - (cols - 1) * 10) // cols
    for i in range(6):
        r, c = divmod(i, cols)
        bx = x + 16 + c * (cell + 10)
        by = y + 72 + r * (cell + 10)
        rrect(d, [bx, by, bx + cell, by + cell], 8, fill=CARD if dark else (255, 255, 255), outline=None if dark else (216, 217, 220), width=1)
        t = tile(GRID[i])
        if t:
            s = int(cell * 0.58); t = t.resize((s, s), Image.LANCZOS)
            img.alpha_composite(t, (int(bx + (cell - s) / 2), int(by + (cell - s) / 2)))


def vis_themes(img):
    d = ImageDraw.Draw(img, "RGBA")
    pw, ph, y = 320, 380, 280
    _mini(img, 1090, y, pw, ph, dark=True)
    _mini(img, 1090 + pw + 30, y, pw, ph, dark=False)
    cy = y + ph + 44
    px = 1090
    for lbl, on in [("Light", False), ("Dark", False), ("Device", True)]:
        bw = text_w(d, lbl, fb(24)) + 60
        pill(d, [px, cy, px + bw, cy + 54], lbl, fb(24), ACCENT if on else (40, 41, 46),
             (255, 255, 255) if on else MUTED, rad=12)
        px += bw + 16


def slide_cta():
    img, d = new_canvas(W, H)
    glow(img, 960, 400, 620, ACCENT, 40)
    glow(img, 960, 540, 360, VIOLET, 30)
    d = ImageDraw.Draw(img, "RGBA")
    adv = brandmark(d, W // 2 - 30, 230, 110)
    text(d, (W // 2, 400), "Try it in the playground", fb(96), TEXT, anchor="ma")
    text(d, (W // 2, 520), "Run the plugin on the community file — search, insert,", fr(38), MUTED, anchor="ma")
    text(d, (W // 2, 568), "replace and resize any logo in seconds.", fr(38), MUTED, anchor="ma")
    # buttons
    b1 = "▶  Run Brands Logo"
    b2 = "brandslogo.vercel.app"
    w1 = text_w(d, b1, fb(30)) + 70
    w2 = text_w(d, b2, fb(30)) + 70
    gap = 28
    total = w1 + w2 + gap
    x = (W - total) // 2
    pill(d, [x, 680, x + w1, 680 + 76], b1, fb(30), ACCENT, (255, 255, 255), rad=38)
    rrect(d, [x + w1 + gap, 680, x + w1 + gap + w2, 680 + 76], 38, fill=None, outline=(255, 255, 255, 90), width=2)
    text(d, (x + w1 + gap + w2 / 2, 680 + 22), b2, fb(30), TEXT, anchor="ma")
    # logo strip
    names = ["figma", "react", "openai", "vue", "github", "stripe", "notion", "slack", "spotify", "vercel"]
    tilesz = 96
    total = len(names) * tilesz + (len(names) - 1) * 20
    sx = (W - total) // 2
    for i, nm in enumerate(names):
        bx = sx + i * (tilesz + 20)
        paste_logo(img, nm, [bx, 860, bx + tilesz, 860 + tilesz], card=True, contain=0.6)
    save(img, "carousel-9.png")


# =========================================================
#  OG image (1200x630)
# =========================================================
def og():
    w, h = 1200, 630
    img, d = new_canvas(w, h)
    bx, by = 110, 120
    adv = brandmark(d, bx, by, 64)
    text(d, (bx + adv + 18, by + 6), "logos", fb(34), TEXT)
    text(d, (110, 250), "%s free SVG logos," % "15,014", fb(52), TEXT)
    text(d, (110, 312), "ready to drop in.", fb(52), TEXT)
    text(d, (110, 408), "Search, filter by category,", fr(28), MUTED)
    text(d, (110, 446), "download, copy or drop into Figma.", fr(28), MUTED)
    text(d, (110, 528), "brandslogo.vercel.app", fb(26), MUTED)
    names = ["react", "figma", "vue", "slack", "firebase", "tailwindcss", "google-chrome", "spotify", "notion"]
    ts, tg = 106, 14
    gx = w - 110 - 3 * ts - 2 * tg
    gy = (h - 3 * ts - 2 * tg) // 2
    for i, nm in enumerate(names):
        r, c = divmod(i, 3)
        bx = gx + c * (ts + tg)
        by = gy + r * (ts + tg)
        paste_logo(img, nm, [bx, by, bx + ts, by + ts], card=True, card_fill=(255, 255, 255, 16), contain=0.62)
    img.convert("RGB").save(os.path.join(ROOT, "assets", "og.png"), optimize=True)
    print("   assets/og.png", os.path.getsize(os.path.join(ROOT, "assets", "og.png")) // 1024, "KB")


if __name__ == "__main__":
    print("Generating Figma Community assets…")
    slide_cover(thumb=True)                      # thumbnail.png
    slide_cover(thumb=False)                     # carousel-1.png (cover)
    slide_feature(2, "Step 01 · Find", ["Search any brand,", "click to drop it in."],
                  ["15,000+ logos and icons, filtered as you type.", "Insert mode adds it to your canvas instantly."], vis_panel_full)
    slide_feature(3, "Step 02 · Replace", ["Swap a logo without", "breaking your layout."],
                  ["Each logo sits in a fixed square frame, so replacing", "keeps the size — nothing ever distorts."], vis_replace, GREEN)
    slide_feature(4, "Auto size", ["Fill any frame,", "rectangle or image."],
                  ["Pick Auto size, select a layer, click a logo —", "it fits the exact bounds you already have."], vis_autosize)
    slide_feature(5, "Sizes", ["Auto, presets,", "or a custom size."],
                  ["Choose the square size before you insert —", "or resize later with the W × H controls."], vis_sizes, VIOLET)
    slide_feature(6, "Two libraries", ["Brands Logo", "+ svgl, in one place."],
                  ["Switch sources with a tap. Your repo's 15,000+ logos,", "plus svgl's curated brand icons."], vis_sources)
    slide_feature(7, "Clean output", ["Tidy, named,", "non-destructive frames."],
                  ["Square frame · clip content · locked aspect ratio,", "with the SVG wrapped and labelled."], vis_layers, GREEN)
    slide_feature(8, "Comfort", ["Light, dark or device", "theme — your call."],
                  ["Match Figma automatically, plus compact / large", "density and a one-tap settings panel."], vis_themes)
    slide_cta()                                  # carousel-9.png
    og()
    print("Done.")
