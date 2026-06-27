"""Read-only Risk Agent simulation — Issue 21K MUNIT precision (N10,3 → N10,5)."""
from __future__ import annotations

import csv
import math
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
RIDR = REPO / "QLA_Migration" / "Output" / "quikridr.csv"
OUT = REPO / "Issue_Log_Items" / "Issue_21" / "Issue_21K_Risk_Simulation.csv"


def num(s: str) -> float:
    try:
        return float(str(s).replace(",", "").strip() or 0)
    except ValueError:
        return 0.0


def trunc3(x: float) -> float:
    return math.floor(x * 1000 + 1e-9) / 1000


def round5(x: float) -> float:
    return round(x, 5)


def sub_mill(x: float) -> bool:
    return abs(x * 1000 - math.floor(x * 1000 + 1e-9)) > 1e-9


def main() -> None:
    rows = list(csv.DictReader(RIDR.open(encoding="latin1", newline="")))
    sim_rows = []
    converter_change_n = 0
    qladmin_recover_n = 0
    pa_recover_n = 0
    max_recover = 0.0
    plan_counter: Counter[str] = Counter()

    for r in rows:
        mu = num(r.get("MUNIT", ""))
        vp = num(r.get("MVPU", ""))
        csv_mu = round5(mu)
        stored_3 = trunc3(mu)
        stored_5 = round5(mu)
        face_csv = csv_mu * vp
        face_3 = stored_3 * vp
        face_5 = stored_5 * vp
        recover = abs(face_csv - face_3)
        is_pa = str(r.get("MPLAN", "")).strip().upper().endswith("PA")

        # Converter "before vs after": no proposed mapping change
        if abs(csv_mu - mu) > 1e-9:
            converter_change_n += 1

        if recover >= 0.009:
            qladmin_recover_n += 1
            plan_counter[(r.get("MPLAN") or "").strip()] += 1
            if is_pa:
                pa_recover_n += 1
            max_recover = max(max_recover, recover)

        if (r.get("MPOLICY") or "").strip() in {"010448806C", "010615191C", "010510671C"}:
            sim_rows.append(
                {
                    "MPOLICY": r.get("MPOLICY", ""),
                    "MPHASE": r.get("MPHASE", ""),
                    "MPLAN": r.get("MPLAN", ""),
                    "csv_MUNIT": f"{csv_mu:.5f}",
                    "stored_N10_3": f"{stored_3:.3f}",
                    "stored_N10_5": f"{stored_5:.5f}",
                    "MVPU": r.get("MVPU", ""),
                    "face_csv": f"{face_csv:.2f}",
                    "face_N10_3": f"{face_3:.2f}",
                    "face_N10_5": f"{face_5:.2f}",
                    "recover_dollars": f"{recover:.2f}",
                }
            )

    submill = sum(sub_mill(num(r.get("MUNIT", ""))) for r in rows)
    frac_cent = sum(int(round(num(r.get("MUNIT", "")) * num(r.get("MVPU", "")) * 100)) % 100 != 0 for r in rows)

    print("=== Issue 21K Risk simulation ===")
    print(f"quikridr_rows: {len(rows)}")
    print(f"converter_rows_would_change: {converter_change_n}")
    print(f"submill_munit_rows: {submill}")
    print(f"fractional_cent_face_rows: {frac_cent}")
    print(f"rows_recovered_by_N10_5_vs_N10_3: {qladmin_recover_n}")
    print(f"pa_rows_recovered: {pa_recover_n}")
    print(f"max_face_recovery_dollars: {max_recover:.2f}")
    print("top_plans_by_recovery_rows:")
    for plan, cnt in plan_counter.most_common(10):
        print(f"  {plan}: {cnt}")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(sim_rows[0].keys()) if sim_rows else [])
        if sim_rows:
            w.writeheader()
            w.writerows(sim_rows)
    print(f"simulation trace: {OUT}")


if __name__ == "__main__":
    main()
