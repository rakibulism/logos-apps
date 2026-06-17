#!/usr/bin/env python3
"""Generate og.png (1200x630), favicon.svg and apple-touch-icon.png for the logos gallery."""
import os, subprocess
from PIL import Image, ImageDraw, ImageFont

SRC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W, H = 1200, 630
BG = (10, 10, 10)
FG = (250, 250, 250)
MUTED = (163, 163, 163)
BORDER = (255, 255, 255, 26)

img = Image.new("RGB", (W, H), BG)
d = ImageDraw.Draw(img, "RGBA")

# dot grid
for x in range(0, W, 24):
    for y in range(0, H, 24):
        d.ellipse([x, y, x + 1.5, y + 1.5], fill=(255, 255, 255, 14))

# guide lines + crosshairs (frame pattern motif)
for yy in (70, H - 70):
    d.line([(0, yy), (W, yy)], fill=BORDER, width=1)
for xx in (70, W - 70):
    d.line([(xx, 0), (xx, H)], fill=BORDER, width=1)
def cross(cx, cy, s=8):
    d.line([(cx - s, cy), (cx + s, cy)], fill=(255, 255, 255, 90), width=2)
    d.line([(cx, cy - s), (cx, cy + s)], fill=(255, 255, 255, 90), width=2)
for cx in (70, W - 70):
    for cy in (70, H - 70):
        cross(cx, cy)

def _font(*cands):
    for c in cands:
        if os.path.exists(c): return c
    raise SystemExit("No suitable font found — install DejaVu (Linux) or run on macOS.")
bold = _font("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
             "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
             "/Library/Fonts/Arial Bold.ttf")
reg = _font("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/System/Library/Fonts/Supplemental/Arial.ttf",
            "/Library/Fonts/Arial.ttf")
f_brand = ImageFont.truetype(bold, 30)
f_title = ImageFont.truetype(bold, 46)
f_sub = ImageFont.truetype(reg, 28)

# brand mark (2x2 rounded grid, bottom-right filled) + name
mx, my, t, g = 110, 120, 26, 8
def rrect(x, y, wd, fill=None, outline=None):
    d.rounded_rectangle([x, y, x + wd, y + wd], radius=7, fill=fill, outline=outline, width=3)
rrect(mx, my, t, outline=FG)
rrect(mx + t + g, my, t, outline=FG)
rrect(mx, my + t + g, t, outline=FG)
rrect(mx + t + g, my + t + g, t, fill=FG)
d.text((mx + 2 * t + g + 18, my + t + g - 12), "logos", font=f_brand, fill=FG)

# title + subtitle
TOTAL = len([f for f in os.listdir(os.path.join(SRC, "logos")) if f.endswith(".svg")])
d.text((110, 258), f"{TOTAL:,} free SVG logos,", font=f_title, fill=FG)
d.text((110, 316), "ready to drop in.", font=f_title, fill=FG)
d.text((110, 412), "Search, filter by category,", font=f_sub, fill=MUTED)
d.text((110, 448), "download or copy in one click.", font=f_sub, fill=MUTED)
d.text((110, 525), "rakibulism.github.io/brands-logo", font=ImageFont.truetype(bold, 26), fill=MUTED)

# row of real logos on the right
logos = ["react", "figma", "vue", "slack", "firebase", "tailwindcss", "chrome", "spotify", "notion"]
tiles = []
for n in logos:
    import tempfile
    out = os.path.join(tempfile.gettempdir(), f"og_{n}.png")
    subprocess.run(["convert", "-background", "none", "-density", "220",
                    os.path.join(SRC, "logos", n + ".svg"), "-resize", "64x64", out],
                   check=True, capture_output=True)
    tiles.append(Image.open(out).convert("RGBA"))

# 3x3 tile grid on the right side
ts, tg = 106, 14
gx, gy = W - 110 - 3 * ts - 2 * tg, (H - 3 * ts - 2 * tg) // 2
for i, tile in enumerate(tiles):
    r, c = divmod(i, 3)
    x, y = gx + c * (ts + tg), gy + r * (ts + tg)
    d.rounded_rectangle([x, y, x + ts, y + ts], radius=16, fill=(255, 255, 255, 10), outline=(255, 255, 255, 22), width=1)
    lw, lh = tile.size
    img.paste(tile, (x + (ts - lw) // 2, y + (ts - lh) // 2), tile)

img.save(os.path.join(SRC, "assets", "og.png"), optimize=True)
print("og.png:", os.path.getsize(os.path.join(SRC, "assets", "og.png")) // 1024, "KB")

# favicon.svg — the grid mark, currentColor-safe (dark-aware via media query)
favicon = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="#171717" stroke-width="2" stroke-linejoin="round">
<style>@media (prefers-color-scheme: dark){rect{stroke:#fafafa}rect.f{fill:#fafafa}}</style>
<rect x="3" y="3" width="8" height="8" rx="2"/><rect x="13" y="3" width="8" height="8" rx="2"/>
<rect x="3" y="13" width="8" height="8" rx="2"/><rect class="f" x="13" y="13" width="8" height="8" rx="2" fill="#171717" stroke="none"/>
</svg>"""
open(os.path.join(SRC, "assets", "favicon.svg"), "w").write(favicon)

# apple-touch-icon.png 180x180
ic = Image.new("RGB", (180, 180), BG)
di = ImageDraw.Draw(ic)
t2, g2, off = 56, 14, 27
def rr2(x, y, fill=None, outline=None):
    di.rounded_rectangle([x, y, x + t2, y + t2], radius=14, fill=fill, outline=outline, width=7)
rr2(off, off, outline=FG)
rr2(off + t2 + g2, off, outline=FG)
rr2(off, off + t2 + g2, outline=FG)
rr2(off + t2 + g2, off + t2 + g2, fill=FG)
ic.save(os.path.join(SRC, "assets", "apple-touch-icon.png"), optimize=True)
print("favicon.svg + apple-touch-icon.png OK")
