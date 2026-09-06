# -*- coding: utf-8 -*-
"""Shared design-system pieces for the Har-El financing canvas artboards.
Values lifted verbatim from the existing index.html brand stylesheet."""

FONTS = ('<link rel="stylesheet" '
         'href="https://fonts.googleapis.com/css2?family=Heebo:wght@300;400;500;600;700;800;900&amp;family=Suez+One&amp;display=swap">')

BASE_CSS = """
:root{
  --navy:#061A22; --navy-2:#0A2733; --navy-3:#103A4A; --navy-4:#16485B;
  --teal:#2BB6AA; --teal-bright:#4FD6C8; --teal-deep:#178379;
  --gold:#C99A3B; --gold-soft:#E7C879;
  --sand:#F4F1EA; --sand-dim:rgba(244,241,234,.7); --sand-faint:rgba(244,241,234,.42);
  --white:#FFFFFF; --ink:#0B2730; --ink-soft:#48626c;
  --line-d:rgba(244,241,234,.12);
  --maxw:1060px; --r:18px;
  --shadow-d:0 34px 80px -34px rgba(0,0,0,.8);
  --shadow-card:0 20px 44px -22px rgba(0,0,0,.55);
}
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:'Heebo',system-ui,sans-serif;background:var(--navy);color:var(--sand);line-height:1.65;-webkit-font-smoothing:antialiased}
a{color:var(--teal-bright);text-decoration:none}
a:hover{color:var(--gold-soft)}
img{display:block;max-width:100%}
svg{width:100%;height:100%;display:block}
.wrap{max-width:var(--maxw);margin-inline:auto;padding-inline:22px}

/* ---- top bar ---- */
.topbar{background:rgba(6,26,34,.82);border-bottom:1px solid var(--line-d)}
.topbar .row{display:flex;align-items:center;justify-content:space-between;gap:20px;padding-block:11px}
.logo-plate{display:inline-flex;align-items:center;gap:12px;direction:ltr;background:var(--sand);padding:8px 15px;border-radius:12px;box-shadow:0 8px 20px -10px rgba(0,0,0,.5)}
.lm-word{height:30px;width:auto}
.lm-chev{height:40px;width:auto}
.lm-tag{display:block;font-size:.7rem;font-weight:800;color:var(--ink);letter-spacing:-.01em;margin-top:3px;direction:rtl;text-align:right}
.lm-tag em{font-style:normal;color:var(--teal-deep)}
.nav{display:flex;align-items:center;gap:19px}
.nav a{font-size:.93rem;font-weight:600;color:var(--sand-dim)}
.nav a:hover{color:var(--teal-bright)}
.nav a.on{color:var(--teal-bright);font-weight:800}
.tb-right{display:flex;align-items:center;gap:14px}
.tb-phone{display:inline-flex;align-items:center;gap:7px;font-size:.95rem;font-weight:800;color:var(--sand)}
.tb-phone svg{width:17px;height:17px;stroke:var(--teal-bright);fill:none;stroke-width:1.9}

/* ---- buttons ---- */
.btn{display:inline-flex;align-items:center;justify-content:center;gap:9px;font-family:'Heebo',sans-serif;font-size:1.06rem;font-weight:800;padding:16px 32px;border-radius:13px;border:none;cursor:pointer;line-height:1.1}
.btn-sm{padding:10px 20px;font-size:.92rem;border-radius:11px}
.btn-primary{background:linear-gradient(135deg,#C99A3B,#E7C879);color:#061A22;box-shadow:0 18px 38px -14px rgba(201,154,59,.6)}
.btn-teal{background:linear-gradient(135deg,#178379,#2BB6AA);color:#fff;box-shadow:0 16px 36px -16px rgba(43,182,170,.7)}
.btn-ghost{background:rgba(16,58,74,.55);color:var(--sand);border:1px solid var(--line-d)}
.btn-wa{background:#25D366;color:#06241b;box-shadow:0 16px 36px -16px rgba(37,211,102,.7)}
.btn-wa svg{width:20px;height:20px}
.cta-row{display:flex;gap:12px;flex-wrap:wrap}

/* ---- section chrome ---- */
section.block{padding-block:60px}
.sec-eyebrow{display:flex;align-items:center;gap:12px;justify-content:center;font-size:.8rem;font-weight:800;letter-spacing:.1em;color:var(--teal-bright);margin-bottom:13px}
.sec-eyebrow::before,.sec-eyebrow::after{content:"";height:1px;width:34px;background:var(--line-d)}
h1{font-family:'Suez One',Georgia,serif;font-weight:400;line-height:1.12;letter-spacing:-.01em}
h2{font-family:'Suez One',Georgia,serif;font-weight:400;font-size:2.35rem;line-height:1.16;text-align:center;margin-bottom:14px}
h3{font-family:'Suez One',Georgia,serif;font-weight:400}
.u{color:var(--teal-bright)}
.g{color:var(--gold-soft)}
.intro-p{text-align:center;max-width:640px;margin:0 auto 40px;color:var(--sand-dim);font-size:1.05rem}
.kicker{display:inline-flex;align-items:center;gap:9px;font-size:.82rem;font-weight:800;letter-spacing:.06em;color:var(--teal-bright);border:1px solid rgba(79,214,200,.4);background:rgba(6,26,34,.5);border-radius:999px;padding:8px 18px}
.kicker svg{width:15px;height:15px;stroke:var(--teal-bright);fill:none;stroke-width:2}

/* ---- placeholder marker: a fact only the client can supply ---- */
.ph{color:var(--gold-soft);border-bottom:1px dashed rgba(201,154,59,.55);font-weight:800;white-space:nowrap}
.tag-sample{display:inline-flex;align-items:center;gap:6px;font-size:.68rem;font-weight:800;letter-spacing:.04em;color:var(--gold-soft);border:1px dashed rgba(201,154,59,.5);border-radius:999px;padding:3px 10px}

/* ---- cards / grids ---- */
.grid{display:grid;gap:20px}
.g2{grid-template-columns:repeat(2,minmax(0,1fr))}
.g3{grid-template-columns:repeat(3,minmax(0,1fr))}
.g4{grid-template-columns:repeat(4,minmax(0,1fr))}
.card{background:rgba(16,58,74,.34);border:1px solid var(--line-d);border-radius:18px;padding:26px 24px;box-shadow:var(--shadow-card);display:flex;flex-direction:column;gap:12px}
.card h3{font-size:1.32rem;line-height:1.25}
.card p{color:var(--sand-dim);font-size:.98rem}
.ic-box{width:46px;height:46px;border-radius:12px;background:rgba(43,182,170,.16);display:grid;place-items:center}
.ic-box svg{width:24px;height:24px;stroke:var(--teal-bright);fill:none;stroke-width:1.9;stroke-linecap:round;stroke-linejoin:round}
.ic-gold{background:rgba(201,154,59,.16)}
.ic-gold svg{stroke:var(--gold-soft)}
.card-link{display:inline-flex;align-items:center;gap:7px;font-size:.95rem;font-weight:800;color:var(--teal-bright);margin-top:auto;padding-top:6px}
.card-link svg{width:15px;height:15px;stroke:currentColor;fill:none;stroke-width:2.2;stroke-linecap:round;stroke-linejoin:round}

/* ---- trust strip ---- */
.trust{background:var(--navy-2);border-block:1px solid var(--line-d)}
.trust-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:8px;padding-block:26px}
.tr{text-align:center;padding:8px 6px}
.tr b{display:block;font-family:'Suez One',Georgia,serif;font-weight:400;font-size:1.7rem;color:var(--teal-bright);line-height:1}
.tr b .ph{font-family:'Heebo',sans-serif;font-size:1.12rem}
.tr span{display:block;margin-top:7px;font-size:.86rem;color:var(--sand-dim);font-weight:600}

/* ---- feature rows ---- */
.feat{display:flex;gap:13px;align-items:flex-start;padding:11px 0;border-bottom:1px dashed var(--line-d)}
.feat:last-child{border-bottom:none}
.feat .ic{flex:0 0 auto;width:36px;height:36px;border-radius:10px;background:rgba(43,182,170,.16);display:grid;place-items:center;margin-top:1px}
.feat .ic svg{width:19px;height:19px;stroke:var(--teal-bright);fill:none;stroke-width:2;stroke-linecap:round;stroke-linejoin:round}
.feat p{font-size:1rem;color:var(--sand)}
.feat p b{color:var(--teal-bright);font-weight:800}

/* ---- numbered steps ---- */
.steps{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:18px}
.step{background:var(--navy-2);border:1px solid var(--line-d);border-radius:16px;padding:24px 20px;display:flex;flex-direction:column;gap:10px}
.step .n{font-family:'Suez One',Georgia,serif;font-weight:400;font-size:1.5rem;color:var(--gold-soft);width:44px;height:44px;border-radius:12px;background:rgba(201,154,59,.14);display:grid;place-items:center;line-height:1}
.step h4{font-size:1.08rem;font-weight:800}
.step p{font-size:.94rem;color:var(--sand-dim)}

/* ---- comparison table ---- */
.tbl{width:100%;border-collapse:separate;border-spacing:0;border:1px solid var(--line-d);border-radius:16px;overflow:hidden;background:rgba(16,58,74,.28)}
.tbl th{background:var(--navy-2);text-align:start;font-size:.86rem;font-weight:800;letter-spacing:.04em;color:var(--teal-bright);padding:14px 18px;border-bottom:1px solid var(--line-d)}
.tbl td{padding:15px 18px;font-size:.96rem;color:var(--sand-dim);border-bottom:1px dashed var(--line-d);vertical-align:top}
.tbl tr:last-child td{border-bottom:none}
.tbl td.k{color:var(--sand);font-weight:800}

/* ---- faq ---- */
.faq{max-width:760px;margin-inline:auto;display:flex;flex-direction:column;gap:12px}
.qa{background:var(--navy-2);border:1px solid var(--line-d);border-radius:14px;padding:20px 22px}
.qa h4{font-size:1.05rem;font-weight:800;margin-bottom:7px;display:flex;align-items:center;gap:10px}
.qa h4 svg{width:17px;height:17px;stroke:var(--teal-bright);fill:none;stroke-width:2.2;flex:0 0 auto}
.qa p{font-size:.96rem;color:var(--sand-dim)}

/* ---- lead form ---- */
.form-card{max-width:540px;margin-inline:auto;background:linear-gradient(165deg,var(--navy-3),var(--navy-2));border:1px solid rgba(201,154,59,.24);border-radius:22px;padding:34px 28px;box-shadow:var(--shadow-d)}
.field{margin-bottom:15px;text-align:start}
.field label{display:block;font-size:.9rem;font-weight:700;margin-bottom:7px}
.field label .req{color:var(--gold-soft)}
.field .inp{width:100%;font-size:1rem;color:var(--sand-faint);background:var(--navy);border:1px solid var(--line-d);border-radius:12px;padding:14px 15px}
.field .sel{display:flex;align-items:center;justify-content:space-between}
.field .sel svg{width:15px;height:15px;stroke:var(--sand-faint);fill:none;stroke-width:2.2}
.consent{display:flex;gap:10px;align-items:flex-start;margin-bottom:20px;font-size:.84rem;color:var(--sand-dim)}
.consent .box{width:17px;height:17px;border:1px solid var(--line-d);border-radius:4px;background:var(--navy);flex:0 0 auto;margin-top:4px}
.form-card .btn{width:100%}
.form-note{text-align:center;font-size:.82rem;color:var(--sand-faint);margin-top:14px}

/* ---- footer ---- */
footer{background:var(--navy-2);border-top:1px solid var(--line-d);padding-block:38px 30px}
.foot-top{display:grid;grid-template-columns:1.3fr 1fr 1fr 1fr;gap:28px;padding-bottom:26px;border-bottom:1px solid var(--line-d)}
.foot-col h5{font-size:.82rem;font-weight:800;letter-spacing:.08em;color:var(--teal-bright);margin-bottom:12px}
.foot-col ul{list-style:none;display:flex;flex-direction:column;gap:8px}
.foot-col a{font-size:.92rem;color:var(--sand-dim)}
.foot-col a:hover{color:var(--teal-bright)}
.foot-blurb{font-size:.9rem;color:var(--sand-dim);margin-top:14px;max-width:280px}
.disclaimer{max-width:900px;margin:22px auto 0;font-size:.76rem;color:var(--sand-faint);line-height:1.75;text-align:center}
.meta-dis{margin-top:12px;font-size:.72rem;color:var(--sand-faint);opacity:.8;text-align:center}
"""

# ---------------------------------------------------------------- icons
_I = {
 "house":'<path d="M3.5 10.6 12 3.8l8.5 6.8"/><path d="M5.8 9.6V20h12.4V9.6"/><path d="M10 20v-5.2h4V20"/>',
 "car":'<path d="M4.6 16.4v-3l1.8-4.2A2 2 0 0 1 8.2 8h7.6a2 2 0 0 1 1.8 1.2l1.8 4.2v3"/><path d="M4.6 13.4h14.8"/><circle cx="7.8" cy="16.6" r="1.7"/><circle cx="16.2" cy="16.6" r="1.7"/>',
 "building":'<path d="M4 20.2V6.4A1.4 1.4 0 0 1 5.4 5h6.2A1.4 1.4 0 0 1 13 6.4v13.8"/><path d="M13 11h5.6A1.4 1.4 0 0 1 20 12.4v7.8"/><path d="M2.8 20.2h18.4"/><path d="M6.8 8.6h3.4M6.8 12h3.4M6.8 15.4h3.4M15.8 14h1.6M15.8 17h1.6"/>',
 "wallet":'<path d="M3.6 8.6A2 2 0 0 1 5.6 6.6h12.9A1.5 1.5 0 0 1 20 8.1V18a1.5 1.5 0 0 1-1.5 1.5H5.6a2 2 0 0 1-2-2z"/><path d="M20 11.6h-3.4a1.6 1.6 0 0 0 0 3.2H20"/>',
 "check":'<path d="M5 12.6 9.4 17 19 7.2"/>',
 "shield":'<path d="M12 3.6 19 6.1v5.4c0 4.2-2.9 7.5-7 8.9-4.1-1.4-7-4.7-7-8.9V6.1z"/><path d="M9 12.2l2 2 4-4"/>',
 "clock":'<circle cx="12" cy="12" r="8.4"/><path d="M12 7.2V12l3.1 1.9"/>',
 "users":'<circle cx="9" cy="8.4" r="3.3"/><path d="M3.2 19.4c0-3.1 2.6-5.2 5.8-5.2s5.8 2.1 5.8 5.2"/><path d="M16.4 5.5a3 3 0 0 1 0 5.8"/><path d="M17.4 14.6c2.2.5 3.8 2.4 3.8 4.8"/>',
 "trend":'<path d="M3.6 16.6 9.6 10.6l3.4 3.4 7-7.4"/><path d="M15.4 6.6H20v4.6"/>',
 "phone":'<path d="M6.2 3.8h3l1.5 3.7-1.9 1.4a11.4 11.4 0 0 0 5.3 5.3l1.4-1.9 3.7 1.5v3a1.8 1.8 0 0 1-1.9 1.8A15.6 15.6 0 0 1 4.4 5.7a1.8 1.8 0 0 1 1.8-1.9z"/>',
 "mail":'<path d="M3.6 7.4h16.8v9.2H3.6z"/><path d="m3.6 7.9 8.4 5.6 8.4-5.6"/>',
 "pin":'<path d="M12 20.8s6.3-5.8 6.3-10.6a6.3 6.3 0 1 0-12.6 0C5.7 15 12 20.8 12 20.8z"/><circle cx="12" cy="10" r="2.3"/>',
 "doc":'<path d="M6.4 3.6h6.8l4.4 4.4v12.4H6.4z"/><path d="M13.2 3.6V8h4.4"/><path d="M9 12.4h6M9 15.4h6"/>',
 "coins":'<ellipse cx="12" cy="6.6" rx="6.6" ry="2.6"/><path d="M5.4 6.6v4.2c0 1.4 3 2.6 6.6 2.6s6.6-1.2 6.6-2.6V6.6"/><path d="M5.4 10.8V15c0 1.4 3 2.6 6.6 2.6s6.6-1.2 6.6-2.6v-4.2"/>',
 "percent":'<circle cx="7.6" cy="7.6" r="2.5"/><circle cx="16.4" cy="16.4" r="2.5"/><path d="M18.4 5.6 5.6 18.4"/>',
 "target":'<circle cx="12" cy="12" r="8.4"/><circle cx="12" cy="12" r="4.6"/><circle cx="12" cy="12" r="1.1"/>',
 "calc":'<rect x="6.2" y="3.4" width="11.6" height="17.2" rx="1.8"/><path d="M9 7.2h6"/><path d="M9.4 11.4h.02M12 11.4h.02M14.6 11.4h.02M9.4 14.4h.02M12 14.4h.02M14.6 14.4h.02M9.4 17.4h.02M12 17.4h.02M14.6 17.4h.02" stroke-width="2.6"/>',
 "key":'<circle cx="8.2" cy="8.2" r="3.6"/><path d="m10.8 10.8 8 8"/><path d="m15.6 15.6 2-2M17.8 17.8l2-2"/>',
 "layers":'<path d="m12 3.6 8.4 4.2-8.4 4.2-8.4-4.2z"/><path d="m3.6 12 8.4 4.2 8.4-4.2"/><path d="m3.6 16.2 8.4 4.2 8.4-4.2"/>',
 "merge":'<path d="M5.4 4.2v4.2c0 2 1.6 3.6 3.6 3.6h6"/><path d="M5.4 19.8v-4.2c0-2 1.6-3.6 3.6-3.6h6"/><path d="m15.6 8.4 3.6 3.6-3.6 3.6"/>',
 "quote":'<path d="M9.6 6.6c-2.8 1-4.4 3.3-4.4 6.3v4.5h5.6v-5.6H8c0-1.7.7-2.9 2.2-3.6z"/><path d="M19.2 6.6c-2.8 1-4.4 3.3-4.4 6.3v4.5h5.6v-5.6h-2.8c0-1.7.7-2.9 2.2-3.6z"/>',
 "q":'<circle cx="12" cy="12" r="8.4"/><path d="M9.7 9.5a2.4 2.4 0 1 1 3.2 2.3c-.6.2-.9.8-.9 1.4v.5"/><path d="M12 16.6h.02" stroke-width="2.6"/>',
 "arrow":'<path d="M15.4 5.6 8.8 12l6.6 6.4"/>',
 "chev":'<path d="m14.6 6.6-5.4 5.4 5.4 5.4"/>',
 "spark":'<path d="M12 3.4 13.9 9l5.6 1.9-5.6 1.9-1.9 5.6-1.9-5.6L4.5 10.9 10.1 9z"/><path d="M18.4 16.4l.7 2 2 .7-2 .7-.7 2-.7-2-2-.7 2-.7z"/>',
 "lock":'<rect x="5.4" y="10.4" width="13.2" height="9.4" rx="2"/><path d="M8.4 10.4V7.8a3.6 3.6 0 0 1 7.2 0v2.6"/>',
 "eye":'<path d="M2.6 12S6 6.4 12 6.4 21.4 12 21.4 12 18 17.6 12 17.6 2.6 12 2.6 12z"/><circle cx="12" cy="12" r="2.8"/>',
 "scale":'<path d="M12 4v16"/><path d="M6.4 6.6h11.2"/><path d="m6.4 6.6-3 6.4h6z"/><path d="m17.6 6.6-3 6.4h6z"/><path d="M8.6 20h6.8"/>',
 "truck":'<path d="M3.6 6.6h9.6v9.8H3.6z"/><path d="M13.2 10h3.6l2.6 2.8v3.6h-6.2z"/><circle cx="7" cy="18" r="1.7"/><circle cx="16.6" cy="18" r="1.7"/>',
 "cap":'<path d="m12 4.4 9 4.2-9 4.2-9-4.2z"/><path d="M6.6 10.6v4.6c0 1.5 2.4 2.8 5.4 2.8s5.4-1.3 5.4-2.8v-4.6"/><path d="M21 8.6v5"/>',
 "heart":'<path d="M12 19.6S4.4 15.2 4.4 10a3.9 3.9 0 0 1 7.6-1.4A3.9 3.9 0 0 1 19.6 10c0 5.2-7.6 9.6-7.6 9.6z"/>',
 "tools":'<path d="M14.4 6.6a3.6 3.6 0 0 0 4.8 4.6L21 13l-8 8-1.8-1.8"/><path d="M9.6 4.6 4.4 9.8l3 3 5.2-5.2z"/><path d="m7.4 12.8-4 4 2.6 2.6 4-4"/>',
}

def icon(name, cls=""):
    body = _I[name]
    c = ' class="%s"' % cls if cls else ""
    return ('<svg%s viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" '
            'stroke-linecap="round" stroke-linejoin="round">%s</svg>' % (c, body))

def wa_icon():
    return ('<svg viewBox="0 0 24 24" fill="currentColor"><path d="M12.04 2C6.58 2 2.13 6.45 2.13 11.91c0 1.75.46 3.45 1.32 4.95L2 22l5.25-1.38a9.9 9.9 0 0 0 4.79 1.22h.01c5.46 0 9.91-4.45 9.91-9.91S17.5 2 12.04 2zm0 18.13c-1.5 0-2.98-.4-4.27-1.17l-.31-.18-3.12.82.83-3.04-.2-.31a8.2 8.2 0 0 1-1.26-4.34c0-4.54 3.7-8.23 8.24-8.23 2.2 0 4.27.86 5.82 2.42a8.18 8.18 0 0 1 2.41 5.82c0 4.54-3.7 8.21-8.14 8.21zm4.52-6.16c-.25-.12-1.47-.72-1.69-.81-.23-.08-.39-.12-.56.13-.16.24-.64.8-.78.97-.14.16-.29.19-.54.06-.25-.12-1.05-.39-1.99-1.23-.74-.65-1.23-1.46-1.38-1.71-.14-.25-.01-.38.11-.5.11-.11.25-.29.37-.43.13-.15.17-.25.25-.41.08-.17.04-.31-.02-.43-.06-.12-.56-1.34-.76-1.84-.2-.48-.4-.42-.56-.43h-.47c-.17 0-.43.06-.66.31-.23.25-.86.85-.86 2.06s.89 2.39 1.01 2.56c.12.16 1.75 2.67 4.23 3.74.59.26 1.05.41 1.41.52.59.19 1.13.16 1.56.1.48-.07 1.47-.6 1.67-1.18.21-.58.21-1.07.15-1.18-.06-.1-.23-.16-.48-.29z"/></svg>')

# ---------------------------------------------------------------- brand chrome
NAV = [("Main", "בית"), ("Mortgage", "משכנתאות"), ("CarLoan", "הלוואות רכב"),
       ("Business", "מימון לעסקים"), ("Personal", "לכל מטרה"),
       ("About", "אודות"), ("Contact", "צור קשר")]

def logo(word_h=30, chev_h=40, tag_size=".7rem"):
    return ('<span class="logo-plate">'
            '<span>'
            '<img class="lm-word" src="wordmark.png" alt="הר-אל" style="height:%dpx">'
            '<span class="lm-tag" style="font-size:%s">פתרונות מימון <em>חכמים</em></span>'
            '</span>'
            '<img class="lm-chev" src="chevrons.png" alt="" style="height:%dpx">'
            '</span>' % (word_h, tag_size, chev_h))

def topbar(active):
    links = "".join('<a href="#" class="%s">%s</a>' % ("on" if k == active else "", t)
                    for k, t in NAV)
    return ('<header class="topbar"><div class="wrap"><div class="row">'
            '<a href="#" style="display:inline-flex">%s</a>'
            '<nav class="nav">%s</nav>'
            '<div class="tb-right">'
            '<span class="tb-phone">%s<span class="ph">[טלפון]</span></span>'
            '<a href="#" class="btn btn-sm btn-primary">בדיקת זכאות</a>'
            '</div></div></div></header>' % (logo(), links, icon("phone")))

DISCLAIMER = ('הר-אל פתרונות מימון חכמים (<span class="ph">[שם החברה הרשומה]</span> בע״מ) · '
              'ח.פ. <span class="ph">[מספר]</span> · בעל רישיון למתן שירותי אשראי מטעם רשות שוק ההון, '
              'הביטוח והחיסכון, רישיון מס׳ <span class="ph">[מספר רישיון]</span>. '
              'אי־עמידה בפירעון ההלוואה עלולה לגרור חיוב בריבית פיגורים והליכי הוצאה לפועל. '
              'האמור באתר הוא מידע כללי בלבד ואינו מהווה ייעוץ, הצעה או התחייבות למתן אשראי; '
              'אישור ההלוואה, סכומה, הריבית ותנאיה נתונים לשיקול דעתו הבלעדי של הגוף המממן וכפופים להסכם חתום.')

def footer():
    def col(title, items):
        lis = "".join("<li><a href=\"#\">%s</a></li>" % i for i in items)
        return '<div class="foot-col"><h5>%s</h5><ul>%s</ul></div>' % (title, lis)
    return ('<footer><div class="wrap">'
            '<div class="foot-top">'
            '<div class="foot-col">%s'
            '<p class="foot-blurb">מלווים משפחות ועסקים בישראל מול הבנקים והגופים החוץ-בנקאיים — '
            'עד שהמימון הנכון נמצא.</p></div>'
            '%s%s%s'
            '</div>'
            '<p class="disclaimer">%s</p>'
            '<p class="meta-dis">© כל הזכויות שמורות להר-אל פתרונות מימון חכמים.</p>'
            '</div></footer>'
            % (logo(26, 34, ".64rem"),
               col("פתרונות מימון", ["משכנתאות", "הלוואות רכב", "מימון לעסקים", "הלוואות לכל מטרה"]),
               col("החברה", ["אודות הר-אל", "הצוות", "תהליך העבודה", "שאלות נפוצות"]),
               col("יצירת קשר", ["[טלפון]", "[אימייל]", "וואטסאפ", "משה דיין 10, פתח תקווה"]),
               DISCLAIMER))

# ---------------------------------------------------------------- page shell
def page(body, bg="#061A22", extra_css=""):
    return ("""<!doctype html>
<html lang="he" dir="rtl">
<head>
  <meta charset="utf-8">
  <script src="./support.js"></script>
</head>
<body>
<x-dc>
<helmet>
  %s
  <style>%s%s</style>
</helmet>
<div dir="rtl" style="background:%s;min-height:100%%">
%s
</div>
</x-dc>
</body>
</html>
""" % (FONTS, BASE_CSS, extra_css, bg, body))
