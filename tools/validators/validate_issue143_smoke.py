"""
Issue #143 — required final-release smoke.

Any FAIL on checks 1–9 blocks release sign-off.

Usage:
  python tools/validators/validate_issue143_smoke.py
"""
from __future__ import annotations

import csv
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[2]
if str(PROJECT) not in sys.path:
    sys.path.insert(0, str(PROJECT))

from qla_core.issue143_rpu_munit import (  # noqa: E402
    ISSUE143_EPS,
    classify_issue143_row,
    is_rpu_paid_up_type,
    seq_is_phase1,
)
from qla_core.normalize_utils import normalize  # noqa: E402

SRC = PROJECT / "QLA_Migration" / "Source"
OUT = PROJECT / "QLA_Migration" / "Output"
EVID = PROJECT / "Issue_Log_Items" / "Issue_143" / "evidence"
REPORTS = PROJECT / "QLA_Migration" / "Reports"
LOCKED_CUT = "20260630"
GOLD = "9010757606C"
GOLD_MUNIT = 19.10196
GOLD_MVPU = 1000.00
GOLD_AMOUNT = 19101.96
AMT_EPS = 0.02
ISSUE55_TRACES = {
    ("9018495BC", "1"): 0.0,
    ("9018495BC", "2"): 0.53,
    ("9018499CC", "1"): 0.0,
    ("9018499CC", "2"): 1.05,
    ("9018510C", "1"): 0.0,
    ("9018510C", "2"): 0.647,
}


def fnum(v):
    s = str(v or "").replace(",", "").strip()
    if not s:
        return None
    try:
        return float(s)
    except ValueError:
        return None


def src_path(stem: str) -> Path:
    return SRC / f"{stem}_Extract_{LOCKED_CUT}.csv"


def read_rows(path: Path, encoding: str = "latin1") -> list[dict[str, str]]:
    with path.open(newline="", encoding=encoding, errors="replace") as fh:
        return [
            {str(k).strip().upper() if k else k: ("" if v is None else v) for k, v in row.items()}
            for row in csv.DictReader(fh)
        ]


def qla_key(pol: str) -> str:
    p = normalize(pol)
    if not p:
        return ""
    return p if p.endswith("C") else p + "C"


def inventory():
    rpu = {}
    for row in read_rows(src_path("PPOLC_PolicyMaster")):
        if is_rpu_paid_up_type(row.get("PAID_UP_TYPE")):
            pol = normalize(row.get("POLICY_NUMBER"))
            if pol:
                rpu[pol] = row
    typ = {}
    for row in read_rows(src_path("PPBENTYP_BenefitType")):
        pol = normalize(row.get("POLICY_NUMBER"))
        if pol in rpu and seq_is_phase1(row.get("BENEFIT_SEQ")):
            typ[pol] = row
    groups = {"candidate": {}, "aligned_bf": {}, "ba": {}}
    for row in read_rows(src_path("PPBEN_PolicyBenefit")):
        pol = normalize(row.get("POLICY_NUMBER"))
        if pol not in rpu or not seq_is_phase1(row.get("BENEFIT_SEQ")):
            continue
        trow = typ.get(pol, {})
        rec = classify_issue143_row(
            policy=pol,
            units=row.get("NUMBER_OF_UNITS"),
            value_per_unit=row.get("VALUE_PER_UNIT"),
            type_code=trow.get("TYPE_CODE"),
            bf_current_db=trow.get("BF_CURRENT_DB"),
            is_rpu=True,
        )
        if rec.kind in groups:
            groups[rec.kind][pol] = rec
    return groups, rpu


def ridr_lookup(store, qla):
    return store.get((qla, "1")) or store.get((qla, "01"))


def check(name: str, ok: bool, detail: str) -> dict:
    return {"id": name, "status": "PASS" if ok else "FAIL", "detail": detail}


def main() -> int:
    checks: list[dict] = []
    groups, _rpu = inventory()
    cand, aligned, ba = groups["candidate"], groups["aligned_bf"], groups["ba"]

    ridr_path = OUT / "quikridr.csv"
    if not ridr_path.is_file():
        print("FAIL: missing quikridr.csv")
        return 1
    ridr = {}
    for row in read_rows(ridr_path):
        ridr[(str(row.get("MPOLICY", "")).strip(), str(row.get("MPHASE", "")).strip())] = row

    mstr = {}
    mstr_path = OUT / "quikmstr.csv"
    if mstr_path.is_file():
        for row in read_rows(mstr_path):
            mstr[str(row.get("MPOLICY", "")).strip()] = str(row.get("MSTATUS", "")).strip()

    # 1. 23 corrected MUNIT
    corrected = 0
    missing = []
    for pol, rec in cand.items():
        row = ridr_lookup(ridr, qla_key(pol))
        munit = fnum((row or {}).get("MUNIT"))
        if row and rec.expected_munit is not None and munit is not None and abs(munit - rec.expected_munit) <= ISSUE143_EPS:
            corrected += 1
        else:
            missing.append(qla_key(pol))
    checks.append(
        check(
            "1_corrected_munit_23",
            len(cand) == 23 and corrected == 23 and not missing,
            f"candidates={len(cand)} corrected={corrected} missing={missing}",
        )
    )

    # 2. Gold
    gold = ridr_lookup(ridr, GOLD) or {}
    g_munit = fnum(gold.get("MUNIT"))
    g_mvpu = fnum(gold.get("MVPU"))
    g_amt = round((g_munit or 0) * (g_mvpu or 0), 2)
    gold_ok = (
        g_munit is not None
        and abs(g_munit - GOLD_MUNIT) < 1e-6
        and g_mvpu is not None
        and abs(g_mvpu - GOLD_MVPU) <= 0.01
        and abs(g_amt - GOLD_AMOUNT) <= AMT_EPS
    )
    checks.append(
        check(
            "2_gold_9010757606C",
            gold_ok,
            f"MUNIT={gold.get('MUNIT')} MVPU={gold.get('MVPU')} AmountIns={g_amt}",
        )
    )

    # 3. Amount Ins = DD
    db_fail = []
    for pol, rec in cand.items():
        row = ridr_lookup(ridr, qla_key(pol))
        if not row or rec.bf_current_db is None:
            db_fail.append(qla_key(pol))
            continue
        amt = round((fnum(row.get("MUNIT")) or 0) * (fnum(row.get("MVPU")) or 0), 2)
        if abs(amt - rec.bf_current_db) > AMT_EPS:
            db_fail.append(f"{qla_key(pol)} {amt}!={rec.bf_current_db}")
    checks.append(check("3_amount_ins_eq_column_dd", not db_fail, f"fails={db_fail or 0}"))

    # 4. 82 aligned unchanged
    aligned_ok = 0
    aligned_fail = []
    for pol, rec in aligned.items():
        row = ridr_lookup(ridr, qla_key(pol))
        munit = fnum((row or {}).get("MUNIT"))
        if row and rec.source_units is not None and munit is not None and abs(munit - rec.source_units) <= ISSUE143_EPS:
            aligned_ok += 1
        else:
            aligned_fail.append(qla_key(pol))
    checks.append(
        check(
            "4_aligned_bf_82_unchanged",
            len(aligned) == 82 and aligned_ok == 82,
            f"aligned={len(aligned)} unchanged={aligned_ok} fail={aligned_fail}",
        )
    )

    # 5. BA no remap (present rows still on source units)
    ba_remap = []
    ba_present_ok = 0
    for pol, rec in ba.items():
        row = ridr_lookup(ridr, qla_key(pol))
        if row is None:
            continue
        munit = fnum(row.get("MUNIT"))
        if rec.source_units is None or munit is None or abs(munit - rec.source_units) > ISSUE143_EPS:
            ba_remap.append(qla_key(pol))
        else:
            ba_present_ok += 1
    checks.append(
        check(
            "5_ba_199_no_remap",
            len(ba) == 199 and not ba_remap,
            f"ba_source={len(ba)} present_unchanged={ba_present_ok} remapped={ba_remap}",
        )
    )

    # 6. Protected fields
    prot_fail = []
    for pol, rec in {**cand, **aligned}.items():
        qla = qla_key(pol)
        row = ridr_lookup(ridr, qla)
        if not row:
            continue
        if rec.value_per_unit is not None:
            mvpu = fnum(row.get("MVPU"))
            if mvpu is None or abs(mvpu - rec.value_per_unit) > 0.01:
                prot_fail.append(f"{qla} MVPU")
        if str(row.get("MPOLICY", "")).strip() != qla:
            prot_fail.append(f"{qla} MPOLICY")
    if str(gold.get("MPREM", "")).strip() != "9.77037":
        prot_fail.append("gold MPREM")
    if str(gold.get("MSAVEUNIT", "")).strip() != "":
        prot_fail.append("gold MSAVEUNIT")
    checks.append(check("6_protected_mprem_mvpu_msave_mpolicy", not prot_fail, f"fails={prot_fail or 0}"))

    # 7. #55 / #108A
    floor_hits = 0
    for (_pol, _ph), row in ridr.items():
        u = fnum(row.get("MUNIT"))
        if u is not None and 0 < u < 0.001:
            floor_hits += 1
    t55 = []
    for (pol, ph), exp in ISSUE55_TRACES.items():
        actual = fnum((ridr.get((pol, ph)) or {}).get("MUNIT"))
        t55.append(actual is not None and abs(actual - exp) <= 0.001)
    i55_script = subprocess.run(
        [sys.executable, str(PROJECT / "tools" / "validators" / "validate_issue55_munit_floor.py")],
        cwd=str(PROJECT),
        capture_output=True,
        text=True,
        errors="replace",
    )
    msave_fail = []
    for pol, rec in cand.items():
        qla = qla_key(pol)
        row = ridr_lookup(ridr, qla) or {}
        if mstr.get(qla) == "45" and str(row.get("MSAVEUNIT") or "").strip() != "":
            msave_fail.append(qla)
    ok55_108 = floor_hits == 0 and all(t55) and i55_script.returncode == 0 and not msave_fail
    checks.append(
        check(
            "7_issue55_issue108a",
            ok55_108,
            f"floor={floor_hits} traces={all(t55)} validate_issue55={i55_script.returncode} msave_fail={msave_fail}",
        )
    )

    # 8. #124 MDB after authorized reseed
    iswl = {}
    iswl_path = OUT / "QuikIswl.csv"
    if iswl_path.is_file():
        for row in read_rows(iswl_path, encoding="utf-8-sig"):
            iswl[str(row.get("MPOLICY", "")).strip()] = fnum(row.get("MDB"))
    mdb_fail = []
    gold_mdb = None
    gold_exp_mdb = GOLD_AMOUNT
    for pol, rec in cand.items():
        qla = qla_key(pol)
        row = ridr_lookup(ridr, qla) or {}
        exp = round((rec.expected_munit or 0) * 1000.0, 2)
        stored = iswl.get(qla)
        if qla == GOLD:
            gold_mdb = stored
        if stored is None or abs(stored - exp) > 0.011:
            mdb_fail.append({"mpolicy": qla, "stored": stored, "expected": exp})
    checks.append(
        check(
            "8_issue124_mdb_after_reseed",
            not mdb_fail,
            f"gold_stored={gold_mdb} gold_expected={gold_exp_mdb} mismatches={len(mdb_fail)}",
        )
    )

    # 9. No unauthorized MUNIT remaps
    unauthorized = []
    for kind, recs in (("aligned_bf", aligned), ("ba", ba)):
        for pol, rec in recs.items():
            row = ridr_lookup(ridr, qla_key(pol))
            if not row or rec.source_units is None:
                continue
            munit = fnum(row.get("MUNIT"))
            if munit is None:
                continue
            if abs(munit - rec.source_units) > ISSUE143_EPS:
                unauthorized.append(qla_key(pol))
    extra_fail = bool(unauthorized) or corrected != 23
    checks.append(
        check(
            "9_no_unauthorized_munit",
            not extra_fail,
            f"unauthorized={unauthorized} authorized_corrected={corrected}",
        )
    )

    overall = "PASS" if all(c["status"] == "PASS" for c in checks) else "FAIL"
    report = {
        "smoke": "#143 Units Incorrect (RPU)",
        "result": overall,
        "blocks_release_on_fail": True,
        "generated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "engine_note": "v58.96 Closed row",
        "checks": checks,
        "issue124_mdb_mismatches": mdb_fail[:23],
    }
    EVID.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)
    evid_path = EVID / "issue143_smoke_summary.json"
    md_path = EVID / "Issue_143_Smoke_Report.md"
    gate_md = REPORTS / "issue143_smoke_latest.md"
    evid_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    lines = [
        "# Issue #143 — Final Release Smoke Report",
        "",
        f"**Generated:** {report['generated']}",
        f"**Overall:** **{overall}**",
        "",
        "A FAIL on any condition blocks final release sign-off.",
        "",
        "| # | Condition | Result | Detail |",
        "|---|-----------|--------|--------|",
    ]
    labels = {
        "1_corrected_munit_23": "23 authorized BF RPU still have corrected MUNIT",
        "2_gold_9010757606C": "Gold 9010757606C MUNIT=19.10196 MVPU=1000 Amount Ins=19101.96",
        "3_amount_ins_eq_column_dd": "23 rows MUNIT×MVPU = BF_CURRENT_DB / Column DD",
        "4_aligned_bf_82_unchanged": "82 aligned BF RPU unchanged",
        "5_ba_199_no_remap": "199 BA RPU receive no #143 remap",
        "6_protected_mprem_mvpu_msave_mpolicy": "MPREM / MVPU / MSAVEUNIT / MPOLICY unaffected",
        "7_issue55_issue108a": "Issue #55 and #108A protections pass",
        "8_issue124_mdb_after_reseed": "After authorized #124 reseed, MDB = corrected MUNIT×1000",
        "9_no_unauthorized_munit": "No unauthorized MUNIT changes outside the 23",
    }
    for c in checks:
        lines.append(f"| {c['id'].split('_', 1)[0]} | {labels.get(c['id'], c['id'])} | **{c['status']}** | {c['detail']} |")
    lines.extend(
        [
            "",
            f"**Issue #143 Smoke: {overall}**",
            "",
            "Command: `python tools/validators/validate_issue143_smoke.py`",
            "Also run via: `python tools/validators/validate_release_closed_issues.py --smoke-only`",
            "",
        ]
    )
    if overall == "FAIL":
        lines.append("RELEASE BLOCKED until every row above is PASS.")
    md = "\n".join(lines) + "\n"
    md_path.write_text(md, encoding="utf-8")
    gate_md.write_text(md, encoding="utf-8")

    print(md)
    print("wrote", evid_path)
    print("wrote", md_path)
    print(f"ISSUE #143 SMOKE: {overall}")
    return 0 if overall == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
