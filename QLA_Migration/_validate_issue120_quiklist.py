"""Issue #120 — validate QuikList emit (active six LST groups)."""
from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from qla_core.quiklist_converter import (
    ACTIVE_QUIKLIST_GROUPS,
    QUIKLIST_DEFAULT_MBILLDAY,
    QUIKLIST_DEFAULT_MBILLMODE,
    QUIKLIST_DEFAULT_MLAPSEL,
    QUIKLIST_DEFAULT_MLAPSEH,
    QUIKLIST_DEFAULT_MSTATUS,
    QUIKLIST_DEFAULT_MSORT,
    QUIKLIST_MCOMP,
    TERMINATED_ORPHAN_GROUPS,
    build_quiklist_rows,
    emit_quiklist_csv,
)
from qla_core.schema_constants import QUIKLIST_SCHEMA

SRC = ROOT / "QLA_Migration" / "Source"
OUT = ROOT / "QLA_Migration" / "Output"
TEST_VAL = OUT / "Test_Validation"
EVIDENCE = ROOT / "Issue_Log_Items" / "Issue_120" / "evidence"

EXPECTED_TRUNCATED_NAMES = {
    "07132": "MISSOURI FEDERAL SAVINGS BANK ",
    "T8342L": "LAND O'LAKES - MINNESOTA - LIF",
    "Z2583L": "NEW ERA LIFE INSURANCE - OMAHA",
}

EXPECTED_ADDRESSES = {
    "07132": {
        "MBILLCITY": "MEMPHIS",
        "MBILLST": "MO",
        "MBILLZIP": "",
    },
    "07777L": {
        "MBILLADDR1": "ATTN:  ANN HETHERINGTON",
        "MBILLADDR2": "PO BOX 34350",
        "MBILLCITY": "OMAHA",
        "MBILLST": "NE",
        "MBILLZIP": "68134",
    },
    "T8342L": {
        "MBILLADDR1": "C/O THE INS CENTER - DARC",
        "MBILLCITY": "ONALASKA",
        "MBILLST": "WI",
        "MBILLZIP": "54650",
    },
}


def _norm(value: object) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    return str(value).strip()


def _check_quikmstr_references(df: pd.DataFrame, errors: list[str]) -> None:
    mstr_path = OUT / "quikmstr.csv"
    if not mstr_path.is_file():
        errors.append("quikmstr.csv missing — cannot verify active group references")
        return
    mstr = pd.read_csv(mstr_path, dtype=str).fillna("")
    active_groups = set(ACTIVE_QUIKLIST_GROUPS)
    referenced = {
        _norm(g)
        for g in mstr.loc[mstr["MBILLFRM"].astype(str).str.strip() == "3", "MGROUP"].tolist()
        if _norm(g) in active_groups
    }
    missing = active_groups - referenced
    if missing:
        errors.append(f"active quikmstr MBILLFRM=3 missing MGROUP refs: {sorted(missing)}")


def _check_orphan_waiver(errors: list[str], warnings: list[str]) -> None:
    mstr_path = OUT / "quikmstr.csv"
    if not mstr_path.is_file():
        return
    mstr = pd.read_csv(mstr_path, dtype=str).fillna("")
    lst_groups = {
        _norm(g)
        for g in mstr.loc[mstr["MBILLFRM"].astype(str).str.strip() == "3", "MGROUP"].tolist()
        if _norm(g)
    }
    orphans_present = sorted(lst_groups & TERMINATED_ORPHAN_GROUPS)
    if not orphans_present:
        warnings.append("no terminated orphan MGROUP values found on quikmstr MBILLFRM=3")
    else:
        warnings.append(
            "DG-QUIKMSTR-015 waiver scope — terminated-only groups on quikmstr without QuikList: "
            + ", ".join(orphans_present)
        )


def main() -> int:
    errors: list[str] = []
    warnings: list[str] = []

    built = build_quiklist_rows(str(SRC))
    if len(built) != 6:
        errors.append(f"build_quiklist_rows expected 6 rows, got {len(built)}")
    built_groups = {_norm(r["MGROUP"]) for r in built}
    if built_groups != set(ACTIVE_QUIKLIST_GROUPS):
        errors.append(f"unexpected built groups: {sorted(built_groups)}")

    info = emit_quiklist_csv(str(SRC), str(OUT))
    out_path = Path(info["path"])
    if not out_path.is_file():
        errors.append(f"missing emit file: {out_path}")
        _report(errors, warnings, info)
        return 1

    df = pd.read_csv(out_path, dtype=str).fillna("")
    if len(df) != 6:
        errors.append(f"expected 6 CSV rows, got {len(df)}")
    if list(df.columns) != QUIKLIST_SCHEMA:
        errors.append("CSV column order mismatch vs Help §7.149 / schema_manifest")

    groups = sorted({_norm(v) for v in df["MGROUP"].tolist()})
    if groups != sorted(ACTIVE_QUIKLIST_GROUPS):
        errors.append(f"unexpected MGROUP keys: {groups}")

    for _, row in df.iterrows():
        group = _norm(row["MGROUP"])
        if _norm(row["MCOMP"]) != QUIKLIST_MCOMP:
            errors.append(f"{group}: MCOMP expected {QUIKLIST_MCOMP}, got {row['MCOMP']!r}")
        if not _norm(row["MBILLNAME"]):
            errors.append(f"{group}: MBILLNAME blank")
        if len(_norm(row["MBILLNAME"])) > 30:
            errors.append(f"{group}: MBILLNAME exceeds 30 chars")
        if _norm(row["MSORT"]) != QUIKLIST_DEFAULT_MSORT:
            errors.append(f"{group}: MSORT expected {QUIKLIST_DEFAULT_MSORT}")
        for field, expected in (
            ("MLAPSEL", str(QUIKLIST_DEFAULT_MLAPSEL)),
            ("MLAPSEH", str(QUIKLIST_DEFAULT_MLAPSEH)),
            ("MBILLDAY", str(QUIKLIST_DEFAULT_MBILLDAY)),
            ("MBILLMODE", str(QUIKLIST_DEFAULT_MBILLMODE)),
        ):
            if _norm(row[field]) != expected:
                errors.append(f"{group}: {field} expected {expected}, got {row[field]!r}")
        if _norm(row["MSTATUS"]) != QUIKLIST_DEFAULT_MSTATUS:
            errors.append(f"{group}: MSTATUS expected {QUIKLIST_DEFAULT_MSTATUS}")

        if group in EXPECTED_TRUNCATED_NAMES:
            actual_name = str(row["MBILLNAME"]) if pd.notna(row["MBILLNAME"]) else ""
            if actual_name != EXPECTED_TRUNCATED_NAMES[group]:
                errors.append(
                    f"{group}: MBILLNAME truncate expected {EXPECTED_TRUNCATED_NAMES[group]!r}, "
                    f"got {actual_name!r}"
                )

        if group in EXPECTED_ADDRESSES:
            for field, expected in EXPECTED_ADDRESSES[group].items():
                if _norm(row[field]) != expected:
                    errors.append(f"{group}: {field} expected {expected!r}, got {row[field]!r}")

        if group == "07777L" and "@" in _norm(row["MBILLADDR1"]):
            errors.append("07777L: postal preference failed — email row chosen")
        if group == "T8342L" and "@" in _norm(row["MBILLADDR1"]):
            errors.append("T8342L: postal preference failed — email row chosen")

    _check_quikmstr_references(df, errors)
    _check_orphan_waiver(errors, warnings)

    summary = {
        "status": "PASS" if not errors else "FAIL",
        "row_count": len(df),
        "groups": groups,
        "terminated_orphan_waiver_groups": sorted(TERMINATED_ORPHAN_GROUPS),
        "orphan_waiver_note": (
            "Approved DG-QUIKMSTR-015 waiver: six terminated-only LST groups remain on "
            "quikmstr.MGROUP without QuikList rows under active-six scope."
        ),
        "errors": errors,
        "warnings": warnings,
        "emit_path": str(out_path),
    }

    EVIDENCE.mkdir(parents=True, exist_ok=True)
    (EVIDENCE / "issue120_validation_summary.json").write_text(
        json.dumps(summary, indent=2),
        encoding="utf-8",
    )

    if errors:
        _report(errors, warnings, info, groups)
        return 1

    TEST_VAL.mkdir(parents=True, exist_ok=True)
    shutil.copy2(out_path, TEST_VAL / "quiklist.csv")
    print("Issue #120 validation: PASS")
    print(f"  rows={len(df)} groups={groups}")
    print(f"  emit={out_path}")
    print(f"  test_validation={TEST_VAL / 'quiklist.csv'}")
    for note in warnings:
        print(f"  waiver: {note}")
    return 0


def _report(errors, warnings, info, groups=None) -> None:
    print("Issue #120 validation: FAIL")
    for err in errors:
        print(f"  - {err}")
    for note in warnings:
        print(f"  waiver: {note}")
    if groups:
        print(f"  groups_seen={groups}")
    print(f"  terminated_orphan_waiver_groups={sorted(TERMINATED_ORPHAN_GROUPS)}")


if __name__ == "__main__":
    raise SystemExit(main())
