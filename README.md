# Tee shop (preview): limited-drop black tees for options traders

Static site, HTML/CSS/vanilla JS, built by `build.py` (Python stdlib only) into `docs/`.
**Preview only.** No repo, store, or account exists yet. All product art is an unapproved,
watermarked draft placeholder.

## Quick start
```bash
python3 build.py                                  # -> docs/
python3 -m http.server 8473 -d docs --bind 127.0.0.1   # open http://localhost:8473
/tmp/pwv/bin/python tools/check_site.py http://localhost:8473   # QA + screenshots
```

## Where to change things
| What | Where |
|---|---|
| **Brand name** (placeholder `[Brand TBD]`) | `src/data/site.json` → `BRAND` (the only place) |
| Drop date / countdown | `site.json` → `DROP_AT` (ISO 8601 with offset; empty = "Date TBA") |
| Email signup | `site.json` → `FORM_ID` (empty = form disabled). `FORM_ACTION_TEMPLATE` defaults to Formspree |
| Products | `src/data/products.json` |
| Buy button | per product: `status: "approved"` **and** `pod_url` set (Printful/Printify/Shopify/Etsy link). Otherwise the button reads "Coming soon" and is disabled |
| Hosting path | `PATH_PREFIX` / `SITE_URL` (env vars or `site.json`). GitHub Actions sets these automatically |

## Swapping in approved designs
1. Put final images in `src/img/products/` (`<slug>-mockup.jpg`, `<slug>-print.jpg`, roughly 4:5).
2. In `products.json`: set `status` to `"approved"`, remove `draft_source`, fill `pod_url`.
3. `python3 build.py`. The build fails if an approved product still points at a draft source,
   if an image is missing, or if anyone tries to use blocked drafts #01/#05.

## Draft placeholders
`tools/make_draft_images.py` reads the raw mockups from `/workspace/merch/space-roadster-v2/`
(kept **outside** the repo) and writes watermarked "DRAFT — NOT APPROVED" JPGs. Designs #01
and #05 are hard-blocked (car resembles a Corvette, trademark risk).

## Deploy later (not done)
`.github/workflows/pages.yml` builds and deploys `docs/` to GitHub Pages once the repo is
pushed and Pages → Source is set to "GitHub Actions". Optional repo variables:
`PATH_PREFIX`, `SITE_URL`, `FORM_ID`. `robots.txt` and `noindex` keep the preview out of search
engines. Remove both at launch.

## Fonts & licenses
Self-hosted in `src/fonts/` with license files: Anton, Shrikhand, Alfa Slab One (SIL OFL 1.1),
Special Elite (Apache 2.0). Alfa Slab One has a Reserved Font Name, so it ships as the
unmodified TTF. No font CDN, no analytics, no third-party requests.
