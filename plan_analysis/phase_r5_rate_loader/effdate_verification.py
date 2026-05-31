"""
Post-emit EFFDATE verification — reads every emitted DBF and confirms all EFFDATE values
equal 19000101 (no blanks, no 00000000). Writes effdate_verification_report.csv.
"""
import os, sys, csv, collections

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
import dbf

HERE = os.path.dirname(__file__)
EMIT_DIR = os.path.join(HERE, "emitted_dbf")
STANDARD = "19000101"


def fmt(d):
    if d is None:
        return ""  # blank date
    return f"{d.year:04d}{d.month:02d}{d.day:02d}"


def main():
    report = []
    all_ok = True
    for fn in sorted(os.listdir(EMIT_DIR)):
        if not fn.lower().endswith(".dbf"):
            continue
        t = dbf.Table(os.path.join(EMIT_DIR, fn)); t.open(mode=dbf.READ_ONLY)
        has_eff = "EFFDATE" in t.field_names
        distinct = collections.Counter()
        if has_eff:
            for r in t:
                distinct[fmt(r.EFFDATE)] += 1
        n = len(t)
        t.close()
        if not has_eff:
            # member/dimension tables (QuikPlGd/Uw/Bd/St) have no EFFDATE field by design
            report.append({
                "TABLE_NAME": fn[:-4], "ROW_COUNT": n,
                "DISTINCT_EFFDATE_VALUES": "N/A (no EFFDATE field)",
                "BLANK_EFFDATE": 0, "ZERO_EFFDATE": 0, "STATUS": "EXEMPT",
            })
            continue
        distinct_vals = sorted(distinct)
        blanks = distinct.get("", 0)
        zeros = distinct.get("00000000", 0)
        ok = (distinct_vals == [STANDARD]) and blanks == 0 and zeros == 0
        all_ok = all_ok and ok
        report.append({
            "TABLE_NAME": fn[:-4], "ROW_COUNT": n,
            "DISTINCT_EFFDATE_VALUES": "|".join(distinct_vals),
            "BLANK_EFFDATE": blanks, "ZERO_EFFDATE": zeros,
            "STATUS": "PASS" if ok else "FAIL",
        })

    out = os.path.join(HERE, "effdate_verification_report.csv")
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["TABLE_NAME", "ROW_COUNT", "DISTINCT_EFFDATE_VALUES",
                                          "BLANK_EFFDATE", "ZERO_EFFDATE", "STATUS"])
        w.writeheader()
        for row in report:
            w.writerow(row)

    for row in report:
        print(f"{row['STATUS']:4} {row['TABLE_NAME']:10} rows={row['ROW_COUNT']:>6} "
              f"effdates={row['DISTINCT_EFFDATE_VALUES']} blanks={row['BLANK_EFFDATE']} zeros={row['ZERO_EFFDATE']}")
    print(f"\nTABLES={len(report)}  ALL_EFFDATE_19000101={all_ok}")


if __name__ == "__main__":
    main()
