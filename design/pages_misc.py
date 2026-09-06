# -*- coding: utf-8 -*-
from _common import page, topbar, footer, icon, wa_icon, logo
from _blocks import page_hero, sec_head, cards_grid, steps_block, cta_band, HERO_BG
from pages_home import team_cards

SEC = '<section class="block"><div class="wrap">%s</div></section>'
SEC_D = ('<section class="block" style="background:#0A2733;'
         'border-block:1px solid rgba(244,241,234,.12)"><div class="wrap">%s</div></section>')


# ----------------------------------------------------------------- אודות
def about():
    hero = page_hero(
        icon("users") + " אודות הר-אל",
        'הקמנו את הר-אל כי ראינו יותר מדי אנשים<br>חותמים על <span class="g">ההצעה הראשונה</span>.',
        "לווים רבים בישראל מקבלים הצעה אחת, מגוף אחד, ומשווים אותה לכלום. "
        "אנחנו עושים את העבודה שאין להם זמן או גישה לעשות: מציגים את אותו תיק לגופים המממנים הרלוונטיים, "
        "ומביאים לשולחן את מה שבאמת אפשר לקבל.",
        "מה מנחה אותנו", "shield",
        ["אומרים לא כשהעסקה לא טובה ללקוח",
         "מציגים תמיד את העלות הכוללת, לא רק את ההחזר",
         "לא גובים תשלום לפני אישור בפועל",
         "לא מעבירים פרטים לגורם שלישי ללא אישור",
         "פועלים תחת רישיון למתן שירותי אשראי"],
        "לדבר איתנו")

    story = ('<div style="display:grid;grid-template-columns:1.15fr .85fr;gap:48px;align-items:start">'
             '<div>'
             '<div class="sec-eyebrow" style="justify-content:flex-start">הסיפור</div>'
             '<h2 style="text-align:start;font-size:2.2rem;margin-bottom:18px">'
             'התחלנו משני צדדים שונים <span class="u">של אותו שולחן</span></h2>'
             '<p style="color:rgba(244,241,234,.78);font-size:1.04rem;margin-bottom:16px">'
             'אביב הגיע מעולם הייעוץ העסקי, שבו כל החלטה מתחילה בשאלה לאן רוצים להגיע. '
             'דן הגיע מעולם המימון, שבו התשובה תמיד תלויה במי יושב מולך בוועדת האשראי. '
             'שנים שלחנו זה לזה לקוחות — עד שהבנו שהם צריכים את שנינו באותה שיחה.</p>'
             '<p style="color:rgba(244,241,234,.78);font-size:1.04rem;margin-bottom:16px">'
             'הר-אל נבנתה סביב עיקרון פשוט: הלקוח לא אמור להתמודד לבד מול מערכת שמכירה '
             'את הכללים הרבה יותר טוב ממנו. אנחנו מביאים את הידע הזה לצד שלכם — '
             'בונים את התיק כמו שצריך, מוציאים אותו למכרז, ומסבירים כל שורה בהצעה שחוזרת.</p>'
             '<p style="color:rgba(244,241,234,.78);font-size:1.04rem">'
             'ולפעמים העבודה הכי חשובה שלנו היא להגיד לכם שההלוואה הזו לא כדאית — '
             'גם כשזה אומר שלא נרוויח על התיק.</p>'
             '</div>'
             '<div style="background:rgba(16,58,74,.34);border:1px solid rgba(244,241,234,.12);'
             'border-radius:18px;padding:26px 24px;box-shadow:0 20px 44px -22px rgba(0,0,0,.55);'
             'display:flex;flex-direction:column;gap:2px">'
             + "".join(
                 '<div style="padding:16px 0;border-bottom:1px dashed rgba(244,241,234,.12)">'
                 '<div style="font-family:\'Suez One\',Georgia,serif;font-size:1.75rem;color:#4FD6C8;'
                 'line-height:1.1">%s</div>'
                 '<div style="font-size:.9rem;color:rgba(244,241,234,.7);margin-top:5px">%s</div></div>'
                 % (b, s) for b, s in [
                     ('<span class="ph">[מס׳]</span>', "משפחות ועסקים שליווינו"),
                     ('<span class="ph">[מס׳]</span>', "בנקים, גופים חוץ-בנקאיים וקרנות"),
                     ('<span class="ph">[סכום]</span>', "היקף אשראי שאושר ללקוחותינו"),
                     ('<span class="ph">[שנה]</span>', "השנה שבה התחלנו")])
             + '</div></div>')

    values = cards_grid([
        ("eye", "שקיפות לפני הכול",
         "כל הצעה מוצגת עם הריבית האפקטיבית, העמלות והעלות הכוללת עד התשלום האחרון. "
         "בלי כוכביות ובלי שורות שמתגלות בחתימה."),
        ("scale", "האינטרס שלנו זהה לשלכם",
         "אנחנו מתוגמלים רק כשההלוואה אושרה ואתם בחרתם לקחת אותה. "
         "אין לנו תמריץ לדחוף מסלול יקר יותר."),
        ("lock", "הפרטים שלכם נשארים אצלנו",
         "לא מוכרים לידים, לא מעבירים מידע לגורם שלישי ולא פונים לשום גוף מממן "
         "לפני שסיכמנו איתכם."),
    ], "g3")

    compliance = ('<div style="background:linear-gradient(165deg,#103A4A,#0A2733);'
                  'border:1px solid rgba(201,154,59,.24);border-radius:20px;padding:30px 28px;'
                  'box-shadow:0 34px 80px -34px rgba(0,0,0,.8);display:grid;'
                  'grid-template-columns:.9fr 1.1fr;gap:34px;align-items:center">'
                  '<div>'
                  '<span class="ic-box ic-gold" style="width:44px;height:44px;margin-bottom:14px">%s</span>'
                  '<h3 style="font-size:1.42rem;margin-bottom:10px">פועלים תחת רישיון</h3>'
                  '<p style="color:rgba(244,241,234,.7);font-size:.98rem">'
                  'מתן שירותי אשראי ותיווך באשראי בישראל הוא תחום מפוקח. '
                  'אנחנו פועלים ברישיון למתן שירותי אשראי מטעם רשות שוק ההון, הביטוח והחיסכון, '
                  'ומחויבים לכללי הגילוי הנאות שנקבעו בחוק.</p></div>'
                  '<div style="display:flex;flex-direction:column;gap:2px">%s</div>'
                  '</div>' % (icon("shield"), "".join(
                      '<div style="display:flex;gap:12px;align-items:flex-start;padding:12px 0;'
                      'border-bottom:1px dashed rgba(244,241,234,.12)">'
                      '<span style="flex:0 0 auto;width:22px;height:22px;border-radius:7px;'
                      'background:rgba(201,154,59,.16);display:grid;place-items:center;color:#E7C879;'
                      'margin-top:2px"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" '
                      'stroke-width="3" stroke-linecap="round" stroke-linejoin="round" '
                      'style="width:12px;height:12px"><path d="M5 12.6 9.4 17 19 7.2"/></svg></span>'
                      '<div><div style="font-weight:800;font-size:.98rem">%s</div>'
                      '<div style="font-size:.88rem;color:rgba(244,241,234,.7)">%s</div></div></div>'
                      % (t, d) for t, d in [
                          ("רישיון למתן שירותי אשראי",
                           'רשות שוק ההון, הביטוח והחיסכון · מס׳ <span class="ph">[מספר רישיון]</span>'),
                          ("גילוי נאות בכתב",
                           "כל הצעה מלווה בפירוט ריבית אפקטיבית, עמלות ועלות כוללת"),
                          ("שכר טרחה מותנה בהצלחה",
                           "מוצג מראש בכתב, נגבה רק לאחר אישור ובחירתכם לקחת את ההלוואה"),
                          ("שמירה על פרטיות",
                           "המידע נשמר בהתאם לחוק הגנת הפרטיות ואינו מועבר ללא אישורכם")])))

    return page(
        topbar("About") + hero
        + SEC % story
        + SEC_D % (sec_head("הצוות", 'שני מייסדים. <span class="u">שתי התמחויות משלימות.</span>',
                            "אחד בונה את האסטרטגיה, השני מביא את הכסף. התיק שלכם עובר דרך שניהם.")
                   + team_cards())
        + SEC % (sec_head("ערכים", 'שלושה דברים <span class="g">שלא משתנים אצלנו</span>') + values)
        + SEC_D % (sec_head("רגולציה ואמון", 'מה <span class="u">מחייב אותנו</span>') + compliance)
        + cta_band("בואו נדבר על מה שאתם צריכים לממן",
                   "שיחה קצרה, בלי התחייבות — ובסופה תדעו בדיוק איפה אתם עומדים.",
                   "לשיחת אבחון",
                   "לא פונים לשום גוף מממן לפני שסיכמנו איתכם מה יוצא ולאן.")
        + footer())


# ----------------------------------------------------------------- צור קשר
def contact():
    fields = "".join(
        '<div class="field"><label>%s%s</label><div class="inp %s">%s%s</div></div>'
        % (lab, ' <span class="req">*</span>' if req else
           ' <span style="color:rgba(244,241,234,.42);font-weight:500">(לא חובה)</span>',
           "sel" if caret else "", val,
           '<span style="display:inline-flex">' + icon("chev") + '</span>' if caret else "")
        for lab, val, req, caret in [
            ("שם מלא", "השם שלך", True, False),
            ("טלפון נייד", "050-0000000", True, False),
            ("אימייל", "name@email.com", False, False),
            ("מה תרצו לממן?", "בחרו מסלול", True, True),
            ("סכום מבוקש", "למשל 250,000 ₪", False, False)])

    form = ('<div style="background:linear-gradient(165deg,#103A4A,#0A2733);'
            'border:1px solid rgba(201,154,59,.24);border-radius:22px;padding:32px 28px;'
            'box-shadow:0 34px 80px -34px rgba(0,0,0,.8)">'
            '<h3 style="font-size:1.42rem;margin-bottom:6px">השאירו פרטים</h3>'
            '<p style="font-size:.94rem;color:rgba(244,241,234,.7);margin-bottom:22px">'
            'נחזור אליכם בשעות הפעילות. אם זה דחוף — וואטסאפ הוא הדרך המהירה.</p>'
            '%s'
            '<div class="field"><label>משהו שכדאי שנדע מראש '
            '<span style="color:rgba(244,241,234,.42);font-weight:500">(לא חובה)</span></label>'
            '<div class="inp" style="min-height:86px;align-items:flex-start">'
            'למשל: יש לי הצעה מהבנק ואני רוצה לדעת אם היא טובה</div></div>'
            '<div class="consent"><span class="box"></span>'
            '<span>מאשר/ת קבלת פנייה חוזרת בטלפון, בוואטסאפ ובאימייל בנוגע לפנייה זו. '
            'הפרטים לא יועברו לגורם שלישי ללא אישורי.</span></div>'
            '<a href="#" class="btn btn-primary" style="width:100%%">שליחה</a>'
            '<p class="form-note">הפנייה אינה כרוכה בתשלום ואינה מחייבת אתכם בדבר.</p>'
            '</div>' % fields)

    def row(ic, label, value, sub=None):
        s = ('<div style="font-size:.85rem;color:rgba(244,241,234,.42);margin-top:3px">%s</div>' % sub) if sub else ""
        return ('<div style="display:flex;gap:14px;align-items:flex-start;padding:16px 0;'
                'border-bottom:1px dashed rgba(244,241,234,.12)">'
                '<span class="ic-box" style="width:40px;height:40px;flex:0 0 auto">%s</span>'
                '<div><div style="font-size:.82rem;font-weight:800;color:#4FD6C8;margin-bottom:2px">%s</div>'
                '<div style="font-size:1.05rem;font-weight:700">%s</div>%s</div></div>'
                % (icon(ic), label, value, s))

    hours = "".join(
        '<div style="display:flex;align-items:center;justify-content:space-between;'
        'font-size:.94rem;padding:7px 0"><span style="color:rgba(244,241,234,.7)">%s</span>'
        '<span style="font-weight:700">%s</span></div>' % (d, h)
        for d, h in [("ראשון–חמישי", '<span class="ph" dir="ltr">[09:00–18:00]</span>'),
                     ("שישי וערבי חג", '<span class="ph" dir="ltr">[09:00–13:00]</span>'),
                     ("שבת", "סגור")])

    details = ('<div style="display:flex;flex-direction:column;gap:22px">'
               '<div style="background:rgba(16,58,74,.34);border:1px solid rgba(244,241,234,.12);'
               'border-radius:18px;padding:8px 24px 10px;box-shadow:0 20px 44px -22px rgba(0,0,0,.55)">'
               '%s%s%s%s</div>'
               '<a href="#" class="btn btn-wa" style="width:100%%">%s לפתוח שיחה בוואטסאפ</a>'
               '<div style="background:rgba(16,58,74,.34);border:1px solid rgba(244,241,234,.12);'
               'border-radius:18px;padding:22px 24px">'
               '<div style="display:flex;align-items:center;gap:10px;margin-bottom:12px">'
               '<span style="color:#4FD6C8;display:inline-flex;width:19px;height:19px">%s</span>'
               '<h4 style="font-size:1.05rem;font-weight:800">שעות פעילות</h4></div>%s</div>'
               '<div style="position:relative;border-radius:18px;overflow:hidden;height:190px;'
               'border:1px solid rgba(244,241,234,.12);'
               'background:repeating-linear-gradient(58deg,rgba(244,241,234,.05) 0 1px,transparent 1px 34px),'
               'repeating-linear-gradient(148deg,rgba(244,241,234,.05) 0 1px,transparent 1px 34px),'
               'linear-gradient(160deg,#103A4A,#061A22)">'
               '<div style="position:absolute;inset:0;display:flex;flex-direction:column;'
               'align-items:center;justify-content:center;gap:8px;color:rgba(244,241,234,.42)">'
               '<span style="color:rgba(79,214,200,.6);display:inline-flex;width:28px;height:28px">%s</span>'
               '<span style="font-size:.86rem;font-weight:700">משה דיין 10, פתח תקווה</span>'
               '<span style="font-size:.72rem">מקום למפה — להטמעה באתר החי</span></div></div>'
               '</div>'
               % (row("phone", "טלפון", '<span class="ph">[מספר טלפון]</span>', "לחיוג ישיר בשעות הפעילות"),
                  row("mail", "אימייל", '<span class="ph">[כתובת אימייל]</span>', '<span class="ph">[זמן מענה]</span>'),
                  row("pin", "משרד", "משה דיין 10, פתח תקווה", "פגישות בתיאום מראש"),
                  row("doc", "רישיון", 'מס׳ <span class="ph">[מספר רישיון]</span>',
                      "רשות שוק ההון, הביטוח והחיסכון"),
                  wa_icon(), icon("clock"), hours, icon("pin")))

    after = steps_block([
        ("חוזרים אליכם", "שיחה קצרה להבין מה צריך, ומה כבר ניסיתם."),
        ("אומרים לכם מה ריאלי", "טווח סכומים, כיוון מסלול, ומה נדרש כדי להגיש."),
        ("רק אז מגישים", "לא פונים לאף גוף מממן לפני שסיכמנו איתכם מה יוצא ולאן."),
        ("מלווים עד הסוף", "עוברים על ההצעות יחד ונשארים איתכם עד ההעמדה בפועל."),
    ])

    return page(
        topbar("Contact")
        + ('<section style="background:%s"><div class="wrap" style="padding-block:54px 22px;'
           'text-align:center">'
           '<span class="kicker" style="margin-bottom:18px">%s צור קשר</span>'
           '<h1 style="font-size:2.75rem;margin-bottom:14px">'
           'שיחה אחת קצרה —<br>ותדעו איפה אתם <span class="u">באמת עומדים</span>.</h1>'
           '<p style="font-size:1.08rem;color:rgba(244,241,234,.78);max-width:620px;margin-inline:auto">'
           'בלי טפסים ארוכים, בלי מוקד ובלי התחייבות. משאירים פרטים או שולחים הודעה — '
           'ואנחנו חוזרים עם תשובה אמיתית.</p>'
           '</div></section>' % (HERO_BG, icon("phone")))
        + ('<section style="padding-block:38px 60px"><div class="wrap">'
           '<div style="display:grid;grid-template-columns:1.06fr .94fr;gap:36px;align-items:start">'
           '%s%s</div></div></section>' % (form, details))
        + SEC_D % (sec_head("מה קורה אחר כך", 'ארבעה שלבים, <span class="g">בלי הפתעות</span>') + after)
        + footer())


# ----------------------------------------------------------------- מובייל
MOBILE_CSS = """
body{font-size:15px}
.wrap{padding-inline:18px}
.g2,.g3,.g4,.steps,.trust-grid{grid-template-columns:1fr}
.trust-grid{grid-template-columns:1fr 1fr}
section.block{padding-block:38px}
h2{font-size:1.72rem}
.card{padding:22px 20px}
.btn{width:100%;font-size:1rem;padding:15px 22px}
.cta-row{flex-direction:column;width:100%}
"""


def mobile_home():
    def burger():
        return ('<span style="display:inline-flex;flex-direction:column;gap:5px;padding:9px 10px;'
                'border:1px solid rgba(244,241,234,.12);border-radius:10px;background:rgba(16,58,74,.5)">'
                + '<span style="display:block;width:19px;height:2px;background:#F4F1EA;border-radius:2px"></span>' * 3
                + '</span>')

    bar = ('<header class="topbar"><div class="wrap">'
           '<div class="row" style="padding-block:10px">%s%s</div></div></header>'
           % ('<a href="#" style="display:inline-flex">%s</a>' % logo(24, 32, ".6rem"), burger()))

    chips = "".join(
        '<span style="display:inline-flex;align-items:center;gap:6px;font-size:.85rem;font-weight:700;'
        'color:rgba(244,241,234,.7)">'
        '<span style="width:17px;height:17px;border-radius:50%%;background:rgba(43,182,170,.18);'
        'display:grid;place-items:center;color:#4FD6C8">'
        '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3.2" '
        'stroke-linecap="round" stroke-linejoin="round" style="width:10px;height:10px">'
        '<path d="M5 12.6 9.4 17 19 7.2"/></svg></span>%s</span>' % t
        for t in ["בדיקה ללא עלות", "לא נרשם בנתוני האשראי", "לא משלמים אם לא לוקחים"])

    hero = ('<section style="background:%s"><div class="wrap" style="padding-block:40px 44px">'
            '<span class="kicker" style="margin-bottom:18px;font-size:.74rem;padding:7px 14px">'
            '%s רישיון למתן שירותי אשראי</span>'
            '<h1 style="font-size:2.05rem;margin-bottom:14px">המימון הנכון קיים.<br>'
            'רק לא תמיד <span class="u">בבנק שלכם</span>.</h1>'
            '<p style="font-size:1rem;color:rgba(244,241,234,.78);margin-bottom:22px">'
            'מציגים את התיק שלכם במקביל לבנקים, לגופים החוץ-בנקאיים ולקרנות — '
            'ומראים לכם את ההצעות שחוזרות זו לצד זו.</p>'
            '<div class="cta-row" style="margin-bottom:20px">'
            '<a href="#" class="btn btn-primary">לבדיקת זכאות ללא עלות</a>'
            '<a href="#" class="btn btn-wa">%s וואטסאפ</a></div>'
            '<div style="display:flex;flex-direction:column;gap:9px">%s</div>'
            '</div></section>' % (HERO_BG, icon("shield"), wa_icon(), chips))

    prods = "".join(
        '<div class="card" style="gap:10px;padding:20px 18px">'
        '<div style="display:flex;align-items:center;gap:12px">'
        '<span class="ic-box" style="width:42px;height:42px;flex:0 0 auto">%s</span>'
        '<h3 style="font-size:1.2rem">%s</h3></div>'
        '<p style="font-size:.94rem">%s</p>'
        '<a href="#" class="card-link">לפרטים %s</a></div>' % (icon(ic), t, d, icon("arrow"))
        for ic, t, d in [
            ("house", "משכנתאות", "ראשונה, מיחזור, הגדלה או איחוד חובות פנימה — מתומחר מול כל הבנקים במקביל."),
            ("car", "הלוואות רכב", "חדש, יד שנייה או סילוק ליסינג — בלי הריבית שהסוכנות מגלגלת פנימה."),
            ("building", "מימון לעסקים", "הון חוזר, ציוד, ניכיון צ׳קים וקרן בערבות מדינה."),
            ("wallet", "לכל מטרה", "שיפוץ, חתונה, לימודים או איחוד הלוואות למקום אחד.")])

    steps = "".join(
        '<div class="step" style="flex-direction:row;gap:14px;align-items:flex-start;padding:18px 16px">'
        '<span class="n" style="width:38px;height:38px;font-size:1.25rem;flex:0 0 auto">%d</span>'
        '<div><h4 style="font-size:1rem;margin-bottom:3px">%s</h4>'
        '<p style="font-size:.9rem">%s</p></div></div>' % (i + 1, t, d)
        for i, (t, d) in enumerate([
            ("שיחת אבחון", "רבע שעה: מה צריך, איזה החזר נוח, ומה מצב הדוחות."),
            ("בניית התיק", "אוספים מסמכים ומרכיבים את הבקשה כך שתוצג בצורה המיטבית."),
            ("מכרז בין הגופים", "אותו תיק יוצא לכמה גופים במקביל."),
            ("חתימה וכסף בחשבון", "עוברים על התנאים סעיף-סעיף, ורק אז חותמים.")]))

    fields = "".join(
        '<div class="field"><label>%s <span class="req">*</span></label>'
        '<div class="inp %s">%s%s</div></div>'
        % (lab, "sel" if caret else "", val,
           '<span style="display:inline-flex">' + icon("chev") + '</span>' if caret else "")
        for lab, val, caret in [("שם מלא", "השם שלך", False),
                                ("טלפון נייד", "050-0000000", False),
                                ("מה תרצו לממן?", "בחרו מסלול", True)])

    cta = ('<section style="padding-block:44px;background:radial-gradient(120%% 60%% at 50%% 0,'
           'rgba(43,182,170,.14),transparent 60%%),#061A22"><div class="wrap">'
           '<h2 style="margin-bottom:10px">נבדוק לכם את הזכאות</h2>'
           '<p style="text-align:center;color:rgba(244,241,234,.7);font-size:.96rem;margin-bottom:24px">'
           'בלי עלות ובלי התחייבות.</p>'
           '<div class="form-card" style="padding:24px 20px">%s'
           '<div class="consent"><span class="box"></span>'
           '<span>מאשר/ת קבלת פנייה חוזרת בנוגע לפנייה זו.</span></div>'
           '<a href="#" class="btn btn-primary">לבדיקת זכאות</a></div>'
           '</div></section>' % fields)

    foot = ('<footer style="padding-block:26px"><div class="wrap" style="text-align:center">'
            '<div style="display:flex;justify-content:center;margin-bottom:14px">%s</div>'
            '<p class="disclaimer" style="font-size:.7rem">'
            'בעלת רישיון למתן שירותי אשראי מטעם רשות שוק ההון, הביטוח והחיסכון, '
            'רישיון מס׳ <span class="ph">[מספר רישיון]</span>. '
            'אי עמידה בפירעון ההלוואה או בהחזר האשראי עלול לגרור חיוב בריבית פיגורים '
            'והליכי הוצאה לפועל. האמור באתר הוא מידע כללי בלבד ואינו מהווה ייעוץ, '
            'הצעה או התחייבות למתן אשראי.</p>'
            '<p class="meta-dis">© הר-אל פתרונות מימון חכמים</p>'
            '</div></footer>' % logo(24, 32, ".6rem"))

    body = (bar + hero
            + '<section class="trust"><div class="wrap"><div class="trust-grid">'
            + "".join('<div class="tr"><b>%s</b><span>%s</span></div>' % (b, s) for b, s in [
                ('<span class="ph">[מס׳]</span>', "לקוחות שליווינו"),
                ('<span class="ph">[מס׳]</span>', "גופים מממנים"),
                ('<span class="ph">[סכום]</span>', "אשראי שאושר"),
                ("0 ₪", "עלות הבדיקה")])
            + '</div></div></section>'
            + '<section class="block"><div class="wrap">'
              '<div class="sec-eyebrow">מה אנחנו עושים</div>'
              '<h2>ארבעה סוגי מימון.<br><span class="u">שיטת עבודה אחת.</span></h2>'
              '<div class="grid g2" style="margin-top:24px">' + prods + '</div></div></section>'
            + '<section class="block" style="background:#0A2733;'
              'border-block:1px solid rgba(244,241,234,.12)"><div class="wrap">'
              '<div class="sec-eyebrow">איך זה עובד</div>'
              '<h2>מהשיחה ועד <span class="g">הכסף בחשבון</span></h2>'
              '<div class="steps" style="margin-top:22px">' + steps + '</div></div></section>'
            + cta + foot)
    return page(body, extra_css=MOBILE_CSS)
