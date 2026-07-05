"""
Issue 30 — RNA relationship name validation.

Validates that Issue 30 RNA relationship rows keyed by IDENTIFYING_ALPHA
are emitted into quikclid/quikclnt and populate quikmstr role IDs.

Usage:
  python tools/validators/validate_issue30_relationship_names.py
  python tools/validators/validate_issue30_relationship_names.py --output-dir QLA_Migration/Output
"""

from __future__ import annotations

import argparse
import csv
import sys
from collections import Counter, defaultdict
from pathlib import Path

import pandas as pd

SCRIPT_VERSION = "1.0"
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT = PROJECT_ROOT / "QLA_Migration" / "Output"
DEFAULT_SOURCE = PROJECT_ROOT / "QLA_Migration" / "Source"
DEFAULT_CROSSWALK = PROJECT_ROOT / "QLA_Migration" / "Mapping" / "Master_Crosswalk.csv"
DEFAULT_POPULATION = PROJECT_ROOT / "Issue_Log_Items" / "Issue_30" / "Issue_30_Missing_Name_Policies.csv"

RNA_FILE = "RelationshipNameAddress_Extract_20260530.csv"
ROLE_TO_MSTR = {
    "IN": "MPRIMID",
    "INSD": "MPRIMID",
    "PO": "MOWNRID",
    "OWNR": "MOWNRID",
    "PA": "MPAYRID",
    "PAYR": "MPAYRID",
}
ROLE_TO_CLID = {
    "IN": "INSD",
    "INSD": "INSD",
    "PO": "OWNR",
    "OWNR": "OWNR",
    "PA": "PAYR",
    "PAYR": "PAYR",
}


def _norm(value: object) -> str:
    text = "" if value is None else str(value).strip().upper()
    return "" if text in {"", "NAN", "NONE"} else text[:-2] if text.endswith(".0") else text


def _read_csv(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, dtype=str, encoding="latin1", on_bad_lines="skip").fillna("")
    df.columns = [str(c).strip().upper() for c in df.columns]
    return df


def _load_crosswalk(path: Path) -> tuple[dict[str, str], dict[str, str]]:
    old_to_new: dict[str, str] = {}
    new_to_old: dict[str, str] = {}
    with path.open("r", newline="", encoding="utf-8-sig", errors="replace") as handle:
        for row in csv.reader(handle):
            if len(row) < 2:
                continue
            old, new = _norm(row[0]), _norm(row[1])
            if old and new:
                old_to_new[old] = new
                new_to_old[new] = old
    return old_to_new, new_to_old


def _rna_keys(old_policy: str) -> set[str]:
    old = _norm(old_policy)
    keys = {old}
    if old:
        keys.add(f"03{old}")
    return keys


def _load_issue_population(path: Path) -> list[str]:
    pop = _read_csv(path)
    if "POLICY" not in pop.columns:
        raise ValueError(f"{path} missing POLICY column")
    return [_norm(p) for p in pop["POLICY"].tolist() if _norm(p)]


def _load_expected_roles(source_dir: Path, policies: list[str], new_to_old: dict[str, str], old_to_new: dict[str, str]):
    rna_path = source_dir / RNA_FILE
    if not rna_path.is_file():
        raise FileNotFoundError(f"Missing RNA source: {rna_path}")

    key_to_policy: dict[str, str] = {}
    for policy in policies:
        old = new_to_old.get(policy, policy)
        for key in _rna_keys(old):
            key_to_policy[key] = policy

    expected: dict[str, list[dict[str, str]]] = defaultdict(list)
    with rna_path.open("r", newline="", encoding="utf-8-sig", errors="replace") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames:
            reader.fieldnames = [str(h).strip().upper() for h in reader.fieldnames]
        for row in reader:
            row = {str(k).strip().upper(): v for k, v in row.items()}
            policy_key = _norm(row.get("POLICY_NUMBER"))
            alpha_key = _norm(row.get("IDENTIFYING_ALPHA"))
            policy = key_to_policy.get(policy_key) or key_to_policy.get(alpha_key)
            if not policy:
                continue
            role = _norm(row.get("RELATE_CODE"))
            name_id = _norm(row.get("NAME_ID"))
            if role not in ROLE_TO_MSTR or not name_id:
                continue
            expected[policy].append({
                "policy": policy,
                "old_policy": new_to_old.get(policy, ""),
                "role": role,
                "name_id": name_id,
                "phase": _norm(row.get("BENEFIT_SEQ_NUMBER")) or "1",
                "first": str(row.get("INDIVIDUAL_FIRST", "")).strip(),
                "last": str(row.get("INDIVIDUAL_LAST", "")).strip(),
            })

    # Match converter behavior: exact source duplicates should validate once.
    deduped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for policy, rows in expected.items():
        seen = set()
        for row in rows:
            key = (row["role"], row["name_id"], row["phase"])
            if key in seen:
                continue
            seen.add(key)
            deduped[policy].append(row)
    return deduped


def validate(output_dir: Path, source_dir: Path, crosswalk_path: Path, population_path: Path) -> int:
    print("=" * 72)
    print(f"ISSUE #30 — RNA RELATIONSHIP NAME VALIDATION (script v{SCRIPT_VERSION})")
    print(f"Output: {output_dir}")
    print(f"Source: {source_dir}")
    print("=" * 72)

    required_outputs = [output_dir / name for name in ("quikmstr.csv", "quikclid.csv", "quikclnt.csv")]
    missing = [str(path) for path in required_outputs if not path.is_file()]
    if missing:
        print(f"FAIL — missing output files: {', '.join(missing)}")
        return 1

    old_to_new, new_to_old = _load_crosswalk(crosswalk_path)
    policies = _load_issue_population(population_path)
    expected = _load_expected_roles(source_dir, policies, new_to_old, old_to_new)

    mstr = _read_csv(output_dir / "quikmstr.csv")
    clid = _read_csv(output_dir / "quikclid.csv")
    clnt = _read_csv(output_dir / "quikclnt.csv")

    clnt_ids = {_norm(v) for v in clnt["MCLIENTID"].tolist()} if "MCLIENTID" in clnt.columns else set()
    clid_keys = {
        (_norm(r.get("MPOLICY")), _norm(r.get("MRELATION")), _norm(r.get("MCLIENTID")), _norm(r.get("MPHASE")) or "1")
        for r in clid.to_dict("records")
    }
    clid_dupes = clid[clid.duplicated(subset=["MCLIENTID", "MPOLICY", "MPHASE", "MRELATION"], keep=False)]

    mstr_by_policy = {
        _norm(row.get("MPOLICY")): row
        for row in mstr.to_dict("records")
        if _norm(row.get("MPOLICY"))
    }

    errors: list[str] = []
    expected_role_count = 0
    print("\nTrace results:")
    for policy in policies:
        rows = expected.get(policy, [])
        role_counts = Counter(row["role"] for row in rows)
        print(f"\n{policy}: expected RNA roles {dict(role_counts)}")
        mrow = mstr_by_policy.get(policy, {})
        expected_mstr_values: dict[str, set[str]] = defaultdict(set)
        for expected_row in rows:
            expected_mstr_values[ROLE_TO_MSTR[expected_row["role"]]].add(expected_row["name_id"])
        for row in rows:
            expected_role_count += 1
            role = row["role"]
            clid_role = ROLE_TO_CLID[role]
            name_id = row["name_id"]
            phase = "1" if row["phase"] in {"", "0"} else row["phase"]
            target_field = ROLE_TO_MSTR[role]
            target_value = _norm(mrow.get(target_field, ""))
            clid_ok = (policy, clid_role, name_id, phase) in clid_keys
            clnt_ok = name_id in clnt_ids
            mstr_ok = target_value in expected_mstr_values[target_field]
            print(
                f"  {role} {name_id} {row['last']}, {row['first']} "
                f"quikclid={'OK' if clid_ok else 'MISS'} "
                f"quikclnt={'OK' if clnt_ok else 'MISS'} "
                f"{target_field}={'OK' if mstr_ok else target_value or 'MISS'}"
            )
            if not clid_ok:
                errors.append(f"{policy}: missing quikclid {clid_role}/{name_id}/phase {phase}")
            if not clnt_ok:
                errors.append(f"{policy}: missing quikclnt MCLIENTID {name_id}")
            if not mstr_ok:
                errors.append(f"{policy}: {target_field} expected {name_id}, got {target_value or '(blank)'}")

    if len(clid_dupes):
        errors.append(f"{len(clid_dupes)} duplicate exact quikclid relationship rows")

    print("\nSummary:")
    print(f"  Issue 30 policies: {len(policies)}")
    print(f"  Expected nonblank RNA roles: {expected_role_count}")
    print(f"  Duplicate exact quikclid rows: {len(clid_dupes)}")

    print("\n" + "=" * 72)
    if errors:
        print(f"RESULT: FAIL ({len(errors)} issue(s))")
        for error in errors[:50]:
            print(f"  - {error}")
        if len(errors) > 50:
            print(f"  ... {len(errors) - 50} more")
        return 1

    print("RESULT: PASS — Issue 30 RNA relationships resolve to quikclid/quikclnt/quikmstr")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Issue 30 RNA relationship name resolution")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--source-dir", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--crosswalk", type=Path, default=DEFAULT_CROSSWALK)
    parser.add_argument("--population", type=Path, default=DEFAULT_POPULATION)
    args = parser.parse_args()
    return validate(
        args.output_dir.resolve(),
        args.source_dir.resolve(),
        args.crosswalk.resolve(),
        args.population.resolve(),
    )


if __name__ == "__main__":
    sys.exit(main())
