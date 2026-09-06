# -*- coding: utf-8 -*-
"""Renders each artboard at its frame width and records its real content height."""
import io, json, os, sys
from playwright.sync_api import sync_playwright
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from build import ARTBOARDS, WIDTHS

SLACK = 1.04          # ~4% slack; surplus paints the artboard background, clipping does not
shots = "--shots" in sys.argv

with sync_playwright() as p:
    b = p.chromium.launch(executable_path="/opt/pw-browsers/chromium-1194/chrome-linux/chrome", args=["--no-sandbox"])
    out = {}
    for name in ARTBOARDS:
        w = WIDTHS[name]
        pg = b.new_page(viewport={"width": w, "height": 900})
        pg.goto("file://%s/%s.dc.html" % (HERE, name))
        pg.wait_for_timeout(1400)          # let Google Fonts settle
        h = pg.evaluate("document.documentElement.scrollHeight")
        out[name] = int(h * SLACK) + 40
        print("%-12s content %5d  ->  frame %5d" % (name, h, out[name]))
        if shots:
            pg.screenshot(path=os.path.join(HERE, "shot_%s.png" % name), full_page=True)
        pg.close()
    b.close()
io.open(os.path.join(HERE, "heights.json"), "w", encoding="utf-8").write(
    json.dumps(out, ensure_ascii=False, indent=2))
