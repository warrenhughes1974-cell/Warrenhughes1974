"""Re-format client-ID columns in Output (+ Test_Validation) to width-12 rule."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

import pandas as pd

from qla_core.normalize_utils import CLIENT_ID_TARGET_FIELDS, format_qladmin_mclientid

OUT = ROOT / "QLA_Migration" / "Output"
TV = OUT / "Test_Validation"
TABLES = (
    "quikclnt.csv",
    "quikclid.csv",
    "quikbenf.csv",
    "quikmstr.csv",
    "quikridr.csv",
)


def _apply(path: Path) -> dict:
    if not path.is_file():
        return {"path": str(path), "skipped": True}
    df = pd.read_csv(path, dtype=str).fillna("")
    cols = {c.strip().upper(): c for c in df.columns}
    touched = []
    for field in CLIENT_ID_TARGET_FIELDS:
        src = cols.get(field)
        if not src:
            continue
        before = df[src].astype(str)
        after = before.map(format_qladmin_mclientid)
        # keep blanks blank
        after = [a if str(b).strip() else "" for a, b in zip(after, before)]
        df[src] = after
        touched.append(field)
    df.to_csv(path, index=False)
    return {"path": str(path), "fields": touched, "rows": len(df)}


def main() -> int:
    results = []
    for name in TABLES:
        results.append(_apply(OUT / name))
        tv = TV / name
        if tv.is_file():
            results.append(_apply(tv))
    for r in results:
        print(r)
    # spot-check
    sample = pd.read_csv(OUT / "quikclnt.csv", dtype=str).fillna("")
    sample.columns = [c.strip().upper() for c in sample.columns]
    v = sample.iloc[0]["MCLIENTID"]
    print("sample MCLIENTID", repr(v), "len", len(v))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
