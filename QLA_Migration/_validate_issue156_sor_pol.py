"""Issue 156 validator: quikspec.SOR_POL = LifePRO PPOLC POLICY_NUMBER (no Issue #2 C).

Fail-closed against full QLA_Migration/Output/quikspec.csv. Exit 1 if the column
is missing, blank, or no longer matches the source policy number.
"""
from __future__ import annotations

import argparse
import csv
import json
import shutil
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from qla_core.lifepro_source_resolver import resolve_table_source  # noqa: E402
from qla_core.normalize_utils import format_qladmin_mpolicy, normalize  # noqa: E402

OUT = ROOT / "QLA_Migration" / "Output"
SRC = ROOT / "QLA_Migration" / "Source"
SPEC = OUT / "quikspec.csv"
TV = OUT / "Test_Validation"
SOR_POL = "SOR_POL"
SCHEMA_PREFIX = ("MPOLICY", "VANISH", "VANISHDT", "RESSTATE", "RESRVCAT", "SOR_POL")
TRACES = {
    "9011050114C": "9011050114",
    "9010143726C": "9010143726",
    "901122D991C": "901122D991",
    "901ML8487C": "901ML8487",
}


def _norm_pol(val: str) -> str:
    return str(val or "").strip().upper()


def _load_source_policy_by_mpolicy(src_dir: Path) -> dict[str, str]:
    path, _label = resolve_table_source(str(src_dir), "quikspec")
    if not path or not Path(path).is_file():
        raise FileNotFoundError(f"PPOLC extract not found under {src_dir}")
    out: dict[str, str] = {}
    with Path(path).open(newline="", encoding="latin1", errors="replace") as fh:
        reader = csv.DictReader(fh)
        cols = {str(c).replace("\ufeff", "").strip().upper(): c for c in (reader.fieldnames or [])}
        pol_c = cols.get("POLICY_NUMBER")
        if not pol_c:
            raise ValueError(f"PPOLC missing POLICY_NUMBER: {path}")
        for row in reader:
            first = [
                str(row.get(reader.fieldnames[i], "") or "")
                for i in range(min(3, len(reader.fieldnames or [])))
            ]
            if any("---" in v for v in first):
                continue
            src = normalize(row.get(pol_c, ""))
            if not src or src.replace("-", "") == "" or src.startswith("----"):
                continue
            mp = format_qladmin_mpolicy(src)
            if not mp:
                continue
            out.setdefault(mp, src)
            out.setdefault(mp.strip(), src)
            out.setdefault(_norm_pol(mp), src)
    return out


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--publish-test-validation", action="store_true")
    args = parser.parse_args()

    failures: list[str] = []
    summary = {
        "rows": 0,
        "filled": 0,
        "blank": 0,
        "source_mismatches": 0,
        "converted_key_copied": 0,
        "traces": {},
    }

    if not SPEC.is_file():
        print(f"FAIL: missing {SPEC}")
        return 1
    qs = pd.read_csv(SPEC, dtype=str).fillna("")
    qs.columns = [str(c).strip().upper() for c in qs.columns]
    missing = [c for c in SCHEMA_PREFIX if c not in qs.columns]
    if missing:
        failures.append(f"quikspec missing columns: {missing}")

    summary["rows"] = len(qs)
    if summary["rows"] < 4000:
        failures.append(f"quikspec rows={summary['rows']} below full-batch floor 4000")

    if SOR_POL in qs.columns:
        vals = qs[SOR_POL].astype(str).map(lambda x: str(x).strip())
        summary["filled"] = int((vals != "").sum())
        summary["blank"] = int((vals == "").sum())
        if summary["blank"]:
            failures.append(f"SOR_POL blank rows={summary['blank']}")
        if summary["rows"] >= 4000 and summary["filled"] == 0:
            failures.append("SOR_POL filled count is 0 on a full quikspec — Issue 156 dropped")

        copied = 0
        for _, row in qs.iterrows():
            mp = str(row.get("MPOLICY", "") or "").strip()
            sor = str(row.get(SOR_POL, "") or "").strip()
            if mp and sor and mp == sor and mp.endswith("C") and len(mp) == 11 and mp[:-1].isdigit():
                copied += 1
        summary["converted_key_copied"] = copied
        if copied:
            failures.append(
                f"SOR_POL equals converted MPOLICY on {copied} 10-digit+C rows "
                "(wrote QLAdmin key instead of LifePRO source)"
            )

    try:
        src_map = _load_source_policy_by_mpolicy(SRC)
    except (FileNotFoundError, ValueError) as exc:
        failures.append(str(exc))
        src_map = {}

    mismatches = 0
    if src_map and "MPOLICY" in qs.columns and SOR_POL in qs.columns:
        for _, row in qs.iterrows():
            mp = str(row.get("MPOLICY", "") or "")
            got = str(row.get(SOR_POL, "") or "").strip()
            exp = src_map.get(mp) or src_map.get(mp.strip()) or src_map.get(_norm_pol(mp), "")
            if exp and got != exp:
                mismatches += 1
        summary["source_mismatches"] = mismatches
        if mismatches:
            failures.append(f"SOR_POL vs PPOLC POLICY_NUMBER mismatches={mismatches}")

    spec_by_pol = {}
    if "MPOLICY" in qs.columns:
        for _, row in qs.iterrows():
            spec_by_pol[_norm_pol(row.get("MPOLICY", ""))] = row
    for pol, exp in TRACES.items():
        row = spec_by_pol.get(_norm_pol(pol), {})
        got = str(row.get(SOR_POL, "") or "").strip() if len(row) else ""
        summary["traces"][pol] = {"sor_pol": got, "expected": exp}
        if got != exp:
            failures.append(f"trace {pol} SOR_POL={got!r} expected {exp!r}")

    print("| Issue 156 SOR_POL               | Result    |")
    print("| ------------------------------- | --------- |")
    print(f"| Rows                            | {summary['rows']:<9} |")
    print(f"| Filled                          | {summary['filled']:<9} |")
    print(f"| Blank                           | {summary['blank']:<9} |")
    print(f"| Source mismatches               | {summary['source_mismatches']:<9} |")
    print(f"| Converted-key copies            | {summary['converted_key_copied']:<9} |")
    for pol, info in summary["traces"].items():
        print(f"| {pol:<31} | {info['sor_pol']:<9} |")

    if failures:
        for f in failures[:20]:
            print(f"FAIL detail: {f}")
        print("FAIL: Issue 156 SOR_POL")
        return 1

    if args.publish_test_validation:
        TV.mkdir(parents=True, exist_ok=True)
        dest = TV / "quikspec.csv"
        shutil.copy2(SPEC, dest)
        print(f"OK: published quikspec.csv to {dest}")

    ev = ROOT / "Issue_Log_Items" / "Issue_156" / "evidence"
    ev.mkdir(parents=True, exist_ok=True)
    (ev / "issue156_validation_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    print(
        "PASS: Issue 156 SOR_POL — "
        f"rows={summary['rows']} filled={summary['filled']} mismatches=0"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
