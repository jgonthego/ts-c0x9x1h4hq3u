# Tee shop (preview): limited-drop black tees

Static site, HTML/CSS/vanilla JS, built by `build.py` (Python stdlib only) into `docs/`.
**Preview only.** No store or checkout exists. Product images are the owner's real designs as
watermarked web copies; nothing is approved for sale and prices are placeholders.

## Quick start
```bash
python3 build.py      # -> docs/   (see "Local preview" below for serving)
```

## Where to change things
| What | Where |
|---|---|
| **Brand name** (placeholder `[Brand TBD]`) | `src/data/site.json` → `BRAND` (the only place) |
| Drop date / countdown | `site.json` → `DROP_AT` (ISO 8601 with offset; empty = "Date TBA") |
| Email signup | `site.json` → `FORM_ID` (empty = form disabled). `FORM_ACTION_TEMPLATE` defaults to Formspree |
| Placeholder price | `site.json` → `PRICE_PLACEHOLDER` (shown as "… placeholder · not final") |
| Categories / filter chips | `site.json` → `CATEGORIES` (`slug` is the shareable `?cat=` value; `adult: true` shows 18+ notices) |
| Products | `src/data/products.json`, **generated** by `tools/import_library.py` |
| Buy button | per product: `status: "approved"`, a final `price`, **and** `pod_url`. Otherwise "Coming soon", disabled. No cart/checkout exists |
| Hosting path | `PATH_PREFIX` / `SITE_URL` (env vars or `site.json`). GitHub Actions sets these automatically |

## Products come from the merch library
```bash
python3 tools/import_library.py /workspace/merch/library   # needs Pillow; ~1 min
python3 build.py
```
The importer reads `catalog.csv`, keeps one product per concept (`best_in_group = yes`), skips the
five garbled mockups, maps rows to categories (rules at the top of the script; anything unmatched goes
to **Other**), writes 600px-wide watermarked WebP copies (`PREVIEW · NOT FOR SALE`) to
`src/img/products/` (originals are never modified), sets the featured top 8, and writes the internal
**`REVIEW.md`** (per-product flags: ODTE letter-O, stamp cut off, risky words). The `_review` data in
`products.json` and `REVIEW.md` are never rendered on public pages.

## Local preview
`PATH_PREFIX` is `/ts-c0x9x1h4hq3u`, so serve the parent of a symlink:
```bash
mkdir -p /tmp/teeshop-serve && ln -sfn "$PWD/docs" /tmp/teeshop-serve/ts-c0x9x1h4hq3u
python3 -m http.server 8473 -d /tmp/teeshop-serve --bind 127.0.0.1
# open http://127.0.0.1:8473/ts-c0x9x1h4hq3u/
/tmp/pwv/bin/python tools/check_site.py http://127.0.0.1:8473/ts-c0x9x1h4hq3u   # QA + screenshots
```

## Deploy later (not done)
`.github/workflows/pages.yml` builds and deploys `docs/` to GitHub Pages once the repo is
pushed and Pages → Source is set to "GitHub Actions". Optional repo variables:
`PATH_PREFIX`, `SITE_URL`, `FORM_ID`. `robots.txt` and `noindex` keep the preview out of search
engines. Remove both at launch.

## Fonts & licenses
Self-hosted in `src/fonts/` with license files: Anton, Shrikhand, Alfa Slab One (SIL OFL 1.1),
Special Elite (Apache 2.0). Alfa Slab One has a Reserved Font Name, so it ships as the
unmodified TTF. No font CDN, no analytics, no third-party requests.
