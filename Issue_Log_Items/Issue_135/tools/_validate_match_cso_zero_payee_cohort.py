#!/usr/bin/env python3
"""Focused validator — Issue #135 MATCH_CSO zero-payee cohort backfill."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

CLMS = ROOT / "QLA_Migration" / "Output" / "quikclms.csv"
CLMP = ROOT / "QLA_Migration" / "Output" / "quikclmp.csv"
EVID = ROOT / "Issue_Log_Items" / "Issue_135" / "evidence"
META = EVID / "issue135_match_cso_zero_payee_apply_meta.json"
CLASS = EVID / "issue135_match_cso_zero_payee_classification.csv"
HOLDS = EVID / "issue135_match_cso_zero_payee_holds.csv"
AUDIT = EVID / "issue135_match_cso_zero_payee_backfill_audit.csv"
OUT = EVID / "issue135_match_cso_zero_payee_validation.json"
GOLDEN = "9011156655C"
TOL = 0.01


def _strip(v) -> str:
    return "" if v is None else str(v).strip()


def _money(v) -> float:
    try:
        return float(str(v).replace(",", "").strip() or 0)
    except (TypeError, ValueError):
        return 0.0


def main() -> int:
    checks: list[dict] = []
    fails = 0

    def check(name: str, ok: bool, detail: str = "") -> None:
        nonlocal fails
        checks.append({"check": name, "status": "PASS" if ok else "FAIL", "detail": detail})
        if not ok:
            fails += 1

    clms = pd.read_csv(CLMS, dtype=str).fillna("")
    clmp = pd.read_csv(CLMP, dtype=str).fillna("")
    check("CLASSIFICATION_PRESENT", CLASS.is_file(), str(CLASS))
    check("HOLDS_PRESENT", HOLDS.is_file(), str(HOLDS))
    check("AUDIT_PRESENT", AUDIT.is_file(), str(AUDIT))
    check("META_PRESENT", META.is_file(), str(META))

    class_df = pd.read_csv(CLASS, dtype=str).fillna("") if CLASS.is_file() else pd.DataFrame()
    holds = pd.read_csv(HOLDS, dtype=str).fillna("") if HOLDS.is_file() else pd.DataFrame()
    meta = json.loads(META.read_text(encoding="utf-8")) if META.is_file() else {}

    safe = (
        class_df[class_df["class"].map(_strip) == "SAFE_BACKFILL"]
        if len(class_df)
        else pd.DataFrame()
    )
    already = (
        class_df[class_df["class"].map(_strip) == "ALREADY_BACKFILLED"]
        if len(class_df)
        else pd.DataFrame()
    )
    hold_n = int(len(holds)) if len(holds) else int(
        class_df["class"].isin(["HOLD_INCOMPLETE", "HOLD_MISMATCH"]).sum()
    ) if len(class_df) else -1

    # Cohort inventory size from classification (includes already/safe/hold)
    check("COHORT_CLASSIFIED", len(class_df) >= 140, f"n={len(class_df)}")
    check("SAFE_COUNT_GE_137", len(safe) + len(already) >= 137, f"safe={len(safe)} already={len(already)}")
    check("HOLD_COUNT_EQ_3", hold_n == 3, f"hold_n={hold_n}")

    # Every SAFE + ALREADY policy must have payees summing to MPAID
    target_pols = set(safe["mpolicy"].map(_strip)) | set(already["mpolicy"].map(_strip))
    if not target_pols and META.is_file():
        # Fallback: audit SUMMARY rows
        audit = pd.read_csv(AUDIT, dtype=str).fillna("") if AUDIT.is_file() else pd.DataFrame()
        if len(audit):
            target_pols = set(
                audit[audit["mseq"].map(_strip) != "SUMMARY"]["mpolicy"].map(_strip)
            )
            target_pols.add(GOLDEN)

    sum_bad = []
    mpaid_changed = []
    mseq_bad = []
    stub_bad = []
    mint_bad = []
    for pol in sorted(target_pols):
        hdr = clms[
            (clms["MPOLICY"].map(_strip) == pol)
            & (clms["CLAIMSTAT"].map(_strip) == "2")
        ]
        pay = clmp[clmp["MPOLICY"].map(_strip) == pol]
        if not len(hdr):
            sum_bad.append(f"{pol}:no_header")
            continue
        h = hdr.iloc[0]
        mpaid = _money(h.get("MPAID", 0))
        header_mseq = _strip(h.get("MSEQ", "0")) or "0"
        if abs(_money(h.get("MINTAMT", 0))) > TOL:
            mint_bad.append(pol)
        if not len(pay):
            sum_bad.append(f"{pol}:no_payees")
            continue
        psum = round(pay["MAMOUNT"].map(_money).sum(), 2)
        if abs(psum - mpaid) > TOL:
            sum_bad.append(f"{pol}:{psum}!={mpaid}")
        # Multi-payee rows must share claim-header MSEQ for QLAdmin relation join.
        if any(_strip(x) != header_mseq for x in pay["MSEQ"]):
            mseq_bad.append(pol)
        for name in pay["MPAYNAME"].map(_strip):
            if not name or "NEEDS_PAYEE" in name.upper() or name.startswith("***"):
                stub_bad.append(pol)
                break

    check("SAFE_PAYEE_SUM_EQ_MPAID", len(sum_bad) == 0, f"bad={sum_bad[:8]}")
    check("PAYEE_MSEQ_MATCHES_HEADER", len(mseq_bad) == 0, f"bad={mseq_bad[:8]}")
    check("NO_FABRICATED_STUBS", len(stub_bad) == 0, f"bad={stub_bad[:8]}")
    check("TARGET_MINTAMT_ZERO", len(mint_bad) == 0, f"bad={mint_bad[:8]}")

    # Global MINTAMT
    mint = pd.to_numeric(clms["MINTAMT"], errors="coerce").fillna(0.0)
    check("MINTAMT_ALL_ZERO", bool((mint.abs() <= TOL).all()), f"nz={(mint.abs()>TOL).sum()}")

    # Golden policy exact
    gpay = clmp[clmp["MPOLICY"].map(_strip) == GOLDEN]
    check("GOLDEN_4_PAYEES", len(gpay) == 4, f"n={len(gpay)}")
    if len(gpay):
        check(
            "GOLDEN_SUM_5145_67",
            abs(round(gpay["MAMOUNT"].map(_money).sum(), 2) - 5145.67) <= TOL,
            str(round(gpay["MAMOUNT"].map(_money).sum(), 2)),
        )

    # Holds must still have zero payees (do not fabricate)
    hold_payee_bad = []
    if len(holds):
        for pol in holds["mpolicy"].map(_strip):
            n = int((clmp["MPOLICY"].map(_strip) == pol).sum())
            if n > 0:
                hold_payee_bad.append(f"{pol}:{n}")
    check("HOLDS_STILL_ZERO_PAYEE", len(hold_payee_bad) == 0, str(hold_payee_bad))

    # Meta / delta (surrender backfill may add more rows afterward)
    if meta:
        expected_total = int(meta.get("before_clmp_rows", 0)) + int(meta.get("rows_added", 0))
        check(
            "CLMP_DELTA_MATCHES_META",
            int(len(clmp)) >= expected_total,
            f"len={len(clmp)} expected>={expected_total}",
        )
        check("QUIKCLMS_NOT_MUTATED_FLAG", meta.get("quikclms_mutated") is False, str(meta.get("quikclms_mutated")))
        check(
            "HEADER_MONEY_UNCHANGED_FLAG",
            bool(meta.get("header_money_unchanged")),
            str(meta.get("header_money_unchanged")),
        )
        check(
            "POLICIES_BACKFILLED_META",
            int(meta.get("policies_backfilled", 0) or 0) >= 137,
            str(meta.get("policies_backfilled")),
        )

    # #134 memo marker still present on a 308 sample if available
    marker = "CSO_CONTROLLED_NO_PACTG_HISTORY"
    memo_hits = int(clms["MEMOTEXT"].astype(str).str.contains(marker, regex=False).sum()) if "MEMOTEXT" in clms.columns else 0
    check("ISSUE134_MARKER_PRESERVED", memo_hits >= 1, f"hits={memo_hits}")

    # Residual MATCH_CSO zero-payee should equal holds only (3)
    clmp_cnt = clmp.groupby(clmp["MPOLICY"].map(_strip)).size().to_dict()
    residual = []
    if len(class_df):
        for _, r in class_df.iterrows():
            pol = _strip(r["mpolicy"])
            cls = _strip(r["class"])
            n = int(clmp_cnt.get(pol, 0))
            if cls in ("SAFE_BACKFILL", "ALREADY_BACKFILLED") and n == 0:
                residual.append(pol)
            if cls.startswith("HOLD") and n == 0:
                pass  # expected
    check("NO_SAFE_LEFT_ZERO", len(residual) == 0, f"residual_safe_zero={residual[:8]}")

    result = {
        "reason": "MATCH_CSO_EXISTING_HEADER_ZERO_PAYEE_COHORT",
        "pass": fails == 0,
        "fail_count": fails,
        "safe_n": int(len(safe)),
        "already_n": int(len(already)),
        "hold_n": hold_n,
        "checks": checks,
        "clmp_total_rows": int(len(clmp)),
        "golden_payees": int(len(gpay)),
    }
    OUT.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps({"pass": result["pass"], "fail_count": fails, "safe_n": result["safe_n"], "hold_n": hold_n}, indent=2))
    for c in checks:
        if c["status"] != "PASS":
            print("FAIL", c)
    print("Wrote", OUT)
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
