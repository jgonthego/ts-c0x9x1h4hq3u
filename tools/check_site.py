#!/usr/bin/env python3
"""Local QA: crawl every page in headless Chrome, report console errors, failed requests,
broken links and mobile overflow, check the category filter, and take screenshots.
    /tmp/pwv/bin/python tools/check_site.py http://127.0.0.1:8473/ts-c0x9x1h4hq3u [--no-shots]
"""
import sys
from urllib.parse import urljoin, urlparse
from playwright.sync_api import sync_playwright

BASE = sys.argv[1].rstrip("/") if len(sys.argv) > 1 else "http://127.0.0.1:8473/ts-c0x9x1h4hq3u"
SHOTS = "--no-shots" not in sys.argv
OUTP = "/workspace/teeshop2-{}.png"
problems = []


def watch(pg):
    pg.on("console", lambda m: m.type in ("error", "warning") and problems.append(f"console {m.type}: {m.text} @ {pg.url}"))
    pg.on("pageerror", lambda ex: problems.append(f"pageerror: {ex} @ {pg.url}"))
    pg.on("requestfailed", lambda r: problems.append(f"requestfailed: {r.url}"))
    pg.on("response", lambda r: r.status >= 400 and problems.append(f"HTTP {r.status}: {r.url}"))
    pg.on("request", lambda r: urlparse(r.url).netloc != urlparse(BASE).netloc and not r.url.startswith("data:")
          and problems.append(f"third-party request: {r.url}"))


with sync_playwright() as p:
    b = p.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--no-sandbox"])
    # desktop crawl
    ctx = b.new_context(viewport={"width": 1280, "height": 800})
    pg = ctx.new_page(); watch(pg)
    q, seen = [BASE + "/"], set()
    while q:
        u = q.pop(0)
        if u in seen: continue
        seen.add(u)
        pg.goto(u, wait_until="load")
        for href in pg.eval_on_selector_all("a[href]", "els=>els.map(e=>e.getAttribute('href'))"):
            full = urljoin(u, href).split("#")[0].split("?")[0]
            if urlparse(full).netloc == urlparse(BASE).netloc and full.startswith(BASE) and full not in seen:
                q.append(full)
    print("desktop pages crawled:", len(seen))
    # filter checks
    pg.goto(BASE + "/?cat=options-gang", wait_until="load")
    vis = pg.eval_on_selector_all("[data-grid] .card", "els=>els.filter(e=>!e.hidden).map(e=>e.dataset.cat)")
    if not vis or set(vis) != {"options-gang"}: problems.append(f"?cat=options-gang filter wrong: {set(vis)} {len(vis)}")
    print("?cat=options-gang shows", len(vis))
    pg.goto(BASE + "/", wait_until="load")
    pg.click('.ftab[data-filter="gym"]')
    if "cat=gym" not in pg.url: problems.append("chip click did not update URL")
    print("after gym chip:", pg.url, pg.eval_on_selector_all("[data-grid] .card", "els=>els.filter(e=>!e.hidden).length"))
    pg.goto(BASE + "/?cat=green-candle", wait_until="load")
    if not pg.is_visible('[data-cat-note="green-candle"]'): problems.append("18+ notice not shown on green-candle")
    feat = pg.eval_on_selector_all(".feat-row .card img", "els=>els.map(e=>e.getAttribute('src').split('/').pop())")
    print("featured:", feat)
    if SHOTS:
        pg.goto(BASE + "/", wait_until="networkidle"); pg.wait_for_timeout(500)
        pg.screenshot(path=OUTP.format("home-desktop"))
        pg.evaluate("document.querySelectorAll('img[loading=lazy]').forEach(i=>i.loading='eager')")
        pg.wait_for_load_state("networkidle"); pg.wait_for_timeout(800)
        pg.screenshot(path=OUTP.format("home-full"), full_page=True)
        pg.goto(BASE + "/?cat=options-gang", wait_until="networkidle")
        pg.evaluate("document.getElementById('shop').scrollIntoView()"); pg.wait_for_timeout(700)
        pg.screenshot(path=OUTP.format("category-options-gang"))
        pg.goto(BASE + "/products/my-account-is-a-crime-scene/", wait_until="networkidle"); pg.wait_for_timeout(400)
        pg.screenshot(path=OUTP.format("product"), full_page=False)
        pg.goto(BASE + "/products/0dte-deep-throat-champ/", wait_until="networkidle"); pg.wait_for_timeout(400)
        pg.screenshot(path=OUTP.format("product-18plus"), full_page=False)
    ctx.close()
    # mobile
    ctx = b.new_context(viewport={"width": 390, "height": 844}, device_scale_factor=2, is_mobile=True, has_touch=True)
    pg = ctx.new_page(); watch(pg)
    for path in ["/", "/?cat=options-gang", "/products/my-account-is-a-crime-scene/", "/size-guide/", "/faq/", "/legal/"]:
        pg.goto(BASE + path, wait_until="load")
        ow = pg.evaluate("document.documentElement.scrollWidth - window.innerWidth")
        if ow > 1: problems.append(f"horizontal overflow {ow}px (mobile) @ {path}")
    pg.goto(BASE + "/", wait_until="networkidle"); pg.wait_for_timeout(500)
    if SHOTS: pg.screenshot(path=OUTP.format("mobile"))
    pg.click(".nav-toggle")
    if not pg.is_visible("#site-nav a[href$='/faq/']"): problems.append("mobile nav did not open")
    if SHOTS:
        pg.goto(BASE + "/?cat=options-gang", wait_until="networkidle")
        pg.evaluate("document.getElementById('shop').scrollIntoView()"); pg.wait_for_timeout(500)
        pg.screenshot(path=OUTP.format("mobile-category"))
    ctx.close()
    b.close()
print("PROBLEMS:" if problems else "No problems found.")
for x in sorted(set(problems)): print(" -", x)
