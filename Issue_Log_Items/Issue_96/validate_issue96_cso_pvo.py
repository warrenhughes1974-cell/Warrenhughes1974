"""Issue #96 — CSO val PVO + QuikPl* wiring for SAL MULTPL / L17 family.

Validates against full QLA_Migration/Output/ (not Test_Validation only).

SAL QuikTvs row counts are active-cut / source-aware: accept >= SAL_TV_MIN
(midyear frozen 508 is not required). L17 family uses the full annual PDAGE-
expanded QuikTvs grid: all five plans share the same row count, anchor source
identity holds, and child rate fingerprints match 1L17SP on TV1+ (TV0 blank
vs .00 allowed only on non-single-premium children per durable TV0 fill).
"""
from __future__ import annotations

import csv
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "QLA_Migration" / "Output"
RATES = OUT / "rates"

FOCUS = (
    "1SALOL",
    "1SALMI",
    "1SALML",
    "1L17SP",
    "10L171",
    "10L172",
    "117JPO",
    "17MJPO",
)
# Midyear package had 508; active 20260731 SAL cut may be higher (e.g. 516).
SAL_TV_MIN = 500
SAL_PLANS = ("1SALOL", "1SALMI", "1SALML")
L17_PLANS = ("1L17SP", "10L171", "10L172", "117JPO", "17MJPO")
L17_PARENT = "1L17SP"
L17_CHILDREN = ("10L171", "10L172", "117JPO", "17MJPO")
# Sparse pre-expansion grid had 38 rows; full annual expansion is much larger.
L17_SPARSE_MAX = 38
L17_ANNUAL_MIN_DURATIONS = 100
PL_KEY_FIELDS = ("MORT", "ETIMORT", "NFOINT", "INTMETHCV", "RSVINT", "RSVMETH", "INTMETHTV")

# Source identity anchors (qla_core/quiktvs_l17_rv.py proof slice F/00 SM).
L17_ANCHOR_GENDER = "F"
L17_ANCHOR_AGE = "00"
L17_ANCHOR_UW = "SM"
L17_ANCHOR_DURATIONS = {
    1: 56.09,
    2: 57.81,
    3: 59.64,
    10: 75.53,
    100: 1000.00,
}
L17_ANCHOR_TOLERANCE = 0.02

try:
    from qla_core import quiktvs_l17_rv as L17RV
    from qla_core.quiktvs_tv0_fill import load_true_single_premium_plans
except ImportError:  # pragma: no cover - repo layout guard
    L17RV = None
    load_true_single_premium_plans = None


def _load(path: Path) -> list[dict]:
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def _plan_rows(rows: list[dict], plan: str) -> list[dict]:
    return [r for r in rows if (r.get("PLAN") or "").strip() == plan]


def _codes(row: dict) -> tuple:
    return tuple((row.get(k) or "").strip() for k in PL_KEY_FIELDS)


def _tv0_is_blank(value: str) -> bool:
    return value.strip() == ""


def _tv0_is_zero_formatted(value: str) -> bool:
    s = value.strip()
    if not s:
        return False
    try:
        return float(s) == 0.0
    except ValueError:
        return False


def _duration_values(row: dict) -> dict[int, str]:
    """Map QL annual duration -> formatted TV cell text for one QuikTvs row."""
    try:
        cntl = int((row.get("CNTL") or "").strip())
    except ValueError:
        return {}
    out: dict[int, str] = {}
    for i in range(10):
        val = (row.get(f"TV{i}") or "").strip()
        if val or i == 0:
            out[cntl * 10 + i] = val
    return out


def l17_annual_fingerprint(rows: list[dict], plan: str) -> dict[tuple, dict[int, str]]:
    """Per-key annual duration grid for an L17-family plan."""
    fp: dict[tuple, dict[int, str]] = {}
    for row in _plan_rows(rows, plan):
        key = tuple((row.get(k) or "").strip() for k in ("AGE", "CNTL", "GENDER", "UWCLASS", "BAND"))
        cells = _duration_values(row)
        if not cells:
            continue
        bucket = fp.setdefault(key, {})
        for dur, val in cells.items():
            if dur not in bucket or (val and not bucket[dur]):
                bucket[dur] = val
    return fp


def _tv0_values_equivalent(parent_tv0: str, child_tv0: str, *, child_is_sp: bool) -> bool:
    if parent_tv0 == child_tv0:
        return True
    if child_is_sp:
        return False
    if _tv0_is_blank(parent_tv0) and _tv0_is_zero_formatted(child_tv0):
        return True
    return False


def _anchor_duration_map(fp: dict[tuple, dict[int, str]]) -> dict[int, str]:
    """Merge F/00 SM durations across all CNTL rows for source-identity checks."""
    merged: dict[int, str] = {}
    for (age, _cntl, gender, uw, _band), cells in fp.items():
        if age != L17_ANCHOR_AGE or gender != L17_ANCHOR_GENDER or uw != L17_ANCHOR_UW:
            continue
        for dur, val in cells.items():
            if val or dur == 0:
                merged[dur] = val
    return merged


def compare_l17_child_fingerprint(
    parent_fp: dict[tuple, dict[int, str]],
    child_fp: dict[tuple, dict[int, str]],
    *,
    child_plan: str,
    sp_plans: set[str],
) -> list[str]:
    """Return human-readable mismatches between child and 1L17SP annual grids."""
    fails: list[str] = []
    child_is_sp = child_plan in sp_plans

    if set(child_fp) != set(parent_fp):
        missing = sorted(set(parent_fp) - set(child_fp))
        extra = sorted(set(child_fp) - set(parent_fp))
        if missing:
            fails.append(f"{child_plan}: missing {len(missing)} QuikTvs key(s) vs {L17_PARENT}")
        if extra:
            fails.append(f"{child_plan}: extra {len(extra)} QuikTvs key(s) vs {L17_PARENT}")
        return fails

    for key in sorted(parent_fp):
        parent_cells = parent_fp[key]
        child_cells = child_fp[key]
        parent_durs = {d for d in parent_cells if d >= 1 and parent_cells.get(d)}
        child_durs = {d for d in child_cells if d >= 1 and child_cells.get(d)}
        if parent_durs != child_durs:
            fails.append(
                f"{child_plan}: duration coverage mismatch at key {key!r} "
                f"(parent={len(parent_durs)} child={len(child_durs)})"
            )
            continue
        for dur in sorted(parent_durs):
            p_val = parent_cells.get(dur, "")
            c_val = child_cells.get(dur, "")
            if p_val != c_val:
                fails.append(
                    f"{child_plan}: Dur{dur} mismatch at key {key!r} "
                    f"(parent={p_val!r} child={c_val!r})"
                )
        p0 = parent_cells.get(0, "")
        c0 = child_cells.get(0, "")
        if not _tv0_values_equivalent(p0, c0, child_is_sp=child_is_sp):
            fails.append(
                f"{child_plan}: TV0 mismatch at key {key!r} "
                f"(parent={p0!r} child={c0!r})"
            )
    return fails


def validate_l17_annual_shape(
    rows: list[dict],
    tv_counts: Counter,
    *,
    sp_plans: set[str] | None = None,
) -> tuple[list[str], list[str]]:
    """Validate L17 full annual grid shape, source identity, and inheritance."""
    fails: list[str] = []
    notes: list[str] = []
    parent_count = tv_counts.get(L17_PARENT, 0)

    if parent_count <= L17_SPARSE_MAX:
        fails.append(
            f"{L17_PARENT}: QuikTvs looks sparse ({parent_count} rows); "
            f"expected full annual expansion (> {L17_SPARSE_MAX})"
        )
        return fails, notes

    for plan in L17_PLANS:
        got = tv_counts.get(plan, 0)
        if got != parent_count:
            fails.append(f"{plan}: QuikTvs expected {parent_count} (match {L17_PARENT}) got {got}")

    parent_fp = l17_annual_fingerprint(rows, L17_PARENT)
    anchor = _anchor_duration_map(parent_fp)
    if not anchor:
        fails.append(
            f"{L17_PARENT}: missing anchor slice "
            f"{L17_ANCHOR_GENDER}/{L17_ANCHOR_AGE} {L17_ANCHOR_UW}"
        )
    else:
        populated = {d for d, v in anchor.items() if d >= 1 and v}
        if len(populated) < L17_ANNUAL_MIN_DURATIONS:
            fails.append(
                f"{L17_PARENT}: anchor annual duration coverage "
                f"{len(populated)} < {L17_ANNUAL_MIN_DURATIONS}"
            )
        for dur, expected in L17_ANCHOR_DURATIONS.items():
            got = anchor.get(dur, "")
            if not got:
                fails.append(
                    f"{L17_PARENT}: anchor Dur{dur} missing on "
                    f"{L17_ANCHOR_GENDER}/{L17_ANCHOR_AGE} {L17_ANCHOR_UW}"
                )
                continue
            try:
                if abs(float(got) - expected) > L17_ANCHOR_TOLERANCE:
                    fails.append(
                        f"{L17_PARENT}: anchor Dur{dur} expected ~{expected} got {got}"
                    )
            except ValueError:
                fails.append(f"{L17_PARENT}: anchor Dur{dur} non-numeric {got!r}")

    resolved_sp = sp_plans if sp_plans is not None else set()
    if not resolved_sp and load_true_single_premium_plans is not None:
        resolved_sp = load_true_single_premium_plans(str(ROOT))

    child_fp_cache: dict[str, dict[tuple, dict[int, str]]] = {}
    for child in L17_CHILDREN:
        child_fp = l17_annual_fingerprint(rows, child)
        child_fp_cache[child] = child_fp
        fails.extend(
            compare_l17_child_fingerprint(
                parent_fp,
                child_fp,
                child_plan=child,
                sp_plans=resolved_sp,
            )
        )

    notes.append(
        f"L17 annual grid: {parent_count} QuikTvs rows/plan; "
        f"anchor F/00 SM Dur1..Dur100 populated; children match {L17_PARENT} TV1+"
    )
    if L17RV is not None:
        notes.append(
            f"L17 RV source module anchors: page1 VALUE1..3 "
            f"{', '.join(L17RV.ANCHOR_PAGE1_VALUES[:3])}"
        )
    return fails, notes


def main() -> int:
    fails: list[str] = []
    notes: list[str] = []
    qp = {(r.get("PLAN") or "").strip(): r for r in _load(OUT / "quikplan.csv")}
    tvs = _load(RATES / "QuikTvs.csv")
    pltv = _load(RATES / "QuikPlTv.csv")
    plcv = _load(RATES / "QuikPlCv.csv")
    tv_counts = Counter((r.get("PLAN") or "").strip() for r in tvs)

    for plan in FOCUS:
        row = qp.get(plan)
        if not row:
            fails.append(f"{plan}: missing from quikplan")
            continue
        if (row.get("PLANVALOPT") or "").strip() != "Y":
            fails.append(f"{plan}: PLANVALOPT expected Y got {(row.get('PLANVALOPT') or '').strip()!r}")
        if (row.get("GDVARYTV") or "").strip() != "Y":
            fails.append(f"{plan}: GDVARYTV expected Y got {(row.get('GDVARYTV') or '').strip()!r}")

        got_tv = tv_counts.get(plan, 0)
        if plan in SAL_PLANS:
            if got_tv < SAL_TV_MIN:
                fails.append(f"{plan}: QuikTvs expected >={SAL_TV_MIN} (active-cut) got {got_tv}")
            else:
                notes.append(
                    f"{plan}: active SAL QuikTvs count {got_tv} accepted "
                    f"(>={SAL_TV_MIN}; midyear frozen 508 not required)"
                )

    l17_fails, l17_notes = validate_l17_annual_shape(tvs, tv_counts)
    fails.extend(l17_fails)
    notes.extend(l17_notes)

    # 1SALMI Pl* codes must match 1SALOL (CSO_Valuation_Setup)
    for label, rows in (("QuikPlTv", pltv), ("QuikPlCv", plcv)):
        ol = sorted(
            ((r.get("GENDER") or "").strip(), _codes(r))
            for r in _plan_rows(rows, "1SALOL")
        )
        mi = sorted(
            ((r.get("GENDER") or "").strip(), _codes(r))
            for r in _plan_rows(rows, "1SALMI")
        )
        if ol and mi and ol != mi:
            fails.append(f"1SALMI {label} codes != 1SALOL ({mi} vs {ol})")

    for plan in FOCUS:
        if plan in L17_PLANS:
            if len(_plan_rows(pltv, plan)) < 2:
                fails.append(f"{plan}: QuikPlTv expected >=2 rows got {len(_plan_rows(pltv, plan))}")
        elif plan.startswith("1SAL") and len(_plan_rows(plcv, plan)) < 2:
            fails.append(f"{plan}: QuikPlCv expected >=2 rows got {len(_plan_rows(plcv, plan))}")

    # Issue A A8e — no A-prefix PLANVALOPT=Y
    a_y = [
        p for p, r in qp.items()
        if p.startswith("A") and (r.get("PLANVALOPT") or "").strip().upper() == "Y"
    ]
    if a_y:
        fails.append(f"A8e: annuity PLANVALOPT=Y plans={a_y}")

    if fails:
        print("FAIL - Issue #96")
        for f in fails:
            print(" ", f)
        return 1
    print("PASS - Issue #96 CSO PVO + SAL/L17 QuikPl* / QuikTvs")
    for n in notes:
        print(f"  NOTE: {n}")
    for plan in FOCUS:
        print(
            f"  {plan}: PVO=Y GDVARYTV=Y QuikTvs={tv_counts.get(plan, 0)} "
            f"PlTv={len(_plan_rows(pltv, plan))} PlCv={len(_plan_rows(plcv, plan))}"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
