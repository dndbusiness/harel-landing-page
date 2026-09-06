# -*- coding: utf-8 -*-
from _common import (page, topbar, footer, icon, wa_icon, logo)

HERO_BG = ("radial-gradient(58% 76% at 84% -6%,rgba(43,182,170,.20),transparent 62%),"
           "radial-gradient(52% 68% at 8% 16%,rgba(201,154,59,.13),transparent 64%),"
           "linear-gradient(180deg,#0A2733 0%,#061A22 78%)")
GRID_OVERLAY = ("repeating-linear-gradient(90deg,rgba(244,241,234,.045) 0 1px,transparent 1px 88px),"
                "repeating-linear-gradient(0deg,rgba(244,241,234,.045) 0 1px,transparent 1px 88px)")

def hero():
    chips = "".join(
        '<span style="display:inline-flex;align-items:center;gap:7px;font-size:.9rem;font-weight:700;'
        'color:rgba(244,241,234,.7)">'
        '<span style="width:19px;height:19px;border-radius:50%%;background:rgba(43,182,170,.18);'
        'display:grid;place-items:center;color:#4FD6C8">'
        '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" '
        'stroke-linecap="round" stroke-linejoin="round" style="width:11px;height:11px">'
        '<path d="M5 12.6 9.4 17 19 7.2"/></svg></span>%s</span>' % t
        for t in ["בדיקת זכאות ללא עלות", "בלי לפגוע בדירוג האשראי", "לא משלמים אם לא לוקחים"])

    form_rows = "".join(
        '<div style="margin-bottom:12px">'
        '<div style="font-size:.82rem;font-weight:700;color:rgba(244,241,234,.7);margin-bottom:6px">%s</div>'
        '<div style="display:flex;align-items:center;justify-content:space-between;background:#061A22;'
        'border:1px solid rgba(244,241,234,.12);border-radius:12px;padding:13px 15px;font-size:.97rem;'
        'color:rgba(244,241,234,.42)">%s%s</div></div>'
        % (lab, val, ('<span style="color:rgba(244,241,234,.42);display:inline-flex;width:14px;height:14px;flex:0 0 auto">'
                      + icon("chev") + '</span>') if caret else "")
        for lab, val, caret in [
            ("מה אתם צריכים לממן?", "משכנתא / מיחזור משכנתא", True),
            ("סכום מבוקש", "250,000 ₪", False),
            ("טלפון לחזרה", "050-0000000", False)])

    return ('<section style="position:relative;overflow:hidden;background:%s">'
            '<div style="position:absolute;inset:0;background:%s;opacity:.55;'
            '-webkit-mask-image:radial-gradient(70%% 70%% at 50%% 10%%,#000,transparent);'
            'mask-image:radial-gradient(70%% 70%% at 50%% 10%%,#000,transparent)"></div>'
            '<div class="wrap" style="position:relative;padding-block:74px 86px">'
            '<div style="display:grid;grid-template-columns:1.08fr .92fr;gap:54px;align-items:center">'

            # --- copy column
            '<div style="display:flex;flex-direction:column;align-items:flex-start;gap:0">'
            '<span class="kicker" style="margin-bottom:22px">%s רישיון מתן אשראי · רשות שוק ההון</span>'
            '<h1 style="font-size:3.3rem;margin-bottom:18px">המימון הנכון קיים.<br>'
            'רק לא תמיד <span class="u">בבנק שלכם</span>.</h1>'
            '<p style="font-size:1.14rem;color:rgba(244,241,234,.78);max-width:520px;margin-bottom:26px">'
            'הר-אל מציגה את התיק שלכם במקביל לבנקים, לגופים החוץ-בנקאיים ולקרנות — '
            'ומביאה את המסלול הזול ביותר שאתם באמת זכאים לו. '
            'משכנתאות, רכב, מימון עסקי והלוואות לכל מטרה.</p>'
            '<div class="cta-row" style="margin-bottom:26px">'
            '<a href="#" class="btn btn-primary">לבדיקת זכאות ללא עלות</a>'
            '<a href="#" class="btn btn-wa">%s לשיחה בוואטסאפ</a></div>'
            '<div style="display:flex;flex-wrap:wrap;gap:10px 22px">%s</div>'
            '</div>'

            # --- eligibility card column
            '<div style="background:linear-gradient(165deg,#103A4A,#0A2733);'
            'border:1px solid rgba(201,154,59,.24);border-radius:22px;padding:28px 26px;'
            'box-shadow:0 34px 80px -34px rgba(0,0,0,.8)">'
            '<div style="display:flex;align-items:center;gap:11px;margin-bottom:6px">'
            '<span class="ic-box ic-gold" style="width:38px;height:38px;border-radius:11px">%s</span>'
            '<h3 style="font-size:1.32rem">בדיקת זכאות ב-60 שניות</h3></div>'
            '<p style="font-size:.92rem;color:rgba(244,241,234,.7);margin-bottom:20px">'
            'ממלאים שלושה שדות — ומקבלים תשובה עקרונית מאיתנו, לא מהמערכת.</p>'
            '%s'
            '<a href="#" class="btn btn-primary" style="width:100%%;margin-top:6px">שלחו לי תשובה עקרונית</a>'
            '<p style="text-align:center;font-size:.8rem;color:rgba(244,241,234,.42);margin-top:13px">'
            'הפרטים נשמרים אצלנו בלבד ואינם מועברים לגורם שלישי ללא אישורכם.</p>'
            '</div>'

            '</div></div></section>'
            % (HERO_BG, GRID_OVERLAY, icon("shield"), wa_icon(), chips, icon("spark"), form_rows))


def trust():
    items = [('<span class="ph">[מס׳]</span>', "משפחות ועסקים שליווינו"),
             ('<span class="ph">[מס׳]</span>', "בנקים וגופים מממנים"),
             ('<span class="ph">[סכום]</span>', "אשראי שאושר ללקוחותינו"),
             ("0 ₪", "עלות בדיקת הזכאות")]
    tr = "".join('<div class="tr"><b>%s</b><span>%s</span></div>' % (b, s) for b, s in items)
    return '<section class="trust"><div class="wrap"><div class="trust-grid">%s</div></div></section>' % tr


def products():
    data = [
        ("house", "משכנתאות",
         "משכנתא ראשונה, מיחזור, הגדלה או איחוד חובות לתוך המשכנתא. אנחנו בונים את תמהיל המסלולים "
         "ומתמחרים אותו מול כל הבנקים במקביל — במקום שתתמקחו לבד מול פקיד אחד."),
        ("car", "הלוואות רכב",
         "רכב חדש מיבואן, יד שנייה או סילוק ליסינג. מימון שמגיע מהגוף המממן ישירות — "
         "בלי הריבית שהסוכנות מגלגלת לתוך מחיר הרכב, ובלי לשעבד את הבית."),
        ("building", "מימון מסחרי לעסקים",
         "הון חוזר, מימון ציוד ורכש, ניכיון צ׳קים וקרן בערבות מדינה. "
         "פתרון שנבנה סביב התזרים האמיתי של העסק — לא סביב התבנית של הבנק."),
        ("wallet", "הלוואות לכל מטרה",
         "שיפוץ, חתונה, לימודים או איחוד הלוואות למקום אחד. "
         "סכום אחד, החזר חודשי אחד, וריבית שאפשר לחיות איתה לאורך כל התקופה."),
    ]
    cards = "".join(
        '<div class="card"><span class="ic-box">%s</span><h3>%s</h3><p>%s</p>'
        '<a href="#" class="card-link">לפרטים על המסלול %s</a></div>' % (icon(ic), t, d, icon("arrow"))
        for ic, t, d in data)
    return ('<section class="block"><div class="wrap">'
            '<div class="sec-eyebrow">מה אנחנו עושים</div>'
            '<h2>ארבעה סוגי מימון. <span class="u">שיטת עבודה אחת.</span></h2>'
            '<p class="intro-p">כל תיק נבדק, נבנה ומוגש באותו סטנדרט — '
            'בין אם מדובר במשכנתא של מיליון שקל או בהלוואה לשיפוץ המטבח.</p>'
            '<div class="grid g2">%s</div></div></section>' % cards)


def why():
    rows = [
        ("users", "אתם לא מתמקחים לבד",
         "הבנק שלכם רואה בקשה אחת ומתמחר אותה כמו שנוח לו. אנחנו מציגים את אותו תיק "
         "לעשרות גופים במקביל — <b>וזה מה שמזיז את הריבית</b>, לא שיחה נוספת עם הפקיד."),
        ("doc", "התיק שלכם מוגש נכון",
         "חלק גדול מהסירובים לא נובעים מהלקוח אלא <b>מהאופן שבו הבקשה הוגשה</b>: "
         "מסמך חסר, הכנסה שלא הוצגה נכון, תזרים שלא הוסבר. אנחנו מסדרים את זה לפני ההגשה."),
        ("key", "אנחנו מכירים את מי שמחליט",
         "עבודה שוטפת מול מנהלות אשראי ומחלקות עסקיות בבנקים המובילים. "
         "כשצריך חריגה מהמדיניות, <b>יש עם מי לדבר</b> — ולא דרך מוקד טלפוני."),
        ("scale", "האינטרס שלנו זהה לשלכם",
         "בדיקת הזכאות לא עולה לכם דבר, ואנחנו מתוגמלים <b>רק אם ההלוואה אושרה ואתם בחרתם לקחת אותה</b>. "
         "אין לנו סיבה לדחוף אתכם למסלול שלא מתאים."),
    ]
    feats = "".join('<div class="feat"><span class="ic">%s</span>'
                    '<div><p style="font-weight:800;margin-bottom:3px">%s</p>'
                    '<p style="color:rgba(244,241,234,.7);font-size:.97rem">%s</p></div></div>'
                    % (icon(ic), t, d) for ic, t, d in rows)
    return ('<section class="block" style="background:#0A2733;border-block:1px solid rgba(244,241,234,.12)">'
            '<div class="wrap">'
            '<div style="display:grid;grid-template-columns:.82fr 1.18fr;gap:52px;align-items:start">'
            '<div>'
            '<div class="sec-eyebrow" style="justify-content:flex-start">למה דרכנו</div>'
            '<h2 style="text-align:start;font-size:2.2rem;margin-bottom:16px">'
            'למה לא פשוט ללכת <span class="u">ישר לבנק</span>?</h2>'
            '<p style="color:rgba(244,241,234,.7);font-size:1.02rem;margin-bottom:22px">'
            'אפשר. רוב האנשים עושים בדיוק את זה — ומקבלים את ההצעה הראשונה שהוצעה להם, '
            'בלי לדעת מה היה אפשר לקבל במקום אחר.</p>'
            '<a href="#" class="btn btn-teal btn-sm">לתהליך העבודה המלא</a>'
            '</div>'
            '<div>%s</div>'
            '</div></div></section>' % feats)


def process():
    steps = [
        ("1", "שיחת אבחון", "רבע שעה בטלפון: מה צריך לממן, איזה החזר חודשי באמת נוח לכם, "
                            "ומה המצב בדוחות ובדירוג האשראי."),
        ("2", "בניית התיק", "אוספים את המסמכים ומרכיבים את הבקשה כך שתתקבל — "
                            "כולל הסבר לכל סעיף שעלול לעורר שאלה."),
        ("3", "מכרז בין הגופים", "התיק יוצא במקביל לגופים הרלוונטיים. "
                                 "משווים את ההצעות שחוזרות — ריבית, עמלות ותנאי פירעון מוקדם."),
        ("4", "חתימה וכסף בחשבון", "עוברים איתכם על התנאים סעיף-סעיף, ורק אחרי שהכול ברור — חותמים."),
    ]
    st = "".join('<div class="step"><span class="n">%s</span><h4>%s</h4><p>%s</p></div>' % s for s in steps)
    return ('<section class="block"><div class="wrap">'
            '<div class="sec-eyebrow">איך זה עובד</div>'
            '<h2>מהשיחה הראשונה <span class="g">ועד הכסף בחשבון</span></h2>'
            '<p class="intro-p">בלי הפתעות באמצע. בכל שלב אתם יודעים איפה התיק עומד ומה השלב הבא.</p>'
            '<div class="steps">%s</div></div></section>' % st)


def team_cards():
    def member(img, name, role, quote, body, tags):
        tg = "".join('<span style="font-size:.82rem;font-weight:700;color:#E7C879;'
                     'border:1px solid rgba(201,154,59,.35);border-radius:999px;padding:5px 13px">%s</span>' % t
                     for t in tags)
        return ('<div style="background:#103A4A;border:1px solid rgba(244,241,234,.12);border-radius:18px;'
                'overflow:hidden;box-shadow:0 20px 44px -22px rgba(0,0,0,.55);display:grid;'
                'grid-template-columns:.72fr 1.28fr">'
                '<div style="position:relative;background:linear-gradient(160deg,#103A4A,#061A22)">'
                '<img src="%s" alt="%s" style="position:absolute;inset:0;width:100%%;height:100%%;'
                'object-fit:cover;object-position:top center"></div>'
                '<div style="padding:26px 24px">'
                '<h3 style="font-size:1.45rem;margin-bottom:3px">%s</h3>'
                '<span style="display:inline-block;font-size:.82rem;font-weight:800;color:#4FD6C8;'
                'margin-bottom:13px">%s</span>'
                '<p style="font-size:1.02rem;color:#E7C879;font-weight:600;border-inline-start:3px solid #C99A3B;'
                'padding-inline-start:12px;margin-bottom:13px;line-height:1.5">%s</p>'
                '<p style="color:rgba(244,241,234,.7);font-size:.96rem;margin-bottom:15px">%s</p>'
                '<div style="display:flex;flex-wrap:wrap;gap:8px">%s</div>'
                '</div></div>' % (img, name, name, role, quote, body, tg))

    return ('<div style="display:flex;flex-direction:column;gap:22px">%s%s</div>'
            % (member("aviv.jpg", "אביב בר", "מייסד שותף · אסטרטגיה פיננסית",
                      "״לפני שמדברים על ריבית, צריך לדעת לאן אתם רוצים להגיע.״",
                      "יועץ עסקי ואסטרטג עם ניסיון רב שנים בליווי עסקים ומשקי בית. "
                      "אביב מתרגם מטרה כלכלית לתוכנית מימון מעשית — כמה באמת צריך ללוות, "
                      "לכמה זמן, ומה ההחזר שלא ישבור לכם את התזרים.",
                      ["תכנון פיננסי", "מבנה החזרים", "ליווי עסקים"]),
               member("dan.jpg", "דן שם טוב", "מייסד שותף · מימון ואשראי",
                      "״יש תמיד יותר מדרך אחת לממן עסקה — צריך רק לדעת לחפש.״",
                      "מומחה מימון עם קשרים עמוקים בעולם הבנקאות והקרנות. "
                      "דן עובד צמוד למנהלות האשראי בבנקים המובילים ומכיר את מדיניות החיתום של כל גוף — "
                      "כולל את המקומות שבהם יש גמישות.",
                      ["מבנה מימון", "משכנתאות", "קשרים בנקאיים", "אשראי עסקי"])))


def team():
    return ('<section class="block" style="background:#0A2733;'
            'border-block:1px solid rgba(244,241,234,.12)"><div class="wrap">'
            '<div class="sec-eyebrow">מי עומד מאחורי זה</div>'
            '<h2>שני מייסדים. <span class="u">שתי התמחויות משלימות.</span></h2>'
            '<p class="intro-p">אחד בונה את האסטרטגיה, השני מביא את הכסף. '
            'התיק שלכם עובר דרך שניהם.</p>%s</div></section>' % team_cards())


def testimonials():
    quotes = [
        ("מיחזרנו משכנתא שישבה עלינו שבע שנים. הפער בין מה שהבנק שלנו הציע לבין מה שהתקבל בסוף "
         "היה כזה שפשוט לא האמנו שזה אותו תיק.", "משפחת ל׳", "מיחזור משכנתא · מרכז"),
        ("הבנק סירב לנו פעמיים על הון חוזר. הר-אל הגישו את אותם נתונים אחרת, "
         "ותוך שבועיים היה אישור. ההבדל היה בהצגה, לא במספרים.", "בעל עסק", "מימון מסחרי · השרון"),
        ("רצינו הלוואה לשיפוץ ויצאנו עם איחוד של שלוש הלוואות ישנות. "
         "ההחזר החודשי ירד, ובפעם הראשונה יש לנו תמונה אחת ברורה.", "א׳ ו-ר׳", "איחוד הלוואות · דרום"),
    ]
    cards = "".join(
        '<div class="card" style="gap:14px">'
        '<div style="display:flex;align-items:center;justify-content:space-between;gap:10px">'
        '<span style="color:rgba(43,182,170,.5);display:inline-flex;width:26px;height:26px;flex:0 0 auto">%s</span>'
        '<span class="tag-sample">טקסט לדוגמה</span></div>'
        '<p style="font-size:1.02rem;color:#F4F1EA;line-height:1.6">%s</p>'
        '<div style="margin-top:auto;padding-top:8px;border-top:1px dashed rgba(244,241,234,.12)">'
        '<div style="font-weight:800;font-size:.98rem">%s</div>'
        '<div style="font-size:.85rem;color:rgba(244,241,234,.42)">%s</div></div></div>'
        % (icon("quote"), q, n, m) for q, n, m in quotes)
    return ('<section class="block"><div class="wrap">'
            '<div class="sec-eyebrow">לקוחות מספרים</div>'
            '<h2>לא הבטחות. <span class="g">תיקים שנסגרו.</span></h2>'
            '<p class="intro-p">שלוש הכרטיסיות הבאות הן טקסט לדוגמה שממחיש את המבנה — '
            'להחלפה בעדויות אמיתיות שתאשרו לפרסום.</p>'
            '<div class="grid g3">%s</div></div></section>' % cards)


def cta():
    fields = "".join(
        '<div class="field"><label>%s <span class="req">*</span></label>'
        '<div class="inp %s">%s%s</div></div>'
        % (lab, "sel" if caret else "", val,
           '<span style="display:inline-flex">' + icon("chev") + '</span>' if caret else "")
        for lab, val, caret in [("שם מלא", "השם שלך", False),
                                ("טלפון נייד", "050-0000000", False),
                                ("מה תרצו לממן?", "בחרו מסלול", True)])
    return ('<section style="position:relative;overflow:hidden;padding-block:66px;'
            'background:radial-gradient(90%% 70%% at 50%% 0,rgba(43,182,170,.14),transparent 60%%),#061A22">'
            '<div class="wrap">'
            '<div class="sec-eyebrow">הצעד הבא</div>'
            '<h2>נבדוק לכם את הזכאות. <span class="u">בלי עלות, בלי התחייבות.</span></h2>'
            '<p class="intro-p">משאירים פרטים, ואנחנו חוזרים אליכם עם תמונה ברורה: '
            'למה אתם זכאים, באיזה גוף, ומה זה אומר בהחזר החודשי.</p>'
            '<div class="form-card">%s'
            '<div class="consent"><span class="box"></span>'
            '<span>מאשר/ת שיצרו איתי קשר בטלפון, בוואטסאפ ובאימייל בנוגע לפנייה זו.</span></div>'
            '<a href="#" class="btn btn-primary">לבדיקת זכאות</a>'
            '<p class="form-note">בדיקת הזכאות אינה כרוכה בתשלום ואינה מחייבת אתכם בדבר.</p>'
            '</div></div></section>' % fields)


def build():
    return page(topbar("Main") + hero() + trust() + products() + why()
                + process() + team() + testimonials() + cta() + footer())
