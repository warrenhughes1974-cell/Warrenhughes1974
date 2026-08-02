#!/usr/bin/env python3
"""Issue #135 — focused production validator (Option-3 + 459 expansion)."""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from qla_core.issue135_cso_claims_expansion import CSO_NO_PACTG_MARKER  # noqa: E402

EVIDENCE = ROOT / "Issue_Log_Items" / "Issue_135" / "evidence"
CLMS = ROOT / "QLA_Migration" / "Output" / "quikclms.csv"
CLMP = ROOT / "QLA_Migration" / "Output" / "quikclmp.csv"
ANALYSIS = EVIDENCE / "issue135_459_analysis_per_policy.csv"
OPTION3_CLMS = EVIDENCE / "issue135_option3_quikclms_overlay.csv"
OPTION3_SUMMARY = EVIDENCE / "issue135_option3_candidate_summary.csv"
TOL = 0.01


def _strip(v) -> str:
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return ""
    t = str(v).strip()
    return "" if t.lower() in ("nan", "none") else t


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
    analysis = pd.read_csv(ANALYSIS, dtype=str, keep_default_na=False)
    o3 = pd.read_csv(OPTION3_CLMS, dtype=str, keep_default_na=False)
    o3sum = (
        pd.read_csv(OPTION3_SUMMARY, dtype=str, keep_default_na=False)
        if OPTION3_SUMMARY.is_file()
        else pd.DataFrame()
    )

    # MINTAMT all zero
    mint = pd.to_numeric(clms["MINTAMT"], errors="coerce").fillna(0.0)
    check("MINTAMT_ALL_ZERO", bool((mint.abs() <= TOL).all()), f"nonzero={(mint.abs()>TOL).sum()}")

    # Duplicate keys
    key = clms["MPOLICY"].map(_strip) + "|" + clms["CLAIMNUM"].map(_strip) + "|" + clms["MSEQ"].map(_strip)
    dups = int(key.duplicated().sum())
    check("NO_DUP_MPOLICY_CLAIMNUM_MSEQ", dups == 0, f"dups={dups}")

    # Schema columns
    need_clms = {
        "MPOLICY", "CLAIMNUM", "CLAIMSTAT", "MPAID", "MINTAMT", "MEMOTEXT", "MPHASE", "MSEQ", "ORIGSTTUS"
    }
    need_clmp = {"MPOLICY", "MAMOUNT", "MPAYNAME", "MSEQ", "MCHECKNO"}
    check("CLMS_SCHEMA", need_clms.issubset(set(clms.columns)), str(sorted(need_clms - set(clms.columns))))
    check("CLMP_SCHEMA", need_clmp.issubset(set(clmp.columns)), str(sorted(need_clmp - set(clmp.columns))))

    # MPOLICY trailing C
    bad_c = int((~clms["MPOLICY"].map(_strip).str.endswith("C")).sum()) if len(clms) else 0
    check("MPOLICY_TRAILING_C", bad_c == 0, f"bad={bad_c}")

    # Option 3 corrected MPAID
    o3_ok = 0
    o3_bad = []
    for _, r in o3.iterrows():
        pol = _strip(r["MPOLICY"])
        exp = _money(r["MPAID"])
        rows = clms[clms["MPOLICY"].map(_strip) == pol]
        death = rows[rows["CLAIMSTAT"].map(_strip) == "2"]
        use = death if len(death) else rows
        if not len(use):
            o3_bad.append(f"{pol}:missing")
            continue
        got = _money(use.iloc[0]["MPAID"])
        if abs(got - exp) <= TOL:
            o3_ok += 1
        else:
            o3_bad.append(f"{pol}:{got}!={exp}")
    check("OPTION3_MPAID_MATCH", len(o3_bad) == 0, f"ok={o3_ok} bad={o3_bad[:5]}")

    # Teachers
    teachers = {
        "9011156098C": 15000.0,
        "9010914301C": 25019.98,
        "9010391359C": 1260.06,
    }
    t_bad = []
    for pol, exp in teachers.items():
        rows = clms[clms["MPOLICY"].map(_strip) == pol]
        if not len(rows) or abs(_money(rows.iloc[0]["MPAID"]) - exp) > TOL:
            t_bad.append(pol)
    check("TEACHER_MPAID", len(t_bad) == 0, str(t_bad))

    # 9 holds not emitted as new death headers from HOLD category
    holds = analysis[analysis["category"].map(_strip) == "HOLD_INCOMPLETE_SOURCE"]
    hold_pols = set(holds["mpolicy"].map(_strip))
    # They must NOT have been newly emitted with ISSUE135 markers; if already absent, stay absent
    hold_present = []
    for pol in sorted(hold_pols):
        rows = clms[clms["MPOLICY"].map(_strip) == pol]
        if len(rows):
            # fail only if our expansion marker/lineage present
            memo = " ".join(rows["MEMOTEXT"].map(_strip).tolist())
            if "ISSUE135_" in memo or CSO_NO_PACTG_MARKER in memo or "HEADER_ONLY_NO_PACTG" in memo:
                hold_present.append(pol)
            # also fail if any death row exists that wasn't there before expansion intent
            # For these 9, recon said absent from output — so any presence is a fail
            hold_present.append(pol)
    # Dedup
    hold_present = sorted(set(hold_present))
    check("HOLD9_NOT_EMITTED", len(hold_present) == 0, f"present={hold_present}")

    # 308 header-only
    no_pactg = analysis[analysis["category"].map(_strip) == "NO_PACTG_HISTORY"]
    n308_ok = 0
    n308_bad = []
    clmp_pols = set(clmp["MPOLICY"].map(_strip))
    for _, r in no_pactg.iterrows():
        pol = _strip(r["mpolicy"])
        exp = _money(r["cso_total_paid"])
        rows = clms[clms["MPOLICY"].map(_strip) == pol]
        if not len(rows):
            n308_bad.append(f"{pol}:missing")
            continue
        row = rows.iloc[0]
        memo = _strip(row.get("MEMOTEXT", ""))
        mpaid = _money(row.get("MPAID"))
        mint = _money(row.get("MINTAMT"))
        has_clmp = pol in clmp_pols
        if (
            abs(mpaid - exp) <= TOL
            and abs(mint) <= TOL
            and CSO_NO_PACTG_MARKER in memo
            and not has_clmp
        ):
            n308_ok += 1
        else:
            n308_bad.append(
                f"{pol}:mpaid={mpaid},marker={CSO_NO_PACTG_MARKER in memo},clmp={has_clmp}"
            )
    check(
        "HEADER_ONLY_308",
        len(n308_bad) == 0 and n308_ok == len(no_pactg),
        f"ok={n308_ok}/{len(no_pactg)} bad_sample={n308_bad[:5]}",
    )

    # 142 derived — header MPAID = CSO; payee sum matches when payees exist
    derived = analysis[analysis["category"].map(_strip) == "DERIVED_HIGH"]
    d_ok = 0
    d_bad = []
    payee_mismatch = []
    for _, r in derived.iterrows():
        pol = _strip(r["mpolicy"])
        exp = _money(r["cso_total_paid"])
        rows = clms[clms["MPOLICY"].map(_strip) == pol]
        if not len(rows):
            d_bad.append(f"{pol}:missing")
            continue
        mpaid = _money(rows.iloc[0]["MPAID"])
        mint = _money(rows.iloc[0]["MINTAMT"])
        if abs(mpaid - exp) > TOL or abs(mint) > TOL:
            d_bad.append(f"{pol}:mpaid={mpaid}")
            continue
        pays = clmp[clmp["MPOLICY"].map(_strip) == pol]
        if len(pays):
            psum = float(pd.to_numeric(pays["MAMOUNT"], errors="coerce").fillna(0).sum())
            if abs(psum - exp) > TOL:
                payee_mismatch.append(f"{pol}:{psum}!={exp}")
                continue
            # no fabricated names
            if pays["MPAYNAME"].map(_strip).str.contains("NEEDS_PAYEE_IDENTITY", na=False).any():
                payee_mismatch.append(f"{pol}:fabricated_name")
                continue
        d_ok += 1
    check(
        "DERIVED_142_HEADERS",
        len(d_bad) == 0,
        f"ok={d_ok}/{len(derived)} missing_or_amt={d_bad[:5]}",
    )
    check("DERIVED_PAYEE_SUMS", len(payee_mismatch) == 0, f"bad={payee_mismatch[:5]}")

    # Non-target table untouched heuristic: only clms/clmp intended — file mtime check skipped;
    # verify a sample of unrelated policies unchanged vs option3 non-targets keep prior if MATCH
    # Spot-check: a known MATCH policy amount still present
    sample_ok = True
    sample_detail = ""
    if "9010402010C" in set(clms["MPOLICY"].map(_strip)):
        got = _money(clms.loc[clms["MPOLICY"].map(_strip) == "9010402010C", "MPAID"].iloc[0])
        sample_ok = abs(got - 8920.15) <= TOL
        sample_detail = f"9010402010C={got}"
    check("NON_TARGET_SPOTCHECK_9010402010C", sample_ok, sample_detail)

    # No fabricated check numbers on new derived/header-only: MCHECKNO digit-only or 0
    # (existing may have real checks)
    # Fabricated NEEDS name absent globally after apply
    fab = int(clmp["MPAYNAME"].map(_strip).str.contains("NEEDS_PAYEE_IDENTITY", na=False).sum()) if len(clmp) else 0
    check("NO_FABRICATED_PAYEE_STUBS", fab == 0, f"count={fab}")

    overall = "PASS" if fails == 0 else "FAIL"
    out = {
        "generated_at": pd.Timestamp.now("UTC").strftime("%Y-%m-%dT%H:%M:%SZ"),
        "overall": overall,
        "fail_count": fails,
        "checks": checks,
        "clms_rows": int(len(clms)),
        "clmp_rows": int(len(clmp)),
        "claimstat_counts": Counter(clms["CLAIMSTAT"].map(_strip)).most_common(),
    }
    out_path = EVIDENCE / "issue135_production_validation.json"
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=2)

    print(f"Issue #135 production validation: {overall} (fails={fails})")
    for c in checks:
        print(f"  {c['status']}: {c['check']} — {c['detail']}")
    print(f"  wrote {out_path}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
