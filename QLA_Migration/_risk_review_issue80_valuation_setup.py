"""Read-only Issue #80 risk simulation: Valuation_Setup coded expected vs Output."""
from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXP_PATH = ROOT / "Issue_Log_Items/Issue_80/evidence/cso_valuation_setup_coded_expected.csv"
OUT_DIR = ROOT / "Issue_Log_Items/Issue_80/evidence"
RATES = ROOT / "QLA_Migration/Output/rates"
QUIKPLAN = ROOT / "QLA_Migration/Output/quikplan.csv"


def load_csv(path: Path) -> list[dict]:
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def norm_log(v) -> str:
    if v is None or v == "":
        return ""
    if isinstance(v, bool):
        return "True" if v else "False"
    s = str(v).strip()
    if s.lower() in ("true", ".t.", "t", "yes"):
        return "True"
    if s.lower() in ("false", ".f.", "f", "no"):
        return "False"
    return s


def norm_char(v) -> str:
    if v is None:
        return ""
    return str(v).strip()


def main() -> None:
    exp = {}
    with EXP_PATH.open(encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r["scope_issue80"] == "IN_SCOPE":
                exp[r["qla_plan"]] = r
    plans = set(exp)

    cv = [r for r in load_csv(RATES / "QuikPlCv.csv") if (r.get("PLAN") or "").strip() in plans]
    tv = [r for r in load_csv(RATES / "QuikPlTv.csv") if (r.get("PLAN") or "").strip() in plans]
    qp = [r for r in load_csv(QUIKPLAN) if (r.get("PLAN") or "").strip() in plans]
    missing_cv = sorted(plans - {r["PLAN"].strip() for r in cv})
    missing_tv = sorted(plans - {r["PLAN"].strip() for r in tv})

    cv_fields = [
        ("MORT", "QuikPlCv_MORT", False),
        ("ETIMORT", "QuikPlCv_ETIMORT", False),
        ("NFOINT", "QuikPlCv_NFOINT", False),
        ("INTMETHCV", "QuikPlCv_INTMETHCV", False),
    ]
    tv_fields = [
        ("MORT", "QuikPlTv_MORT", False),
        ("RSVINT", "QuikPlTv_RSVINT", False),
        ("RSVMETH", "QuikPlTv_RSVMETH", False),
        ("INTMETHTV", "QuikPlTv_INTMETHTV", False),
        ("STOREMEANS", "QuikPlTv_STOREMEANS", True),
        ("CALCMIDS", "QuikPlTv_CALCMIDS", True),
    ]
    qp_fields = [
        ("NFOINT", "QuikPlCv_NFOINT", False),
        ("INTMETHCV", "QuikPlCv_INTMETHCV", False),
    ]

    def analyze(rows, field_pairs, label):
        cell_change = cell_same = blank_to_val = val_to_blank = val_to_val = 0
        row_change = 0
        by_field: Counter = Counter()
        plan_change: set[str] = set()
        diffs = []
        nfo_pairs: Counter = Counter()
        for r in rows:
            plan = r["PLAN"].strip()
            e = exp[plan]
            changed = False
            for fld, efld, logical in field_pairs:
                before = norm_log(r.get(fld)) if logical else norm_char(r.get(fld))
                after = norm_log(e.get(efld)) if logical else norm_char(e.get(efld))
                if before == after:
                    cell_same += 1
                else:
                    cell_change += 1
                    by_field[fld] += 1
                    changed = True
                    if before == "" and after != "":
                        blank_to_val += 1
                    elif before != "" and after == "":
                        val_to_blank += 1
                    else:
                        val_to_val += 1
                    if fld == "NFOINT":
                        nfo_pairs[(before or "<blank>", after or "<blank>")] += 1
                    if len(diffs) < 60:
                        diffs.append(
                            {
                                "table": label,
                                "PLAN": plan,
                                "FIELD": fld,
                                "BEFORE": before,
                                "AFTER": after,
                                "GENDER": r.get("GENDER", ""),
                                "UWCLASS": r.get("UWCLASS", ""),
                            }
                        )
            if changed:
                row_change += 1
                plan_change.add(plan)
        return {
            "rows": len(rows),
            "rows_change": row_change,
            "rows_unchanged": len(rows) - row_change,
            "cells_change": cell_change,
            "cells_same": cell_same,
            "blank_to_val": blank_to_val,
            "val_to_blank": val_to_blank,
            "val_to_val": val_to_val,
            "plans_change": len(plan_change),
            "by_field": dict(by_field),
            "diffs": diffs,
            "nfo_pairs": nfo_pairs,
        }

    cv_a = analyze(cv, cv_fields, "QuikPlCv")
    tv_a = analyze(tv, tv_fields, "QuikPlTv")
    qp_a = analyze(qp, qp_fields, "quikplan")

    for name, a in [("QuikPlCv", cv_a), ("QuikPlTv", tv_a), ("quikplan", qp_a)]:
        print("====", name)
        for k in [
            "rows",
            "rows_change",
            "rows_unchanged",
            "cells_change",
            "blank_to_val",
            "val_to_blank",
            "val_to_val",
            "plans_change",
        ]:
            print(k, a[k])
        print("by_field", a["by_field"])
        if a["nfo_pairs"]:
            print("NFOINT", dict(a["nfo_pairs"]))

    print("missing_QuikPlCv", missing_cv)
    print("missing_QuikPlTv", missing_tv)

    with (OUT_DIR / "issue80_risk_impact_summary.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(
            [
                "table",
                "rows",
                "rows_change",
                "rows_unchanged",
                "cells_change",
                "blank_to_val",
                "val_to_blank",
                "val_to_val",
                "plans_with_key",
                "plans_change",
                "plans_missing_key",
            ]
        )
        w.writerow(
            [
                "QuikPlCv",
                cv_a["rows"],
                cv_a["rows_change"],
                cv_a["rows_unchanged"],
                cv_a["cells_change"],
                cv_a["blank_to_val"],
                cv_a["val_to_blank"],
                cv_a["val_to_val"],
                48,
                cv_a["plans_change"],
                len(missing_cv),
            ]
        )
        w.writerow(
            [
                "QuikPlTv",
                tv_a["rows"],
                tv_a["rows_change"],
                tv_a["rows_unchanged"],
                tv_a["cells_change"],
                tv_a["blank_to_val"],
                tv_a["val_to_blank"],
                tv_a["val_to_val"],
                48,
                tv_a["plans_change"],
                len(missing_tv),
            ]
        )
        w.writerow(
            [
                "quikplan",
                qp_a["rows"],
                qp_a["rows_change"],
                qp_a["rows_unchanged"],
                qp_a["cells_change"],
                qp_a["blank_to_val"],
                qp_a["val_to_blank"],
                qp_a["val_to_val"],
                51,
                qp_a["plans_change"],
                0,
            ]
        )

    diffs = cv_a["diffs"] + tv_a["diffs"] + qp_a["diffs"]
    with (OUT_DIR / "issue80_risk_sample_diffs.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(
            f, fieldnames=["table", "PLAN", "FIELD", "BEFORE", "AFTER", "GENDER", "UWCLASS"]
        )
        w.writeheader()
        w.writerows(diffs)

    anchors = ["1960PO", "1658C1", "17CSI3", "1L1095", "221END", "1668SP"]
    with (OUT_DIR / "issue80_risk_anchor_plans.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["PLAN", "surface", "field", "before", "after"])
        w.writeheader()
        for plan in anchors:
            e = exp[plan]
            cv_rows = [r for r in cv if r["PLAN"].strip() == plan]
            tv_rows = [r for r in tv if r["PLAN"].strip() == plan]
            qp_rows = [r for r in qp if r["PLAN"].strip() == plan]

            def first(rows, fld, logical=False):
                if not rows:
                    return "<no row>"
                return norm_log(rows[0].get(fld)) if logical else norm_char(rows[0].get(fld))

            for fld, ef, log in cv_fields:
                w.writerow(
                    {
                        "PLAN": plan,
                        "surface": "QuikPlCv",
                        "field": fld,
                        "before": first(cv_rows, fld),
                        "after": e[ef],
                    }
                )
            for fld, ef, log in tv_fields:
                w.writerow(
                    {
                        "PLAN": plan,
                        "surface": "QuikPlTv",
                        "field": fld,
                        "before": first(tv_rows, fld, log),
                        "after": e[ef],
                    }
                )
            for fld, ef, log in qp_fields:
                w.writerow(
                    {
                        "PLAN": plan,
                        "surface": "quikplan",
                        "field": fld,
                        "before": first(qp_rows, fld),
                        "after": e[ef],
                    }
                )

    print("wrote", OUT_DIR / "issue80_risk_impact_summary.csv")


if __name__ == "__main__":
    main()
