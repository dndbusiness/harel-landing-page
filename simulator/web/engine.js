/* oshsim engine — port of the Python package. Money is integer agorot; rates and
   percentages are parsed into scaled integers and accumulated as BigInt, so no
   floating point ever touches an amount. */
const OSH = (() => {
  "use strict";
  // ---------- money ----------
  const MINUS = "-−‒–—";
  const AMOUNT_RE = new RegExp(`^\\s*([${MINUS}])?\\s*₪?\\s*(\\d{1,3}(?:,\\d{3})*|\\d+)(?:\\.(\\d{1,2}))?\\s*₪?\\s*([${MINUS}])?\\s*$`);
  function parseAmount(text) {
    if (text == null) throw new Error("סכום חסר");
    const t = String(text).replace(/[‏‎]/g, "").replace(/\xa0/g, " ").trim();
    const m = AMOUNT_RE.exec(t);
    if (!m) throw new Error(`לא ניתן לפרש סכום: "${text}"`);
    if (m[1] && m[4]) throw new Error(`סימן מינוס כפול: "${text}"`);
    let v = parseInt(m[2].replace(/,/g, ""), 10) * 100 + parseInt((m[3] || "0").padEnd(2, "0"), 10);
    return (m[1] || m[4]) ? -v : v;
  }
  const isAmount = s => { try { parseAmount(s); return true; } catch { return false; } };
  // "12.5" → 125000 (×10^4). Throws on anything but a plain decimal.
  function parseScaled(s, places = 4) {
    const m = /^\s*([+-])?(\d+)(?:\.(\d+))?\s*$/.exec(String(s ?? ""));
    if (!m) throw new Error(`מספר לא חוקי: "${s}"`);
    if ((m[3] || "").length > places) throw new Error(`יותר מ-${places} ספרות אחרי הנקודה: "${s}"`);
    const v = BigInt(m[2]) * 10n ** BigInt(places) + BigInt((m[3] || "").padEnd(places, "0") || "0");
    return m[1] === "-" ? -v : v;
  }
  const fromShekels = s => Number(parseScaled(s, 2));
  // round-half-away-from-zero integer division (Decimal ROUND_HALF_UP)
  function roundDiv(n, d) {
    const neg = (n < 0n) !== (d < 0n);
    n = n < 0n ? -n : n; d = d < 0n ? -d : d;
    const q = (2n * n + d) / (2n * d);
    return neg ? -q : q;
  }
  // magnitude × (1 + pct/100), pct as string
  function scalePct(agorot, pct) {
    const p = parseScaled(pct, 4);               // pct × 10^4
    return Number(roundDiv(BigInt(agorot) * (1000000n + p), 1000000n));
  }
  function fmt(a, sign = true) {
    if (a == null || a === "") return "";
    const neg = a < 0, x = Math.abs(a);
    const s = `${Math.trunc(x / 100).toLocaleString("en-US")}.${String(x % 100).padStart(2, "0")}`;
    return neg && sign ? "-" + s : s;
  }

  // ---------- dates (ISO strings, UTC arithmetic) ----------
  const D = s => new Date(s + "T00:00:00Z");
  const iso = d => d.toISOString().slice(0, 10);
  const addDays = (s, n) => { const d = D(s); d.setUTCDate(d.getUTCDate() + n); return iso(d); };
  const weekday = s => (D(s).getUTCDay() + 6) % 7;   // Mon=0 … Sat=5, Sun=6 (Python convention)
  const FRI = 4, SAT = 5;
  const month = s => s.slice(0, 7);
  const prevMonth = s => month(addDays(s.slice(0, 8) + "01", -1));
  const daysIn = (y, m) => new Date(Date.UTC(y, m, 0)).getUTCDate();
  const nominal = (y, m, dom) => `${y}-${String(m).padStart(2, "0")}-${String(Math.min(dom, daysIn(y, m))).padStart(2, "0")}`;
  const dmy = s => s ? `${s.slice(8, 10)}/${s.slice(5, 7)}/${s.slice(0, 4)}` : "";
  const dmyShort = s => `${s.slice(8, 10)}/${s.slice(5, 7)}/${s.slice(2, 4)}`;
  function parseDate(t) {
    const m = /^(\d{1,2})[/.](\d{1,2})[/.](\d{2}|\d{4})$/.exec(String(t).trim());
    if (!m) throw new Error(`תאריך לא חוקי: "${t}"`);
    let y = +m[3]; if (y < 100) y += 2000;
    return `${y}-${m[2].padStart(2, "0")}-${m[1].padStart(2, "0")}`;
  }
  const isDate = t => /^(\d{1,2})[/.](\d{1,2})[/.](\d{2}|\d{4})$/.test(String(t || "").trim());

  // ---------- calendar ----------
  class Calendar {
    constructor(holidays, fridayBusiness = false, extra = []) {
      this.hol = Object.assign({}, holidays); for (const d of extra) this.hol[d] = "סגירה (הגדרות)";
      this.fri = fridayBusiness;
    }
    isClosed(d) { return weekday(d) === SAT || d in this.hol; }
    isBusiness(d) { return !this.isClosed(d) && (this.fri || weekday(d) !== FRI); }
    firstBusiness(y, m) { let d = nominal(y, m, 1); while (!this.isBusiness(d)) d = addDays(d, 1); return d; }
    move(d, dir) { const s = dir === "forward" ? 1 : -1; d = addDays(d, s); while (!this.isBusiness(d)) d = addDays(d, s); return d; }
    shift(nom, fri, closed) {
      if (weekday(nom) === FRI && !this.isClosed(nom)) return fri === "same" ? nom : this.move(nom, fri);
      return this.isClosed(nom) ? this.move(nom, closed) : nom;
    }
  }

  // ---------- Hebrew visual order ----------
  const HEB = /[֐-׿]/;
  const LTR_RUN = /[0-9A-Za-z](?:[0-9A-Za-z.,/:%\-]*[0-9A-Za-z])?/g;
  const MIRROR = { "(": ")", ")": "(", "[": "]", "]": "[", "{": "}", "}": "{", "<": ">", ">": "<" };
  function visualToLogical(s) {
    if (!HEB.test(s || "")) return s;
    const rev = [...s].reverse().map(c => MIRROR[c] || c).join("");
    return rev.replace(LTR_RUN, r => [...r].reverse().join(""));
  }
  const norm = s => String(s).replace(/[‏‎]/g, "").replace(/\xa0/g, " ").replace(/\s+/g, " ").trim();
  function splitChannel(desc) {
    const m = /\(([יפ])\)/.exec(desc);
    if (!m) return [desc.trim(), null];
    return [norm(desc.slice(0, m.index) + desc.slice(m.index + m[0].length)), m[1] === "י" ? "direct" : "banker"];
  }

  // ---------- transactions ----------
  // הדף: ימים מהחדש לישן, בתוך יום בסדר הדף עם היתרה בשורה האחרונה. הופכים רק את סדר הימים.
  function chronological(txns) {
    const days = new Map(); for (const t of txns) { if (!days.has(t.date)) days.set(t.date, []); days.get(t.date).push(t); }
    return [...days.keys()].reverse().flatMap(d => days.get(d));
  }
  function finalize(txns) {
    const seen = {};
    for (const t of txns) {
      const k = [t.date, t.desc, t.amt, t.ref].join("|");
      t.occ = seen[k] || 0; seen[k] = t.occ + 1;
      t.id = [t.date, t.desc, t.amt, t.ref, t.occ].join("|");
    }
    return txns;
  }
  function makeTxn(o) {
    return Object.assign({ ref: "", bal: null, ch: null, cat: "", sub: "", cp: "", kind: "", rid: null,
                           src: "", page: null, raw: "", vdate: null }, o);
  }

  // ---------- CSV ----------
  function parseCSVText(text) {
    const rows = []; let row = [], cur = "", q = false;
    for (let i = 0; i < text.length; i++) {
      const c = text[i];
      if (q) { if (c === '"') { if (text[i + 1] === '"') { cur += '"'; i++; } else q = false; } else cur += c; }
      else if (c === '"') q = true;
      else if (c === ",") { row.push(cur); cur = ""; }
      else if (c === "\n" || c === "\r") { if (c === "\r" && text[i + 1] === "\n") i++; row.push(cur); rows.push(row); row = []; cur = ""; }
      else cur += c;
    }
    if (cur || row.length) { row.push(cur); rows.push(row); }
    return rows.filter(r => r.some(x => x.trim()));
  }
  function parseCSV(text, src) {
    const rows = parseCSVText(text.replace(/^﻿/, ""));
    const head = rows[0].map(h => h.trim());
    const col = n => head.indexOf(n);
    for (const n of ["date", "description", "amount"]) if (col(n) < 0) throw new Error(`${src}: חסרה עמודה ${n}`);
    const txns = rows.slice(1).map((r, i) => {
      const get = n => col(n) >= 0 ? (r[col(n)] || "").trim() : "";
      try {
        const [desc, ch0] = splitChannel(get("description"));
        const ch = get("channel") || ch0;
        if (ch && ch !== "direct" && ch !== "banker") throw new Error(`channel לא חוקי: ${ch}`);
        return makeTxn({ date: parseDate(get("date")), vdate: isDate(get("value_date")) ? parseDate(get("value_date")) : null,
          desc, amt: parseAmount(get("amount")), bal: get("balance") ? parseAmount(get("balance")) : null,
          ref: get("reference"), ch: ch || null, src, raw: r.join(",") });
      } catch (e) { throw new Error(`${src} שורה ${i + 2}: ${e.message}`); }
    });
    if (!txns.length) throw new Error(`${src}: קובץ ריק`);
    return { src, txns: finalize(txns[0].date > txns[txns.length - 1].date ? chronological(txns) : txns) };
  }

  // ---------- PDF (Mizrahi-Tefahot "עובר ושב") ----------
  const HEADER_ALIASES = {
    date: ["תאריך"], value_date: ["תאריך ערך", "ערך"], description: ["סוג תנועה", "תיאור", "פירוט"],
    amount: ["זכות/חובה", "זכות / חובה", "חובה/זכות", "סכום"], balance: ["יתרה", 'יתרה בש"ח'],
    reference: ["אסמכתה", "אסמכתא"],
  };
  const ROW_TOL = 3;
  function rowsOf(words) {
    const rows = [];
    for (const w of [...words].sort((a, b) => a.top - b.top || a.x0 - b.x0)) {
      if (rows.length && Math.abs(rows[rows.length - 1][0].top - w.top) <= ROW_TOL) rows[rows.length - 1].push(w);
      else rows.push([w]);
    }
    return rows;
  }
  const xc = w => (w.x0 + w.x1) / 2;
  const lineText = (row, rev) => norm([...row].sort((a, b) => xc(b) - xc(a)).map(w => rev ? visualToLogical(w.text) : w.text).join(" "));
  function columnCenters(row, rev) {
    const ordered = [...row].sort((a, b) => xc(b) - xc(a));
    const texts = ordered.map(w => rev ? visualToLogical(w.text) : w.text);
    const centers = {}, used = new Set();
    const pairs = Object.entries(HEADER_ALIASES).flatMap(([c, al]) => al.map(a => [c, a])).sort((a, b) => b[1].length - a[1].length);
    for (const [c, alias] of pairs) {
      if (c in centers) continue;
      const tok = alias.split(" ");
      for (let i = 0; i + tok.length <= texts.length; i++) {
        const span = tok.map((_, k) => i + k);
        if (tok.every((t, k) => texts[i + k] === t) && span.every(k => !used.has(k))) {
          centers[c] = span.reduce((s, k) => s + xc(ordered[k]), 0) / span.length; span.forEach(k => used.add(k)); break;
        }
      }
    }
    return centers;
  }
  function detectHeader(rows) {
    for (const rev of [false, true]) for (let i = 0; i < rows.length; i++) {
      const line = lineText(rows[i], rev);
      const found = Object.keys(HEADER_ALIASES).filter(c => HEADER_ALIASES[c].some(a => line.includes(a)));
      if (["date", "description", "amount", "balance"].every(c => found.includes(c))) return { i, centers: columnCenters(rows[i], rev), rev };
    }
    return null;
  }
  // pages: [{page, words:[{text,x0,x1,top}]}]
  function parsePdfWords(pages, src) {
    const disp = []; let centers = null, rev = false;
    for (const { page, words } of pages) {
      let rows = rowsOf(words);
      const h = detectHeader(rows);
      if (h) { centers = h.centers; rev = h.rev; rows = rows.slice(h.i + 1); }
      else if (!centers) continue;
      for (const row of rows) {
        const cells = {};
        for (const w of row) {
          const c = Object.keys(centers).reduce((a, b) => Math.abs(centers[a] - xc(w)) <= Math.abs(centers[b] - xc(w)) ? a : b);
          (cells[c] = cells[c] || []).push(w);
        }
        const text = {}; for (const c in cells) text[c] = lineText(cells[c], rev);
        const raw = lineText(row, rev);
        if (isDate(text.date || "")) disp.push({ cells: text, page, raw });
        else if (disp.length && text.description && !text.amount) {
          const last = disp[disp.length - 1];
          last.cells.description = norm((last.cells.description || "") + " " + text.description); last.raw += " | " + raw;
        }
      }
    }
    if (!disp.length) throw new Error(`${src}: לא נמצאה טבלת תנועות. ייתכן שהפריסה שונה מדף מזרחי טפחות.`);
    const txns = disp.map(r => {
      const c = r.cells, where = `עמוד ${r.page}: `;
      let amt; try { amt = parseAmount(c.amount || ""); } catch (e) { throw new Error(where + e.message + " | שורה: " + r.raw); }
      const bt = c.balance || ""; let bal = null;
      if (bt) { if (!isAmount(bt)) throw new Error(`${where}יתרה לא חוקית "${bt}" | שורה: ${r.raw}`); bal = parseAmount(bt); }
      const [desc, ch] = splitChannel(c.description || "");
      const ref = (c.reference || "").replace(/\s+/g, "");
      if (HEB.test(ref)) throw new Error(`${where}אסמכתה לא צפויה "${ref}" | שורה: ${r.raw}`);
      return makeTxn({ date: parseDate(c.date), vdate: isDate(c.value_date || "") ? parseDate(c.value_date) : null,
        desc, amt, bal, ref, ch, src, page: r.page, raw: r.raw });
    });
    return { src, txns: finalize(chronological(txns)) };
  }

  // ---------- merge & validate ----------
  function merge(statements) {
    statements = [...statements].sort((a, b) => a.txns[0].date.localeCompare(b.txns[0].date));
    const byKey = new Map(), issues = [], dayBal = {}; let dropped = 0;
    for (const st of statements) for (const t of st.txns) {
      if (byKey.has(t.id)) { dropped++; const p = byKey.get(t.id); if (p.bal == null && t.bal != null) p.bal = t.bal; continue; }
      byKey.set(t.id, t);
      if (t.bal != null) {
        if (t.date in dayBal && dayBal[t.date][0] !== t.bal) issues.push(`${dmy(t.date)}: יתרת סוף יום שונה בין ${dayBal[t.date][1]} ל-${st.src}`);
        if (!(t.date in dayBal)) dayBal[t.date] = [t.bal, st.src];
      }
    }
    const order = [...byKey.values()];
    const pos = new Map(order.map((t, i) => [t, i]));
    return { txns: order.sort((a, b) => a.date.localeCompare(b.date) || pos.get(a) - pos.get(b)), issues, dropped };
  }
  function validate(txns) {
    const days = new Map(); for (const t of txns) { if (!days.has(t.date)) days.set(t.date, []); days.get(t.date).push(t); }
    const bal = {}, errors = [], gaps = [], log = [];
    for (const t of txns) if (t.bal != null) {
      if (t.date in bal && bal[t.date] !== t.bal) errors.push(`${dmy(t.date)}: שתי יתרות שונות באותו יום`);
      if (!(t.date in bal)) bal[t.date] = t.bal;
    }
    const rep = { opening: null, closing: null, daysChecked: 0, gaps, errors, log };
    const dk = [...days.keys()];
    if (!Object.keys(bal).length) { errors.push("אין אף יתרה בדף — אי אפשר לאמת"); rep.ok = false; return rep; }
    const first = dk.find(d => d in bal);
    const upto = txns.filter(t => t.date <= first).reduce((s, t) => s + t.amt, 0);
    rep.opening = bal[first] - upto;
    log.push(`פתיחה נגזרה מ-${dmy(first)}: ${fmt(bal[first])} − (${fmt(upto)})`);
    let run = rep.opening;
    for (const d of dk) {
      run += days.get(d).reduce((s, t) => s + t.amt, 0);
      if (d in bal) { rep.daysChecked++; if (bal[d] !== run) { gaps.push({ day: d, expected: run, actual: bal[d], diff: bal[d] - run }); run = bal[d]; } }
    }
    if (!(dk[dk.length - 1] in bal)) errors.push(`היום האחרון בדף (${dmy(dk[dk.length - 1])}) בלי יתרה — אין סכום ביקורת לסוף התקופה`);
    rep.closing = run; rep.ok = !gaps.length && !errors.length;
    return rep;
  }

  // ---------- categorize ----------
  const cpKey = s => s.replace(/[\d.,/\\\-:#()"']+/g, " ").replace(/\s+/g, " ").trim();
  function compileRules(rules) {
    return rules.map(r => ({ ...r, _d: r.description ? new RegExp(r.description) : null, _r: r.reference ? new RegExp(r.reference) : null,
      _min: r.min != null ? fromShekels(String(r.min)) : null, _max: r.max != null ? fromShekels(String(r.max)) : null,
      direction: r.direction || "any", priority: r.priority || 0 })).sort((a, b) => b.priority - a.priority);
  }
  function ruleMatch(r, t) {
    if (r._d && !r._d.test(t.desc)) return false;
    if (r._r && !r._r.test(t.ref || "")) return false;
    const a = Math.abs(t.amt);
    if (r._min != null && a < r._min) return false;
    if (r._max != null && a > r._max) return false;
    if (r.direction === "credit" && t.amt <= 0) return false;
    if (r.direction === "debit" && t.amt >= 0) return false;
    return true;
  }
  const UNCAT = "לא מסווג";
  function categorize(txns, rules) {
    const queue = []; let matched = 0;
    for (const t of txns) {
      t.cp = cpKey(t.desc);
      const r = rules.find(r => ruleMatch(r, t));
      if (r) { t.cat = r.category; t.sub = r.subcategory || ""; t.kind = r.kind || ""; matched++; }
      else { t.cat = UNCAT; t.sub = ""; t.kind = ""; }
    }
    const done = txns.filter(t => t.cat !== UNCAT);
    for (const t of txns) if (t.cat === UNCAT) queue.push({ t, ...suggest(t, done) });
    return { queue, matched };
  }
  function suggest(t, done) {
    const w = new Set(cpKey(t.desc).split(" ").filter(Boolean)); let best = null, bn = 0, bd = 1;
    for (const c of done) {
      const cw = new Set(cpKey(c.desc).split(" ").filter(Boolean));
      if (!cw.size || !w.size) continue;
      const inter = [...w].filter(x => cw.has(x)).length, uni = new Set([...w, ...cw]).size;
      if (inter * bd > bn * uni) { best = c; bn = inter; bd = uni; }
    }
    if (!best || 3 * bn < bd) return { cat: UNCAT, sub: "", why: "אין תנועה דומה מסווגת" };
    return { cat: best.cat, sub: best.sub, why: `דומה ל-"${best.desc}"` };
  }
  const esc = s => s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  function ruleFromApproval(t, cat, sub) {
    const key = cpKey(t.desc);
    return { id: "client-" + Date.now(), category: cat, subcategory: sub || "", priority: 1000,
      description: key ? key.split(" ").map(esc).join("[\\d\\s.,/\\\\\\-:#()\"']*") : null,
      direction: t.amt > 0 ? "credit" : "debit", source: "אישור יועץ" };
  }

  // ---------- recurring patterns ----------
  const KIND_HE = { fixed: "קבוע", drifting: "נע", variable: "משתנה", one_off: "חד-פעמי" };
  function classify(amounts, months, count) {
    if (count === 1) return "one_off";
    if (months < 2 || 2 * count > 3 * months) return "variable";
    if (new Set(amounts).size === 1) return "fixed";
    // drift: every month-to-month step within 3%  ⇔  100·|b−a| ≤ 3·|a|
    const ok = amounts.slice(1).every((b, i) => amounts[i] && 100 * Math.abs(b - amounts[i]) <= 3 * Math.abs(amounts[i]));
    return ok ? "drifting" : "variable";
  }
  function detect(txns, cal) {
    const groups = new Map();
    for (const t of txns) {
      if (t.kind === "direct_channel_fee" || t.kind === "interest") continue;
      const k = (t.cp || t.desc) + "\u0001" + (t.amt > 0 ? "credit" : "debit");
      if (!groups.has(k)) groups.set(k, []); groups.get(k).push(t);
    }
    const pats = []; let n = 0;
    for (const [k, ts] of [...groups.entries()].sort((a, b) => a[0].localeCompare(b[0]))) {
      const [cp, dir] = k.split("\u0001");
      ts.sort((a, b) => a.date.localeCompare(b.date));
      const byM = {}; for (const t of ts) byM[month(t.date)] = (byM[month(t.date)] || 0) + t.amt;
      const ms = Object.keys(byM).sort(), monthly = ms.map(m => byM[m]);
      const kind = classify(monthly, ms.length, ts.length);
      const normal = ts.filter(t => cal.isBusiness(t.date)).map(t => +t.date.slice(8));
      const pool = normal.length ? normal : ts.map(t => +t.date.slice(8));
      const cnt = {}; pool.forEach(x => cnt[x] = (cnt[x] || 0) + 1);
      const dom = +Object.keys(cnt).sort((a, b) => cnt[b] - cnt[a] || pool.indexOf(+a) - pool.indexOf(+b))[0];
      const ev = {};
      if (kind === "fixed" || kind === "drifting") for (const t of ts) {
        const nom = nominal(+t.date.slice(0, 4), +t.date.slice(5, 7), dom);
        if (weekday(nom) === FRI && !cal.isClosed(nom)) { const r = "friday_" + (t.date === nom ? "same" : t.date > nom ? "forward" : "back"); ev[r] = (ev[r] || 0) + 1; }
        else if (cal.isClosed(nom)) { const r = "closed_" + (t.date > nom ? "forward" : "back"); ev[r] = (ev[r] || 0) + 1; }
      }
      const fr = ["same", "forward", "back"].reduce((a, b) => (ev["friday_" + b] || 0) > (ev["friday_" + a] || 0) ? b : a);
      const cr = ["forward", "back"].reduce((a, b) => (ev["closed_" + b] || 0) > (ev["closed_" + a] || 0) ? b : a);
      const sorted = [...monthly].sort((a, b) => a - b), mid = sorted.length >> 1;
      const median = sorted.length % 2 ? sorted[mid] : Math.trunc((sorted[mid - 1] + sorted[mid]) / 2);
      const chCnt = {}; ts.forEach(t => chCnt[t.ch] = (chCnt[t.ch] || 0) + 1);
      const catCnt = {}; ts.forEach(t => catCnt[t.cat] = (catCnt[t.cat] || 0) + 1);
      const p = { id: `R${String(++n).padStart(3, "0")}`, cp, dir, kind, dom, byMonth: byM, typical: median,
        ch: Object.keys(chCnt).sort((a, b) => chCnt[b] - chCnt[a])[0], cat: Object.keys(catCnt).sort((a, b) => catCnt[b] - catCnt[a])[0],
        fri: ev["friday_" + fr] ? fr : "same", closed: ev["closed_" + cr] ? cr : "forward", learned: Object.keys(ev).length > 0, ev };
      if (p.ch === "null") p.ch = null;
      if (kind !== "one_off") ts.forEach(t => t.rid = p.id);
      pats.push(p);
    }
    return pats;
  }
  function amountFor(p, m) {
    if (m in p.byMonth) return p.byMonth[m];
    if (p.kind === "variable") return p.typical;
    const prior = Object.keys(p.byMonth).sort().filter(x => x <= m);
    return prior.length ? p.byMonth[prior[prior.length - 1]] : p.typical;
  }

  // ---------- params ----------
  function makeParams({ feeRate, freeQuota, rates, limit, overlimit, dayCount }) {
    const P = { fee: null, rates: [], limit: null, dayCount: dayCount || 365 };
    if (feeRate !== "" && feeRate != null) P.fee = { rate: fromShekels(feeRate), free: parseInt(freeQuota || 0, 10) };
    for (const r of rates || []) if (r.debit !== "" && r.debit != null)
      P.rates.push({ from: r.from, debit: parseScaled(r.debit), credit: parseScaled(r.credit || "0"),
                     over: r.over ? parseScaled(r.over) : null });
    P.rates.sort((a, b) => a.from.localeCompare(b.from));
    if (limit !== "" && limit != null) P.limit = fromShekels(limit);
    return P;
  }
  const feeOf = (P, n) => Math.max(0, n - P.fee.free) * P.fee.rate;
  function rateOn(table, d) { let cur = null; for (const r of table) if (r.from <= d) cur = r; return cur; }
  // one day's interest as a BigInt numerator over DEN(P)
  const DEN = P => BigInt(100 * 10000 * P.dayCount);
  function dailyNum(P, table, bal, d) {
    const r = rateOn(table, d); if (!r || bal === 0) return 0n;
    const b = BigInt(bal);
    if (bal > 0) return b * r.credit;
    if (P.limit != null && r.over != null && -bal > P.limit) return BigInt(-P.limit) * r.debit + BigInt(bal + P.limit) * r.over;
    return b * r.debit;
  }

  // ---------- deltas ----------
  function selMatch(s, r) {
    if (r.kind === "direct_channel_fee" || r.kind === "interest") return false;
    if (s.category && r.cat !== s.category) return false;
    if (s.subcategory && r.sub !== s.subcategory) return false;
    if (s.description && !new RegExp(s.description).test(r.desc)) return false;
    if (s.rid && r.rid !== s.rid) return false;
    if (s.direction === "credit" && r.amt <= 0) return false;
    if (s.direction === "debit" && r.amt >= 0) return false;
    return true;
  }
  const inRange = (d, s, e) => (!s || d >= s) && (!e || d <= e);
  const selText = s => [s.category && `קטגוריה "${s.category}"`, s.subcategory && `"${s.subcategory}"`,
    s.description && `תיאור "${s.description}"`, s.ridLabel && `"${s.ridLabel}"`].filter(Boolean).join(" ") || "כל התנועות";
  function applyDelta(dl, rows, ctx) {
    const label = dl.label || dl.type;
    if (dl.type === "change") {
      let hit = 0, card = 0;
      const out = rows.map(r => {
        if (r.origin === "removed" || !selMatch(dl.select, r) || !inRange(r.date, dl.start, dl.end)) return r;
        const sign = r.amt >= 0 ? 1 : -1, mag = Math.abs(r.amt);
        let nm = dl.setTo != null && dl.setTo !== "" ? Math.abs(fromShekels(dl.setTo))
          : dl.pct != null && dl.pct !== "" ? scalePct(mag, dl.pct) : mag + fromShekels(dl.amount);
        nm = Math.max(0, nm); hit++; if (r.kind === "card_charge") card++;
        return { ...r, amt: sign * nm, origin: "modified", base: r.base ?? r.amt, note: label };
      });
      if (card) ctx.notes.push(`${label}: ${card} חיובי כרטיס אשראי שונו כסכום כולל. זה לא שינוי בקטגוריית הוצאה, כי אין דף אשראי מקושר שמפרק את החיוב`);
      if (!hit) ctx.notes.push(`אזהרה — ${label}: אין תנועות שמתאימות ל-${selText(dl.select)}`);
      return out;
    }
    if (dl.type === "remove") {
      let hit = 0;
      const out = rows.map(r => {
        if (r.origin === "removed" || !selMatch(dl.select, r) || !inRange(r.date, dl.start, dl.end)) return r;
        hit++; return { ...r, origin: "removed", base: r.amt, amt: 0, note: label };
      });
      if (!hit) ctx.notes.push(`אזהרה — ${label}: אין תנועות לביטול (${selText(dl.select)})`);
      return out;
    }
    if (dl.type === "add") {
      const s = dl.start && dl.start > ctx.start ? dl.start : ctx.start, e = dl.end && dl.end < ctx.end ? dl.end : ctx.end;
      const out = [...rows]; let y = +s.slice(0, 4), m = +s.slice(5, 7);
      while (nominal(y, m, 1) <= e) {
        const d = ctx.cal.shift(nominal(y, m, +dl.dom), dl.fri || "same", dl.closed || "forward");
        if (d >= s && d <= e) out.push(row(d, dl.description, fromShekels(dl.amount), dl.ch || null, "added", { cat: dl.category || "", note: label }));
        m++; if (m > 12) { m = 1; y++; }
      }
      return out;
    }
    if (dl.type === "oneoff") {
      if (dl.date < ctx.start || dl.date > ctx.end) { ctx.notes.push(`אזהרה — ${label}: התאריך ${dmy(dl.date)} מחוץ לטווח הסימולציה`); return rows; }
      return [...rows, row(dl.date, dl.description, fromShekels(dl.amount), dl.ch || null, "added", { note: label })];
    }
    if (dl.type === "loan") {
      if (!dl.schedule.length && !dl.payoff) throw new Error(`${label}: נדרש לוח סילוקין מהלקוח או סכום פירעון`);
      const out = applyDelta({ type: "remove", select: dl.select, start: dl.start, label }, rows, ctx);
      if (dl.payoff) out.push(row(dl.start, "פירעון מוקדם (תרחיש)", -Math.abs(fromShekels(dl.payoff)), null, "added", { cat: "הלוואות", note: label }));
      for (const [d, a] of dl.schedule) if (d >= ctx.start && d <= ctx.end) out.push(row(d, "החזר הלוואה (תרחיש)", -Math.abs(a), null, "added", { cat: "הלוואות", note: label }));
      return out;
    }
    if (dl.type === "rate") return rows;
    throw new Error("סוג שינוי לא מוכר: " + dl.type);
  }
  function row(date, desc, amt, ch, origin, extra = {}) {
    return Object.assign({ date, desc, amt, ch, origin, ref: "", cat: "", sub: "", kind: "", tid: "", rid: null, base: null, note: "", seq: 1e9 }, extra);
  }

  // ---------- engine ----------
  class Engine {
    constructor(txns, opening, P, cal, patterns) {
      this.txns = txns; this.opening = opening; this.P = P; this.cal = cal; this.patterns = patterns || [];
      this.hist = txns.map((t, i) => row(t.date, t.desc, t.amt, t.ch, "historical",
        { ref: t.ref, cat: t.cat, sub: t.sub, kind: t.kind, tid: t.id, rid: t.rid, seq: i }));
      this.first = txns[0].date; this.last = txns[txns.length - 1].date;
      this.histCounts = Engine.counts(this.hist);
      this.histBal = this.balances(this.hist, this.first, this.last);
    }
    static counts(rows) {
      const c = {}; for (const r of rows) if (r.origin !== "removed" && r.ch === "direct" && r.kind !== "direct_channel_fee" && r.kind !== "interest") c[month(r.date)] = (c[month(r.date)] || 0) + 1;
      return c;
    }
    balances(rows, s, e) {
      const by = {}; for (const r of rows) by[r.date] = (by[r.date] || 0) + r.amt;
      const out = {}; let b = this.opening;
      for (let d = s; d <= e; d = addDays(d, 1)) { b += by[d] || 0; out[d] = b; }
      return out;
    }
    feeCalibration() {
      return this.hist.filter(r => r.kind === "direct_channel_fee").map(r => {
        const m = prevMonth(r.date), ref = /^\d+$/.test(r.ref.trim()) ? +r.ref : null;
        const total = ref ?? (this.histCounts[m] || 0);
        return { date: r.date, month: m, observed: this.histCounts[m] || 0, ref, model: this.P.fee ? -feeOf(this.P, total) : null, actual: r.amt };
      });
    }
    interestCalibration() {
      if (!this.P.rates.length) return [];
      const out = []; let prev = null;
      for (const r of this.hist) if (r.kind === "interest") {
        const start = prev || this.first; let acc = 0n;
        for (let d = start; d < r.date; d = addDays(d, 1)) acc += dailyNum(this.P, this.P.rates, this.histBal[d], d);
        const model = Number(roundDiv(acc, DEN(this.P)));
        const err = r.amt ? Number(roundDiv(BigInt(model - r.amt) * 1000n, BigInt(Math.abs(r.amt)))) : null;   // ‰
        out.push({ date: r.date, start, end: addDays(r.date, -1), model, actual: r.amt, partial: prev == null, errPermille: err });
        prev = r.date;
      }
      return out;
    }
    project(s, e) {
      const out = []; let y = +s.slice(0, 4), m = +s.slice(5, 7);
      while (nominal(y, m, 1) <= e) {
        const mm = `${y}-${String(m).padStart(2, "0")}`;
        for (const p of this.patterns) {
          if (p.kind === "one_off") continue;
          const d = this.cal.shift(nominal(y, m, p.dom), p.fri, p.closed);
          if (d >= s && d <= e) out.push(row(d, p.cp, amountFor(p, mm), p.ch, "projected", { cat: p.cat, rid: p.id, note: p.kind === "variable" ? "הערכה (סכום חציוני)" : "הערכה" }));
        }
        const fd = this.cal.firstBusiness(y, m);
        if (this.P.fee && fd >= s && fd <= e) out.push(row(fd, "עמלת פעולות בערוץ ישיר (הערכה)", 0, null, "fee", { kind: "direct_channel_fee", cat: "עמלות וריבית", note: "לפי פעולות (י) בחודש הקודם" }));
        if (this.P.rates.length && [1, 4, 7, 10].includes(m) && fd >= s && fd <= e) out.push(row(fd, "ריבית (הערכה)", 0, null, "interest", { kind: "interest", cat: "עמלות וריבית", note: "מודל ריבית (הערכה)" }));
        m++; if (m > 12) { m = 1; y++; }
      }
      return out;
    }
    run(sc) {
      let start = this.first, end = this.last, projFrom = null;
      const notes = [];
      let rows = this.hist.map(r => ({ ...r }));
      if (sc.mode === "forward") {
        projFrom = addDays(this.last, 1);
        let y = +this.last.slice(0, 4), m = +this.last.slice(5, 7) + (sc.months || 3);
        while (m > 12) { m -= 12; y++; }
        end = nominal(y, m, 31);
        rows = rows.concat(this.project(projFrom, end));
        notes.push(`מ-${dmy(projFrom)} התנועות הן הקרנה לפי דפוסים, והן הערכה בלבד`);
        if (!this.P.rates.length) notes.push("לא הוזן שיעור ריבית, ולכן בהקרנה אין חיובי ריבית");
      }
      const ctx = { cal: this.cal, start, end, notes };
      let table = this.P.rates;
      for (const dl of sc.deltas || []) {
        rows = applyDelta(dl, rows, ctx);
        if (dl.type === "rate") {
          if (!this.P.rates.length) throw new Error("שינוי ריבית דורש שיעור בסיס בפרמטרים, אחרת אין מול מה להשוות");
          table = dl.rates;
        }
      }
      const recompute = this.P.rates.length > 0;
      if (!recompute && (sc.deltas || []).length) notes.push('לא הוזן שיעור ריבית: ריבית העו"ש נשארה כפי שנרשמה בפועל ולא הותאמה לשינוי ביתרה');
      if (!this.P.fee && (sc.deltas || []).length) notes.push("לא הוגדרה עמלת ערוץ ישיר: העמלה נשארה כפי שנרשמה בפועל");
      const counts = Engine.counts(rows);
      const removed = rows.filter(r => r.origin === "removed");
      const live = rows.filter(r => r.origin !== "removed").sort((a, b) => a.date.localeCompare(b.date) || (a.tid ? 0 : 1) - (b.tid ? 0 : 1) || a.seq - b.seq);
      const by = {}; for (const r of live) (by[r.date] = by[r.date] || []).push(r);
      const days = [], daily = {}; let bal = this.opening, accRun = 0n, accHist = 0n; const den = DEN(this.P);
      for (let d = start; d <= end; d = addDays(d, 1)) {
        const today = [];
        for (let r of by[d] || []) {
          if (r.kind === "direct_channel_fee" && this.P.fee) {
            if (r.origin === "historical") {
              const m = prevMonth(r.date), base = /^\d+$/.test(r.ref.trim()) ? +r.ref : (this.histCounts[m] || 0);
              const runTotal = base + (counts[m] || 0) - (this.histCounts[m] || 0);
              const diff = feeOf(this.P, runTotal) - feeOf(this.P, base);
              if (diff) r = { ...r, origin: "modified", base: r.amt, amt: r.amt - diff, ref: String(runTotal), note: `עמלה חושבה מחדש: ${runTotal} פעולות (י)` };
            } else { const n = counts[prevMonth(d)] || 0; r = { ...r, amt: -feeOf(this.P, n), ref: String(n) }; }
          } else if (r.kind === "interest" && recompute) {
            if (r.origin === "historical") {
              const diff = Number(roundDiv(accRun - accHist, den));
              if (diff) r = { ...r, origin: "modified", base: r.amt, amt: r.amt + diff, note: "ריבית הותאמה לשינוי ביתרה או בשיעור" };
            } else r = { ...r, amt: Number(roundDiv(accRun, den)) };
            accRun = 0n; accHist = 0n;
          }
          today.push(r);
        }
        bal += today.reduce((s, r) => s + r.amt, 0); daily[d] = bal;
        if (recompute) {
          accRun += dailyNum(this.P, table, bal, d);
          if (d in this.histBal) accHist += dailyNum(this.P, this.P.rates, this.histBal[d], d);
        }
        if (today.length) days.push({ date: d, rows: today, bal });
      }
      const res = { name: sc.name, mode: sc.mode || "replay", opening: this.opening, days, daily, start, end, projFrom, notes, removed,
        recompute, feeCal: this.feeCalibration(), intCal: this.interestCalibration(), unposted: recompute ? Number(roundDiv(accRun, den)) : 0 };
      const full = res.intCal.filter(c => !c.partial && c.errPermille != null);
      res.estimate = !recompute || !full.length || full.some(c => Math.abs(c.errPermille) > (this.P.maxErrPermille ?? 50));
      return res;
    }
  }
  // ---------- balance audit (port of validate/audit.py) ----------
  function auditKeys(txns) {
    const seen = {};
    return txns.map(t => { const k = [t.date, t.desc, t.ref].join("|"); const n = seen[k] || 0; seen[k] = n + 1; return k + "|" + n; });
  }
  function derivedOpening(txns) {
    const first = txns.find(t => t.bal != null);
    return first.bal - txns.filter(t => t.date <= first.date).reduce((s, t) => s + t.amt, 0);
  }
  function audit(txns, original) {
    const opening = derivedOpening(original || txns);
    const origBy = new Map(), origDay = {};
    if (original) { auditKeys(original).forEach((k, i) => origBy.set(k, original[i])); original.forEach(t => { if (t.bal != null) origDay[t.date] = t.bal; }); }
    let run = opening;
    const keys = auditKeys(txns);
    const rows = txns.map((t, i) => {
      run += t.amt;
      const o = original ? origBy.get(keys[i]) : null; if (o) origBy.delete(keys[i]);
      const status = !original ? "same" : !o ? "added" : o.amt !== t.amt ? "changed" : "same";
      return { date: t.date, desc: t.desc, ch: t.ch, ref: t.ref, amt: t.amt, run, stated: t.bal, origAmt: o ? o.amt : null, status };
    });
    const removedByDay = {}; for (const t of origBy.values()) removedByDay[t.date] = (removedByDay[t.date] || 0) - t.amt;
    const byDay = {}; rows.forEach(r => (byDay[r.date] = byDay[r.date] || []).push(r));
    let prevStated = opening, prevGap = 0, checked = 0; const errors = [];
    for (const d of Object.keys(byDay).sort()) {
      const day = byDay[d], last = day[day.length - 1]; last.end = true;
      const sum = day.reduce((s, r) => s + r.amt, 0), stated = [...day].reverse().find(r => r.stated != null)?.stated ?? null;
      const expected = prevStated + sum;
      if (original) { last.gapToday = day.reduce((s, r) => s + r.amt - (r.origAmt || 0), 0) + (removedByDay[d] || 0); last.gapCarried = prevGap; }
      if (stated != null) {
        checked++; last.expected = expected; last.error = stated - expected; if (last.error) errors.push(last);
        if (original && d in origDay) { last.origStated = origDay[d]; last.gap = stated - origDay[d]; prevGap = last.gap; }
        prevStated = stated;
      } else { prevStated = expected; if (original) prevGap += last.gapToday; }
    }
    return { rows, opening, checked, errors, removed: [...origBy.values()], hasOriginal: !!original };
  }

  const rowsOfRes = res => res.days.flatMap(d => d.rows);
  const closing = res => res.daily[res.end];
  const minBal = res => Object.entries(res.daily).reduce((a, b) => b[1] < a[1] ? b : a);
  const totalOf = (res, k) => rowsOfRes(res).filter(r => r.kind === k).reduce((s, r) => s + r.amt, 0);
  const daysOver = (res, lim) => lim == null ? null : Object.values(res.daily).filter(b => b < -lim).length;
  function identityMismatches(res, txns) {
    const out = [], rows = rowsOfRes(res);
    if (rows.length !== txns.length) out.push(`מספר שורות: ${rows.length} מול ${txns.length}`);
    rows.forEach((r, i) => { const t = txns[i]; if (t && (r.date !== t.date || r.desc !== t.desc || r.amt !== t.amt || r.ref !== t.ref)) out.push(`${dmy(t.date)} ${t.desc}: ${fmt(r.amt)} מול ${fmt(t.amt)}`); });
    for (const t of txns) if (t.bal != null && res.daily[t.date] !== t.bal) out.push(`יתרה ${dmy(t.date)}: ${fmt(res.daily[t.date])} מול ${fmt(t.bal)}`);
    return out;
  }

  return { parseAmount, fmt, fromShekels, parseScaled, scalePct, roundDiv, dmy, dmyShort, addDays, weekday, month,
    Calendar, visualToLogical, parseCSV, parsePdfWords, merge, validate, compileRules, categorize, ruleFromApproval, UNCAT,
    detect, KIND_HE, makeParams, audit, Engine, rowsOfRes, closing, minBal, totalOf, daysOver, identityMismatches, makeTxn, finalize, splitChannel };
})();
if (typeof module !== "undefined") module.exports = OSH;
