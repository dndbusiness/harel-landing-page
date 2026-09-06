# עיצוב אתר הר-אל פתרונות מימון חכמים

קנבס העיצוב (Claude Design) של האתר המלא. כל עמוד הוא artboard נפרד.

## הקבצים

| קובץ | תפקיד |
|---|---|
| `_common.py` | מערכת העיצוב: משתני צבע, טיפוגרפיה, אייקוני SVG, כותרת עליונה, פוטר |
| `_blocks.py` | בלוקים חוזרים לעמודים הפנימיים: הירו, טבלה, שלבים, שאלות נפוצות, פס CTA |
| `pages_home.py` | דף הבית |
| `pages_products.py` | משכנתאות · הלוואות רכב · מימון לעסקים · הלוואות לכל מטרה |
| `pages_misc.py` | אודות · צור קשר · תצוגת מובייל |
| `build.py` | כותב את קבצי ה-`.dc.html` ואת `canvas.json` |
| `measure.py` | מודד את הגובה האמיתי של כל עמוד בדפדפן (מזין את `heights.json`) |
| `review.py` | צילומי מסך לבדיקה ויזואלית |
| `wordmark.png`, `chevrons.png` | הלוגו, מופרד מדף הנחיתה הקיים לשם החלפת התגית |
| `aviv.jpg`, `dan.jpg` | תמונות המייסדים |

הפלטה, הפונטים (Heebo + Suez One) והרכיבים נלקחו כמות שהם מ-`index.html` שבשורש
המאגר, כדי שהאתר החדש יישב על אותה שפה עיצובית.

## בנייה מחדש

```bash
cd design
python3 build.py      # כותב את קבצי ה-.dc.html
python3 measure.py    # מודד גבהים (דורש playwright + chromium)
python3 build.py      # כותב מחדש את canvas.json עם הגבהים המדודים

BASE="<תיקיית ה-skill של design>"
node "$BASE/seed-canvas.mjs" --template "$BASE/payload.template.html" \
  --out har-el-financing-site.html --title "אתר הר-אל פתרונות מימון" \
  --artboard Main.dc.html --artboard Mortgage.dc.html --artboard CarLoan.dc.html \
  --artboard Business.dc.html --artboard Personal.dc.html --artboard About.dc.html \
  --artboard Contact.dc.html --artboard MobileHome.dc.html \
  --image wordmark.png --image chevrons.png --image aviv.jpg --image dan.jpg \
  --canvas canvas.json
```

## נתונים שצריך למלא

כל טקסט מודגש בזהב עם קו מקווקו הוא נתון שאין לנו: טלפון, אימייל, שם החברה
הרשומה וח.פ., מספר רישיון מרשות שוק ההון, מספרי לקוחות והיקפי אשראי,
טווחי סכומים, תקופות וריביות, ושעות הפעילות. שלוש עדויות הלקוחות בדף הבית
מסומנות "טקסט לדוגמה" ומיועדות להחלפה בעדויות אמיתיות שאושרו לפרסום.
