"""Issue #27 validation runner (read-only, validation phase)."""
from __future__ import annotations

import json
import random
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "QLA_Migration" / "Output"
ISSUE = Path(__file__).resolve().parent
AUDIT = ISSUE / "Issue_27_SL_Suppression_Audit.csv"
SL_POP = ISSUE / "Issue_27_SL_Impact_Population.csv"
PREM_POP = ISSUE / "Issue_27_SL_Premium_Population.csv"


def read_csv(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, dtype=str, encoding="latin1", on_bad_lines="skip").fillna("")
    df.columns = [c.strip().upper() for c in df.columns]
    return df


def ridr_amt(r) -> float:
    try:
        return round(float(r["MUNIT"] or 0) * float(r["MVPU"] or 0), 2)
    except ValueError:
        return 0.0


def main() -> None:
    ridr = read_csv(OUT / "quikridr.csv")
    mstr = read_csv(OUT / "quikmstr.csv")
    plan = read_csv(OUT / "quikplan.csv")
    audit = read_csv(AUDIT)
    pop = read_csv(SL_POP)
    prem = read_csv(PREM_POP)

    sl_qla = sorted({str(x).strip() for x in pop["_QLA"] if str(x).strip()})
    audit_qla = sorted({str(x).strip() for x in audit["QLA_POLICY_NUMBER"] if str(x).strip()})

    ridr["_POL"] = ridr["MPOLICY"].str.strip()
    mstr["_POL"] = mstr["MPOLICY"].str.strip()

    # 1 Population
    missing_mstr = [p for p in sl_qla if p not in set(mstr["_POL"])]
    sl_phases = {
        (str(r["QLA_POLICY_NUMBER"]).strip(), str(r["BENEFIT_SEQ"]).strip())
        for _, r in audit.iterrows()
    }
    ridr["_PH"] = ridr["MPHASE"].str.strip()
    sl_in_ridr = ridr[ridr.apply(lambda r: (r["_POL"], r["_PH"]) in sl_phases, axis=1)]

    # 2 Duplicate face
    dup_pairs = []
    for pol in sl_qla:
        sub = ridr[ridr["_POL"] == pol]
        seen: dict[tuple[float, str], str] = {}
        for _, r in sub.iterrows():
            a = ridr_amt(r)
            if a <= 0:
                continue
            key = (a, str(r["MPLAN"]).strip())
            ph = str(r["MPHASE"]).strip()
            if key in seen:
                dup_pairs.append({"QLA": pol, "PH1": seen[key], "PH2": ph, "AMT": key[0], "MPLAN": key[1]})
            else:
                seen[key] = ph

    # Trace 010448806C
    trace = ridr[ridr["_POL"] == "010448806C"].sort_values("MPHASE")
    trace_detail = [
        {
            "MPHASE": str(r["MPHASE"]).strip(),
            "MPLAN": str(r["MPLAN"]).strip(),
            "FACE": ridr_amt(r),
            "MPREM": str(r["MPREM"]).strip(),
        }
        for _, r in trace.iterrows()
    ]

    # 3 Premium
    prem_results = []
    prem_mismatch = 0
    for _, r in prem.iterrows():
        qla = str(r["QLA"]).strip()
        pp = float(r["PPOLC_MODE_PREM"])
        ms = mstr[mstr["_POL"] == qla]
        if ms.empty:
            prem_results.append({"QLA": qla, "status": "MISSING_MSTR"})
            continue
        mm = float(str(ms.iloc[0]["MMODEPREM"]).strip() or 0)
        ok = abs(pp - mm) <= 0.10
        if not ok:
            prem_mismatch += 1
        prem_results.append({"QLA": qla, "PPOLC": pp, "MMODEPREM": mm, "match": ok})

    # 4 Financial counts
    sl_ridr = ridr[ridr["_POL"].isin(sl_qla)]
    sl_face_total = sum(ridr_amt(r) for _, r in sl_ridr.iterrows())

    # 5 Audit
    audit_dup = audit.duplicated(subset=["QLA_POLICY_NUMBER", "BENEFIT_SEQ"]).sum()
    table_pop = int((audit["SL_TABLE_CODE"].astype(str).str.strip() != "").sum())
    reason_ok = int((audit["SUPPRESSION_REASON"].astype(str).str.strip() == "Issue #27").sum())

    # 7 Random sample (deterministic seed)
    rng = random.Random(27)
    sample_policies = rng.sample(sl_qla, min(10, len(sl_qla)))
    samples = []
    for pol in sorted(sample_policies):
        sub = ridr[ridr["_POL"] == pol]
        aud = audit[audit["QLA_POLICY_NUMBER"].str.strip() == pol]
        dup = any(
            ridr_amt(r) > 0
            for i, (_, r) in enumerate(sub.iterrows())
            for j, (_, r2) in enumerate(sub.iterrows())
            if i < j
            and ridr_amt(r) == ridr_amt(r2)
            and str(r["MPLAN"]).strip() == str(r2["MPLAN"]).strip()
        )
        ms = mstr[mstr["_POL"] == pol]
        samples.append(
            {
                "QLA": pol,
                "quikridr_rows": len(sub),
                "audit_rows": len(aud),
                "duplicate_face": dup,
                "mmodeprem": str(ms.iloc[0]["MMODEPREM"]).strip() if len(ms) else "",
                "has_base_phase": any(str(r["MPHASE"]).strip() == "1" for _, r in sub.iterrows()),
            }
        )

    report = {
        "engine_version": "v57.39",
        "population": {
            "sl_policies_expected": len(sl_qla),
            "sl_policies_in_audit": len(audit_qla),
            "missing_quikmstr": missing_mstr,
            "sl_phases_in_quikridr": len(sl_in_ridr),
            "all_policies_converted": len(missing_mstr) == 0,
        },
        "duplicate_face": {
            "pairs_before_planning": 46,
            "pairs_after": len(dup_pairs),
            "trace_010448806C": trace_detail,
        },
        "premium": {
            "premium_bearing_count": len(prem),
            "match_count": len(prem) - prem_mismatch,
            "mismatch_count": prem_mismatch,
        },
        "financial": {
            "quikmstr_rows": len(mstr),
            "quikridr_rows": len(ridr),
            "quikplan_rows": len(plan),
            "sl_policy_quikridr_rows": len(sl_ridr),
            "sl_policy_face_total": round(sl_face_total, 2),
        },
        "audit": {
            "rows": len(audit),
            "unique_policies": audit["QLA_POLICY_NUMBER"].nunique(),
            "sl_table_code_populated": table_pop,
            "suppression_reason_ok": reason_ok,
            "duplicate_audit_rows": int(audit_dup),
        },
        "random_sample": samples,
    }

    out_path = ISSUE / "Issue_27_Validation_Metrics.json"
    out_path.write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
