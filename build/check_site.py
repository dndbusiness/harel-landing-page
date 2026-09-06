# -*- coding: utf-8 -*-
"""בדיקות אוטומטיות לאתר: קישורים שבורים, גלישה אופקית, אייקונים ותפריט."""
import os, re, io, sys
from playwright.sync_api import sync_playwright
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAGES = ["index.html", "mashkanta.html", "rechev.html", "asakim.html",
         "kol-matara.html", "about.html", "contact.html", "404.html"]

# ---- קישורים ומשאבים
bad = []
for p in PAGES:
    html = io.open(os.path.join(ROOT, p), encoding="utf-8").read()
    for attr in ("href", "src"):
        for m in re.finditer(r'%s="([^"]+)"' % attr, html):
            t = m.group(1)
            if t.startswith(("http", "#", "mailto:", "tel:", "data:")) or not t:
                continue
            f = t.split("#")[0]
            if f and not os.path.exists(os.path.join(ROOT, f)):
                bad.append("%s -> %s" % (p, t))
    for anchor in re.findall(r'href="([a-z0-9\-]+\.html)#([a-z\-]+)"', html):
        tgt = io.open(os.path.join(ROOT, anchor[0]), encoding="utf-8").read()
        if 'id="%s"' % anchor[1] not in tgt:
            bad.append("%s -> %s#%s (עוגן חסר)" % (p, anchor[0], anchor[1]))
print("קישורים שבורים:", sorted(set(bad)) or "אין")

# ---- רינדור
WIDTHS = [("mobile", 390), ("tablet", 768), ("desktop", 1440)]
shots = os.path.join(ROOT, "build", "shots")
os.makedirs(shots, exist_ok=True)
with sync_playwright() as pw:
    b = pw.chromium.launch(executable_path="/opt/pw-browsers/chromium-1194/chrome-linux/chrome",
                           args=["--no-sandbox"])
    for p in PAGES:
        for label, w in WIDTHS:
            pg = b.new_page(viewport={"width": w, "height": 900})
            errs = []
            pg.on("pageerror", lambda e: errs.append(str(e)))
            pg.on("console", lambda m: errs.append(m.text) if m.type == "error" else None)
            pg.goto("file://%s/%s" % (ROOT, p))
            pg.evaluate("window.scrollTo(0,document.body.scrollHeight)")
            pg.wait_for_timeout(700)
            pg.evaluate("window.scrollTo(0,0)")
            pg.wait_for_timeout(900)
            info = pg.evaluate("""() => ({
              overflow: document.documentElement.scrollWidth > window.innerWidth + 1
                        ? document.documentElement.scrollWidth : 0,
              svgBad: [...document.querySelectorAll('svg')].filter(s=>{
                if (!s.getClientRects().length) return false;   // מוסתר — לא רלוונטי
                const r=s.getBoundingClientRect(); return r.width>70||r.height>70||r.width<6;}).length,
              imgBad: [...document.querySelectorAll('img')].filter(i=>i.getClientRects().length
                && (!i.complete||i.naturalWidth===0)).length,
              h1: document.querySelectorAll('h1').length,
              titleLen: document.title.length
            })""")
            flags = []
            if info["overflow"]: flags.append("גלישה %d" % info["overflow"])
            if info["svgBad"]: flags.append("svg %d" % info["svgBad"])
            if info["imgBad"]: flags.append("תמונות %d" % info["imgBad"])
            if info["h1"] != 1: flags.append("h1=%d" % info["h1"])
            errs = [e for e in errs if "fonts.googleapis" not in e and "ERR_CONNECTION_RESET" not in e]
            if errs: flags.append("שגיאות JS: %s" % errs[:2])
            if flags: print("  %-16s %-8s %s" % (p, label, " | ".join(flags)))
            if label != "tablet":
                pg.screenshot(path=os.path.join(shots, "%s_%s.png" % (p.replace(".html",""), label)),
                              full_page=True)
            pg.close()
    # ---- תפריט מובייל וטופס
    pg = b.new_page(viewport={"width": 390, "height": 844})
    pg.goto("file://%s/index.html" % ROOT); pg.wait_for_timeout(900)
    pg.click(".burger"); pg.wait_for_timeout(350)
    open_ok = pg.evaluate("document.getElementById('drawer').classList.contains('open')")
    pg.keyboard.press("Escape"); pg.wait_for_timeout(350)
    closed_ok = not pg.evaluate("document.getElementById('drawer').classList.contains('open')")
    print("תפריט מובייל: נפתח=%s נסגר=%s" % (open_ok, closed_ok))
    wa = pg.evaluate("document.querySelector('a.btn-wa').href")
    print("קישור וואטסאפ:", "תקין" if "chat.whatsapp.com" in wa else "שגוי (%s)" % wa)
    # ולידציה: שליחה ריקה חייבת לסמן שגיאות ולא להגיע ל-thanks
    pg.goto("file://%s/contact.html" % ROOT); pg.wait_for_timeout(900)
    pg.evaluate("document.querySelector('form.lead-form button[type=submit]').click()")
    pg.wait_for_timeout(300)
    print("ולידציית טופס ריק: שדות שסומנו=%d, מסך תודה=%s"
          % (pg.evaluate("document.querySelectorAll('.field.err').length"),
             pg.evaluate("!!document.querySelector('.form-card.done')")))
    b.close()
print("done")
