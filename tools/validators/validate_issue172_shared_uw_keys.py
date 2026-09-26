#!/usr/bin/env python3
"""Issue #172 — fail-closed shared UW-class rate key validation (Option K).

Validates:
  - 1659C2 QuikCvs/QuikPlCv PR == ST (except UWCLASS); no unauthorized NT/PQ CV
  - quikplan UWVARYCV=N for 1659C2
  - Anchors 9011006697C / 9010713704C remain MUWCLASS=PR; ST control 9010718276C
  - Category C 1658C1 CV PR vs ST remain distinct
  - 1L14SC four-class equality on approved #168/#172 tables

Usage:
  python tools/validators/validate_issue172_shared_uw_keys.py
  python tools/validators/validate_issue172_shared_uw_keys.py --rates-dir PATH
  python tools/validators/validate_issue172_shared_uw_keys.py --output-dir QLA_Migration/Output

--rates-dir validates a staged rates directory while quikplan/quikridr still
come from --output-dir (default QLA_Migration/Output). Default rates path is
Output/rates.

Exit 1 on missing/unequal/conflict.
"""
from __future__ import annotations

import argparse
import csv
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT = ROOT / "QLA_Migration" / "Output"

PLAN_PRIMARY = "1659C2"
PLAN_L14 = "1L14SC"
PLAN_CAT_C = "1658C1"
AUTH_PRIMARY = "ST"
TARGET_PRIMARY = "PR"
FORBIDDEN_PRIMARY_CV = frozenset({"NT", "PQ"})
L14_CLASSES = ("NT", "PQ", "PR", "ST")

L14_TABLES = {
    "QuikTvs.csv": None,
    "QuikNps.csv": None,
    "QuikCvs.csv": None,
    "QuikNff.csv": None,
    "QuikPlTv.csv": None,
    "QuikPlCv.csv": None,
    "QuikPlDb.csv": None,
    "QuikPlDv.csv": None,
}

ANCHORS = {
    "9011006697C": "PR",
    "9010713704C": "PR",
    "9010718276C": "ST",
}

FACTOR_BASE = ("AGE", "CNTL", "GENDER", "BAND", "ISSCNTRY", "ISSUEST", "EFFDATE")
KEY_BASE = ("GENDER", "BAND", "ISSCNTRY", "ISSUEST", "EFFDATE")


def _t(v: object) -> str:
    return "" if v is None else str(v).strip()


def _read_plan_rows(path: Path, plan: str) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    with path.open(encoding="utf-8-sig", newline="") as fh:
        for row in csv.DictReader(fh):
            if _t(row.get("PLAN")) != plan:
                continue
            rows.append({_t(k): (v if v is not None else "") for k, v in row.items()})
    return rows


def _payload_ex_uw(row: dict[str, str]) -> tuple[tuple[str, str], ...]:
    return tuple(sorted((k, _t(v)) for k, v in row.items() if k != "UWCLASS"))


def _by_class(rows: list[dict[str, str]]) -> dict[str, list[dict[str, str]]]:
    out: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        out[_t(row.get("UWCLASS")).upper()].append(row)
    return out


def _index(rows: list[dict[str, str]], base_fields: tuple[str, ...]) -> dict[tuple[str, ...], dict[str, str]]:
    indexed: dict[tuple[str, ...], dict[str, str]] = {}
    for row in rows:
        key = tuple(_t(row.get(f)) for f in base_fields)
        indexed[key] = row
    return indexed


def _compare_classes(
    rows: list[dict[str, str]],
    auth: str,
    target: str,
    base_fields: tuple[str, ...],
    label: str,
    errors: list[str],
) -> None:
    by_uw = _by_class(rows)
    if auth not in by_uw:
        errors.append(f"{label}: missing auth UWCLASS={auth}")
        return
    if target not in by_uw:
        errors.append(f"{label}: missing target UWCLASS={target}")
        return
    if len(by_uw[auth]) != len(by_uw[target]):
        errors.append(
            f"{label}: count mismatch {auth}={len(by_uw[auth])} "
            f"{target}={len(by_uw[target])}"
        )
    auth_idx = _index(by_uw[auth], base_fields)
    tgt_idx = _index(by_uw[target], base_fields)
    missing = [k for k in auth_idx if k not in tgt_idx]
    extra = [k for k in tgt_idx if k not in auth_idx]
    if missing:
        errors.append(f"{label}: {len(missing)} {auth} keys missing on {target} (e.g. {missing[0]})")
    if extra:
        errors.append(f"{label}: {len(extra)} unexpected {target} keys (e.g. {extra[0]})")
    mismatch = 0
    for key, arow in auth_idx.items():
        trow = tgt_idx.get(key)
        if trow is None:
            continue
        if _payload_ex_uw(arow) != _payload_ex_uw(trow):
            mismatch += 1
            if mismatch <= 5:
                errors.append(f"{label}: value/metadata differ {auth} vs {target} at {key}")
    if mismatch > 5:
        errors.append(f"{label}: {mismatch} total value mismatches {auth} vs {target}")


def validate(output_dir: Path, rates_dir: Path | None = None) -> int:
    rates = rates_dir if rates_dir is not None else (output_dir / "rates")
    errors: list[str] = []

    print("=" * 72)
    print("ISSUE #172 shared UW-class rate keys (Option K)")
    print(f"Output (quikplan/quikridr): {output_dir}")
    print(f"Rates: {rates}")
    print("=" * 72)

    if not rates.is_dir():
        print(f"FAIL: rates dir missing: {rates}")
        return 1

    # --- Primary 1659C2 CV ---
    cvs_path = rates / "QuikCvs.csv"
    plcv_path = rates / "QuikPlCv.csv"
    if not cvs_path.is_file():
        errors.append(f"missing {cvs_path}")
    if not plcv_path.is_file():
        errors.append(f"missing {plcv_path}")

    if cvs_path.is_file() and plcv_path.is_file():
        cvs = _read_plan_rows(cvs_path, PLAN_PRIMARY)
        plcv = _read_plan_rows(plcv_path, PLAN_PRIMARY)
        cvs_uw = sorted(_by_class(cvs))
        plcv_uw = sorted(_by_class(plcv))
        print(f"  {PLAN_PRIMARY} QuikCvs UWCLASS={cvs_uw} counts="
              + str({k: len(v) for k, v in _by_class(cvs).items()}))
        print(f"  {PLAN_PRIMARY} QuikPlCv UWCLASS={plcv_uw} counts="
              + str({k: len(v) for k, v in _by_class(plcv).items()}))

        forbidden = sorted(set(cvs_uw) & FORBIDDEN_PRIMARY_CV)
        if forbidden:
            errors.append(
                f"{PLAN_PRIMARY} QuikCvs has unauthorized UWCLASS {forbidden} "
                "(#172 must not add NT/PQ; #118 ISWL ST|PR only)"
            )
        forbidden_k = sorted(set(plcv_uw) & FORBIDDEN_PRIMARY_CV)
        if forbidden_k:
            errors.append(
                f"{PLAN_PRIMARY} QuikPlCv has unauthorized UWCLASS {forbidden_k}"
            )

        _compare_classes(
            cvs, AUTH_PRIMARY, TARGET_PRIMARY, FACTOR_BASE,
            f"{PLAN_PRIMARY} QuikCvs", errors,
        )
        _compare_classes(
            plcv, AUTH_PRIMARY, TARGET_PRIMARY, KEY_BASE,
            f"{PLAN_PRIMARY} QuikPlCv", errors,
        )

    # --- UWVARYCV ---
    plan_path = output_dir / "quikplan.csv"
    if not plan_path.is_file():
        errors.append(f"missing {plan_path}")
    else:
        found = False
        with plan_path.open(encoding="utf-8-sig", newline="") as fh:
            for row in csv.DictReader(fh):
                if _t(row.get("PLAN")) == PLAN_PRIMARY:
                    found = True
                    flag = _t(row.get("UWVARYCV")).upper()
                    print(f"  {PLAN_PRIMARY} UWVARYCV={flag}")
                    if flag != "N":
                        errors.append(
                            f"{PLAN_PRIMARY} UWVARYCV={flag} expected N "
                            "(Option K / Closed #136)"
                        )
                    break
        if not found:
            errors.append(f"{PLAN_PRIMARY} missing from quikplan.csv")

    # --- Anchors via quikridr ---
    ridr_path = output_dir / "quikridr.csv"
    if not ridr_path.is_file():
        errors.append(f"missing {ridr_path}")
    else:
        seen: dict[str, str] = {}
        with ridr_path.open(encoding="utf-8-sig", newline="") as fh:
            for row in csv.DictReader(fh):
                pol = _t(row.get("MPOLICY"))
                if pol not in ANCHORS:
                    continue
                if _t(row.get("MPHASE")) != "1":
                    continue
                seen[pol] = _t(row.get("MUWCLASS")).upper()
                mplan = _t(row.get("MPLAN"))
                if mplan != PLAN_PRIMARY:
                    errors.append(f"{pol}: MPLAN={mplan} expected {PLAN_PRIMARY}")
        for pol, expected in ANCHORS.items():
            got = seen.get(pol)
            print(f"  anchor {pol} MUWCLASS={got} (expect {expected})")
            if got is None:
                errors.append(f"anchor {pol} missing phase-1 quikridr row")
            elif got != expected:
                errors.append(f"anchor {pol} MUWCLASS={got} expected {expected}")

    # --- Category C control 1658C1 ---
    if cvs_path.is_file():
        c1 = _read_plan_rows(cvs_path, PLAN_CAT_C)
        by_uw = _by_class(c1)
        print(
            f"  {PLAN_CAT_C} QuikCvs counts="
            + str({k: len(v) for k, v in by_uw.items()})
        )
        if "PR" not in by_uw or "ST" not in by_uw:
            errors.append(f"{PLAN_CAT_C}: expected both PR and ST CV grids")
        else:
            # Must remain distinct (Category C)
            pr_idx = _index(by_uw["PR"], FACTOR_BASE)
            st_idx = _index(by_uw["ST"], FACTOR_BASE)
            shared = [k for k in pr_idx if k in st_idx]
            if not shared:
                errors.append(f"{PLAN_CAT_C}: no overlapping PR/ST keys to compare")
            else:
                identical = 0
                for key in shared:
                    if _payload_ex_uw(pr_idx[key]) == _payload_ex_uw(st_idx[key]):
                        identical += 1
                if identical == len(shared):
                    errors.append(
                        f"{PLAN_CAT_C}: PR and ST CV grids are identical — "
                        "Category C control lost"
                    )
                else:
                    print(
                        f"  {PLAN_CAT_C}: PR/ST remain distinct "
                        f"({len(shared) - identical}/{len(shared)} keys differ)"
                    )

    # --- L14 four-class equality ---
    for filename in L14_TABLES:
        path = rates / filename
        if not path.is_file():
            errors.append(f"missing L14 table {path}")
            continue
        rows = _read_plan_rows(path, PLAN_L14)
        by_uw = _by_class(rows)
        counts = {c: len(by_uw.get(c, [])) for c in L14_CLASSES}
        print(f"  {PLAN_L14} {filename}: " + " ".join(f"{c}={counts[c]}" for c in L14_CLASSES))
        if len(set(counts.values())) != 1 or counts["NT"] == 0:
            errors.append(f"{filename}: L14 class counts {counts} not equal/non-zero")
            continue
        is_key = filename.startswith("QuikPl")
        base_fields = KEY_BASE if is_key else FACTOR_BASE
        by_key: dict[tuple[str, ...], dict[str, dict[str, str]]] = defaultdict(dict)
        for cls in L14_CLASSES:
            for row in by_uw[cls]:
                by_key[tuple(_t(row.get(f)) for f in base_fields)][cls] = row
        mismatch = 0
        for key, class_rows in by_key.items():
            missing = [c for c in L14_CLASSES if c not in class_rows]
            if missing:
                mismatch += 1
                if mismatch <= 3:
                    errors.append(f"{filename}: key {key} missing {missing}")
                continue
            nt_payload = _payload_ex_uw(class_rows["NT"])
            for cls in ("PQ", "PR", "ST"):
                if _payload_ex_uw(class_rows[cls]) != nt_payload:
                    mismatch += 1
                    if mismatch <= 3:
                        errors.append(f"{filename}: values differ NT vs {cls} at {key}")
        if mismatch > 3:
            errors.append(f"{filename}: {mismatch} L14 equality issues")

    print("-" * 72)
    if errors:
        print(f"FAIL - {len(errors)} error(s):")
        for err in errors:
            print(f"  - {err}")
        return 1
    print("PASS - Issue #172 shared UW keys")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate Issue #172 shared UW keys")
    ap.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    ap.add_argument(
        "--rates-dir",
        type=Path,
        default=None,
        help="Staged rates directory (default: <output-dir>/rates)",
    )
    args = ap.parse_args()
    return validate(args.output_dir, args.rates_dir)


if __name__ == "__main__":
    sys.exit(main())
