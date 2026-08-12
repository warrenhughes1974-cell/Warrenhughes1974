#!/usr/bin/env python3
"""Full-batch smoke: QuikSpec resident state (PPOLC.RES_STATE → quikspec.RESSTATE).

Cut-agnostic. Compares Output/quikspec.csv to:
  - authoritative converted population (Output/quikmstr.MPOLICY)
  - active PPOLC extract RES_STATE (trim + upper only; no business translation)

Fails if hygiene relocated quikspec.csv out of Output.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from qla_core.lifepro_source_resolver import resolve_table_source  # noqa: E402
from qla_core.normalize_utils import format_qladmin_mpolicy, normalize  # noqa: E402
from qla_core.run_logging import _is_allowed_output_table_csv  # noqa: E402

OUT = ROOT / "QLA_Migration" / "Output"
SPEC = OUT / "quikspec.csv"
MSTR = OUT / "quikmstr.csv"
REPORTS = ROOT / "QLA_Migration" / "Reports"
SRC_DIR = ROOT / "QLA_Migration" / "Source"

REQUIRED_COLS = ("MPOLICY", "VANISH", "VANISHDT", "RESSTATE")


def _load_ppolc_res_state(src_dir: Path) -> dict[str, str]:
    path, _label = resolve_table_source(str(src_dir), "quikspec")
    if not path:
        path, _label = resolve_table_source(str(src_dir), "quikmstr")
    if not path or not Path(path).is_file():
        raise FileNotFoundError(f"PPOLC extract not found under {src_dir}")

    df = pd.read_csv(path, dtype=str, encoding="latin1", low_memory=False).fillna("")
    df.columns = [str(c).replace("\ufeff", "").strip().upper() for c in df.columns]
    if "POLICY_NUMBER" not in df.columns or "RES_STATE" not in df.columns:
        raise ValueError(f"PPOLC missing POLICY_NUMBER/RES_STATE: {path}")

    # Same separator skip as conversion (dashed extract banner rows).
    mask = ~df.iloc[:, :3].astype(str).apply(
        lambda r: any("---" in str(v) for v in r), axis=1
    )
    df = df.loc[mask].copy()
    out: dict[str, str] = {}
    for _, row in df.iterrows():
        pol = normalize(row.get("POLICY_NUMBER", ""))
        if not pol:
            continue
        mpolicy = format_qladmin_mpolicy(pol)
        if not mpolicy:
            continue
        # First real row wins (PPOLC is policy-grain; no arbitrary later override).
        if mpolicy in out:
            continue
        out[mpolicy] = normalize(row.get("RES_STATE", ""))
    return out


def main() -> int:
    summary = {
        "file_exists": "FAIL",
        "expected_policies": 0,
        "quikspec_rows": 0,
        "missing_mpolicy": 0,
        "duplicate_mpolicy": 0,
        "missing_expected": 0,
        "unexpected": 0,
        "resstate_mismatches": 0,
        "populated_src_blank_tgt": 0,
        "output_hygiene": "FAIL",
    }
    failures: list[str] = []

    if not _is_allowed_output_table_csv("quikspec.csv"):
        failures.append("quikspec.csv not on Output hygiene allowlist")

    reports_hit = sorted(REPORTS.glob("quikspec*.csv")) if REPORTS.is_dir() else []
    if SPEC.is_file():
        summary["file_exists"] = "PASS"
        summary["output_hygiene"] = "PASS"
    else:
        failures.append(f"missing {SPEC}")
        if reports_hit:
            failures.append(
                "quikspec.csv missing from Output but present under Reports "
                f"({reports_hit[0].name}) — hygiene/relocation failure"
            )
            summary["output_hygiene"] = "FAIL"

    if not MSTR.is_file():
        failures.append(f"missing authoritative policy population {MSTR}")
        _print_summary(summary)
        for f in failures:
            print(f"FAIL detail: {f}")
        return 1

    qm = pd.read_csv(MSTR, dtype=str, encoding="latin1").fillna("")
    qm.columns = [str(c).strip().upper() for c in qm.columns]
    if "MPOLICY" not in qm.columns:
        failures.append("quikmstr missing MPOLICY")
        _print_summary(summary)
        for f in failures:
            print(f"FAIL detail: {f}")
        return 1

    expected = {str(v).strip() for v in qm["MPOLICY"] if str(v).strip()}
    summary["expected_policies"] = len(expected)

    if SPEC.is_file():
        qs = pd.read_csv(SPEC, dtype=str).fillna("")
        qs.columns = [str(c).strip().upper() for c in qs.columns]
        missing_cols = [c for c in REQUIRED_COLS if c not in qs.columns]
        if missing_cols:
            failures.append(f"quikspec missing columns: {missing_cols}")

        summary["quikspec_rows"] = len(qs)
        pols = qs["MPOLICY"].astype(str) if "MPOLICY" in qs.columns else pd.Series(dtype=str)
        pol_stripped = pols.map(lambda x: str(x).strip())
        summary["missing_mpolicy"] = int((pol_stripped == "").sum())
        summary["duplicate_mpolicy"] = int(pol_stripped[pol_stripped != ""].duplicated().sum())

        got = {p for p in pol_stripped.tolist() if p}
        summary["missing_expected"] = len(expected - got)
        summary["unexpected"] = len(got - expected)

        if summary["missing_mpolicy"]:
            failures.append(f"blank MPOLICY rows={summary['missing_mpolicy']}")
        if summary["duplicate_mpolicy"]:
            failures.append(f"duplicate MPOLICY rows={summary['duplicate_mpolicy']}")
        if summary["missing_expected"]:
            failures.append(
                f"missing expected policies={summary['missing_expected']}"
            )
        if summary["unexpected"]:
            failures.append(f"unexpected policies={summary['unexpected']}")

        try:
            src_map = _load_ppolc_res_state(SRC_DIR)
        except Exception as exc:
            failures.append(f"PPOLC RES_STATE load failed: {exc}")
            src_map = {}

        if src_map and "RESSTATE" in qs.columns and "MPOLICY" in qs.columns:
            mismatches = 0
            blank_tgt = 0
            for _, row in qs.iterrows():
                pol = str(row.get("MPOLICY", "")).strip()
                if not pol:
                    continue
                tgt = normalize(row.get("RESSTATE", ""))
                if pol not in src_map:
                    # Population already covered by unexpected/missing checks.
                    continue
                src = src_map[pol]
                if src and not tgt:
                    blank_tgt += 1
                elif src != tgt:
                    mismatches += 1
            summary["resstate_mismatches"] = mismatches
            summary["populated_src_blank_tgt"] = blank_tgt
            if mismatches:
                failures.append(f"RESSTATE mismatches={mismatches}")
            if blank_tgt:
                failures.append(
                    f"populated source / blank target={blank_tgt}"
                )

    _print_summary(summary)
    if failures:
        for f in failures[:20]:
            print(f"FAIL detail: {f}")
        print("FAIL: QuikSpec resident-state smoke")
        return 1

    print(
        "PASS: QuikSpec resident-state smoke — "
        f"rows={summary['quikspec_rows']} expected={summary['expected_policies']} "
        f"mismatches=0 hygiene=PASS"
    )
    return 0


def _print_summary(summary: dict) -> None:
    print("| QuikSpec Check                  | Result    |")
    print("| ------------------------------- | --------- |")
    print(f"| File exists                     | {summary['file_exists']:<9} |")
    print(f"| Expected policies               | {summary['expected_policies']:<9} |")
    print(f"| QuikSpec rows                   | {summary['quikspec_rows']:<9} |")
    print(f"| Missing MPOLICY                 | {summary['missing_mpolicy']:<9} |")
    print(f"| Duplicate MPOLICY               | {summary['duplicate_mpolicy']:<9} |")
    print(f"| Missing expected policies       | {summary['missing_expected']:<9} |")
    print(f"| Unexpected policies             | {summary['unexpected']:<9} |")
    print(f"| RESSTATE mismatches             | {summary['resstate_mismatches']:<9} |")
    print(f"| Populated source / blank target | {summary['populated_src_blank_tgt']:<9} |")
    print(f"| Output hygiene                  | {summary['output_hygiene']:<9} |")


if __name__ == "__main__":
    raise SystemExit(main())
