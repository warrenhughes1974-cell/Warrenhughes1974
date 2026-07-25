"""
Issue #110 — quikmstr MDIVOPT (dividend option) from the PPBENTYP cache.

Before v58.34 MDIVOPT was 0 on all 5,083 policies. The enrichment resolved its cache key
through Master_Crosswalk.csv, whose New_Value column still holds pre-Issue-#2 10-character
keys, so every lookup missed and the dividend election was dropped fleet-wide. The fix
points the lookup at the raw source POLICY_NUMBER, the same key the cache is built on.

This validator does not trust the emitted values — it rebuilds the expected election from
PPBENTYP the way app.py builds the cache (BENEFIT_SEQ 1, DIVIDEND column, DV_* translation)
and requires an exact match on every policy.

Rules:
  1. MDIVOPT domain 0-5
  2. Every policy's MDIVOPT equals the translated source dividend option
  3. Non-zero elections are present (guards the fleet-wide-zero regression)

Usage:
  python tools/validators/validate_issue110_mdivopt.py
  python tools/validators/validate_issue110_mdivopt.py --ppbentyp path/to/PPBENTYP.csv
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT = PROJECT_ROOT / "QLA_Migration" / "Output"
DEFAULT_SOURCE = PROJECT_ROOT / "QLA_Migration" / "Source"
TRANSLATION = PROJECT_ROOT / "QLA_Migration" / "Mapping" / "Master_Value_Translation.csv"
EVIDENCE = PROJECT_ROOT / "Issue_Log_Items" / "Issue_110" / "evidence" / "issue110_mdivopt_validation.csv"

SCRIPT_VERSION = "1.0"
EXPECTED_ROW_COUNT = 5083
# v58.34 fingerprint. A drop back toward zero means the cache key regressed again.
MIN_NONZERO = 800
VALID_DOMAIN = {"", "0", "1", "2", "3", "4", "5"}


def _n(v: object) -> str:
    s = ("" if v is None else str(v)).strip()
    if s.endswith(".0"):
        s = s[:-2]
    if s.lower() in ("nan", "none", "null"):
        return ""
    return s


def _load_csv(path: Path, encoding: str = "utf-8") -> list[dict]:
    with path.open(newline="", encoding=encoding, errors="replace") as f:
        return list(csv.DictReader(f))


def _find_ppbentyp(explicit: Path | None) -> Path | None:
    """Resolve the newest PPBENTYP extract, matching app.py's find_extract behaviour.

    Hardcoding a dated filename is what left several sibling validators stranded on an
    extract that no longer ships.
    """
    if explicit:
        return explicit if explicit.exists() else None
    if not DEFAULT_SOURCE.exists():
        return None
    cands = [
        p for p in DEFAULT_SOURCE.glob("*.csv")
        if "ppbentyp" in p.name.lower()
        and not any(bad in p.name.lower() for bad in ("copy", "old", "backup", "archive"))
    ]
    return max(cands, key=lambda p: p.stat().st_mtime) if cands else None


def _load_dv_translation() -> dict[str, str]:
    trans: dict[str, str] = {}
    with TRANSLATION.open(encoding="latin1", newline="") as f:
        for row in csv.reader(f):
            if len(row) < 2:
                continue
            k = row[0].strip()
            if k.startswith("DV_"):
                trans[k] = row[1].strip()
    return trans


def _translate(raw: str, trans: dict[str, str]) -> str:
    if not raw:
        return "0"
    val = trans.get(f"DV_{raw.upper()}")
    if val is None:
        return "0"
    return val if val.isdigit() else "0"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    ap.add_argument("--ppbentyp", type=Path, default=None)
    args = ap.parse_args()

    mstr_path = args.output_dir / "quikmstr.csv"
    if not mstr_path.exists():
        print(f"FAIL: missing {mstr_path}")
        return 1

    rows = _load_csv(mstr_path)
    errors: list[str] = []

    if len(rows) != EXPECTED_ROW_COUNT:
        errors.append(f"row count {len(rows)} != expected {EXPECTED_ROW_COUNT}")

    bad_domain = [r for r in rows if _n(r.get("MDIVOPT")) not in VALID_DOMAIN]
    if bad_domain:
        errors.append(
            f"MDIVOPT outside 0-5 on {len(bad_domain)} policies "
            f"(e.g. {_n(bad_domain[0].get('MPOLICY'))}={_n(bad_domain[0].get('MDIVOPT'))})"
        )

    nonzero = sum(1 for r in rows if _n(r.get("MDIVOPT")) not in ("", "0"))
    if nonzero < MIN_NONZERO:
        errors.append(
            f"only {nonzero} policies carry a dividend election (expected >= {MIN_NONZERO}) — "
            "the PPBENTYP cache lookup is missing again"
        )

    # Rebuild the expected election from source.
    ppb_path = _find_ppbentyp(args.ppbentyp)
    checked = mismatched = 0
    detail: list[dict] = []
    if not ppb_path:
        errors.append("no PPBENTYP extract found in QLA_Migration/Source — cannot verify against source")
    else:
        trans = _load_dv_translation()
        if not trans:
            errors.append(f"no DV_* rows in {TRANSLATION.name}")
        src: dict[str, str] = {}
        for r in _load_csv(ppb_path, encoding="latin1"):
            keys = {k.strip().upper(): v for k, v in r.items() if k}
            pol = _n(keys.get("POLICY_NUMBER"))
            if not pol or "---" in pol:
                continue
            seq = _n(keys.get("BENEFIT_SEQ")) or _n(keys.get("COVERAGE_SEQ"))
            if seq and seq not in ("1", "01"):
                continue
            src.setdefault(pol, _n(keys.get("DIVIDEND")))

        for r in rows:
            pol = _n(r.get("MPOLICY"))
            # MPOLICY is source POLICY_NUMBER + "C" since Issue #2 (v58.29).
            src_key = pol[:-1] if pol.endswith("C") else pol
            expected = _translate(src.get(src_key, ""), trans)
            got = _n(r.get("MDIVOPT")) or "0"
            checked += 1
            if got != expected:
                mismatched += 1
                detail.append({
                    "MPOLICY": pol,
                    "SOURCE_DIVIDEND": src.get(src_key, "(no source row)"),
                    "EXPECTED_MDIVOPT": expected,
                    "EMITTED_MDIVOPT": got,
                })

        if mismatched:
            for d in detail[:5]:
                errors.append(
                    f"MDIVOPT mismatch {d['MPOLICY']}: source={d['SOURCE_DIVIDEND']!r} "
                    f"expected={d['EXPECTED_MDIVOPT']} got={d['EMITTED_MDIVOPT']}"
                )
            if mismatched > 5:
                errors.append(f"MDIVOPT mismatches: {mismatched} total (see {EVIDENCE.name})")

    EVIDENCE.parent.mkdir(parents=True, exist_ok=True)
    with EVIDENCE.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(
            f, fieldnames=["MPOLICY", "SOURCE_DIVIDEND", "EXPECTED_MDIVOPT", "EMITTED_MDIVOPT"]
        )
        w.writeheader()
        w.writerows(detail or [{
            "MPOLICY": "(fleet)", "SOURCE_DIVIDEND": "",
            "EXPECTED_MDIVOPT": "", "EMITTED_MDIVOPT": f"all {checked} policies match source",
        }])

    print(f"validate_issue110_mdivopt v{SCRIPT_VERSION}")
    print(f"  source: {ppb_path.name if ppb_path else '(none)'}")
    print(f"  rows={len(rows)} nonzero_elections={nonzero}")
    print(f"  source reconciliation: checked={checked} mismatched={mismatched}")

    if errors:
        print("FAIL:")
        for e in errors:
            print(f"  - {e}")
        return 1

    print("PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
