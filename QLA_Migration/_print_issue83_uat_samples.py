"""Print Issue #83 UAT sample checklist from loaded Output/rates."""
import csv
from pathlib import Path

RATES = Path("QLA_Migration/Output/rates")
QP = Path("QLA_Migration/Output/quikplan.csv")

SAMPLES = [
    ("221END", "END85 anchor - your screenshot plan; CV had M only, now F+M"),
    ("222END", "END85 pair - same CV pattern"),
    ("1960PO", "960 PO - #80 valuation anchor"),
    ("1658CS", "ISWL - stub families + real F/M"),
    ("17MJPO", "Was CV F-only - companion M added (Values=N)"),
    ("5646AT", "Was CV F-only"),
    ("130JEB", "Was CV M-only - companion F added (Values=N)"),
    ("2665ST", "Was CV M-only"),
]


def read(p):
    with p.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def factor_genders(plan, fname):
    fp = RATES / fname
    if not fp.exists():
        return set()
    return {
        (r.get("GENDER") or "").strip()
        for r in read(fp)
        if (r.get("PLAN") or "").strip() == plan
    }


def keys(plan, table):
    return [
        r for r in read(RATES / f"{table}.csv")
        if (r.get("PLAN") or "").strip() == plan
    ]


def main():
    qp = {(r.get("PLAN") or "").strip(): r for r in read(QP)}
    gd_rows = read(RATES / "QuikPlGd.csv")

    print("Reload: QLA_Migration/Output/rates/*.csv + quikplan.csv")
    print("(or Test_Validation/quikplan.csv + Test_Validation/rates/)\n")

    for plan, note in SAMPLES:
        cv_keys = keys(plan, "QuikPlCv")
        tv_keys = keys(plan, "QuikPlTv")
        cv_fac = factor_genders(plan, "QuikCvs.csv")
        tv_fac = factor_genders(plan, "QuikTvs.csv")
        gd = sorted({
            (r.get("GDCODE") or "").strip()
            for r in gd_rows
            if (r.get("PLAN") or "").strip() == plan
        })
        pvo = qp.get(plan, {})

        print(f"PLAN {plan}")
        print(f"  {note}")
        print(f"  Gender members: {', '.join(gd)}")
        print("  Cash Values keys (Plan Rate File Options Keys):")
        for r in sorted(cv_keys, key=lambda x: x.get("GENDER", "")):
            g = (r.get("GENDER") or "").strip()
            values = "Y" if g in cv_fac else "N"
            print(
                f"    Sex={g}  Values={values}  "
                f"MORT={r.get('MORT', '')}  ETIMORT={r.get('ETIMORT', '')}  "
                f"NFOINT={r.get('NFOINT', '')}  CvMeth={r.get('INTMETHCV', '')}  "
                f"Eff={r.get('EFFDATE', '')}"
            )
        if tv_keys:
            print("  Terminal Value keys:")
            for r in sorted(tv_keys, key=lambda x: x.get("GENDER", "")):
                g = (r.get("GENDER") or "").strip()
                values = "Y" if g in tv_fac else "N"
                print(f"    Sex={g}  Values={values}")
        if pvo:
            print(
                f"  Plan Values Options: GDVARYCV={pvo.get('GDVARYCV', '')}  "
                f"GDVARYTV={pvo.get('GDVARYTV', '')}  PLANVALOPT={pvo.get('PLANVALOPT', '')}"
            )
        print()


if __name__ == "__main__":
    main()
