#!/usr/bin/env python3
"""Make WATERMARKED web placeholders from unapproved draft mockups.

Only run locally. The unwatermarked originals stay outside the repo
(/workspace/merch by default; each product's draft_source is a path under it,
without extension); only watermarked JPGs land in src/img/products/.
Designs that need a trademark check (e.g. v2 #01/#05, car resembles a Corvette)
carry tm_check in products.json and show an internal badge; build.py refuses to
approve them until it is cleared. If a design has no "-print.png", the print
view is cropped from the chest of the mockup.

    python3 tools/make_draft_images.py [SOURCE_DIR]
"""
import json, sys, math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
SRC = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/workspace/merch")
OUT = ROOT / "src" / "img" / "products"
FONT = "/usr/share/fonts/truetype/sand-box/google/Anton/Anton-Regular.ttf"
MARK = "DRAFT — NOT APPROVED"


def font(size):
    try:
        return ImageFont.truetype(FONT, size)
    except OSError:
        return ImageFont.load_default()


def watermark(im: Image.Image) -> Image.Image:
    im = im.convert("RGBA")
    w, h = im.size
    # diagonal repeated text tile
    layer = Image.new("RGBA", (w * 2, h * 2), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    f = font(max(28, w // 16))
    step_y = max(90, h // 6)
    for i, y in enumerate(range(0, h * 2, step_y)):
        x0 = -(i % 2) * (w // 4)
        d.text((x0, y), ("  " + MARK + "  ") * 4, font=f, fill=(255, 255, 255, 70))
    layer = layer.rotate(28, resample=Image.BICUBIC)
    layer = layer.crop((w // 2, h // 2, w // 2 + w, h // 2 + h))
    im = Image.alpha_composite(im, layer)
    # solid red banner top + bottom
    d = ImageDraw.Draw(im)
    bh = max(44, h // 14)
    fb = font(int(bh * 0.62))
    for y in (0, h - bh):
        d.rectangle((0, y, w, y + bh), fill=(176, 0, 18, 235))
        tw = d.textlength(MARK + " · PLACEHOLDER ONLY", font=fb)
        d.text(((w - tw) / 2, y + bh * 0.14), MARK + " · PLACEHOLDER ONLY", font=fb, fill=(255, 255, 255, 255))
    return im


def main():
    products = json.loads((ROOT / "src" / "data" / "products.json").read_text())["products"]
    OUT.mkdir(parents=True, exist_ok=True)
    for p in products:
        src = p.get("draft_source")
        if not src:
            continue
        for suffix, kind, bg in (("", "mockup", None), ("-print", "print", (10, 10, 10))):
            f = SRC / f"{src}{suffix}.png"
            if not f.exists() and kind == "print":  # no separate print file: crop the chest
                m = Image.open(SRC / f"{src}.png").convert("RGBA")
                w, h = m.size
                f = m.crop((int(w * .25), int(h * .2), int(w * .75), int(h * .86)))
            im = f if isinstance(f, Image.Image) else Image.open(f)
            if bg:  # flatten transparent print file onto near-black, pad to 4:5
                im = im.convert("RGBA")
                H = int(im.height * 1.3)
                W = max(int(H * 0.8), int(im.width * 1.15))
                H = int(W * 1.25)
                canvas = Image.new("RGBA", (W, H), bg + (255,))
                canvas.alpha_composite(im, ((W - im.width) // 2, (H - im.height) // 2))
                im = canvas
            else:  # tighten the grey border a bit
                w, h = im.size
                im = im.crop((int(w * .04), int(h * .03), int(w * .96), int(h * .97)))
            im.thumbnail((1000, 1250))
            out = watermark(im).convert("RGB")
            dest = OUT / f"{p['slug']}-{kind}.jpg"
            out.save(dest, "JPEG", quality=82, optimize=True, progressive=True)
            print("wrote", dest.relative_to(ROOT), out.size)


if __name__ == "__main__":
    main()
