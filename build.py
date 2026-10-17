#!/usr/bin/env python3
"""Static site builder: src/ -> docs/.  Pure standard library.

    python3 build.py                     # local build, links rooted at "/"
    PATH_PREFIX=/tee-shop python3 build.py   # e.g. GitHub project Pages
    SITE_URL=https://example.com python3 build.py

Config: src/data/site.json (BRAND lives there and only there).
Products: src/data/products.json.
"""
import html, json, os, random, shutil, sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
OUT = ROOT / "docs"

CFG = json.loads((SRC / "data" / "site.json").read_text())
PRODUCTS = json.loads((SRC / "data" / "products.json").read_text())["products"]

BRAND = CFG["BRAND"]
PREFIX = os.environ.get("PATH_PREFIX", CFG.get("PATH_PREFIX", "")).rstrip("/")
SITE_URL = os.environ.get("SITE_URL", CFG.get("SITE_URL", "")).rstrip("/")
FORM_ID = os.environ.get("FORM_ID", CFG.get("FORM_ID", "")).strip()
COLLECTIONS = CFG.get("COLLECTIONS", [])
COLL = {c["key"]: c for c in COLLECTIONS}

e = html.escape


def url(path=""):
    """Site-absolute URL honoring PATH_PREFIX."""
    return f"{PREFIX}/{path.lstrip('/')}"


def money(n):
    return f"${n:,.0f}" if float(n).is_integer() else f"${n:,.2f}"


# ---------------------------------------------------------------- SVG bits
SKULL = """<svg class="skull" viewBox="0 0 100 112" aria-hidden="true"><path fill="currentColor" d="M50 4C24 4 8 22 8 46c0 14 6 25 15 31v15c0 5 3 8 7 8h40c4 0 7-3 7-8V77c9-6 15-17 15-31C92 22 76 4 50 4z"/><ellipse cx="33" cy="50" rx="12" ry="13" fill="#000"/><ellipse cx="67" cy="50" rx="12" ry="13" fill="#000"/><path d="M50 62l-7 14h14z" fill="#000"/><path d="M36 86v14M44 86v14M52 86v14M60 86v14M68 86v14" stroke="#000" stroke-width="3"/><path d="M50 4l-4 12 7 7-6 10" stroke="#000" stroke-width="2.5" fill="none"/></svg>"""


def candles_svg(n=42, seed=7, w=1200, h=420, cls="candles"):
    """Decorative falling candlestick chart. Not real market data."""
    r = random.Random(seed)
    price, bars = 100.0, []
    for i in range(n):
        drift = -1.1 if i > n * 0.25 else 0.9
        o = price
        c = o + r.gauss(drift, 3.2)
        hi = max(o, c) + abs(r.gauss(0, 2))
        lo = min(o, c) - abs(r.gauss(0, 2))
        bars.append((o, hi, lo, c))
        price = c
    if n > 30:  # final capitulation candle
        o = price; c = o - 14
        bars.append((o, o + 1.5, c - 4, c))
    allv = [v for b in bars for v in b]
    mn, mx = min(allv), max(allv)
    sy = lambda v: 10 + (mx - v) / (mx - mn) * (h - 20)
    bw = w / len(bars)
    parts = []
    for i, (o, hi, lo, c) in enumerate(bars):
        x = i * bw + bw / 2
        up = c >= o
        col = "#f2ece0" if up else "#d10a1e"
        parts.append(f'<line x1="{x:.1f}" x2="{x:.1f}" y1="{sy(hi):.1f}" y2="{sy(lo):.1f}" stroke="{col}" stroke-width="2"/>')
        top, bot = sy(max(o, c)), sy(min(o, c))
        parts.append(f'<rect x="{x - bw*0.32:.1f}" y="{top:.1f}" width="{bw*0.64:.1f}" height="{max(2, bot-top):.1f}" fill="{col if not up else "none"}" stroke="{col}" stroke-width="2"/>')
    return f'<svg class="{cls}" viewBox="0 0 {w} {h}" preserveAspectRatio="none" aria-hidden="true">{"".join(parts)}</svg>'


def stamp(top, mid, bot, cls=""):
    return (f'<div class="stamp {cls}" aria-hidden="true"><span class="stamp-top">{e(top)}</span>'
            f'<span class="stamp-mid">{e(mid)}</span><span class="stamp-bot">{e(bot)}</span></div>')


TICKER_WORDS = ["0DTE", "THETA GANG", "ASSIGNED AT 4:01", "IV CRUSH", "MAX PAIN", "BAGHOLDER",
                "EXPIRED WORTHLESS", "ROLL IT", "BUYING POWER: $0.00", "NOT FINANCIAL ADVICE"]


def ticker():
    items = "".join(f'<span class="tk">{e(w)} <b>{"▼" if i % 3 else "▲"}</b></span>' for i, w in enumerate(TICKER_WORDS))
    return f'<div class="ticker" aria-hidden="true"><div class="ticker-track">{items}{items}</div></div>'


# ---------------------------------------------------------------- layout
def page(title, body, path="", desc=None, og_image=None):
    desc = desc or f"{BRAND}: limited-drop black tees for options traders. {CFG['TAGLINE']}"
    full_title = f"{title} | {BRAND}" if title else f"{BRAND}: {CFG['TAGLINE']}"
    canon = f'<link rel="canonical" href="{e(SITE_URL + url(path))}">' if SITE_URL else ""
    og_img = ""
    if og_image and SITE_URL:
        og_img = f'<meta property="og:image" content="{e(SITE_URL + url(og_image))}">'
    nav = [("", "Drop"), ("size-guide/", "Size guide"), ("faq/", "FAQ"), ("legal/", "Fine print")]
    cur = ' aria-current="page"'
    nav_html = "".join(
        f'<a href="{url(p)}"{cur if p == path else ""}>{e(t)}</a>' for p, t in nav)
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(full_title)}</title>
<meta name="description" content="{e(desc)}">
<meta name="robots" content="noindex,nofollow,noarchive">
<meta name="theme-color" content="#000000">
<meta property="og:title" content="{e(full_title)}">
<meta property="og:description" content="{e(desc)}">
<meta property="og:type" content="website">
{og_img}
{canon}
<link rel="icon" href="{url('img/favicon.svg')}" type="image/svg+xml">
<link rel="preload" href="{url('fonts/Anton-Regular.woff2')}" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="{url('css/site.css')}">
</head>
<body>
<a class="skip" href="#main">Skip to content</a>
<div class="preview-bar" role="note"><strong>Preview site.</strong> Every design shown is an unapproved draft. Nothing is for sale yet. Not financial advice.</div>
{ticker()}
<header class="site-header">
  <a class="logo" href="{url()}"><span class="logo-skull">{SKULL}</span><span class="logo-text" data-brand>{e(BRAND)}</span></a>
  <button class="nav-toggle" aria-expanded="false" aria-controls="site-nav"><span></span><span></span><span></span><span class="sr">Menu</span></button>
  <nav id="site-nav" class="site-nav">{nav_html}</nav>
</header>
<main id="main">
{body}
</main>
<footer class="site-footer">
  <div class="footer-grid">
    <div>
      <p class="footer-brand">{e(BRAND)}</p>
      <p class="muted">{e(CFG['TAGLINE'])}</p>
    </div>
    <div class="footer-disclaimer">
      <p><strong>Not financial advice.</strong> This is a humor apparel brand. Nothing here is investment, tax, or trading advice, and no one here is a licensed anything. Options trading carries substantial risk of loss. If a T-shirt is part of your risk management, please talk to a professional.</p>
      <p>Not affiliated with any broker, exchange, trading platform, or space/automotive company. All designs on this preview are drafts and may change or never be sold.</p>
    </div>
    <nav class="footer-nav"><a href="{url('size-guide/')}">Size guide</a><a href="{url('faq/')}">FAQ</a><a href="{url('legal/')}">Fine print &amp; credits</a></nav>
  </div>
  <p class="copy muted">© {date.today().year} {e(BRAND)}. Humor. Not advice.</p>
</footer>
<script>window.SITE={json.dumps({"dropAt": CFG.get("DROP_AT", ""), "formEnabled": bool(FORM_ID)})};</script>
<script src="{url('js/site.js')}" defer></script>
</body>
</html>
"""


def countdown_block():
    return f"""<div class="countdown" data-countdown>
  <p class="cd-label">{e(CFG['DROP_NAME'])} opens in</p>
  <div class="cd-grid" data-cd-grid hidden>
    <div><span data-cd="d">00</span><small>days</small></div>
    <div><span data-cd="h">00</span><small>hrs</small></div>
    <div><span data-cd="m">00</span><small>min</small></div>
    <div><span data-cd="s">00</span><small>sec</small></div>
  </div>
  <p class="cd-tba" data-cd-tba>Date TBA</p>
  <p class="cd-note muted">Join the list to hear first. No spam. Just pain.</p>
</div>"""


def signup_block(heading="Join the drop list"):
    action = CFG["FORM_ACTION_TEMPLATE"].replace("{FORM_ID}", FORM_ID) if FORM_ID else ""
    dis = "" if FORM_ID else " disabled"
    note = ("We'll email you when a drop opens. Unsubscribe anytime." if FORM_ID else
            "Sign-ups open soon. The list isn't live yet, so this form is switched off.")
    return f"""<section class="signup" id="drop-list">
  <div class="signup-inner">
    <h2 class="distress slab">{e(heading)}</h2>
    <p>Small runs. No restocks planned. Get the heads-up before a drop opens.</p>
    <form class="signup-form" method="POST" action="{e(action)}"{dis and ' aria-disabled="true"'}>
      <label class="sr" for="email">Email address</label>
      <input id="email" name="email" type="email" required autocomplete="email" placeholder="you@bagholder.com"{dis}>
      <input type="text" name="_gotcha" tabindex="-1" autocomplete="off" class="hp" aria-hidden="true">
      <button type="submit" class="btn btn-red"{dis}>{"Notify me" if FORM_ID else "Opening soon"}</button>
    </form>
    <p class="form-note muted">{e(note)}</p>
  </div>
</section>"""


def badge(p):
    out = '<span class="badge-draft">Draft · not approved</span>' if p["status"] != "approved" else ""
    if p.get("tm_check"):
        out += f'<span class="badge-tm" title="{e(p["tm_check"])}">Internal: trademark check needed</span>'
    return out


def coll_name(p, short=False):
    c = COLL.get(p.get("collection"), {})
    return c.get("short", c.get("name", "")) if short else c.get("name", "")


def buy_button(p, big=False):
    cls = "btn btn-buy" + (" btn-lg" if big else "")
    if p["status"] == "approved" and p.get("pod_url"):
        return f'<a class="{cls} btn-red" href="{e(p["pod_url"])}" rel="noopener" target="_blank">Buy now · {money(p["target_price"])}</a>'
    return f'<button class="{cls}" disabled aria-disabled="true">Coming soon</button>'


def product_card(p, i):
    return f"""<article class="card" data-collection="{e(p.get('collection', ''))}">
  <a class="card-link" href="{url('products/' + p['slug'] + '/')}">
    <div class="card-img">
      <img src="{url(p['images']['mockup'])}" alt="Draft mockup: black tee printed '{e(p['slogan_top'])} {e(p['slogan_bottom'])}'" loading="lazy" width="1000" height="1149">
    </div>
    <div class="card-body">
      <div class="card-tags"><span class="card-no">No. {i:02d}</span>{badge(p)}</div>
      <p class="card-coll">{e(coll_name(p, True))}{' · type mockup' if p.get('art') == 'typographic' else ''}</p>
      <h3 class="card-title">{e(p['title'])}</h3>
      <p class="card-slogan">“{e(p['slogan_top'])} {e(p['slogan_bottom'])}”</p>
      <div class="card-meta"><span>Target {money(p['target_price'])}<small> · not final</small></span><span class="edition">Planned run /{p['edition_size']}</span></div>
    </div>
  </a>
  <div class="card-cta">{buy_button(p)}</div>
</article>"""


GLOSSARY = [
    ("0DTE", "Options expiring today. A full financial lifecycle in six and a half hours."),
    ("Theta gang", "People who sell options and collect decay. Right 90% of the time; the other 10% gets a shirt."),
    ("Assigned", "When the option you sold gets exercised and you suddenly own 100 shares of something you hate."),
    ("IV crush", "Nailing the earnings direction and still losing money. Volatility left the building with your premium."),
    ("Max pain", "The strike where the most options expire worthless. Also: a lifestyle."),
]


def home():
    cards = "\n".join(product_card(p, i + 1) for i, p in enumerate(PRODUCTS))
    counts = {c["key"]: sum(1 for p in PRODUCTS if p.get("collection") == c["key"]) for c in COLLECTIONS}
    tabs = f'<button type="button" class="ftab" data-filter="all" aria-pressed="true">All <span>{len(PRODUCTS)}</span></button>' + "".join(
        f'<button type="button" class="ftab" data-filter="{e(c["key"])}" aria-pressed="false">{e(c.get("short", c["name"]))} <span>{counts[c["key"]]}</span></button>'
        for c in COLLECTIONS if counts[c["key"]])
    gloss = "".join(f'<div class="gl-item"><dt>{e(t)}</dt><dd>{e(d)}</dd></div>' for t, d in GLOSSARY)
    body = f"""
<section class="hero">
  {candles_svg()}
  <div class="hero-inner">
    <div class="hero-copy">
      {stamp(CFG['DROP_NAME'], 'LIMITED', 'NUMBERED RUNS', 'stamp-hero')}
      <h1 class="hero-title">
        <span class="ht-1 distress slab">EXPIRED</span>
        <span class="ht-2 distress script">worthless</span>
        <span class="ht-3 distress">&amp; dressed for it.</span>
      </h1>
      <p class="hero-sub">{e(CFG['TAGLINE'])} Small, numbered runs of black tees for 0DTE degenerates, theta gang, and anyone who has ever been assigned at 4:01.</p>
      <div class="hero-ctas"><a class="btn btn-red btn-lg" href="#drop">See the drop</a><a class="btn btn-ghost btn-lg" href="#drop-list">Join the drop list</a></div>
    </div>
    <aside class="hero-side">
      <div class="hero-skull">{SKULL}</div>
      {countdown_block()}
    </aside>
  </div>
</section>

<section class="drop" id="drop">
  <div class="section-head">
    <p class="kicker">{e(CFG['DROP_NAME'])} · preview</p>
    <h2 class="distress slab">{e(CFG['DROP_SUBTITLE'])}</h2>
    <p class="muted">Placeholder lineup. These are <strong>draft concepts, not approved designs</strong>, shown so the layout can be reviewed. Prices and run sizes are proposals. Designs marked “type mockup” are slogan-only placeholders: the illustration hasn't been drawn yet.</p>
  </div>
  <div class="filters" role="group" aria-label="Filter by collection" data-filters>{tabs}</div>
  <p class="filter-note muted small" data-filter-note aria-live="polite"></p>
  <div class="grid" data-grid>
{cards}
  </div>
</section>

<section class="how">
  <div class="how-grid">
    <div class="how-item"><span class="how-no">01</span><h3>Limited drops</h3><p>Each design is planned as one numbered run. When the run closes, the design retires.</p></div>
    <div class="how-item"><span class="how-no">02</span><h3>Black tees only</h3><p>Heavy black cotton, red and bone-white ink. Like your P&amp;L, but wearable.</p></div>
    <div class="how-item"><span class="how-no">03</span><h3>Printed to order</h3><p>Every shirt is printed when it's ordered. No warehouse of unsold inventory. We learned.</p></div>
  </div>
</section>

<section class="glossary">
  <div class="section-head"><p class="kicker">Required reading</p><h2 class="distress slab">Glossary of pain</h2></div>
  <dl class="gl-grid">{gloss}</dl>
</section>

{signup_block()}
"""
    return page("", body, "")


def product_page(p, i):
    n = len(PRODUCTS)
    prev_p, next_p = PRODUCTS[(i - 1) % n], PRODUCTS[(i + 1) % n]
    draft_note = ""
    if p["status"] != "approved":
        draft_note = """<div class="draft-note"><strong>Draft, not approved.</strong> This artwork is a placeholder concept and is watermarked on purpose. It may change completely or never be produced.</div>"""
        if p.get("art") == "typographic":
            draft_note += """<div class="draft-note"><strong>Type-only mockup.</strong> This concept has no finished illustration yet. The image is a quick slogan layout with simple placeholder shapes.</div>"""
    if p.get("tm_check"):
        draft_note += f"""<div class="draft-note tm-note"><strong>Internal note: trademark check needed.</strong> {e((lambda t: t[:1].upper() + t[1:])(p["tm_check"].split(": ", 1)[-1]))}. Not cleared for sale.</div>"""
    sizes = "".join(f"<option>{s}</option>" for s in ["S", "M", "L", "XL", "2XL", "3XL"])
    body = f"""
<section class="product">
  <nav class="crumbs"><a href="{url()}">Drop</a> / <span>{e(coll_name(p))}</span> / <span>{e(p['title'])}</span></nav>
  <div class="product-grid">
    <div class="gallery" data-gallery>
      <div class="gallery-main">
        <img data-gallery-main src="{url(p['images']['mockup'])}" alt="Draft mockup of the {e(p['title'])} tee" width="1000" height="1149">
      </div>
      <div class="gallery-thumbs" role="tablist" aria-label="Product images">
        <button class="thumb is-active" role="tab" aria-selected="true" data-src="{url(p['images']['mockup'])}" data-alt="Draft mockup of the {e(p['title'])} tee"><img src="{url(p['images']['mockup'])}" alt="" width="1000" height="1149"><span>On tee</span></button>
        <button class="thumb" role="tab" aria-selected="false" data-src="{url(p['images']['print'])}" data-alt="Draft print artwork for {e(p['title'])}"><img src="{url(p['images']['print'])}" alt="" width="926" height="1157"><span>Artwork</span></button>
      </div>
    </div>
    <div class="product-info">
      {stamp(CFG['DROP_NAME'], f"No. {i+1:02d}", f"PLANNED RUN /{p['edition_size']}", 'stamp-product')}
      <h1 class="product-title distress slab">{e(p['title'])}</h1>
      <div class="card-tags">{badge(p)}</div>
      <p class="product-slogan"><span>{e(p['slogan_top'])}</span> <span class="red">{e(p['slogan_bottom'])}</span></p>
      <p class="product-price">{money(p['target_price'])} <small>target price · not final</small></p>
      {draft_note}
      <p class="product-blurb">{e(p['blurb'])}</p>
      <form class="buy-form" onsubmit="return false">
        <label for="size">Size <a href="{url('size-guide/')}">Size guide</a></label>
        <select id="size" name="size" disabled>{sizes}</select>
        {buy_button(p, big=True)}
      </form>
      <p class="muted small">Not on sale yet. Buying opens when the drop goes live and the final design is approved.</p>
      <ul class="spec">
        <li><span>Tee</span>{e(p['tee_color'])} unisex crew (final blank TBD)</li>
        <li><span>Print</span>Front, printed to order (method set by print partner)</li>
        <li><span>Run</span>Planned limited run of {p['edition_size']}. Not yet produced</li>
        <li><span>Tags</span>{e(' · '.join(p['tags']))}</li>
      </ul>
      <p class="fine">Humor product. Not financial advice. Not affiliated with any broker, exchange, or space/automotive company.</p>
    </div>
  </div>
  <nav class="pn">
    <a href="{url('products/' + prev_p['slug'] + '/')}">← {e(prev_p['title'])}</a>
    <a href="{url('products/' + next_p['slug'] + '/')}">{e(next_p['title'])} →</a>
  </nav>
</section>
{signup_block("Get pinged when it drops")}
"""
    return page(p["title"], body, f"products/{p['slug']}/",
                desc=f"{p['slogan_top']} {p['slogan_bottom']} A limited-drop black tee (draft preview).",
                og_image=p["images"]["mockup"])


SIZE_ROWS = [  # inches: (size, chest width, body length). Typical unisex retail-fit tee.
    ("S", 18, 28), ("M", 20, 29), ("L", 22, 30), ("XL", 24, 31), ("2XL", 26, 32), ("3XL", 28, 33)]


def size_guide():
    rows = "".join(
        f"<tr><th scope=row>{s}</th><td>{w}\"</td><td>{w*2.54:.0f} cm</td><td>{l}\"</td><td>{l*2.54:.0f} cm</td></tr>"
        for s, w, l in SIZE_ROWS)
    body = f"""
<section class="page">
  <p class="kicker">Fit check</p>
  <h1 class="distress slab">Size guide</h1>
  <div class="draft-note"><strong>Placeholder chart.</strong> These are typical measurements for a unisex retail-fit tee. The real chart will be copied from the exact blank our print partner uses before anything goes on sale.</div>
  <div class="table-wrap"><table class="size-table">
    <thead><tr><th>Size</th><th colspan=2>Chest width (flat)</th><th colspan=2>Body length</th></tr></thead>
    <tbody>{rows}</tbody>
  </table></div>
  <div class="how-grid how-tight">
    <div class="how-item"><span class="how-no">A</span><h3>Chest width</h3><p>Lay a tee you like flat. Measure armpit to armpit. Compare.</p></div>
    <div class="how-item"><span class="how-no">B</span><h3>Body length</h3><p>From the high point of the shoulder straight down to the hem.</p></div>
    <div class="how-item"><span class="how-no">C</span><h3>Between sizes?</h3><p>Size up. Unlike your position size, here that's fine.</p></div>
  </div>
</section>"""
    return page("Size guide", body, "size-guide/")


FAQ = [
    ("Is any of this financial advice?", "No. It's T-shirts. It's jokes. Nothing on this site is investment, trading, or tax advice. Options can lose you more than you expect, faster than you expect. Act accordingly."),
    ("Can I buy a shirt right now?", "Not yet. This is a preview. The designs shown are unapproved drafts and every Buy button is switched off until a drop goes live."),
    ("When does the drop open?", "Date TBA. When one is set, the countdown on the home page will show it. Join the drop list to hear first once sign-ups open."),
    ("What does “limited” mean here?", "Each design is planned as a single numbered run with a fixed size. When the run closes, that design retires. Run sizes on the preview are proposals."),
    ("Will there be restocks?", "None are planned. That's the point of a drop."),
    ("How are shirts made and shipped?", "Each shirt will be printed to order by a print-on-demand partner. Production times, shipping rates, and regions will be posted before launch."),
    ("Returns and exchanges?", "The policy will be posted before anything goes on sale and will follow the print partner's terms for misprints and damaged items. Check the size guide first. It saves everyone pain."),
    ("Are you affiliated with a broker, exchange, or space company?", "No. No broker, exchange, trading app, automaker, or rocket company is involved with or endorses this."),
    ("Why is everything watermarked “DRAFT”?", "Because the artwork isn't approved. Placeholders are marked so nobody mistakes them for final product."),
]


def faq():
    items = "".join(f"<details><summary>{e(q)}</summary><p>{e(a)}</p></details>" for q, a in FAQ)
    body = f"""
<section class="page">
  <p class="kicker">Questions you should have asked before buying that call</p>
  <h1 class="distress slab">FAQ</h1>
  <div class="faq">{items}</div>
</section>
{signup_block()}"""
    return page("FAQ", body, "faq/")


def legal():
    body = f"""
<section class="page prose">
  <p class="kicker">Read this before you sue us</p>
  <h1 class="distress slab">The fine print</h1>
  <h2>Not financial advice</h2>
  <p>{e(BRAND)} is a humor apparel brand. Everything on this site and on our shirts is satire and jokes about trading culture. None of it is investment, financial, legal, tax, or trading advice, and nobody involved is acting as your advisor. Trading options involves substantial risk and is not suitable for everyone. You can lose your entire investment, and some strategies can lose more than that.</p>
  <h2>Humor &amp; parody</h2>
  <p>References to trading slang (0DTE, theta gang, diamond hands, IV crush, max pain, and so on) are used descriptively and for comedic effect. No broker, exchange, trading platform, automaker, or aerospace company is affiliated with, sponsors, or endorses these products. Any resemblance of the art to real vehicles, people, or marks is unintended.</p>
  <h2>Preview status</h2>
  <p>This is a preview build. All product images are <strong>unapproved draft placeholders</strong>, watermarked as such. Prices and run sizes are proposals. Nothing can be bought here yet, and nothing on this page is an offer to sell.</p>
  <h2>Privacy</h2>
  <p>When the drop list goes live, we'll collect only the email address you submit, use it only to tell you about drops, and let you unsubscribe at any time. This site sets no tracking cookies and loads no third-party analytics or fonts.</p>
  <h2>Credits</h2>
  <ul>
    <li>Anton, Shrikhand, Alfa Slab One: SIL Open Font License 1.1 (<a href="{url('fonts/Anton-OFL.txt')}">Anton</a>, <a href="{url('fonts/Shrikhand-OFL.txt')}">Shrikhand</a>, <a href="{url('fonts/AlfaSlabOne-OFL.txt')}">Alfa Slab One</a>). Self-hosted.</li>
    <li>Special Elite: Apache License 2.0 (<a href="{url('fonts/SpecialElite-LICENSE-Apache-2.0.txt')}">license</a>). Self-hosted.</li>
    <li>Candlestick charts, textures, and the skull mark are generated by this site's build scripts. The charts are decorative, not market data.</li>
  </ul>
</section>"""
    return page("Fine print", body, "legal/")


def not_found():
    body = f"""<section class="page center">
  <p class="kicker">Error 404</p>
  <h1 class="distress slab huge">Expired<br><span class="script red">worthless</span></h1>
  <p>This page went to zero. It happens to the best of us.</p>
  <p><a class="btn btn-red" href="{url()}">Back to the drop</a></p>
</section>"""
    return page("Page not found", body, "404")


FAVICON = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 112"><rect width="100" height="112" fill="#000"/><g transform="translate(10 10) scale(.8)">""" + \
    SKULL.replace('class="skull" viewBox="0 0 100 112" aria-hidden="true"', "").replace("<svg >", "").replace("</svg>", "").replace('fill="currentColor"', 'fill="#d10a1e"') + "</g></svg>"


def validate():
    errs = []
    slugs = set()
    for p in PRODUCTS:
        for k in ("id", "slug", "status", "title", "slogan_top", "slogan_bottom", "target_price", "edition_size", "images"):
            if k not in p:
                errs.append(f"{p.get('id','?')}: missing {k}")
        if p.get("slug") in slugs:
            errs.append(f"duplicate slug {p['slug']}")
        slugs.add(p.get("slug"))
        if COLLECTIONS and p.get("collection") not in COLL:
            errs.append(f"{p['id']}: unknown collection {p.get('collection')!r}")
        if p.get("status") == "approved" and p.get("tm_check"):
            errs.append(f"{p['id']}: approved product still has an open trademark check")
        for img in p.get("images", {}).values():
            if not (SRC / img).exists():
                errs.append(f"{p['id']}: missing image {img}")
        if p.get("status") == "approved" and p.get("draft_source"):
            errs.append(f"{p['id']}: approved product still points at a draft_source image")
    if errs:
        sys.exit("Build failed:\n  " + "\n  ".join(errs))


def write(rel, text):
    f = OUT / rel
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(text, encoding="utf-8")


def main():
    validate()
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir()
    for d in ("css", "js", "fonts", "img"):
        shutil.copytree(SRC / d, OUT / d)
    write("img/favicon.svg", FAVICON)
    shutil.copy(SRC / "img" / "favicon.ico", OUT / "favicon.ico")
    write("index.html", home())
    for i, p in enumerate(PRODUCTS):
        write(f"products/{p['slug']}/index.html", product_page(p, i))
    write("size-guide/index.html", size_guide())
    write("faq/index.html", faq())
    write("legal/index.html", legal())
    write("404.html", not_found())
    write(".nojekyll", "")
    write("robots.txt", "User-agent: *\nDisallow: /\n")  # preview: keep out of search engines
    n = sum(1 for _ in OUT.rglob("*.html"))
    print(f"Built {n} pages -> {OUT}  (BRAND={BRAND!r}, PATH_PREFIX={PREFIX!r}, form={'on' if FORM_ID else 'off'})")


if __name__ == "__main__":
    main()
