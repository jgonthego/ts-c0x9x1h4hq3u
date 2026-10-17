#!/usr/bin/env python3
"""Import the owner's real designs from the merch library into the site.

    python3 tools/import_library.py [LIBRARY_DIR]     # default /workspace/merch/library

Reads LIBRARY_DIR/catalog.csv and LIBRARY_DIR/images/*.jpg (originals are only read,
never modified), keeps one product per concept (best_in_group == "yes"), skips garbled
mockups, maps each row to a site category, and writes:
  * src/img/products/<slug>.webp          600px-wide web copy with the PREVIEW watermark
  * src/img/products/<slug>-detail.webp   600px-wide chest crop, same watermark
  * src/data/products.json                product data used by build.py
  * REVIEW.md                             internal review list (flags never reach public pages)
Requires Pillow (local tool only; build.py itself stays stdlib-only).
"""
import csv, json, re, sys
from collections import Counter, OrderedDict
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
LIB = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/workspace/merch/library")
OUT_IMG = ROOT / "src" / "img" / "products"
FONT = "/usr/share/fonts/truetype/sand-box/google/Anton/Anton-Regular.ttf"
MARK = "PREVIEW · NOT FOR SALE"
WIDTH = 600

EXCLUDE = ["7pA43", "lo9YF", "hcijd", "YFVtD", "Zpzj7"]          # garbled text
FEATURED = ["9rz6l", "4Tnuh", "9P2Ix", "zc3Yh", "mN0Ug", "wsdNu", "wqmft", "pF9td"]
STAMP_CUT = ["9rz6l", "heark"]                                    # known: edition stamp cut off

# category rules, first match wins; (key, regex over slogan+visuals+notes, required series or None)
RULES = [
    ("political", r"\btrump\b|\bmidterms?\b|\bvote[d]?\b|\belection\b", None),
    ("green-candle", r".", "innuendo"),
    ("gym", r"\bdeadlift\b|\bhyrox\b|\bspotter\b|\bbarbell\b", None),
    ("night-nurse", r"\bnight shift\b|\bnurse\b|\bstethoscope\b|\bwork nights\b", None),
    ("dachshund", r"\bdachshund\b|\blong dog\b|\bshort legs\b|\bwiener\b", None),
    ("adhd", r"\btoo many tabs\b|\bexecutive dysfunction\b|\badhd\b", None),
    ("options-gang", r"\btheta\b|\biron condor\b|\bwheel\b|\bgreeks?\b|\bvega\b|\bgamma\b|\bcovered call\b|\bsell premium\b", None),
    ("0dte-losses", r".", "loss"),
]
RISKY = [r"whore", r"slut", r"deep throat", r"full throat", r"\bthroat\b", r"\bsuck", r"\bmouth\b", r"\bchoke",
         r"made me hard", r"\bcame\b", r"\briot\b"]


def slugify(s):
    s = s.replace("Ø", "0").lower()
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")


def display(s):
    """Site text uses the correct term 0DTE (digit zero). The printed designs are NOT changed."""
    return re.sub(r"\b[OØ]DTE\b|ØDTE", "0DTE", s)


def font(size):
    try:
        return ImageFont.truetype(FONT, size)
    except OSError:
        return ImageFont.load_default()


def watermark(im):
    """Same approach as the old draft placeholders (diagonal tiled text + red banner), lighter."""
    im = im.convert("RGBA")
    w, h = im.size
    layer = Image.new("RGBA", (w * 2, h * 2), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    f = font(max(22, w // 18))
    for i, y in enumerate(range(0, h * 2, max(80, h // 6))):
        d.text((-(i % 2) * (w // 4), y), ("   " + MARK + "   ") * 4, font=f, fill=(255, 255, 255, 34))
    layer = layer.rotate(28, resample=Image.BICUBIC).crop((w // 2, h // 2, w // 2 + w, h // 2 + h))
    im = Image.alpha_composite(im, layer)
    d = ImageDraw.Draw(im)
    bh = max(30, h // 26)
    fb = font(int(bh * 0.6))
    y = h - bh
    d.rectangle((0, y, w, h), fill=(176, 0, 18, 225))
    tw = d.textlength(MARK, font=fb)
    d.text(((w - tw) / 2, y + bh * 0.16), MARK, font=fb, fill=(255, 255, 255, 255))
    return im.convert("RGB")


def main():
    rows = list(csv.DictReader(open(LIB / "catalog.csv", newline="", encoding="utf-8")))
    need = {"filename", "slogan_text", "series", "key_visuals", "print_quality", "near_duplicate_group", "best_in_group", "notes"}
    assert need <= set(rows[0]), f"unexpected columns: {list(rows[0])}"
    excluded, kept = [], []
    for r in rows:
        fid = r["filename"].rsplit(".", 1)[0]
        if any(x in r["filename"] for x in EXCLUDE):
            excluded.append((r, "garbled text (excluded by request)"))
        elif r["best_in_group"].strip().lower() not in ("yes", "true", "1"):
            continue
        else:
            kept.append(r)
    OUT_IMG.mkdir(parents=True, exist_ok=True)
    for f in OUT_IMG.iterdir():
        f.unlink()
    products, slugs, unmapped = [], set(), []
    for r in kept:
        fid = r["filename"].rsplit(".", 1)[0]
        hay = " ".join([r["slogan_text"], r["key_visuals"], r["notes"]]).lower()
        cat = next((k for k, rx, ser in RULES if (ser is None or r["series"] == ser) and re.search(rx, hay)), "other")
        if cat == "other":
            unmapped.append(r)
        parts = [p.strip() for p in r["slogan_text"].split(" / ")]
        title, sub = display(parts[0]), display(" / ".join(parts[1:]))
        slug = slugify(title)
        if slug in slugs:
            slug += "-" + fid.lower()
        slugs.add(slug)
        # images
        src = Image.open(LIB / "images" / r["filename"])
        im = src.copy(); im.thumbnail((WIDTH, 2000), Image.LANCZOS)
        watermark(im).save(OUT_IMG / f"{slug}.webp", "WEBP", quality=74, method=6)
        w, h = src.size
        det = src.crop((int(w * .14), int(h * .16), int(w * .86), int(h * .70)))
        det.thumbnail((WIDTH, 2000), Image.LANCZOS)
        watermark(det).save(OUT_IMG / f"{slug}-detail.webp", "WEBP", quality=74, method=6)
        # internal flags (REVIEW.md only)
        s = r["slogan_text"]
        if "Ø" in s:
            odte = "no: slashed zero Ø (per catalog notes)"
        elif re.search(r"\bODTE\b", s):
            odte = "yes: catalog transcription reads 'ODTE' (letter O); art not visually verified"
        else:
            odte = "none in transcribed slogan; small print on art unverified"
        stamp = "yes (" + (r["notes"] or "known issue") + ")" if fid in STAMP_CUT else (
            "yes (" + r["notes"] + ")" if "stamp" in r["notes"].lower() and "crop" in r["notes"].lower() else "not noted; unverified")
        risky = sorted({m.group(0).strip() for rx in RISKY for m in re.finditer(rx, s, re.I)}, key=str.lower)
        extra = []
        if re.search(r"\btrump\b", s, re.I):
            extra.append("real-person name (Trump): POD/marketplace policy check, unverified")
        if r["print_quality"] != "clean":
            extra.append(f"print_quality={r['print_quality']}")
        if r["notes"] and fid not in STAMP_CUT and "Ø" not in s:
            extra.append("catalog note: " + r["notes"])
        products.append(OrderedDict(
            id=fid, slug=slug, status="preview", category=cat, source_file=r["filename"],
            title=title, subtitle=sub, slogan=display(s), slogan_as_printed=s,
            series=r["series"], group=r["near_duplicate_group"],
            featured=FEATURED.index(fid) + 1 if fid in FEATURED else None,
            images={"main": f"img/products/{slug}.webp", "detail": f"img/products/{slug}-detail.webp"},
            img_size=[im.width, im.height], pod_url="",
            _review={"odte_letter_o": odte, "stamp_cut_off": stamp,
                     "risky_words": (", ".join(risky) + " (POD/payment rules unchecked)") if risky else "none detected in slogan (unverified)",
                     "other": extra},
        ))
    missing = [f for f in FEATURED if f not in {p["id"] for p in products}]
    assert not missing, f"featured not found: {missing}"
    (ROOT / "src" / "data" / "products.json").write_text(json.dumps(
        {"_comment": "GENERATED by tools/import_library.py from /workspace/merch/library/catalog.csv. "
                     "Edit the import rules, not this file. Internal review flags live only in the gitignored REVIEW.md.",
         "products": [{k: v for k, v in p.items() if k != "_review"} for p in products]}, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    write_review(rows, products, excluded, unmapped)
    c = Counter(p["category"] for p in products)
    print(f"{len(products)} products; categories: {dict(c)}; unmapped->other: {[u['filename'] for u in unmapped]}; excluded: {[x[0]['filename'] for x in excluded]}")


def write_review(rows, products, excluded, unmapped):
    cfg = json.loads((ROOT / "src" / "data" / "site.json").read_text())
    names = {c["key"]: c["name"] for c in cfg["CATEGORIES"]}
    c = Counter(p["category"] for p in products)
    L = ["# Internal review list (NOT published)", "",
         "Generated by `tools/import_library.py` from `/workspace/merch/library/catalog.csv`. "
         "Nothing in this file is rendered on the public pages. Designs were **not** modified.", "",
         f"- Catalog rows: {len(rows)}; concepts (near-duplicate groups): {len({r['near_duplicate_group'] for r in rows})}",
         f"- Included products (best_in_group = yes, garbled excluded): **{len(products)}**",
         "- Groups with no clean pick (`best_in_group = no - none clean`), so no product: "
         + "; ".join(sorted({r['near_duplicate_group'] for r in rows if 'none clean' in r['best_in_group']})),
         "", "## Per category", "", "| Category | Count |", "|---|---|"]
    L += [f"| {names[k]} | {c.get(k, 0)} |" for k in names]
    L += ["", "## Unmapped rows (placed in Other)", ""]
    L += [f"- `{u['filename']}` {u['slogan_text']} (series `{u['series']}`; visuals: {u['key_visuals']})" for u in unmapped] or ["- none"]
    L += ["", "## Excluded", ""]
    L += [f"- `{r['filename']}` \"{r['slogan_text']}\": {why}; best_in_group = `{r['best_in_group']}`" for r, why in excluded]
    L += ["- `heark.jpg` (stamp cut off) is not best_in_group, so not included; its group G09 uses `9rz6l.jpg`.",
          "- All other best_in_group = no rows (near-duplicates) are not shown.", "",
          "## Mapping rules", "",
          "First match wins: Political (trump / midterm / vote / election in slogan+visuals) → Green Candle (series `innuendo`) → "
          "Gym (deadlift / hyrox) → Night Shift Nurse → Dachshund (dachshund / long dog / short legs) → ADHD (too many tabs / "
          "executive dysfunction) → Options Gang (theta, iron condor, wheel, Greeks, vega, gamma, covered call, sell premium) → "
          "0DTE Losses (series `loss`) → Other. Note: three `loss`-series theta jokes (DMUuz, daEwE, FrsML) land in Options Gang; "
          "\"I VOTED FOR THE GREEN CANDLE / Trump Era\" and \"ASSIGNED BY TRUMP\" land in Political.", "",
          "## Flag legend", "",
          "- **ODTE-letter-O**: based on the catalog's slogan transcription only. The art itself was not checked letter-by-letter, so treat as unverified.",
          "- **stamp-cut-off**: from the known-issue list / catalog notes. Other designs weren't inspected for cropping (unverified).",
          "- **risky-word**: keyword scan of the slogan for terms that may break print-on-demand or payment-processor content rules. Rules not checked (unverified).",
          "- Site titles show `0DTE` (digit zero) as site copy; the printed art still says whatever it says (`slogan_as_printed` in products.json).", "",
          "## Products", "",
          "| # | File | Title (site) | Category | Featured | ODTE-letter-O | Stamp cut off | Risky words | Other |",
          "|---|---|---|---|---|---|---|---|---|"]
    for i, p in enumerate(products, 1):
        rv = p["_review"]
        L.append(f"| {i} | `{p['source_file']}` | {p['slogan'].replace('|', '/')} | {names[p['category']]} | {p['featured'] or ''} | "
                 f"{rv['odte_letter_o']} | {rv['stamp_cut_off']} | {rv['risky_words']} | {'; '.join(rv['other'])} |")
    (ROOT / "REVIEW.md").write_text("\n".join(L) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
