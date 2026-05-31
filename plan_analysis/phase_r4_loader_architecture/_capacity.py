"""
PHASE R4 - Rate factor capacity / overflow analysis (READ-ONLY).

Confirmed field capacity (from DBF descriptors + ~7.3M populated ground-truth cells):
  Every factor column (GP0..GP9, CV*, DB*, DV*, NP*, TV*) is Character(7), decimals=0.
  100% of populated cells use a fixed 2-decimal text format "9999.99".
  => positive max = 9999.99 ; negative max magnitude = 999.99 (minus sign uses 1 char).

Overflow = the 2-decimal formatted string (with sign) does not fit in 7 chars.

Produces:
  rate_factor_capacity_analysis.csv   (per RATE_FAMILY/PLAN/TYPE_CODE)
  overflow_detail_report.csv          (one row per overflowing source factor)
"""
import os, csv, collections
import openpyxl

ROOT = r"plan_analysis/source_data"
OUTDIR = r"plan_analysis/phase_r4_loader_architecture"
SRC = os.path.join(ROOT, "rates", "Rate_Table_Extract_20260427.csv")
XLSX = os.path.join(ROOT, "crosswalk", "Policy Form Crosswalk 5.22.26.xlsx")

TYPE_TO_TABLE = {"CV": "QuikCvs", "DB": "QuikDbs", "NP": "QuikNps",
                 "DV": "QuikDvs", "RV": "QuikTvs", "PR": "QuikGps"}
PREFIX = {"QuikGps": "GP", "QuikCvs": "CV", "QuikDbs": "DB",
          "QuikDvs": "DV", "QuikNps": "NP", "QuikTvs": "TV"}
FAMILY = {"QuikGps": "GROSS_PREMIUM", "QuikCvs": "CASH_VALUE", "QuikDbs": "DEATH_BENEFIT",
          "QuikDvs": "DIVIDEND", "QuikNps": "NET_PREMIUM", "QuikTvs": "TERMINAL_RESERVE"}
EXCLUDED = {"NN", "PN", "TP", "TX", "UF", "NF", "SL"}
CAP_STR = "CHAR(7) fixed 2dp: pos<=9999.99, neg>=-999.99"
POS_MAX = 9999.99
NEG_MIN = -999.99


def fits(v):
    """Does value fit Character(7) under the confirmed 2-decimal format?"""
    return len(f"{v:.2f}") <= 7


def overflow_amount(v):
    if v > POS_MAX:
        return round(v - POS_MAX, 4)
    if v < NEG_MIN:
        return round(v - NEG_MIN, 4)  # negative = how far below the negative floor
    return 0.0


def to_float(s):
    s = (s or "").strip()
    if s in ("", ".", "-", "-."):
        return None
    try:
        return float(s)
    except ValueError:
        return None


def load_xwalk():
    wb = openpyxl.load_workbook(XLSX, read_only=True, data_only=True)
    ws = wb["Sheet1"]; m = {}
    for i, row in enumerate(ws.iter_rows(values_only=True)):
        if i == 0:
            continue
        if row[0] and row[2]:
            m[str(row[0]).strip()] = str(row[2]).strip()
    return m


def main():
    os.makedirs(OUTDIR, exist_ok=True)
    xwalk = load_xwalk()
    agg = {}  # (family,plan,typ) -> stats
    detail_path = os.path.join(OUTDIR, "overflow_detail_report.csv")
    df = open(detail_path, "w", newline="", encoding="utf-8")
    dw = csv.writer(df)
    dw.writerow(["PLAN", "TYPE_CODE", "AGE", "DURATION", "VALUE", "TARGET_TABLE",
                 "TARGET_FIELD", "FIELD_CAPACITY", "OVERFLOW_AMOUNT"])
    overflow_total = 0
    DETAIL_CAP = 5000  # detail rows are written in full up to this safety cap

    with open(SRC, encoding="utf-8-sig", errors="replace", newline="") as f:
        rd = csv.reader(f); next(rd)
        for r in rd:
            if len(r) < 8:
                continue
            cov = r[0].strip(); typ = r[1].strip(); age = r[2].strip()
            dur = r[6].strip(); val = r[7].strip()
            if set(cov) == {"-"}:
                continue
            if typ in EXCLUDED or typ not in TYPE_TO_TABLE:
                continue
            plan = xwalk.get(cov)
            if not plan:
                continue
            v = to_float(val)
            if v is None:
                continue
            table = TYPE_TO_TABLE[typ]; fam = FAMILY[table]
            k = (fam, plan, typ)
            st = agg.get(k)
            if st is None:
                st = {"count": 0, "sum": 0.0, "min": v, "max": v, "of": 0}
                agg[k] = st
            st["count"] += 1; st["sum"] += v
            if v < st["min"]:
                st["min"] = v
            if v > st["max"]:
                st["max"] = v
            if not fits(v):
                st["of"] += 1; overflow_total += 1
                if overflow_total <= DETAIL_CAP:
                    try:
                        ql = int(dur) - 1; col = ql % 10
                    except ValueError:
                        col = ""
                    dw.writerow([plan, typ, age, dur, val, table,
                                 f"{PREFIX[table]}{col}", CAP_STR, overflow_amount(v)])
    df.close()

    cap_path = os.path.join(OUTDIR, "rate_factor_capacity_analysis.csv")
    with open(cap_path, "w", newline="", encoding="utf-8") as cf:
        cw = csv.writer(cf)
        cw.writerow(["RATE_FAMILY", "PLAN", "TYPE_CODE", "COUNT", "MIN_VALUE", "MAX_VALUE",
                     "AVG_VALUE", "OVERFLOW_COUNT", "OVERFLOW_PERCENT", "FIELD_CAPACITY", "NOTES"])
        for (fam, plan, typ), st in sorted(agg.items()):
            avg = st["sum"] / st["count"] if st["count"] else 0
            pct = 100.0 * st["of"] / st["count"] if st["count"] else 0
            note = ""
            if st["of"]:
                note = f"OVERFLOW: {st['of']} factor(s) exceed 9999.99; requires business decision before load"
            elif st["max"] > 9000:
                note = "near-capacity (max>9000); monitor"
            cw.writerow([fam, plan, typ, st["count"], f"{st['min']:.4f}", f"{st['max']:.4f}",
                         f"{avg:.4f}", st["of"], f"{pct:.2f}", CAP_STR, note])

    # console summary
    by_fam = collections.Counter(); plans_of = collections.Counter()
    famcount = collections.Counter()
    for (fam, plan, typ), st in agg.items():
        if st["of"]:
            by_fam[fam] += st["of"]; plans_of[(fam, plan)] += st["of"]
        famcount[fam] += st["count"]
    print("TOTAL overflow factors:", overflow_total, "(detail capped at %d)" % DETAIL_CAP)
    print("overflow by family:", dict(by_fam))
    print("rows scanned by family:", dict(famcount))
    print("distinct plans with overflow:", len(set(p for (f, p) in plans_of)))
    print("top overflow plans:", plans_of.most_common(10))


if __name__ == "__main__":
    main()
