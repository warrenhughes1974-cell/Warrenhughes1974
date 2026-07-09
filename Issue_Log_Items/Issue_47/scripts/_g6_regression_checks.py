"""Issue #47 G6 regression checks (read-only)."""
from __future__ import annotations

import re
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
MIG = ROOT / "QLA_Migration"
EVID = Path(__file__).resolve().parents[1] / "evidence"
OUT = MIG / "Output"
APP = ROOT / "app.py"


def main() -> int:
    errors: list[str] = []
    qm = pd.read_csv(OUT / "quikmstr.csv", dtype=str, low_memory=False).fillna("")
    qm.columns = [c.strip().upper() for c in qm.columns]
    qm["MPOLICY"] = qm["MPOLICY"].astype(str).str.strip()

    text = APP.read_text(encoding="utf-8", errors="replace")
    m = re.search(r'"quikmstr":\s*\[(.*?)\]', text, re.S)
    if not m:
        errors.append("could not parse quikmstr schema from app.py")
        schema = []
    else:
        schema = [c.strip().strip('"') for c in m.group(1).split(",") if c.strip()]
    if list(qm.columns) != schema:
        errors.append(f"quikmstr column order mismatch (out={len(qm.columns)} schema={len(schema)})")

    lens = qm["MPOLICY"].astype(str).map(len)
    if lens.max() > 10:
        errors.append(f"MPOLICY length >10 found (max={lens.max()})")

    # risk delta matches emitted
    delta = pd.read_csv(EVID / "issue47_risk_delta_simulation.csv", dtype=str)
    delta["MPOLICY"] = delta["MPOLICY"].astype(str).str.strip()
    merged = delta.merge(qm[["MPOLICY", "MBILLDAY"]], on="MPOLICY", how="left")
    fail = merged[
        merged["MBILLDAY_after"].astype(str).str.strip() != merged["MBILLDAY"].astype(str).str.strip()
    ]
    if len(fail):
        errors.append(f"risk delta vs output mismatches: {len(fail)}")

    edges = pd.read_csv(EVID / "issue47_paid_ne_billed_edges.csv", dtype=str)
    for _, e in edges.iterrows():
        pol = e["New_Value"]
        exp = str(e["mb_after"]).strip()
        got = qm.loc[qm["MPOLICY"] == pol, "MBILLDAY"]
        g = str(got.iloc[0]).strip() if len(got) else "MISSING"
        if g != exp:
            errors.append(f"edge {pol}: got={g} expect={exp}")

    # #26 ridr present / MPREM column exists
    ridr_path = OUT / "quikridr.csv"
    if ridr_path.is_file():
        ridr = pd.read_csv(ridr_path, dtype=str, nrows=3)
        if "MPREM" not in ridr.columns:
            errors.append("quikridr missing MPREM column")
    else:
        errors.append("quikridr.csv missing (spot-check skipped)")

    # zeros gone
    zeros = int(qm["MBILLDAY"].astype(str).str.strip().isin(["", "0", "0.0", "00"]).sum())
    if zeros:
        errors.append(f"unexpected MBILLDAY zeros remaining: {zeros}")

    summary = pd.DataFrame(
        [
            {"metric": "quikmstr_rows", "value": len(qm)},
            {"metric": "schema_cols_match", "value": int(list(qm.columns) == schema)},
            {"metric": "mpolicy_max_len", "value": int(lens.max())},
            {"metric": "mbillday_zeros", "value": zeros},
            {"metric": "risk_delta_fail", "value": len(fail)},
            {"metric": "edge_fail", "value": sum(1 for e in errors if e.startswith("edge "))},
        ]
    )
    EVID.mkdir(parents=True, exist_ok=True)
    summary.to_csv(EVID / "issue47_regression_summary.csv", index=False)
    print(summary.to_string(index=False))

    if errors:
        print("FAIL:")
        for e in errors:
            print(" -", e)
        return 1
    print("PASS: Issue #47 G6 regression")
    return 0


if __name__ == "__main__":
    sys.exit(main())
