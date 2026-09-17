"""Issue #169 - 667 ART (5667AT) net valuation premium must be present in Output.

Fail-closed release smoke. LifePRO stores this plan's net valuation premium by
ATTAINED AGE in PAAGERAT; PDAGE carries no NP rows for the family and nothing read
the PAAGERAT NP leg, so 5667AT emitted zero QuikNps rows, MTABNET valued 0, and the
plan reserved $0 against LifePRO's $133,546.48 across 96 valued rows.

The loader (`qla_core/paagerat_np_loader.py`) expands the attained-age vector onto the
issue-age x duration grid QLAdmin reads for net premium, because QuikNps has no
quikplan VARY field that would let it read a slot axis as attained age.

Reconciliation at the time of the fix: 94 of the 96 valued rows match LifePRO's
RV_MEAN_RV to the cent. The two that do not are known and out of scope here - one sits in
the 19950101 (667 ART 95) generation, and policy 9010886099 seq 2 carries $1,317.00
against zero units, which no per-unit grid can reproduce.

Both era generations are checked independently. 19000101 is the base '667 ART' segment;
19950101 is the PSUBSSEG-substituted '667 ART 95' band. Checking only the total row count
would let one generation vanish silently while the other kept the floor satisfied, which is
the exact drop class this smoke exists to catch.

Exits 1 if the emit is missing, truncated, zeroed, or loses its valuation assumptions.

Usage:
    python tools/validators/validate_issue169_667art_np.py
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RATES = ROOT / "QLA_Migration/Output/rates"

PLAN = "5667AT"

NP_COLS = [f"NP{i}" for i in range(10)]

# Era generations, each floored on its own. Floors are from the proven 2026-09-17 emit:
# growth is fine, a drop means a leg broke.
GENERATIONS = {
    "19000101": {"label": "667 ART base", "min_rows": 1736, "min_nonzero": 15000},
    "19950101": {"label": "667 ART 95 (PSUBSSEG band)", "min_rows": 1736, "min_nonzero": 15000},
}
MIN_TOTAL_ROWS = 3472

EXPECTED_KEYS = {("M", "PR"), ("M", "ST"), ("F", "PR"), ("F", "ST")}

# Golden cells, M/PR, first duration block - proven to the cent against LifePRO
# RV_MEAN_RV on 94 of the 96 valued rows (see module docstring for the two exceptions).
# Both generations carry the same attained-age vector.
GOLDEN = {
    ("35", "00", "NP0"): "2.05",
    ("45", "00", "NP0"): "4.47",
    ("65", "00", "NP0"): "25.11",
}


def _read(path: Path) -> list[dict]:
    with path.open(encoding="utf-8-sig") as fh:
        return list(csv.DictReader(fh))


def _as_float(value) -> float:
    try:
        return round(float(str(value or "0").strip() or 0), 2)
    except ValueError:
        return 0.0


def _check_generation(effdate: str, spec: dict, rows: list[dict]) -> tuple[list[str], int]:
    """Validate one era generation's QuikNps grid. Returns (failures, cell pairs checked)."""
    failures: list[str] = []
    tag = f"{PLAN} EFFDATE={effdate} ({spec['label']})"

    if not rows:
        return [f"QuikNps {tag}: no rows at all - this generation dropped"], 0

    if len(rows) < spec["min_rows"]:
        failures.append(
            f"QuikNps {tag}: {len(rows)} rows, expected >= {spec['min_rows']} "
            "(PAAGERAT NP leg dropped or truncated)"
        )

    missing = EXPECTED_KEYS - {(r["GENDER"], r["UWCLASS"]) for r in rows}
    if missing:
        failures.append(f"QuikNps {tag}: missing gender/class keys {sorted(missing)}")

    nonzero = sum(1 for r in rows for c in NP_COLS if _as_float(r.get(c)) != 0.0)
    if nonzero < spec["min_nonzero"]:
        failures.append(
            f"QuikNps {tag}: {nonzero} non-zero cells, expected >= {spec['min_nonzero']} "
            "(grid emitted but zeroed)"
        )

    mpr = {
        (r["AGE"], r["CNTL"]): r
        for r in rows
        if r["GENDER"] == "M" and r["UWCLASS"] == "PR"
    }
    for (age, cntl, col), expected in sorted(GOLDEN.items()):
        row = mpr.get((age, cntl))
        if row is None:
            failures.append(f"QuikNps {tag} M/PR: missing AGE={age} CNTL={cntl}")
            continue
        got = (row.get(col) or "").strip()
        if _as_float(got) != _as_float(expected):
            failures.append(
                f"QuikNps {tag} M/PR AGE={age} CNTL={cntl} {col}: "
                f"got {got!r}, expected {expected!r}"
            )

    # Attained-age invariant: the same attained age must carry the same net premium
    # whichever issue age reaches it. NP[age][d] == NP[age+1][d-1].
    checked = 0
    for age in range(20, 71):
        a, b = mpr.get((f"{age:02d}", "00")), mpr.get((f"{age + 1:02d}", "00"))
        if not a or not b:
            continue
        for d in range(1, 10):
            left, right = _as_float(a.get(f"NP{d}")), _as_float(b.get(f"NP{d - 1}"))
            if left == 0.0 and right == 0.0:
                continue
            checked += 1
            if abs(left - right) > 0.005:
                failures.append(
                    f"QuikNps {tag} attained-age break: AGE={age} NP{d}={left} != "
                    f"AGE={age + 1} NP{d - 1}={right}"
                )
    if checked < 200:
        failures.append(
            f"QuikNps {tag}: only {checked} attained-age cell pairs verifiable, expected >= 200"
        )

    return failures, checked


def main() -> int:
    failures: list[str] = []

    nps_path = RATES / "QuikNps.csv"
    pltv_path = RATES / "QuikPlTv.csv"
    for path in (nps_path, pltv_path):
        if not path.exists():
            print(f"FAIL: missing {path}")
            return 1

    rows = [r for r in _read(nps_path) if (r.get("PLAN") or "").strip() == PLAN]

    if len(rows) < MIN_TOTAL_ROWS:
        failures.append(
            f"QuikNps {PLAN}: {len(rows)} rows total, expected >= {MIN_TOTAL_ROWS} "
            f"across {len(GENERATIONS)} era generations"
        )

    total_pairs = 0
    for effdate, spec in sorted(GENERATIONS.items()):
        gen_rows = [r for r in rows if r.get("EFFDATE") == effdate]
        gen_failures, pairs = _check_generation(effdate, spec, gen_rows)
        failures.extend(gen_failures)
        total_pairs += pairs

    unexpected = {r.get("EFFDATE") for r in rows} - set(GENERATIONS)
    if unexpected:
        print(f"  NOTE: additional {PLAN} generations present: {sorted(unexpected)}")

    # A grid with no valuation assumptions still reserves $0 (the 7619PU lesson), so every
    # generation's QuikPlTv keys must carry mortality, interest and method.
    pltv = [r for r in _read(pltv_path) if (r.get("PLAN") or "").strip() == PLAN]
    for effdate in sorted(GENERATIONS):
        gen_keys = [r for r in pltv if r.get("EFFDATE") == effdate]
        if not gen_keys:
            failures.append(
                f"QuikPlTv {PLAN}: no EFFDATE={effdate} key rows - grid will be ignored"
            )
            continue
        classes = {r.get("UWCLASS") for r in gen_keys}
        for required in ("PR", "ST"):
            if required not in classes:
                failures.append(
                    f"QuikPlTv {PLAN} EFFDATE={effdate}: no {required} key row"
                )
        for r in gen_keys:
            blank = [f for f in ("MORT", "RSVINT", "RSVMETH") if not (r.get(f) or "").strip()]
            if blank:
                failures.append(
                    f"QuikPlTv {PLAN} EFFDATE={effdate} {r.get('GENDER')}/{r.get('UWCLASS')}: "
                    f"blank {blank} - reserve will value 0"
                )

    label = (
        f"validate_issue169_667art_np: {PLAN} QuikNps rows={len(rows)} "
        f"generations={len(GENERATIONS)} QuikPlTv keys={len(pltv)}"
    )
    if failures:
        print(f"{label}\nFAIL:")
        for f in failures:
            print(f"  - {f}")
        return 1

    print(label)
    for effdate, spec in sorted(GENERATIONS.items()):
        n = sum(1 for r in rows if r.get("EFFDATE") == effdate)
        print(f"  EFFDATE={effdate} {spec['label']}: {n} rows")
    print(
        f"PASS: {PLAN} net premium emitted on all {len(GENERATIONS)} generations "
        f"({total_pairs} attained-age pairs consistent, "
        f"{len(pltv)} QuikPlTv keys with MORT/RSVINT/RSVMETH)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
