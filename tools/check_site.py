#!/usr/bin/env python3
"""Local QA: crawl pages in headless Chrome, report console errors, failed requests,
broken links, horizontal overflow on mobile, and take screenshots.
    /tmp/pwv/bin/python tools/check_site.py http://localhost:8765
"""
import sys
from urllib.parse import urljoin, urlparse
from playwright.sync_api import sync_playwright

BASE = sys.argv[1].rstrip("/") if len(sys.argv) > 1 else "http://localhost:8765"
SHOTS = len(sys.argv) <= 2 or sys.argv[2] != "--no-shots"
problems = []
with sync_playwright() as p:
    b = p.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--no-sandbox"])
    seen, queue = set(), [BASE + "/"]
    for vp_name, vp in (("desktop", {"width": 1440, "height": 900}), ("mobile", {"width": 390, "height": 844})):
        ctx = b.new_context(viewport=vp, device_scale_factor=1 if vp_name == "desktop" else 2,
                            is_mobile=vp_name == "mobile", has_touch=vp_name == "mobile")
        pg = ctx.new_page()
        pg.on("console", lambda m: m.type in ("error", "warning") and problems.append(f"console {m.type}: {m.text} @ {pg.url}"))
        pg.on("pageerror", lambda ex: problems.append(f"pageerror: {ex} @ {pg.url}"))
        pg.on("requestfailed", lambda r: problems.append(f"requestfailed: {r.url}"))
        pg.on("response", lambda r: r.status >= 400 and problems.append(f"HTTP {r.status}: {r.url}"))
        q = [BASE + "/"] if vp_name == "mobile" else queue
        visited = set()
        while q:
            u = q.pop(0)
            if u in visited: continue
            visited.add(u)
            pg.goto(u, wait_until="networkidle")
            pg.evaluate("document.fonts.ready")
            if vp_name == "desktop":
                for href in pg.eval_on_selector_all("a[href]", "els=>els.map(e=>e.getAttribute('href'))"):
                    full = urljoin(u, href).split("#")[0]
                    if urlparse(full).netloc == urlparse(BASE).netloc and full not in visited:
                        q.append(full)
            ow = pg.evaluate("document.documentElement.scrollWidth - window.innerWidth")
            if ow > 1: problems.append(f"horizontal overflow {ow}px ({vp_name}) @ {u}")
            fonts = pg.evaluate("[...document.fonts].filter(f=>f.status==='loaded').map(f=>f.family)")
        print(vp_name, "pages:", len(visited), "| fonts loaded on last page:", sorted(set(fonts)))
        if SHOTS and vp_name == "desktop":
            pg.goto(BASE + "/", wait_until="networkidle"); pg.wait_for_timeout(600)
            pg.screenshot(path="/workspace/teeshop-home.png", full_page=True)
            pg.goto(BASE + "/products/diamond-hands-no-pulse/", wait_until="networkidle"); pg.wait_for_timeout(400)
            pg.screenshot(path="/workspace/teeshop-product.png", full_page=True)
        if SHOTS and vp_name == "mobile":
            pg.goto(BASE + "/", wait_until="networkidle"); pg.wait_for_timeout(600)
            pg.screenshot(path="/workspace/teeshop-mobile.png", full_page=True)
            # nav toggle works?
            pg.click(".nav-toggle")
            if not pg.is_visible("#site-nav a[href$='/faq/']"): problems.append("mobile nav did not open")
            for path in ("/products/kept-the-car/", "/size-guide/", "/faq/", "/legal/"):
                pg.goto(BASE + path, wait_until="networkidle")
                ow = pg.evaluate("document.documentElement.scrollWidth - window.innerWidth")
                if ow > 1: problems.append(f"horizontal overflow {ow}px (mobile) @ {path}")
        ctx.close()
    b.close()
print("PROBLEMS:" if problems else "No problems found.")
for x in sorted(set(problems)): print(" -", x)
