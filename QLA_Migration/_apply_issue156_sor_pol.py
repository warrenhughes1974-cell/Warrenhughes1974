"""One-shot: add quikspec.SOR_POL from PPOLC.POLICY_NUMBER on current Output."""
from __future__ import annotations

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from qla_core.lifepro_source_resolver import resolve_table_source
from qla_core.normalize_utils import format_qladmin_mpolicy, normalize

OUT = ROOT / "QLA_Migration" / "Output" / "quikspec.csv"
SRC = ROOT / "QLA_Migration" / "Source"
TV = ROOT / "QLA_Migration" / "Output" / "Test_Validation" / "quikspec.csv"
COLS = ["MPOLICY", "VANISH", "VANISHDT", "RESSTATE", "RESRVCAT", "SOR_POL"]


def _keys(pol: str) -> list[str]:
    raw = str(pol or "").strip()
    n = normalize(raw)
    keys: list[str] = []
    for item in (
        raw,
        n,
        format_qladmin_mpolicy(n),
        format_qladmin_mpolicy(n).strip(),
    ):
        if item and item not in keys:
            keys.append(item)
    return keys


def main() -> int:
    path, _label = resolve_table_source(str(SRC), "quikspec")
    if not path:
        print("FAIL: PPOLC not found")
        return 1
    src_by_mpolicy: dict[str, str] = {}
    non_numeric = 0
    with Path(path).open(newline="", encoding="latin1", errors="replace") as fh:
        reader = csv.DictReader(fh)
        cols = {str(c).replace("\ufeff", "").strip().upper(): c for c in (reader.fieldnames or [])}
        pol_c = cols.get("POLICY_NUMBER")
        if not pol_c:
            print("FAIL: POLICY_NUMBER missing")
            return 1
        for row in reader:
            first = [str(row.get(reader.fieldnames[i], "") or "") for i in range(min(3, len(reader.fieldnames or [])))]
            if any("---" in v for v in first):
                continue
            src = normalize(row.get(pol_c, ""))
            if not src or src.replace("-", "") == "" or src.startswith("----"):
                continue
            if not src.isdigit():
                non_numeric += 1
            for k in _keys(src):
                src_by_mpolicy.setdefault(k, src)

    with OUT.open(newline="", encoding="utf-8-sig", errors="replace") as fh:
        rows = list(csv.DictReader(fh))
    filled = missing = 0
    out_rows = []
    for row in rows:
        mp = str(row.get("MPOLICY", "") or "")
        src = ""
        for k in (mp, mp.strip(), normalize(mp)):
            src = src_by_mpolicy.get(k, "")
            if src:
                break
        if src:
            filled += 1
        else:
            missing += 1
        out_rows.append({
            "MPOLICY": mp,
            "VANISH": row.get("VANISH", ""),
            "VANISHDT": row.get("VANISHDT", ""),
            "RESSTATE": row.get("RESSTATE", ""),
            "RESRVCAT": row.get("RESRVCAT", ""),
            "SOR_POL": src,
        })

    with OUT.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=COLS, lineterminator="\n")
        w.writeheader()
        w.writerows(out_rows)

    TV.parent.mkdir(parents=True, exist_ok=True)
    with TV.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=COLS, lineterminator="\n")
        w.writeheader()
        w.writerows(out_rows)

    print(f"rows={len(out_rows)} filled={filled} missing={missing} source_non_numeric={non_numeric}")
    sample = next((r for r in out_rows if "9011050114" in str(r.get("MPOLICY", ""))), None)
    if sample:
        print("sample", sample)
    return 0 if missing == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
