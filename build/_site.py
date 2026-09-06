# -*- coding: utf-8 -*-
"""מעטפת משותפת לכל עמודי האתר: head, header, footer ורכיבים חוזרים."""
import os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "design"))
from _common import icon, wa_icon                                   # noqa: E402

# כתובת האתר — לשנות כאן בלבד כשמחברים דומיין משלכם
SITE_URL = "https://dndbusiness.github.io/harel-landing-page"
BRAND = "הר-אל פתרונות מימון חכמים"
ADDRESS = "משה דיין 10, פתח תקווה"

NAV = [("index.html", "בית"),
       ("mashkanta.html", "משכנתאות"),
       ("rechev.html", "הלוואות רכב"),
       ("asakim.html", "מימון לעסקים"),
       ("kol-matara.html", "לכל מטרה"),
       ("about.html", "אודות"),
       ("contact.html", "צור קשר")]


def logo(cls=""):
    return ('<span class="logo-plate %s">'
            '<span><img class="lm-word" src="assets/wordmark.png" alt="הר-אל" width="326" height="99">'
            '<span class="lm-tag">פתרונות מימון <em>חכמים</em></span></span>'
            '<img class="lm-chev" src="assets/chevrons.png" alt="" width="133" height="142">'
            '</span>' % cls)


def head(title, desc, page):
    url = "%s/%s" % (SITE_URL, "" if page == "index.html" else page)
    ld = ('{"@context":"https://schema.org","@type":"FinancialService",'
          '"name":"%s","url":"%s","areaServed":"IL","currenciesAccepted":"ILS",'
          '"address":{"@type":"PostalAddress","streetAddress":"משה דיין 10",'
          '"addressLocality":"פתח תקווה","addressCountry":"IL"},'
          '"description":"תיווך ובניית תיקי מימון מול בנקים, גופים חוץ-בנקאיים וקרנות: '
          'משכנתאות, הלוואות רכב, מימון לעסקים והלוואות לכל מטרה."}' % (BRAND, SITE_URL))
    return """<!doctype html>
<html lang="he" dir="rtl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>%(title)s</title>
<meta name="description" content="%(desc)s">
<link rel="canonical" href="%(url)s">
<meta property="og:type" content="website">
<meta property="og:site_name" content="%(brand)s">
<meta property="og:locale" content="he_IL">
<meta property="og:title" content="%(title)s">
<meta property="og:description" content="%(desc)s">
<meta property="og:url" content="%(url)s">
<meta name="twitter:card" content="summary_large_image">
<meta name="theme-color" content="#061A22">
<link rel="icon" href="assets/favicon.svg" type="image/svg+xml">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Heebo:wght@300;400;500;600;700;800;900&amp;family=Suez+One&amp;display=swap">
<link rel="stylesheet" href="assets/style.css">
<script type="application/ld+json">%(ld)s</script>
</head>
<body>
<a class="skip" href="#main">דילוג לתוכן המרכזי</a>
""" % {"title": title, "desc": desc, "url": url, "brand": BRAND, "ld": ld}


def header(active):
    links = "".join('<a href="%s"%s>%s</a>' % (h, ' class="on" aria-current="page"' if h == active else "", t)
                    for h, t in NAV)
    return ('<header class="topbar"><div class="wrap"><div class="row">'
            '<a href="index.html" aria-label="%s — לדף הבית">%s</a>'
            '<nav class="nav" aria-label="ניווט ראשי">%s</nav>'
            '<div class="tb-right">'
            '<a class="tb-phone" href="tel:">%s<span class="ph">[טלפון]</span></a>'
            '<a class="btn btn-sm btn-primary tb-cta" href="contact.html">בדיקת זכאות</a>'
            '<button class="burger" type="button" aria-expanded="false" aria-controls="drawer" '
            'aria-label="פתיחת תפריט"><span></span><span></span><span></span></button>'
            '</div></div></div>'
            '<div class="drawer" id="drawer"><nav aria-label="ניווט נייד">%s</nav>'
            '<div class="d-actions">'
            '<a class="btn btn-primary" href="contact.html">בדיקת זכאות ללא עלות</a>'
            '<a class="btn btn-wa" href="#">%s לשיחה בוואטסאפ</a></div></div>'
            '</header>\n<main id="main">\n' % (BRAND, logo(), links, icon("phone"), links, wa_icon()))


DISCLAIMER = ('%s (<span class="ph">[שם החברה הרשומה]</span> בע״מ) · '
              'ח.פ. <span class="ph">[מספר]</span> · בעלת רישיון למתן שירותי אשראי מטעם רשות שוק ההון, '
              'הביטוח והחיסכון, רישיון מס׳ <span class="ph">[מספר רישיון]</span>. '
              'אי עמידה בפירעון ההלוואה או בהחזר האשראי עלול לגרור חיוב בריבית פיגורים והליכי הוצאה לפועל. '
              'האמור באתר הוא מידע כללי בלבד ואינו מהווה ייעוץ, הצעה או התחייבות למתן אשראי; '
              'אישור ההלוואה, סכומה, הריבית ותנאיה נתונים לשיקול דעתו הבלעדי של הגוף המממן '
              'וכפופים להסכם חתום.' % BRAND)


def footer():
    def col(title, items):
        return ('<div class="foot-col"><h2>%s</h2><ul>%s</ul></div>'
                % (title, "".join('<li><a href="%s">%s</a></li>' % (h, t) for h, t in items)))
    return ("""</main>
<footer><div class="wrap">
<div class="foot-top">
<div class="foot-col">%s
<p class="foot-blurb">מלווים משפחות ועסקים בישראל מול הבנקים והגופים החוץ-בנקאיים —
עד שנמצה עבורכם את האפשרויות.</p></div>
%s%s%s
</div>
<p class="disclaimer">%s</p>
<p class="meta-dis">© <span class="year">2026</span> כל הזכויות שמורות ל%s.</p>
</div></footer>
<a class="wa-float" href="#" aria-label="שליחת הודעה בוואטסאפ">%s</a>
<script src="assets/site.js" defer></script>
</body>
</html>
""" % (logo(),
       col("פתרונות מימון", [("mashkanta.html", "משכנתאות"), ("rechev.html", "הלוואות רכב"),
                             ("asakim.html", "מימון לעסקים"), ("kol-matara.html", "הלוואות לכל מטרה")]),
       col("החברה", [("about.html", "אודות הר-אל"), ("about.html#team", "הצוות"),
                     ("index.html#process", "תהליך העבודה"), ("contact.html", "יצירת קשר")]),
       '<div class="foot-col"><h2>יצירת קשר</h2><ul>'
       '<li><a href="tel:"><span class="ph">[טלפון]</span></a></li>'
       '<li><a href="mailto:"><span class="ph">[אימייל]</span></a></li>'
       '<li><a class="btn-wa-link" href="#">וואטסאפ</a></li>'
       '<li><span style="font-size:.91rem;color:var(--sand-dim)">%s</span></li></ul></div>' % ADDRESS,
       DISCLAIMER, BRAND, wa_icon()))


# ------------------------------------------------------------------ רכיבים
def tick():
    return ('<span class="tick"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" '
            'stroke-width="3.2" stroke-linecap="round" stroke-linejoin="round">'
            '<path d="M5 12.6 9.4 17 19 7.2"/></svg></span>')


def hero(kicker_icon, kicker, h1, sub, points, panel_icon, panel_title, panel_lead, panel_items,
         cta_text="לבדיקת זכאות ללא עלות", cta_href="contact.html", panel_body=None):
    pts = "".join("<li>%s%s</li>" % (tick(), p) for p in points)
    items = (panel_body if panel_body is not None else
             '<ul class="panel-list">%s</ul>'
             % "".join("<li>%s<span>%s</span></li>" % (tick(), i) for i in panel_items))
    lead = '<p class="panel-lead">%s</p>' % panel_lead if panel_lead else ""
    return ('<section class="hero"><div class="wrap"><div class="hero-grid">'
            '<div class="hero-copy">'
            '<span class="kicker">%s %s</span>'
            '<h1>%s</h1><p class="sub">%s</p>'
            '<div class="cta-row"><a class="btn btn-primary" href="%s">%s</a>'
            '<a class="btn btn-wa" href="#">%s לשיחה בוואטסאפ</a></div>'
            '<ul class="hero-points">%s</ul></div>'
            '<div class="hero-panel"><div class="panel-head">'
            '<span class="ic-box ic-gold">%s</span><h2>%s</h2></div>%s%s</div>'
            '</div></div></section>'
            % (icon(kicker_icon), kicker, h1, sub, cta_href, cta_text, wa_icon(),
               pts, icon(panel_icon), panel_title, lead, items))


def sec(inner, band=False, sid=""):
    return ('<section class="block%s"%s><div class="wrap">%s</div></section>'
            % (" band" if band else "", ' id="%s"' % sid if sid else "", inner))


def head2(eyebrow, title, intro=None):
    return ('<p class="sec-eyebrow">%s</p><h2>%s</h2>%s'
            % (eyebrow, title, '<p class="intro-p">%s</p>' % intro if intro else ""))


def cards(items, cols="g2", link=None):
    out = []
    for ic, t, d, href in items:
        lk = ('<a class="card-link" href="%s">%s %s</a>' % (href, link, icon("arrow"))) if link and href else ""
        out.append('<article class="card reveal"><span class="ic-box">%s</span><h3>%s</h3><p>%s</p>%s</article>'
                   % (icon(ic), t, d, lk))
    return '<div class="grid %s">%s</div>' % (cols, "".join(out))


def feats(rows):
    return ('<div class="feats">%s</div>' % "".join(
        '<div class="feat reveal"><span class="ic">%s</span><div><b>%s</b><p>%s</p></div></div>'
        % (icon(ic), t, d) for ic, t, d in rows))


def steps(items):
    return ('<div class="steps">%s</div>' % "".join(
        '<div class="step reveal"><span class="n">%d</span><div><h3>%s</h3><p>%s</p></div></div>'
        % (i + 1, t, d) for i, (t, d) in enumerate(items)))


def table(headers, rows):
    th = "".join("<th scope=\"col\">%s</th>" % h for h in headers)
    tr = "".join("<tr>%s</tr>" % "".join(
        ('<th scope="row" class="k">%s</th>' % c) if i == 0 else ("<td>%s</td>" % c)
        for i, c in enumerate(r)) for r in rows)
    return ('<div class="table-scroll"><table class="tbl"><thead><tr>%s</tr></thead>'
            '<tbody>%s</tbody></table></div>'
            '<p class="scroll-hint">אפשר לגלול את הטבלה הצידה →</p>' % (th, tr))


def faq(qas):
    return ('<div class="faq">%s</div>' % "".join(
        '<details class="qa reveal"><summary><span class="q-ic">%s</span>%s'
        '<span class="chev">%s</span></summary><div class="a">%s</div></details>'
        % (icon("q"), q, icon("chev"), a) for q, a in qas))


def strip(items, note=""):
    return ('<section class="band"><div class="wrap"><div class="trust-grid">%s</div>%s</div></section>'
            % ("".join('<div class="tr"><b>%s</b><span>%s</span></div>' % (b, s) for b, s in items),
               '<p class="strip-note">%s</p>' % note if note else ""))


def cta_band(title, sub, note, cta="לבדיקת זכאות ללא עלות"):
    return ('<section class="cta-band"><div class="wrap">'
            '<h2>%s</h2><p class="intro-p">%s</p>'
            '<div class="cta-row"><a class="btn btn-primary" href="contact.html">%s</a>'
            '<a class="btn btn-wa" href="#">%s לשיחה בוואטסאפ</a></div>'
            '<p class="note">%s</p></div></section>' % (title, sub, cta, wa_icon(), note))


_FORM_N = [0]


def lead_form(source, fields, submit="לבדיקת זכאות", note=None, title=None, lead=None, wide=False):
    """fields: (name, label, type, placeholder, required, options).
    כל טופס מקבל סיומת מזהה קצרה כדי ששדות לא יתנגשו בין טפסים באותו עמוד."""
    _FORM_N[0] += 1
    fid = "f%d" % _FORM_N[0]
    out = []
    for nm, lab, typ, ph, req, opts in fields:
        r = ' <span class="req">*</span>' if req else ' <span class="opt">(לא חובה)</span>'
        if typ == "select":
            o = '<option value="" disabled selected>%s</option>' % ph
            o += "".join('<option>%s</option>' % x for x in opts)
            ctl = '<select id="%s" name="%s"%s>%s</select>' % (nm, nm, " required" if req else "", o)
            msg = "נא לבחור מסלול"
        elif typ == "textarea":
            ctl = '<textarea id="%s" name="%s" placeholder="%s"></textarea>' % (nm, nm, ph)
            msg = ""
        else:
            ac = {"fullname": "name", "phone": "tel", "email": "email"}.get(nm, "off")
            im = ' inputmode="numeric"' if typ == "tel" else ""
            ctl = ('<input type="%s" id="%s" name="%s" placeholder="%s" autocomplete="%s"%s%s>'
                   % (typ, nm, nm, ph, ac, im, " required" if req else ""))
            msg = {"fullname": "נא להזין שם מלא", "phone": "נא להזין מספר טלפון תקין",
                   "email": "נא להזין כתובת אימייל תקינה"}.get(nm, "נא למלא שדה זה")
        ctl = ctl.replace('id="%s"' % nm, 'id="%s-%s"' % (nm, fid), 1)
        out.append('<div class="field"><label for="%s-%s">%s%s</label>%s'
                   '<span class="err-msg">%s</span></div>' % (nm, fid, lab, r, ctl, msg))
    return ('<div class="form-card%s">%s'
            '<form class="lead-form form-live" data-source="%s" novalidate>%s'
            '<div class="hp"><label for="company-%s">אל תמלאו</label>'
            '<input type="text" id="company-%s" name="company" tabindex="-1" autocomplete="off"></div>'
            '<div class="field consent"><input type="checkbox" id="consent-%s" name="consent" required>'
            '<label for="consent-%s">מאשר/ת קבלת פנייה חוזרת בטלפון, בוואטסאפ ובאימייל בנוגע לפנייה זו. '
            'הפרטים לא יועברו לגורם שלישי ללא אישורי.</label>'
            '<span class="err-msg">נדרש אישור כדי שנוכל לחזור אליכם</span></div>'
            '<button type="submit" class="btn btn-primary">%s</button>'
            '<p class="form-note">%s</p></form>'
            '<div class="thanks"><div class="check"><svg viewBox="0 0 24 24" fill="none" '
            'stroke="currentColor" stroke-linecap="round" stroke-linejoin="round">'
            '<path d="M5 12.6 9.4 17 19 7.2"/></svg></div>'
            '<h3>קיבלנו את הפרטים</h3>'
            '<p>נחזור אליכם בשעות הפעילות. אם זה דחוף — אפשר לכתוב לנו בוואטסאפ כבר עכשיו.</p>'
            '<a class="btn btn-wa" href="#">%s לשיחה בוואטסאפ</a></div>'
            '</div>'
            % (" wide" if wide else "",
               (('<h2 class="start" style="font-size:1.4rem;margin-bottom:6px">%s</h2>' % title) if title else "")
               + (('<p class="panel-lead">%s</p>' % lead) if lead else ""),
               source, "".join(out), fid, fid, fid, fid, submit,
               note or "הפנייה אינה כרוכה בתשלום ואינה מחייבת אתכם בדבר.", wa_icon()))
