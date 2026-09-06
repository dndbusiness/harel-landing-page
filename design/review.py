# -*- coding: utf-8 -*-
"""Screenshots an artboard in readable slices for visual review."""
import os, sys
from playwright.sync_api import sync_playwright
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from build import WIDTHS

name = sys.argv[1]
slice_h = int(sys.argv[2]) if len(sys.argv) > 2 else 1500
w = WIDTHS[name]
out = os.path.join(HERE, "shots")
os.makedirs(out, exist_ok=True)

with sync_playwright() as p:
    b = p.chromium.launch(executable_path="/opt/pw-browsers/chromium-1194/chrome-linux/chrome",
                          args=["--no-sandbox"])
    pg = b.new_page(viewport={"width": w, "height": 900}, device_scale_factor=1)
    pg.goto("file://%s/%s.dc.html" % (HERE, name))
    pg.wait_for_timeout(1500)
    full = os.path.join(out, "%s_full.png" % name)
    pg.screenshot(path=full, full_page=True)
    b.close()

im = Image.open(full)
W, H = im.size
n = 0
for top in range(0, H, slice_h):
    part = im.crop((0, top, W, min(top + slice_h, H)))
    part.thumbnail((820, 10000), Image.LANCZOS)
    part.save(os.path.join(out, "%s_%02d.png" % (name, n)))
    n += 1
print(name, im.size, "->", n, "slices")
