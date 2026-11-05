#!/usr/bin/env python3
# /// script
# dependencies = ["playwright"]
# ///
"""Find the logos and screenshots an explainer reel needs, logos in their original colours.

Usage: uv run fetch_assets.py <assets.json> <out_dir> [--brand-dir DIR]

assets.json lists what the reel shows, by the name the composition uses:
  [{"name": "claude", "domain": "claude.ai", "logo": "claude"},
   {"name": "chrome", "url": "https://upload.wikimedia.org/.../Google_Chrome_icon.svg"},
   {"name": "ffmpeg-site", "screenshot": "https://ffmpeg.org"}]

A logo comes from the first source that has it, never recoloured:
  1. the brand kit (--brand-dir): <name>.svg / .png / .webp, the team's own files
  2. "url": a logo file picked by hand, when the automatic pick was wrong
  3. the site's own SVG icon, from "domain": vector, full colour
  4. the site's largest raster icon, when at least SHARP_RASTER_PX wide: the brand's current mark
  5. Simple Icons, by slug ("logo"): vector in the colour Simple Icons lists, one colour and
     sometimes an old brand colour, so only when the site has no sharp icon
  6. the site's raster icon down to MIN_RASTER_PX: blurry when shown large
  7. nothing: the composition draws a monogram instead
A screenshot is the page at SCREEN_W x SCREEN_H in a fresh browser (no cookies, no login),
with cookie and consent banners hidden.

Writes the files into <out_dir> and <out_dir>/manifest.json:
  {"claude": {"file": "claude.svg", "source": "site-svg"}, ...}
source is "brand", "url", "site-svg", "simpleicons", "site-raster", "screenshot" or "missing".
Always look at the logos before using them: a site icon can be a seasonal or wrong mark.
"""
import argparse
import json
import shutil
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
from pathlib import Path

SIMPLE_ICONS = "https://cdn.simpleicons.org/{slug}"  # SVG filled with the brand's official colour
# A logo tile shows the mark about 40 px wide: 64 px still holds there, 128 px holds anywhere.
MIN_RASTER_PX = 64
SHARP_RASTER_PX = 128
BRAND_EXTS = (".svg", ".png", ".webp")
SCREEN_W, SCREEN_H, SCREEN_SCALE = 1440, 900, 2
PAGE_TIMEOUT_MS = 20000
ICON_LINKS = 'link[rel~="icon"], link[rel="apple-touch-icon"], link[rel="apple-touch-icon-precomposed"]'
HIDE_BANNERS = """
[id*="cookie" i], [class*="cookie" i], [id*="consent" i], [class*="consent" i],
[id*="onetrust" i], [class*="gdpr" i], [aria-label*="cookie" i] { display: none !important; }
"""


def download(url):
    """Bytes at url, or None when the source does not have it."""
    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (explainer-reel asset fetch)"})
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            return response.read()
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError):
        return None


def raster_width(data, ext):
    """Widest image in the file; the real extension matters, ffprobe misreads an .ico by content alone."""
    with tempfile.NamedTemporaryFile(suffix=ext) as tmp:
        tmp.write(data)
        tmp.flush()
        out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "stream=width", "-of", "csv=p=0", tmp.name],
                             capture_output=True, text=True).stdout.strip().splitlines()
    return max((int(w) for w in out if w.isdigit()), default=0)


def is_svg(data):
    return data is not None and b"<svg" in data[:2000]


def find_logo(item, out_dir, brand_dir, fetch=download, site_icons=lambda domain: {}):
    """site_icons(domain) -> {"svg": bytes or None, "raster": (bytes, ext, width) or None}."""
    name = item["name"]

    def keep(data, ext, source):
        (out_dir / f"{name}{ext}").write_bytes(data)
        return {"file": f"{name}{ext}", "source": source}

    if brand_dir:
        for ext in BRAND_EXTS:
            own = brand_dir / f"{name}{ext}"
            if own.exists():
                shutil.copy(own, out_dir / own.name)
                return {"file": own.name, "source": "brand"}
    if item.get("url"):
        data = fetch(item["url"])
        if data:
            return keep(data, ".svg" if is_svg(data) else Path(item["url"]).suffix or ".png", "url")
    icons = site_icons(item["domain"]) if item.get("domain") else {}
    if icons.get("svg"):
        return keep(icons["svg"], ".svg", "site-svg")
    raster = icons.get("raster")
    if raster and raster[2] >= SHARP_RASTER_PX:
        return keep(raster[0], raster[1], "site-raster")
    if item.get("logo"):
        svg = fetch(SIMPLE_ICONS.format(slug=item["logo"]))
        if is_svg(svg):
            return keep(svg, ".svg", "simpleicons")
    if raster:
        return keep(raster[0], raster[1], "site-raster")
    return {"file": None, "source": "missing"}


def browser_site_icons(context):
    """Icons a site declares in its <head>, read in a real browser (many sites block plain HTTP clients)."""

    def get(url):
        try:
            response = context.request.get(url, timeout=PAGE_TIMEOUT_MS)
            return response.body() if response.ok else None
        except Exception:
            return None

    def icons(domain):
        page = context.new_page()
        try:
            page.goto(f"https://{domain}", wait_until="domcontentloaded", timeout=PAGE_TIMEOUT_MS)
            hrefs = page.eval_on_selector_all(ICON_LINKS, "els => els.map(e => e.href)")
        except Exception:
            hrefs = []
        finally:
            page.close()
        hrefs = [h for h in dict.fromkeys(hrefs + [f"https://{domain}/apple-touch-icon.png"]) if h.startswith("http")]
        found = {"svg": None, "raster": None}
        best_width = MIN_RASTER_PX - 1
        for href in hrefs:
            data = get(href)
            if not data:
                continue
            if is_svg(data):
                found["svg"] = found["svg"] or data
                continue
            ext = Path(href.split("?")[0]).suffix.lower() or ".png"
            width = raster_width(data, ext)
            if width > best_width:
                best_width, found["raster"] = width, (data, ext, width)
        return found

    return icons


def take_screenshot(context, item, out_dir):
    page = context.new_page()
    try:
        page.goto(item["screenshot"], wait_until="networkidle", timeout=PAGE_TIMEOUT_MS)
    except Exception as error:  # a slow page still shows something worth keeping
        print(f"  {item['name']}: {type(error).__name__}, taking what loaded", file=sys.stderr)
    page.add_style_tag(content=HIDE_BANNERS)
    file = f"{item['name']}.png"
    page.screenshot(path=str(out_dir / file))
    page.close()
    return {"file": file, "source": "screenshot"}


def main():
    from playwright.sync_api import sync_playwright

    ap = argparse.ArgumentParser()
    ap.add_argument("assets")
    ap.add_argument("out_dir")
    ap.add_argument("--brand-dir")
    args = ap.parse_args()

    items = json.loads(Path(args.assets).read_text())
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    brand_dir = Path(args.brand_dir).expanduser() if args.brand_dir else None

    manifest = {}
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome")
        context = browser.new_context(viewport={"width": SCREEN_W, "height": SCREEN_H},
                                      device_scale_factor=SCREEN_SCALE)
        site_icons = browser_site_icons(context)
        for item in items:
            if "screenshot" in item:
                manifest[item["name"]] = take_screenshot(context, item, out_dir)
            else:
                manifest[item["name"]] = find_logo(item, out_dir, brand_dir, site_icons=site_icons)
        browser.close()
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=1))
    for name, found in manifest.items():
        print(f"{found['source']:<12} {name}" + (f" → {found['file']}" if found["file"] else ""))


if __name__ == "__main__":
    main()
