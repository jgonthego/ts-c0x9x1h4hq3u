#!/usr/bin/env python3
"""Free, code-only typographic mockups for text-only concepts (products with art == "typographic").

Reads type_spec from src/data/products.json, renders slogan type (open fonts: Anton, Shrikhand,
Alfa Slab One, Special Elite, Space Mono) plus a simple vector motif, distresses it, places it on a
flat black tee, and writes WATERMARKED jpgs to src/img/products/<slug>-{mockup,print}.jpg.
No AI image generation, no paid services, no likenesses of real people.

    python3 tools/make_type_mockups.py [slug ...]
"""
import json, math, random, sys, zlib
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageChops

sys.path.insert(0, str(Path(__file__).resolve().parent))
from make_draft_images import watermark  # same DRAFT — NOT APPROVED treatment as the real art

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "src" / "img" / "products"
G = "/usr/share/fonts/truetype/sand-box/google/"
FONTS = {"anton": G + "Anton/Anton-Regular.ttf", "shrikhand": G + "Shrikhand/Shrikhand-Regular.ttf",
         "alfa": G + "Alfa Slab One/AlfaSlabOne-Regular.ttf", "elite": G + "Special Elite/SpecialElite-Regular.ttf",
         "spacemono": G + "Space Mono/SpaceMono-Bold.ttf",
         "greek": "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"}  # Δ / Γ glyphs only
COL = {"bone": (242, 236, 224, 255), "red": (209, 10, 30, 255), "white": (255, 255, 255, 255)}
BONE, RED, INK = COL["bone"], COL["red"], (12, 12, 12, 255)
PW, PH = 900, 1125  # print canvas (4:5)


def F(name, size):
    return ImageFont.truetype(FONTS[name], max(8, int(size)))


def ctext(d, cx, y, t, font, fill, anchor="mt"):
    d.text((cx, y), t, font=font, fill=fill, anchor=anchor)


def rot_text(t, font, fill, angle, box=True, pad=14, border=None):
    """Rubber-stamp style rotated text (optionally boxed)."""
    tmp = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    l, tp, r, b = tmp.textbbox((0, 0), t, font=font)
    w, h = r - l + pad * 2, b - tp + pad * 2
    im = Image.new("RGBA", (w + 8, h + 8), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    if box:
        d.rectangle((4, 4, w + 4, h + 4), outline=border or fill, width=max(4, h // 12))
    d.text((4 + pad - l, 4 + pad - tp), t, font=font, fill=fill)
    return im.rotate(angle, expand=True, resample=Image.BICUBIC)


# ------------------------------------------------------------------ motifs (box = x0, y0, x1, y1)
def skull(d, cx, cy, s, col=BONE, hat=False):
    d.ellipse((cx - s, cy - s * 1.05, cx + s, cy + s * .75), fill=col)
    d.rounded_rectangle((cx - s * .55, cy + s * .4, cx + s * .55, cy + s * 1.05), radius=s * .15, fill=col)
    for ex in (-.42, .42):
        d.ellipse((cx + ex * s - s * .27, cy - s * .2, cx + ex * s + s * .27, cy + s * .32), fill=INK)
    d.polygon([(cx, cy + s * .35), (cx - s * .12, cy + s * .58), (cx + s * .12, cy + s * .58)], fill=INK)
    for tx in (-.3, -.1, .1, .3):
        d.line((cx + tx * s, cy + s * .72, cx + tx * s, cy + s * 1.02), fill=INK, width=max(2, int(s * .05)))
    d.line((cx - s * .1, cy - s * 1.0, cx + s * .05, cy - s * .7, cx - s * .08, cy - s * .45), fill=INK, width=max(2, int(s * .05)))
    if hat:
        d.chord((cx - s * 1.05, cy - s * 1.45, cx + s * 1.05, cy - s * .25), 180, 360, fill=RED)
        d.rectangle((cx - s * 1.3, cy - s * .88, cx + s * 1.3, cy - s * .72), fill=RED)


def candle(d, cx, yb, h, w=26):
    d.rectangle((cx - w / 2, yb - h, cx + w / 2, yb), fill=BONE)
    d.polygon([(cx, yb - h - w * 1.6), (cx - w * .35, yb - h - w * .3), (cx + w * .35, yb - h - w * .3)], fill=RED)


def candles(d, box, n=16, seed=3, down=True):
    x0, y0, x1, y1 = box
    r = random.Random(seed); p = 0; vals = []
    for i in range(n):
        o = p; c = o + r.gauss(-1.2 if down else 1.2, 2.4); vals.append((o, c, max(o, c) + abs(r.gauss(0, 1)), min(o, c) - abs(r.gauss(0, 1)))); p = c
    mn = min(v[3] for v in vals); mx = max(v[2] for v in vals)
    sy = lambda v: y0 + (mx - v) / (mx - mn) * (y1 - y0)
    bw = (x1 - x0) / n
    for i, (o, c, hi, lo) in enumerate(vals):
        x = x0 + i * bw + bw / 2; col = BONE if c >= o else RED
        d.line((x, sy(hi), x, sy(lo)), fill=col, width=4)
        t, b = sorted((sy(o), sy(c)))
        d.rectangle((x - bw * .3, t, x + bw * .3, max(b, t + 4)), fill=col if c < o else None, outline=col, width=4)


def slice_(d, cx, cy, s, angle=0, bite=False):
    pts = [(0, -s), (-s * .62, s * .7), (s * .62, s * .7)]
    a = math.radians(angle)
    tr = lambda p: (cx + p[0] * math.cos(a) - p[1] * math.sin(a), cy + p[0] * math.sin(a) + p[1] * math.cos(a))
    d.polygon([tr(p) for p in pts], fill=(232, 190, 90, 255))
    d.line([tr((-s * .66, s * .72)), tr((s * .66, s * .72))], fill=BONE, width=int(s * .16))
    for px, py in ((0, -s * .25), (-s * .22, s * .3), (s * .22, s * .25), (0, s * .45)):
        x, y = tr((px, py)); r = s * .12
        d.ellipse((x - r, y - r, x + r, y + r), fill=RED)


def m_roulette(d, box, im):
    x0, y0, x1, y1 = box; cx, cy = (x0 + x1) / 2, (y0 + y1) / 2; R = min(x1 - x0, y1 - y0) / 2
    d.ellipse((cx - R, cy - R, cx + R, cy + R), fill=BONE)
    n = 16
    for i in range(n):
        d.pieslice((cx - R * .92, cy - R * .92, cx + R * .92, cy + R * .92), i * 360 / n, (i + 1) * 360 / n, fill=RED if i % 2 else INK)
    f = F("spacemono", R * .1)
    for i, s in enumerate(["380C", "385C", "390C", "395P", "400C", "375P", "410C", "370P"]):
        a = math.radians(i * 45 + 11); ctext(d, cx + math.cos(a) * R * .72, cy + math.sin(a) * R * .72, s, f, BONE, "mm")
    d.ellipse((cx - R * .42, cy - R * .42, cx + R * .42, cy + R * .42), fill=BONE)
    ctext(d, cx, cy, "Δ", F("greek", R * .5), INK, "mm")


def m_drip(d, box, im):
    x0, y0, x1, y1 = box; r = random.Random(5)
    for i in range(9):
        x = x0 + 90 + i * (x1 - x0 - 180) / 8; L = r.randint(30, int((y1 - y0) * .55)); w = r.randint(10, 22)
        d.rectangle((x - w / 2, y0, x + w / 2, y0 + L), fill=RED); d.ellipse((x - w * .8, y0 + L - w * .6, x + w * .8, y0 + L + w), fill=RED)
    candle(d, x1 - 150, y1 - 10, (y1 - y0) * .35)
    d.rectangle((x0 + 110, y1 - 70, x0 + 290, y1 - 10), outline=RED, width=4)
    ctext(d, x0 + 200, y1 - 40, "0DTE · ADMIT 1", F("spacemono", 18), RED, "mm")


def m_penny(d, box, im):
    x0, y0, x1, y1 = box; cx = (x0 + x1) / 2; R = (y1 - y0) * .32
    d.rounded_rectangle((x0 + 60, y0, x1 - 60, y0 + (y1 - y0) * .36), radius=50, fill=RED)
    for k in range(6):
        xx = x0 + 110 + k * (x1 - x0 - 220) / 5; d.line((xx, y0 + 12, xx, y0 + (y1 - y0) * .34), fill=INK, width=6)
    cy = y0 + (y1 - y0) * .62
    d.ellipse((cx - R - 14, cy - R - 14, cx + R + 14, cy + R + 14), outline=BONE, width=8)
    d.ellipse((cx - R, cy - R, cx + R, cy + R), fill=BONE)
    ctext(d, cx, cy, "1¢", F("alfa", R * .9), INK, "mm")


def m_wheel(d, box, im):
    x0, y0, x1, y1 = box; cx, cy = (x0 + x1) / 2, (y0 + y1) / 2; R = min(x1 - x0, y1 - y0) / 2
    d.ellipse((cx - R, cy - R, cx + R, cy + R), outline=BONE, width=14)
    for i in range(12):
        a = math.radians(i * 30); d.line((cx + math.cos(a) * R * .55, cy + math.sin(a) * R * .55, cx + math.cos(a) * R, cy + math.sin(a) * R), fill=BONE, width=6)
    f = F("spacemono", R * .095)
    for a, t in ((-90, "NEXT WEEK"), (0, "NEXT MONTH"), (90, "LEAPS"), (180, "MY GRANDKIDS")):
        rr = math.radians(a); x, y = cx + math.cos(rr) * R * 1.0, cy + math.sin(rr) * R * 1.0
        l, tp, r, b = d.textbbox((x, y), t, font=f, anchor="mm"); d.rectangle((l - 8, tp - 6, r + 8, b + 6), fill=RED); ctext(d, x, y, t, f, BONE, "mm")
    skull(d, cx, cy + R * .05, R * .36); candle(d, cx, cy - R * .4, R * .12, 16)


def m_can(d, box, im):
    x0, y0, x1, y1 = box; cx = (x0 + x1) / 2; w = (x1 - x0) * .3; t, b = y0 + 10, y1 - 10
    pts = [(cx - w, t), (cx + w, t), (cx + w * .8, t + (b - t) * .4), (cx + w * 1.1, t + (b - t) * .5), (cx + w * .75, t + (b - t) * .6), (cx + w, b),
           (cx - w, b), (cx - w * .8, t + (b - t) * .62), (cx - w * 1.1, t + (b - t) * .5), (cx - w * .75, t + (b - t) * .38)]
    d.polygon(pts, fill=BONE)
    d.rectangle((cx - w, t, cx + w, t + 18), fill=(180, 176, 168, 255)); d.rectangle((cx - w, b - 18, cx + w, b), fill=(180, 176, 168, 255))
    ctext(d, cx, t + (b - t) * .22, "IV", F("alfa", w * .8), RED, "mm")
    ctext(d, cx, t + (b - t) * .78, "EARNINGS EDITION", F("spacemono", w * .13), INK, "mm")
    im.alpha_composite(rot_text("beat on EPS. down 40%.", F("elite", 30), RED, 8), (int(cx + w * .7), int(t + (b - t) * .35)))


def m_pin(d, box, im):
    x0, y0, x1, y1 = box; ym = (y0 + y1) / 2 + 40; r = random.Random(9)
    for i in range(14):
        x = x0 + 60 + i * (x1 - x0 - 120) / 13; start = ym + r.choice([-1, 1]) * r.randint(60, 160)
        d.line((x, start, x, ym), fill=BONE, width=5); d.rectangle((x - 9, min(start, ym) + 10 if start < ym else ym + 10, x + 9, (start if start > ym else ym) - 10), outline=BONE, width=4)
    d.line((x0 + 20, ym, x1 - 20, ym), fill=RED, width=10)
    ctext(d, x1 - 30, ym - 14, "STRIKE", F("anton", 34), RED, "rb")
    skull(d, (x0 + x1) / 2, y0 + 70, 60)


def m_candles(d, box, im):
    candles(d, (box[0] + 40, box[1], box[2] - 40, box[3]), 18, 4)


def m_gamma(d, box, im):
    x0, y0, x1, y1 = box; cx, cy = (x0 + x1) / 2, (y0 + y1) / 2; R = (y1 - y0) / 2
    d.rounded_rectangle((cx - R * 1.1, cy - R, cx + R * 1.1, cy + R), radius=R * .7, fill=RED)
    d.rounded_rectangle((cx + R * .7, cy - R * .2, cx + R * 1.5, cy + R * .7), radius=R * .3, fill=RED)
    ctext(d, cx, cy, "Γ", F("greek", R * 1.4), BONE, "mm")
    d.line((cx - R * .9, cy - R * .5, cx - R * .5, cy - R * .1, cx - R * .7, cy + R * .3), fill=INK, width=6)


def m_flatline(d, box, im):
    x0, y0, x1, y1 = box; cx = (x0 + x1) / 2
    skull(d, cx, y0 + (y1 - y0) * .32, (y1 - y0) * .2, hat=True)
    sign = rot_text("WILL SELL PREMIUM FOR FOOD", F("elite", 30), INK, -4, box=False, pad=16)
    bg = Image.new("RGBA", sign.size, (200, 170, 120, 255)); bg.alpha_composite(sign); bg = bg.rotate(0)
    im.alpha_composite(bg, (int(cx - bg.width / 2), int(y0 + (y1 - y0) * .58)))
    yl = y1 - 40
    d.line((x0 + 40, yl, cx - 60, yl, cx - 40, yl - 30, cx - 20, yl + 25, cx, yl, x1 - 40, yl), fill=RED, width=6)
    ctext(d, x1 - 40, yl + 12, "VOL: 12M", F("spacemono", 24), BONE, "rt")


def m_thermo(d, box, im):
    x0, y0, x1, y1 = box; cx = (x0 + x1) / 2
    d.rounded_rectangle((cx - 34, y0, cx + 34, y1 - 70), radius=34, outline=BONE, width=10)
    d.rectangle((cx - 16, y0 + 30, cx + 16, y1 - 90), fill=RED); d.ellipse((cx - 60, y1 - 130, cx + 60, y1 - 10), fill=RED)
    for k in range(5): d.line((cx + 44, y0 + 40 + k * 40, cx + 74, y0 + 40 + k * 40), fill=BONE, width=5)
    for ang, dx in ((-35, -1), (35, 1)):
        d.line((cx + dx * 30, y0 + 10, cx + dx * 90, y0 - 30), fill=RED, width=8)


def m_bond(d, box, im):
    x0, y0, x1, y1 = box; m = 110
    d.rectangle((x0 + m, y0 + 20, x1 - m, y1 - 20), fill=BONE); d.rectangle((x0 + m + 14, y0 + 34, x1 - m - 14, y1 - 34), outline=INK, width=4)
    ctext(d, (x0 + x1) / 2, y0 + 70, "TREASURY BOND", F("alfa", 40), INK, "mt"); ctext(d, (x0 + x1) / 2, y0 + 130, "30 YEAR · DURATION: YES", F("spacemono", 22), INK, "mt")
    d.line((x0 + m + 40, (y0 + y1) / 2 + 20, x0 + (x1 - x0) / 2, (y0 + y1) / 2 - 10, x1 - m - 40, y1 - 60), fill=RED, width=8)
    for sx in (-1, 1):
        xx = x0 + m - 40 if sx < 0 else x1 - m + 40
        d.polygon([(xx, (y0 + y1) / 2 - 40), (xx, (y0 + y1) / 2 + 40), (xx - sx * 50, (y0 + y1) / 2)], fill=RED)
    r = random.Random(2)
    for _ in range(7):
        x, y = r.choice([x0 + m - 70, x1 - m + 70]) + r.randint(-20, 20), r.randint(int(y0), int(y1)); d.ellipse((x - 16, y - 16, x + 16, y + 16), outline=BONE, width=5)


def m_arch(d, box, im):
    x0, y0, x1, y1 = box; cx = (x0 + x1) / 2; R = (x1 - x0) / 2 - 20
    for k, col in enumerate([RED, BONE, RED, BONE, RED]):
        rr = R - k * 30; d.pieslice((cx - rr, y1 - rr, cx + rr, y1 + rr), 180, 360, fill=col)
    rr = R - 150; d.pieslice((cx - rr, y1 - rr, cx + rr, y1 + rr), 180, 360, fill=INK)
    d.polygon([(cx, y1 - rr + 20), (cx - 30, y1 - 60), (cx + 30, y1 - 60)], fill=BONE); d.rectangle((cx - 30, y1 - 60, cx + 30, y1), fill=BONE)
    f = F("spacemono", 20)
    for k, t in enumerate(["25C", "30C", "35C", "50C"]): ctext(d, cx + 60, y1 - 150 + k * 34, t, f, BONE, "lm")


def m_panels(d, box, im):
    x0, y0, x1, y1 = box; w = (x1 - x0 - 40) / 3
    for k, (t, sm) in enumerate((("WEEK 1", "+$300"), ("WEEK 3", "+$310"), ("WEEK 5", "——"))):
        a = x0 + k * (w + 20); d.rectangle((a, y0, a + w, y1), outline=BONE, width=6)
        ctext(d, a + w / 2, y0 + 20, t, F("anton", 40), BONE, "mt"); ctext(d, a + w / 2, y1 - 20, sm, F("spacemono", 34), RED if k == 2 else BONE, "mb")
        cy = (y0 + y1) / 2; r = 34
        if k == 2:
            d.rectangle((a + 16, y0 + 80, a + w - 16, cy + 30), fill=(60, 60, 60, 255))
            d.ellipse((a + w / 2 - r, cy + 20, a + w / 2 + r, cy + 20 + r * 2), fill=BONE)
        else:
            d.ellipse((a + w / 2 - r, cy - r, a + w / 2 + r, cy + r), fill=BONE); ctext(d, a + w / 2, cy, "1¢", F("alfa", 26), INK, "mm")


def m_ticket(d, box, im):
    x0, y0, x1, y1 = box; m = 60
    d.rectangle((x0 + m, y0, x1 - m, y1), fill=BONE)
    for x in range(int(x0 + m + 10), int(x1 - m - 10), 26): d.line((x, y0 + 12, x + 12, y0 + 12), fill=RED, width=4); d.line((x, y1 - 12, x + 12, y1 - 12), fill=RED, width=4)
    sx0, sy0, sx1, sy1 = x0 + m + 40, y0 + 50, x1 - m - 40, y1 - 90
    d.rectangle((sx0, sy0, sx1, sy1), fill=(150, 150, 150, 255)); d.rectangle((sx0, sy0, (sx0 + sx1) / 2 + 40, sy1), fill=(250, 250, 250, 255))
    ctext(d, (sx0 + sx1) / 2 - 80, (sy0 + sy1) / 2, "390C · 0DTE · 0.92", F("spacemono", 34), INK, "mm")
    cx = sx1 - 70; cy = (sy0 + sy1) / 2; d.ellipse((cx - 44, cy - 44, cx + 44, cy + 44), fill=(214, 160, 80, 255))
    ctext(d, x0 + m + 40, y1 - 40, "DRAW TIME 3:59", F("anton", 30), RED, "lm")
    skull(d, x1 - m - 70, y1 - 45, 26, INK)


def m_shield(d, box, im):
    x0, y0, x1, y1 = box; cx = (x0 + x1) / 2; w = (y1 - y0) * .42
    pts = [(cx - w, y0), (cx + w, y0), (cx + w, y0 + (y1 - y0) * .5), (cx, y1), (cx - w, y0 + (y1 - y0) * .5)]
    d.polygon(pts, fill=BONE); d.line(pts + [pts[0]], fill=RED, width=10)
    d.line((cx - w * .5, y0 + 50, cx + w * .5, y0 + (y1 - y0) * .55), fill=INK, width=14); d.line((cx + w * .5, y0 + 50, cx - w * .5, y0 + (y1 - y0) * .55), fill=INK, width=14)
    d.line((cx + 20, y0 + 20, cx - 10, y0 + 120, cx + 30, y0 + 200), fill=INK, width=5)
    st = rot_text("ASSIGNED", F("anton", 70), RED, 14)
    im.alpha_composite(st, (int(cx - st.width / 2), int(y0 + (y1 - y0) * .42 - st.height / 2)))


def m_chairs(d, box, im):
    x0, y0, x1, y1 = box; cx, cy = (x0 + x1) / 2, (y0 + y1) / 2; R = min(x1 - x0, y1 - y0) / 2 - 30
    for i in range(10):
        a = math.radians(i * 36); x, y = cx + math.cos(a) * R, cy + math.sin(a) * R * .8
        d.rectangle((x - 18, y - 6, x + 18, y + 6), fill=BONE); d.line((x - 16, y, x - 16, y + 34), fill=BONE, width=5); d.line((x + 16, y, x + 16, y + 34), fill=BONE, width=5)
        d.rectangle((x - 18, y - 34, x + 18, y - 26), fill=BONE)
    m_can(d, (cx - 110, cy - 90, cx + 110, cy + 90), im) if False else None
    d.polygon([(cx - 36, cy - 60), (cx + 36, cy - 60), (cx + 46, cy), (cx + 30, cy + 60), (cx - 36, cy + 60), (cx - 48, cy)], fill=BONE)
    ctext(d, cx, cy, "IV", F("alfa", 40), RED, "mm")
    ck = (x1 - 60, y0 + 40); d.ellipse((ck[0] - 36, ck[1] - 36, ck[0] + 36, ck[1] + 30), outline=BONE, width=5)
    d.line((ck[0], ck[1], ck[0], ck[1] - 22), fill=BONE, width=4); d.line((ck[0], ck[1], ck[0] + 16, ck[1] + 8), fill=BONE, width=4)
    d.rectangle((ck[0] - 6, ck[1] + 28, ck[0] + 6, ck[1] + 60), fill=BONE)


def m_trap(d, box, im):
    x0, y0, x1, y1 = box; cx, cy = (x0 + x1) / 2, (y0 + y1) / 2; R = (y1 - y0) * .48
    steel, tooth = (175, 175, 175, 255), (215, 215, 215, 255)
    for a0, a1 in ((200, 340), (20, 160)):
        d.arc((cx - R * 1.25, cy - R, cx + R * 1.25, cy + R), a0, a1, fill=steel, width=18)
        for k in range(9):
            a = math.radians(a0 + 8 + k * (a1 - a0 - 16) / 8)
            bx, by = cx + math.cos(a) * R * 1.25, cy + math.sin(a) * R
            tx, ty = cx + math.cos(a) * R * .95, cy + math.sin(a) * R * .72
            d.polygon([(bx - 13, by), (bx + 13, by), (tx, ty)], fill=tooth)
    for sx in (-1, 1):
        d.ellipse((cx + sx * R * 1.25 - 22, cy - 22, cx + sx * R * 1.25 + 22, cy + 22), fill=steel)
    d.line((cx + R * 1.25, cy, x1, cy + R * .3), fill=steel, width=6)
    slice_(d, cx, cy + 6, R * .55, angle=12)


def m_pineapple(d, box, im):
    x0, y0, x1, y1 = box; cx = (x0 + x1) / 2 - 60; cy = (y0 + y1) / 2 + 40; rw, rh = (y1 - y0) * .22, (y1 - y0) * .32
    d.ellipse((cx - rw, cy - rh, cx + rw, cy + rh), fill=(230, 180, 60, 255))
    for k in range(-5, 6):
        d.line((cx - rw + k * 30, cy - rh, cx + rw + k * 30, cy + rh), fill=INK, width=3); d.line((cx + rw + k * 30, cy - rh, cx - rw + k * 30, cy + rh), fill=INK, width=3)
    d.ellipse((cx - rw, cy - rh, cx + rw, cy + rh), outline=INK, width=4)
    for k in (-2, -1, 0, 1, 2):
        d.polygon([(cx + k * 18, cy - rh + 10), (cx + k * 18 - 18, cy - rh + 10), (cx + k * 34, cy - rh - 110 + abs(k) * 25)], fill=BONE)
    d.rectangle((cx - rw - 40, cy + rh - 10, cx + rw + 40, cy + rh + 10), fill=BONE)  # dock rail
    st = rot_text("GUILTY", F("anton", 92), RED, -14)
    im.alpha_composite(st, (int(cx + rw - 20), int(cy - st.height / 2)))


def m_tomb(d, box, im):
    x0, y0, x1, y1 = box; cx = (x0 + x1) / 2 + 80; w = (y1 - y0) * .34
    d.rounded_rectangle((cx - w, y0 + 20, cx + w, y1), radius=w, fill=(150, 150, 150, 255)); d.rectangle((cx - w, y0 + w, cx + w, y1), fill=(150, 150, 150, 255))
    for i, t in enumerate(("HE ATE", "THE", "CRUST")): ctext(d, cx, y0 + w * .75 + i * 50, t, F("alfa", 40), INK, "mt")
    d.line((cx - w * .3, y1 - 50, cx + w * .3, y1 - 50), fill=INK, width=4)
    sx = x0 + 170; skull(d, sx, y0 + (y1 - y0) * .5, (y1 - y0) * .17)
    slice_(d, sx, y1 - 60, 60, angle=90)
    candle(d, sx + 130, y1 - 10, 90, 22)


def m_ivbag(d, box, im):
    x0, y0, x1, y1 = box; cx = (x0 + x1) / 2; w = (y1 - y0) * .26
    d.line((cx, y0, cx, y0 + 30), fill=BONE, width=6); d.ellipse((cx - 16, y0, cx + 16, y0 + 24), outline=BONE, width=5)
    d.rounded_rectangle((cx - w, y0 + 30, cx + w, y1 - 120), radius=36, outline=BONE, width=8)
    d.rounded_rectangle((cx - w + 14, y0 + 130, cx + w - 14, y1 - 134), radius=26, fill=RED)
    d.rectangle((cx - w * .7, y0 + 170, cx + w * .7, y0 + 260), fill=BONE)
    ctext(d, cx, y0 + 190, "SAUCE", F("anton", 40), INK, "mt"); ctext(d, cx, y0 + 236, "Type: MARINARA · 500 ml", F("spacemono", 16), INK, "mt")
    d.line((cx, y1 - 120, cx, y1 - 70, cx + 60, y1 - 40, cx + 140, y1 - 30), fill=RED, width=8)


def m_box(d, box, im):
    x0, y0, x1, y1 = box; cx, cy = (x0 + x1) / 2, (y0 + y1) / 2; s = (y1 - y0) * .42
    d.polygon([(cx - s * 1.2, cy - s * .2), (cx + s * 1.2, cy - s * .2), (cx + s * 1.4, cy + s), (cx - s * 1.4, cy + s)], fill=(196, 160, 110, 255))
    d.polygon([(cx - s * 1.2, cy - s * .2), (cx + s * 1.2, cy - s * .2), (cx + s, cy - s), (cx - s, cy - s)], fill=(170, 136, 92, 255))
    r = random.Random(6)
    for _ in range(9):
        x, y, rr = cx + r.uniform(-s, s), cy + r.uniform(0, s * .8), r.uniform(10, 28); d.ellipse((x - rr, y - rr * .7, x + rr, y + rr * .7), fill=(120, 80, 40, 255))
    note = Image.new("RGBA", (220, 200), (250, 225, 90, 255)); nd = ImageDraw.Draw(note)
    nd.text((110, 100), "I'm fine", font=F("elite", 44), fill=INK, anchor="mm")
    note = note.rotate(-9, expand=True, resample=Image.BICUBIC); im.alpha_composite(note, (int(cx + s * .2), int(cy - s * 1.15)))


def m_decay(d, box, im):
    x0, y0, x1, y1 = box; L, B = x0 + 80, y1 - 30
    d.line((L, y0 + 10, L, B, x1 - 40, B), fill=BONE, width=6)
    pts = [(L + t * (x1 - 60 - L), B - (B - y0 - 40) * (1 - t) ** 2.2 - 6) for t in [i / 40 for i in range(41)]]
    d.line(pts, fill=RED, width=9, joint="curve")
    slice_(d, L + 70, y0 + 70, 55, angle=-10)
    ctext(d, x1 - 50, B - 14, "COLD", F("anton", 34), RED, "rb"); ctext(d, L + 10, B + 8, "HOT", F("spacemono", 20), BONE, "lt")
    cx, cy = x1 - 170, y0 + 110; d.ellipse((cx - 60, cy - 60, cx + 60, cy + 50), outline=BONE, width=6)
    d.polygon([(cx - 40, cy + 40), (cx + 10, cy + 45), (cx - 10, cy + 110)], fill=BONE)
    d.line((cx, cy, cx, cy - 40), fill=BONE, width=5); d.line((cx, cy, cx + 30, cy + 10), fill=BONE, width=5)


MOTIFS = {k[2:]: v for k, v in globals().items() if k.startswith("m_")}
MOTIF_H = 380


def distress(im, seed):
    w, h = im.size
    n = Image.effect_noise((w // 3, h // 3), 90).resize((w, h), Image.BICUBIC).filter(ImageFilter.GaussianBlur(1.2))
    holes = n.point(lambda v: 0 if v > 205 else 255)
    r = random.Random(seed); sc = Image.new("L", (w, h), 255); sd = ImageDraw.Draw(sc)
    for _ in range(26):  # scratches
        x, y = r.randint(0, w), r.randint(0, h); sd.line((x, y, x + r.randint(-120, 120), y + r.randint(-30, 30)), fill=0, width=r.randint(2, 4))
    a = ImageChops.multiply(im.getchannel("A"), ImageChops.multiply(holes, sc))
    im.putalpha(a)
    return im


def render_print(p):
    sp = p["type_spec"]; lines = sp["lines"]; motif = sp.get("motif"); at = sp.get("motif_at", len(lines))
    items = [("t", l) for l in lines]
    if motif: items.insert(at, ("m", motif))
    tmp = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    TW = PW - 80

    def size_for(text, font, scale):
        s = 260 * scale
        while s > 20:
            l, t, r, b = tmp.textbbox((0, 0), text, font=F(font, s))
            if r - l <= TW * min(1, scale + .05): break
            s -= 4
        return s

    plan = []
    for kind, v in items:
        if kind == "t":
            text, font, col, scale = v; s = size_for(text, font, scale); l, t, r, b = tmp.textbbox((0, 0), text, font=F(font, s))
            plan.append(["t", text, font, col, s, b - t + 22])
        else:
            plan.append(["m", v, MOTIF_H + 30])
    scar_h = 90
    total = sum(x[-1] for x in plan) + scar_h
    k = min(1.0, (PH - 60) / total)
    im = Image.new("RGBA", (PW, PH), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    y = (PH - total * k) / 2
    for x in plan:
        if x[0] == "t":
            _, text, font, col, s, h = x; f = F(font, s * k); l, t, r, b = d.textbbox((0, 0), text, font=f)
            d.text((PW / 2 - (l + r) / 2, y - t), text, font=f, fill=COL[col]); y += h * k
        else:
            mh = MOTIF_H * k; MOTIFS[x[1]](d, (60, y + 10 * k, PW - 60, y + 10 * k + mh), im); d = ImageDraw.Draw(im); y += x[-1] * k
    sc = sp.get("scarcity") or f"No. ___/{p['edition_size']}"
    f = F("elite", 26); l, t, r, b = d.textbbox((0, 0), sc, font=f); bw = r - l + 40
    yy = y + 20; d.rectangle((PW / 2 - bw / 2, yy, PW / 2 + bw / 2, yy + 52), outline=BONE, width=3)
    d.text((PW / 2 - (l + r) / 2, yy + 26 - (t + b) / 2), sc, font=f, fill=BONE)
    return distress(im, zlib.crc32(p["slug"].encode()))


def tee(print_im):
    W, H = 1000, 1149
    im = Image.new("RGBA", (W, H), (205, 201, 193, 255)); d = ImageDraw.Draw(im)
    body = [(330, 92), (140, 165), (38, 370), (172, 438), (232, 338), (232, 1105), (768, 1105), (768, 338), (828, 438), (962, 370), (860, 165), (670, 92)]
    d.polygon([(x + 6, y + 10) for x, y in body], fill=(170, 166, 158, 255))
    d.polygon(body, fill=(16, 16, 16, 255))
    d.ellipse((392, 40, 608, 150), fill=(205, 201, 193, 255)); d.arc((386, 36, 614, 160), 0, 180, fill=(40, 40, 40, 255), width=16)
    for x0, x1 in ((232, 238), (762, 768)): d.rectangle((x0, 340, x1, 1105), fill=(28, 28, 28, 255))
    pw = 420; ph = int(pw * PH / PW); pr = print_im.resize((pw, ph), Image.LANCZOS)
    im.alpha_composite(pr, ((W - pw) // 2, 205))
    return im


def main():
    data = json.loads((ROOT / "src" / "data" / "products.json").read_text())["products"]
    only = set(sys.argv[1:])
    OUT.mkdir(parents=True, exist_ok=True)
    for p in data:
        if p.get("art") != "typographic" or (only and p["slug"] not in only):
            continue
        pr = render_print(p)
        mock = watermark(tee(pr)).convert("RGB")
        mock.save(OUT / f"{p['slug']}-mockup.jpg", "JPEG", quality=82, optimize=True, progressive=True)
        canvas = Image.new("RGBA", (1000, 1250), (10, 10, 10, 255)); canvas.alpha_composite(pr.resize((900, 1125), Image.LANCZOS), (50, 62))
        watermark(canvas).convert("RGB").save(OUT / f"{p['slug']}-print.jpg", "JPEG", quality=82, optimize=True, progressive=True)
        print("wrote", p["slug"])


if __name__ == "__main__":
    main()
