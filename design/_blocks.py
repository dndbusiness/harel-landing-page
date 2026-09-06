# -*- coding: utf-8 -*-
"""Reusable section blocks shared by the inner pages."""
from _common import icon, wa_icon

HERO_BG = ("radial-gradient(56% 84% at 82% -10%,rgba(43,182,170,.19),transparent 62%),"
           "radial-gradient(48% 70% at 6% 10%,rgba(201,154,59,.12),transparent 64%),"
           "linear-gradient(180deg,#0A2733 0%,#061A22 88%)")


def page_hero(eyebrow, h1, sub, panel_title, panel_icon, panel_items, cta="לבדיקת זכאות ללא עלות"):
    """Compact inner-page hero: copy on the start side, a checklist panel on the end side."""
    items = "".join(
        '<div style="display:flex;gap:11px;align-items:flex-start;padding:10px 0;'
        'border-bottom:1px dashed rgba(244,241,234,.12)">'
        '<span style="flex:0 0 auto;width:20px;height:20px;border-radius:6px;'
        'background:rgba(43,182,170,.18);display:grid;place-items:center;color:#4FD6C8;margin-top:3px">'
        '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3.2" '
        'stroke-linecap="round" stroke-linejoin="round" style="width:11px;height:11px">'
        '<path d="M5 12.6 9.4 17 19 7.2"/></svg></span>'
        '<span style="font-size:.98rem;color:rgba(244,241,234,.82)">%s</span></div>' % t
        for t in panel_items)
    return ('<section style="position:relative;overflow:hidden;background:%s">'
            '<div class="wrap" style="padding-block:64px 70px">'
            '<div style="display:grid;grid-template-columns:1.12fr .88fr;gap:52px;align-items:center">'
            '<div style="display:flex;flex-direction:column;align-items:flex-start">'
            '<span class="kicker" style="margin-bottom:20px">%s</span>'
            '<h1 style="font-size:2.9rem;margin-bottom:16px">%s</h1>'
            '<p style="font-size:1.1rem;color:rgba(244,241,234,.78);max-width:540px;margin-bottom:26px">%s</p>'
            '<div class="cta-row">'
            '<a href="#" class="btn btn-primary">%s</a>'
            '<a href="#" class="btn btn-wa">%s וואטסאפ</a></div>'
            '</div>'
            '<div style="background:linear-gradient(165deg,#103A4A,#0A2733);'
            'border:1px solid rgba(201,154,59,.24);border-radius:20px;padding:26px 24px;'
            'box-shadow:0 34px 80px -34px rgba(0,0,0,.8)">'
            '<div style="display:flex;align-items:center;gap:11px;margin-bottom:14px">'
            '<span class="ic-box ic-gold" style="width:38px;height:38px;border-radius:11px">%s</span>'
            '<h3 style="font-size:1.18rem">%s</h3></div>%s</div>'
            '</div></div></section>'
            % (HERO_BG, eyebrow, h1, sub, cta, wa_icon(), icon(panel_icon), panel_title, items))


def sec_head(eyebrow, h2, intro=None, dark=False):
    p = '<p class="intro-p">%s</p>' % intro if intro else ""
    return ('<div class="sec-eyebrow">%s</div><h2>%s</h2>%s' % (eyebrow, h2, p))


def cards_grid(items, cols="g3", link=None):
    cards = "".join(
        '<div class="card"><span class="ic-box">%s</span><h3>%s</h3><p>%s</p>%s</div>'
        % (icon(ic), t, d,
           ('<a href="#" class="card-link">%s %s</a>' % (link, icon("arrow"))) if link else "")
        for ic, t, d in items)
    return '<div class="grid %s">%s</div>' % (cols, cards)


def table(headers, rows):
    th = "".join("<th>%s</th>" % h for h in headers)
    tr = "".join("<tr>" + "".join('<td class="%s">%s</td>' % ("k" if i == 0 else "", c)
                                  for i, c in enumerate(r)) + "</tr>" for r in rows)
    return ('<div style="overflow-x:auto"><table class="tbl"><thead><tr>%s</tr></thead>'
            '<tbody>%s</tbody></table></div>' % (th, tr))


def steps_block(steps):
    st = "".join('<div class="step"><span class="n">%s</span><h4>%s</h4><p>%s</p></div>'
                 % (str(i + 1), t, d) for i, (t, d) in enumerate(steps))
    return '<div class="steps">%s</div>' % st


def faq_block(qas):
    qa = "".join('<div class="qa"><h4>%s%s</h4><p>%s</p></div>' % (icon("q"), q, a) for q, a in qas)
    return '<div class="faq">%s</div>' % qa


def terms_strip(items, note):
    tr = "".join('<div class="tr"><b>%s</b><span>%s</span></div>' % (b, s) for b, s in items)
    return ('<section class="trust"><div class="wrap">'
            '<div class="trust-grid">%s</div>'
            '<p style="text-align:center;font-size:.78rem;color:rgba(244,241,234,.42);'
            'padding-bottom:22px;margin-top:-6px">%s</p>'
            '</div></section>' % (tr, note))


def cta_band(title, sub, cta="לבדיקת זכאות ללא עלות",
             note="הבדיקה אינה כרוכה בתשלום ואינה מחייבת אתכם בדבר."):
    return ('<section style="position:relative;overflow:hidden;padding-block:62px;'
            'background:radial-gradient(90%% 70%% at 50%% 0,rgba(43,182,170,.14),transparent 60%%),#061A22">'
            '<div class="wrap" style="text-align:center">'
            '<h2 style="margin-bottom:12px">%s</h2>'
            '<p class="intro-p" style="margin-bottom:28px">%s</p>'
            '<div class="cta-row" style="justify-content:center">'
            '<a href="#" class="btn btn-primary">%s</a>'
            '<a href="#" class="btn btn-wa">%s לשיחה בוואטסאפ</a></div>'
            '<p style="font-size:.82rem;color:rgba(244,241,234,.42);margin-top:16px">'
            '%s</p>'
            '</div></section>' % (title, sub, cta, wa_icon(), note))
