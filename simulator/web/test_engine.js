const OSH = require("./engine.js"); const fs = require("fs");
const data = JSON.parse(fs.readFileSync(__dirname + "/data.json")); const exp = JSON.parse(fs.readFileSync(__dirname + "/py_expect.json"));
const st = OSH.parseCSV(fs.readFileSync(process.argv[2], "utf8"), "synthetic.csv");
const m = OSH.merge([st]); const rep = OSH.validate(m.txns); if (!rep.ok) throw new Error("validation");
const rules = OSH.compileRules(data.rules); const cat = OSH.categorize(m.txns, rules);
const cal = new OSH.Calendar(data.holidays); const pats = OSH.detect(m.txns, cal);
const P0 = OSH.makeParams({ feeRate: "1.76" });
const P1 = OSH.makeParams({ feeRate: "1.76", rates: [{ from: "2026-01-01", debit: "12.5", credit: "0", over: "18" }], limit: "40000" });
const SAL = { category: "הכנסות", subcategory: "משכורת" };
function r(P, deltas, mode = "replay", months = 3) {
  const e = new OSH.Engine(m.txns, rep.opening, P, cal, pats);
  const id = OSH.identityMismatches(e.run({ name: "b", deltas: [] }), m.txns); if (id.length) throw new Error("identity " + id[0]);
  const b = e.run({ name: "b", mode, months, deltas: [] }), s = e.run({ name: "t", mode, months, deltas });
  return { closing: OSH.closing(s), min: OSH.minBal(s)[1], interest: OSH.totalOf(s, "interest"), fee: OSH.totalOf(s, "direct_channel_fee"),
    unposted: s.unposted, rows: OSH.rowsOfRes(s).length, base_closing: OSH.closing(b), intcal: s.intCal.map(c => [c.model, c.actual]) };
}
const got = {
  sal10: r(P0, [{ type: "change", select: SAL, pct: "10", start: "2026-07-01" }]),
  sal1000_rates: r(P1, [{ type: "change", select: SAL, amount: "1000" }]),
  rate15: r(P1, [{ type: "rate", rates: OSH.makeParams({ rates: [{ from: "2026-01-01", debit: "15", credit: "0", over: "18" }] }).rates }]),
  nobit: r(P0, [{ type: "remove", select: { description: "ביט" }, start: "2026-07-01", end: "2026-07-31" }]),
  fwd: r(P1, [{ type: "change", select: { category: "כרטיסי אשראי" }, pct: "-15" }, { type: "remove", select: { description: "ביטוח בריאות" }, start: "2026-08-01" },
    { type: "add", description: "חיסכון", amount: "-500", dom: 12, start: "2026-07-01", ch: "direct" }, { type: "oneoff", date: "2026-08-15", amount: "3000", description: "מענק" }], "forward", 3),
};
let bad = 0;
for (const k in exp) for (const f in exp[k]) if (JSON.stringify(exp[k][f]) !== JSON.stringify(got[k][f])) { bad++; console.log("MISMATCH", k, f, exp[k][f], got[k][f]); }
console.log(bad ? `${bad} mismatches` : "all match python", "| queue", cat.queue.length, "| patterns", pats.filter(p => p.kind !== "one_off").map(p => p.cp + ":" + p.kind + ":" + p.fri).join(", "));
