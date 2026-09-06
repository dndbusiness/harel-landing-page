# -*- coding: utf-8 -*-
"""Writes the .dc.html artboards for the Har-El financing design canvas."""
import io, json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import pages_home, pages_products, pages_misc

ARTBOARDS = {
    "Main":       pages_home.build,
    "Mortgage":   pages_products.mortgage,
    "CarLoan":    pages_products.carloan,
    "Business":   pages_products.business,
    "Personal":   pages_products.personal,
    "About":      pages_misc.about,
    "Contact":    pages_misc.contact,
    "MobileHome": pages_misc.mobile_home,
}

# frame width per artboard; heights are measured by measure.py into heights.json
WIDTHS = {n: 1440 for n in ARTBOARDS}
WIDTHS["MobileHome"] = 390

TITLES = {
    "Main": "דף הבית", "Mortgage": "משכנתאות", "CarLoan": "הלוואות רכב",
    "Business": "מימון לעסקים", "Personal": "הלוואות לכל מטרה",
    "About": "אודות והצוות", "Contact": "צור קשר", "MobileHome": "דף הבית · מובייל",
}

# canvas rows: (page id, [artboard names])
ROWS = [["Main", "MobileHome"],
        ["Mortgage", "CarLoan", "Business", "Personal"],
        ["About", "Contact"]]

GAP_X, GAP_Y = 110, 150


def write_artboards():
    for name, fn in ARTBOARDS.items():
        path = os.path.join(HERE, "%s.dc.html" % name)
        io.open(path, "w", encoding="utf-8").write(fn())
        print("%-12s %6.1f KB" % (name + ".dc.html", os.path.getsize(path) / 1024.0))


def write_canvas(heights):
    boards, y = [], 0
    for row in ROWS:
        x = 0
        for name in row:
            w = WIDTHS[name]
            boards.append({"file": "%s.dc.html" % name, "x": x, "y": y,
                           "w": w, "h": heights[name], "title": TITLES[name]})
            x += w + GAP_X
        y += max(heights[n] for n in row) + GAP_Y
    doc = {"artboards": boards,
           "annotations": [
               {"id": "brief", "x": 0, "y": -220, "w": 620,
                "text": "הר-אל פתרונות מימון חכמים — אתר מלא, עברית RTL.\n"
                        "הפלטה, הטיפוגרפיה והרכיבים לקוחים מדף הנחיתה הקיים (index.html).\n"
                        "טקסט מודגש בזהב עם קו מקווקו = נתון שצריך למלא (טלפון, רישיון, סכומים, ריביות)."},
               {"id": "row-products", "x": 0, "y": heights["Main"] + 26, "w": 1440,
                "text": "ארבעת עמודי המוצר חולקים מבנה: הירו + פאנל בדיקה, סקשן פתרונות, תהליך, "
                        "שאלות נפוצות ופס CTA. במשכנתאות, רכב ולכל מטרה נוספת גם טבלה או הדגמה."},
           ],
           "launch": {"view": "canvas"}}
    path = os.path.join(HERE, "canvas.json")
    io.open(path, "w", encoding="utf-8").write(json.dumps(doc, ensure_ascii=False, indent=2))
    print("canvas.json written")


if __name__ == "__main__":
    write_artboards()
    hpath = os.path.join(HERE, "heights.json")
    if os.path.exists(hpath):
        write_canvas(json.load(io.open(hpath, encoding="utf-8")))
    else:
        print("heights.json missing - run measure.py first, then build.py again")
