# -*- coding: utf-8 -*-
"""כותב את קבצי ה-HTML של האתר לשורש המאגר, יחד עם sitemap ו-robots."""
import io, os, sys, datetime
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from pages import PAGES                                            # noqa: E402
from _site import SITE_URL                                         # noqa: E402

FAVICON = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
<rect width="64" height="64" rx="13" fill="#061A22"/>
<path d="M14 20.5 46 13v8.5L14 29z" fill="#A6DCD6"/>
<path d="M14 31.5 46 24v8.5L14 40z" fill="#2BB6AA"/>
<path d="M14 42.5 46 35v8.5L14 51z" fill="#178379"/>
</svg>
"""

ROBOTS = "User-agent: *\nAllow: /\n\nSitemap: %s/sitemap.xml\n" % SITE_URL


def sitemap():
    today = datetime.date.today().isoformat()
    urls = ""
    for page in PAGES:
        if page == "404.html":
            continue
        loc = "%s/%s" % (SITE_URL, "" if page == "index.html" else page)
        pri = "1.0" if page == "index.html" else "0.8"
        urls += ("  <url><loc>%s</loc><lastmod>%s</lastmod>"
                 "<changefreq>monthly</changefreq><priority>%s</priority></url>\n"
                 % (loc, today, pri))
    return ('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n%s</urlset>\n' % urls)


def write(path, content):
    full = os.path.join(ROOT, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    io.open(full, "w", encoding="utf-8").write(content)
    return os.path.getsize(full)


if __name__ == "__main__":
    for name, fn in PAGES.items():
        print("%-16s %5.1f KB" % (name, write(name, fn()) / 1024.0))
    write("assets/favicon.svg", FAVICON)
    write("robots.txt", ROBOTS)
    write("sitemap.xml", sitemap())
    print("assets/favicon.svg, robots.txt, sitemap.xml written")
