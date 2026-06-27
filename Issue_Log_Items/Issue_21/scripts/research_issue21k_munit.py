"""Read-only population analysis for Issue 21K — MUNIT precision (Planning Agent)."""
from __future__ import annotations

import csv
import math
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
RIDR = REPO / "QLA_Migration" / "Output" / "quikridr.csv"
OUT = REPO / "Issue_Log_Items" / "Issue_21" / "reports" / "Issue_21K_MUNIT_Precision_Trace.csv"


def num(s: str) -> float:
    try:
        return float(str(s).replace(",", "").strip() or 0)
    except ValueError:
        return 0.0


def trunc3(x: float) -> float:
    return math.floor(x * 1000 + 1e-9) / 1000


def sub_mill(x: float) -> bool:
    return abs(x * 1000 - math.floor(x * 1000 + 1e-9)) > 1e-9


def main() -> None:
    rows = list(csv.DictReader(RIDR.open(encoding="latin1", newline="")))
    trace_rows = []

    submill_n = frac_cent_n = pa_n = pa_submill_n = delta_n = pa_delta_n = 0
    pol_delta = set()
    pol_pa_delta = set()
    max_delta = 0.0

    for r in rows:
        mu = num(r.get("MUNIT", ""))
        vp = num(r.get("MVPU", ""))
        face = mu * vp
        tface = trunc3(mu) * vp
        delta = abs(face - tface)
        is_pa = str(r.get("MPLAN", "")).strip().upper().endswith("PA")
        sm = sub_mill(mu)
        fc = int(round(face * 100)) % 100 != 0

        if sm:
            submill_n += 1
        if fc:
            frac_cent_n += 1
        if is_pa:
            pa_n += 1
        if is_pa and sm:
            pa_submill_n += 1
        if delta >= 0.009:
            delta_n += 1
            pol = (r.get("MPOLICY") or "").strip()
            pol_delta.add(pol)
            if is_pa:
                pa_delta_n += 1
                pol_pa_delta.add(pol)
        max_delta = max(max_delta, delta)

        if (r.get("MPOLICY") or "").strip() in {
            "010448806C",
            "010615191C",
            "010367438C",
            "010510671C",
        }:
            trace_rows.append(
                {
                    "MPOLICY": r.get("MPOLICY", ""),
                    "MPHASE": r.get("MPHASE", ""),
                    "MPLAN": r.get("MPLAN", ""),
                    "MUNIT": r.get("MUNIT", ""),
                    "MVPU": r.get("MVPU", ""),
                    "face_amount": f"{face:.2f}",
                    "face_if_3dp_munit": f"{tface:.2f}",
                    "face_delta": f"{delta:.2f}",
                    "is_pua_style_pa": "Y" if is_pa else "N",
                }
            )

    print("=== Issue 21K MUNIT population (read-only) ===")
    print(f"total_rows: {len(rows)}")
    print(f"submill_munit_rows: {submill_n}")
    print(f"fractional_cent_face_rows: {frac_cent_n}")
    print(f"pa_rows: {pa_n}")
    print(f"pa_submill: {pa_submill_n}")
    print(f"face_delta_ge_1cent: {delta_n}")
    print(f"face_delta_ge_1cent_pa: {pa_delta_n}")
    print(f"policies_face_delta_ge_1cent: {len(pol_delta)}")
    print(f"policies_pa_face_delta: {len(pol_pa_delta)}")
    print(f"max_face_delta: {max_delta:.2f}")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(
            fh,
            fieldnames=[
                "MPOLICY",
                "MPHASE",
                "MPLAN",
                "MUNIT",
                "MVPU",
                "face_amount",
                "face_if_3dp_munit",
                "face_delta",
                "is_pua_style_pa",
            ],
        )
        w.writeheader()
        w.writerows(trace_rows)
    print(f"trace written: {OUT}")


if __name__ == "__main__":
    main()
