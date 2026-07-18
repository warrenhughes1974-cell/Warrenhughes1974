"""
Issue #83 — read-only fleet audit: gender member variances missing companion rate keys.

For each plan with QuikPlGd members F and M, and each GP/DB/CV/TV/DV key family that
already has at least one F/M key, report genders that lack a key row.

Values=N in QLAdmin means the key header exists but no factor grid rows exist —
this script confirms companion gaps have zero factor rows (safe to stub keys only).

Outputs:
  Issue_Log_Items/Issue_83/evidence/issue83_gender_companion_key_gaps.csv
  Issue_Log_Items/Issue_83/evidence/issue83_gender_companion_summary.md
"""
from __future__ import annotations

import csv
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RATES = ROOT / "QLA_Migration" / "Output" / "rates"
EVID = ROOT / "Issue_Log_Items" / "Issue_83" / "evidence"

FAMILIES = ("QuikPlGp", "QuikPlDb", "QuikPlCv", "QuikPlTv", "QuikPlDv")
FACTOR = {
    "QuikPlGp": "QuikGps",
    "QuikPlDb": "QuikDbs",
    "QuikPlCv": "QuikCvs",
    "QuikPlTv": "QuikTvs",
    "QuikPlDv": "QuikDvs",
}
REAL_G = ("F", "M")


def _load_gd() -> dict[str, set[str]]:
    out: dict[str, set[str]] = defaultdict(set)
    with (RATES / "QuikPlGd.csv").open(newline="", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            out[(r.get("PLAN") or "").strip()].add((r.get("GDCODE") or "").strip())
    return out


def _load_keys(table: str) -> dict[str, set[str]]:
    out: dict[str, set[str]] = defaultdict(set)
    fp = RATES / f"{table}.csv"
    if not fp.exists():
        return out
    with fp.open(newline="", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            out[(r.get("PLAN") or "").strip()].add((r.get("GENDER") or "").strip())
    return out


def _load_factors(table: str) -> dict[str, set[str]]:
    out: dict[str, set[str]] = defaultdict(set)
    fp = RATES / f"{FACTOR[table]}.csv"
    if not fp.exists():
        return out
    with fp.open(newline="", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            out[(r.get("PLAN") or "").strip()].add((r.get("GENDER") or "").strip())
    return out


def main() -> int:
    if not (RATES / "QuikPlGd.csv").exists():
        print(f"MISSING rates package: {RATES}")
        return 2

    EVID.mkdir(parents=True, exist_ok=True)
    gd = _load_gd()
    rows = []
    for fam in FAMILIES:
        keys = _load_keys(fam)
        fac = _load_factors(fam)
        for plan, members in sorted(gd.items()):
            real = sorted(m for m in members if m in REAL_G)
            if len(real) < 2:
                continue
            have = keys.get(plan, set())
            if not any(g in have for g in REAL_G):
                continue
            for g in real:
                if g in have:
                    continue
                has_fac = g in fac.get(plan, set())
                rows.append({
                    "KEY_TABLE": fam,
                    "PLAN": plan,
                    "MISSING_GENDER": g,
                    "EXISTING_GENDERS": "|".join(sorted(h for h in have if h in REAL_G)),
                    "FACTOR_ROWS_FOR_MISSING": "Y" if has_fac else "N",
                    "QLA_VALUES_EXPECTED": "Y" if has_fac else "N",
                })

    out_csv = EVID / "issue83_gender_companion_key_gaps.csv"
    with out_csv.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()) if rows else [
            "KEY_TABLE", "PLAN", "MISSING_GENDER", "EXISTING_GENDERS",
            "FACTOR_ROWS_FOR_MISSING", "QLA_VALUES_EXPECTED",
        ])
        w.writeheader()
        w.writerows(rows)

    by_fam = Counter(r["KEY_TABLE"] for r in rows)
    plans = sorted({r["PLAN"] for r in rows})
    unexpected = sum(1 for r in rows if r["FACTOR_ROWS_FOR_MISSING"] == "Y")
    anchor = [r for r in rows if r["PLAN"] == "221END"]

    summary = EVID / "issue83_gender_companion_summary.md"
    lines = [
        "# Issue #83 — Gender companion key gap summary",
        "",
        f"**Rates package:** `{RATES.as_posix()}`",
        f"**Gap rows:** {len(rows)}",
        f"**Unique plans:** {len(plans)}",
        f"**Unexpected (missing gender has factors):** {unexpected}",
        "",
        "## By key family",
        "",
        "| Family | Companion keys to add |",
        "|--------|----------------------:|",
    ]
    for fam in FAMILIES:
        lines.append(f"| {fam} | {by_fam.get(fam, 0)} |")
    lines += [
        "",
        "## Anchor 221END",
        "",
        "| Family | Missing gender | Values expected |",
        "|--------|----------------|-----------------|",
    ]
    for r in anchor:
        lines.append(
            f"| {r['KEY_TABLE']} | {r['MISSING_GENDER']} | {r['QLA_VALUES_EXPECTED']} |"
        )
    if not anchor:
        lines.append("| (none) | | |")
    lines += ["", f"Detail CSV: `{out_csv.as_posix()}`", ""]
    summary.write_text("\n".join(lines), encoding="utf-8")

    print(f"Wrote {out_csv} ({len(rows)} gaps)")
    print(f"Wrote {summary}")
    print(f"by family: {dict(by_fam)}")
    print(f"221END: {anchor}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
