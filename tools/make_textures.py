#!/usr/bin/env python3
"""Generate the procedural textures used by the site (no AI, no stock assets).
grunge-mask.png: alpha mask with specks/scratches/cracks for distressed type.
noise.png: faint film grain overlay.  Run once; outputs are committed."""
import random, math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter

OUT = Path(__file__).resolve().parent.parent / "src" / "img"
OUT.mkdir(parents=True, exist_ok=True)
rnd = random.Random(1337)
S = 600

# --- grunge mask (white = visible, transparent = worn away) ---
a = Image.new("L", (S, S), 255)
d = ImageDraw.Draw(a)
def wrap_ellipse(x, y, r):
    for dx in (-S, 0, S):
        for dy in (-S, 0, S):
            d.ellipse((x+dx-r, y+dy-r, x+dx+r, y+dy+r), fill=0)
for _ in range(2600):  # fine specks
    wrap_ellipse(rnd.uniform(0, S), rnd.uniform(0, S), rnd.choice([0.6, 0.8, 1, 1.2, 1.6]))
for _ in range(90):  # bigger chips
    wrap_ellipse(rnd.uniform(0, S), rnd.uniform(0, S), rnd.uniform(1.8, 4.2))
for _ in range(14):  # cracks: jagged random walks
    x, y = rnd.uniform(0, S), rnd.uniform(0, S)
    ang = rnd.uniform(0, math.tau)
    pts = [(x, y)]
    for _ in range(rnd.randint(8, 22)):
        ang += rnd.uniform(-0.9, 0.9)
        x += math.cos(ang) * rnd.uniform(6, 18); y += math.sin(ang) * rnd.uniform(6, 18)
        pts.append((x % S, y % S) if 0 <= x < S and 0 <= y < S else (x, y))
    d.line(pts, fill=0, width=rnd.choice([1, 1, 2]))
for _ in range(40):  # scratches
    x, y = rnd.uniform(0, S), rnd.uniform(0, S)
    L = rnd.uniform(20, 90); ang = rnd.uniform(-0.4, 0.4)
    d.line((x, y, x + math.cos(ang)*L, y + math.sin(ang)*L), fill=0, width=1)
a = a.filter(ImageFilter.GaussianBlur(0.35))
img = Image.new("RGBA", (S, S), (255, 255, 255, 0)); img.putalpha(a)
img.save(OUT / "grunge-mask.png", optimize=True)

# --- grain ---
n = Image.new("LA", (200, 200))
px = n.load()
for yy in range(200):
    for xx in range(200):
        v = rnd.randint(0, 255)
        px[xx, yy] = (v, rnd.randint(0, 38))
n.save(OUT / "noise.png", optimize=True)
print("textures written")

# --- favicon.ico (for browsers that ignore the SVG icon) ---
ico = Image.new("RGBA", (64, 64), (0, 0, 0, 255))
dd = ImageDraw.Draw(ico)
dd.ellipse((10, 6, 54, 46), fill=(209, 10, 30, 255)); dd.rectangle((20, 36, 44, 56), fill=(209, 10, 30, 255))
dd.ellipse((17, 20, 29, 33), fill=(0, 0, 0, 255)); dd.ellipse((35, 20, 47, 33), fill=(0, 0, 0, 255))
dd.polygon([(32, 34), (28, 41), (36, 41)], fill=(0, 0, 0, 255))
for x in (26, 32, 38): dd.line((x, 46, x, 56), fill=(0, 0, 0, 255), width=2)
ico.save(OUT / "favicon.ico", sizes=[(16, 16), (32, 32), (48, 48), (64, 64)])
