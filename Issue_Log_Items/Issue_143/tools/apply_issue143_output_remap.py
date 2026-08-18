"""Apply Issue #143 BF RPU MUNIT remap to Output/quikridr.csv (23-row set only).

Uses the same locked rule as qla_core.issue143_rpu_munit. Does not rewrite
MPREM, MVPU, MSAVEUNIT, MPOLICY, or QuikIswl (#124).
"""
from __future__ import annotations

import csv
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from qla_core.issue143_rpu_munit import (  # noqa: E402
    ISSUE143_EPS,
    classify_issue143_row,
    is_rpu_paid_up_type,
    seq_is_phase1,
)
from qla_core.normalize_utils import normalize  # noqa: E402
from qla_core.quikridr_decimal_emit import format_quikridr_decimal_field  # noqa: E402

SRC = ROOT / "QLA_Migration" / "Source"
OUT = ROOT / "QLA_Migration" / "Output"
EVID = ROOT / "Issue_Log_Items" / "Issue_143" / "evidence"
TV = OUT / "Test_Validation"
LOCKED_CUT = "20260630"
GOLD = "9010757606C"
ISWL_PLANS = {"1658C1", "1659C2", "1659CR"}


def _src(name: str) -> Path:
    p = SRC / f"{name}_Extract_{LOCKED_CUT}.csv"
    if not p.is_file():
        raise SystemExit(f"missing locked source {p}")
    return p


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="latin1", errors="replace") as fh:
        return list(csv.DictReader(fh))


def _norm_headers(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    out = []
    for row in rows:
        out.append({str(k).strip().upper() if k else k: (v if v is not None else "") for k, v in row.items()})
    return out


def inventory() -> dict[str, dict]:
    rpu: set[str] = set()
    for row in _norm_headers(_read_csv(_src("PPOLC_PolicyMaster"))):
        if is_rpu_paid_up_type(row.get("PAID_UP_TYPE")):
            pol = normalize(row.get("POLICY_NUMBER", ""))
            if pol:
                rpu.add(pol)

    typ: dict[str, dict] = {}
    for row in _norm_headers(_read_csv(_src("PPBENTYP_BenefitType"))):
        pol = normalize(row.get("POLICY_NUMBER", ""))
        if pol in rpu and seq_is_phase1(row.get("BENEFIT_SEQ")):
            typ[pol] = row

    by_kind: dict[str, dict] = {"candidate": {}, "aligned_bf": {}, "ba": {}}
    for row in _norm_headers(_read_csv(_src("PPBEN_PolicyBenefit"))):
        pol = normalize(row.get("POLICY_NUMBER", ""))
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
        if rec.kind in by_kind:
            by_kind[rec.kind][pol] = rec
    return by_kind


def main() -> int:
    ridr_path = OUT / "quikridr.csv"
    if not ridr_path.is_file():
        raise SystemExit(f"missing {ridr_path}")

    pops = inventory()
    candidates = pops["candidate"]
    if len(candidates) != 23:
        raise SystemExit(f"locked candidate count is 23; source classified {len(candidates)}")

    EVID.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup = EVID / f"quikridr_pre_issue143_{stamp}.csv"
    shutil.copy2(ridr_path, backup)

    with ridr_path.open(newline="", encoding="latin1", errors="replace") as fh:
        reader = csv.DictReader(fh)
        fieldnames = reader.fieldnames or []
        rows = list(reader)

    changed = []
    protected_ok = True
    for row in rows:
        keys = {str(k).strip().upper(): k for k in row if k}
        pol_k = keys.get("MPOLICY")
        ph_k = keys.get("MPHASE")
        un_k = keys.get("MUNIT")
        if not pol_k or not ph_k or not un_k:
            continue
        mpolicy = str(row[pol_k]).strip()
        phase = str(row[ph_k]).strip()
        if phase not in ("1", "01"):
            continue
        src_pol = mpolicy[:-1] if mpolicy.endswith("C") else mpolicy
        rec = candidates.get(normalize(src_pol))
        if rec is None:
            continue
        before = row[un_k]
        before_mprem = row.get(keys.get("MPREM", ""), "")
        before_mvpu = row.get(keys.get("MVPU", ""), "")
        before_msave = row.get(keys.get("MSAVEUNIT", ""), "")
        before_mpolicy = row[pol_k]
        work = {"MUNIT": before}
        work["MUNIT"] = rec.expected_munit
        row[un_k] = format_quikridr_decimal_field("MUNIT", work["MUNIT"])
        after_mprem = row.get(keys.get("MPREM", ""), "")
        after_mvpu = row.get(keys.get("MVPU", ""), "")
        after_msave = row.get(keys.get("MSAVEUNIT", ""), "")
        after_mpolicy = row[pol_k]
        if (
            after_mprem != before_mprem
            or after_mvpu != before_mvpu
            or after_msave != before_msave
            or after_mpolicy != before_mpolicy
        ):
            protected_ok = False
        changed.append(
            {
                "mpolicy": mpolicy,
                "mplan": str(row.get(keys.get("MPLAN", ""), "")).strip(),
                "before_munit": before,
                "after_munit": row[un_k],
                "expected_munit": rec.expected_munit,
                "bf_current_db": rec.bf_current_db,
                "vpu": rec.value_per_unit,
                "amount_ins": round((rec.expected_munit or 0) * (rec.value_per_unit or 0), 2),
                "mprem": after_mprem,
                "mvpu": after_mvpu,
                "msaveunit": after_msave,
            }
        )

    tmp = ridr_path.with_suffix(".csv.tmp")
    with tmp.open("w", newline="", encoding="latin1") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    tmp.replace(ridr_path)

    TV.mkdir(parents=True, exist_ok=True)
    shutil.copy2(ridr_path, TV / "quikridr.csv")

    iswl_mdb = []
    iswl_path = OUT / "QuikIswl.csv"
    iswl_by_pol = {}
    if iswl_path.is_file():
        for row in csv.DictReader(iswl_path.open(newline="", encoding="utf-8-sig", errors="replace")):
            iswl_by_pol[str(row.get("MPOLICY", "")).strip()] = row
    for rec in changed:
        if rec["mplan"] not in ISWL_PLANS:
            continue
        cur = iswl_by_pol.get(rec["mpolicy"], {})
        new_mdb = round((rec["expected_munit"] or 0) * 1000.0, 2)
        try:
            old_mdb = float(str(cur.get("MDB", "") or "0").replace(",", ""))
        except ValueError:
            old_mdb = None
        iswl_mdb.append(
            {
                "mpolicy": rec["mpolicy"],
                "mplan": rec["mplan"],
                "current_quikiswl_mdb": old_mdb,
                "expected_mdb_after_next_seed": new_mdb,
                "note": "Issue #124 MDB=MUNIT*1000; QuikIswl not rewritten by #143",
            }
        )

    gold = next((r for r in changed if r["mpolicy"].strip() == GOLD), None)
    summary = {
        "source_cut": LOCKED_CUT,
        "candidate_count": len(candidates),
        "aligned_bf_count": len(pops["aligned_bf"]),
        "ba_count": len(pops["ba"]),
        "changed_output_rows": len(changed),
        "protected_fields_untouched": protected_ok,
        "gold": gold,
        "backup": str(backup.relative_to(ROOT)),
        "test_validation": "QLA_Migration/Output/Test_Validation/quikridr.csv",
        "issue124_expected_mdb": iswl_mdb,
        "eps": ISSUE143_EPS,
    }
    evid_path = EVID / "issue143_apply_summary.json"
    evid_path.write_text(json.dumps({"summary": summary, "changed": changed}, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))
    print("wrote", evid_path)
    return 0 if len(changed) == 23 and gold and protected_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
