"""Emit QLAdmin QuikGps + QuikPlGp from CFIC PDF staging (standalone — not Warren app.py)."""
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]  # CFIC_Rates
REPO = ROOT.parent
STAGING = ROOT / "extracted_pdf_rates" / "staging"
OUT_DIR = ROOT / "output" / "rates"

sys.path.insert(0, str(REPO))
from qla_core.rate_dbf_schema import (  # noqa: E402
    STANDARD_EFFDATE,
    format_factor,
    key_table_fields,
    factor_table_fields,
)


def load_staging(plan: str) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    plan_dir = STAGING / plan
    for path in sorted(plan_dir.glob("*.csv")):
        with path.open(newline="", encoding="utf-8") as f:
            rows.extend(csv.DictReader(f))
    return rows


def emit_quikgps(rows: list[dict[str, str]], ql_plan: str) -> list[dict[str, str]]:
    """One QuikGps row per age/gender/uw/band; annual rate in GP0."""
    out: list[dict[str, str]] = []
    for row in rows:
        for band_code, rate_field in [("01", "rate_under_100k"), ("02", "rate_over_100k")]:
            rate = (row.get(rate_field) or "").strip()
            if not rate:
                continue
            gp0, fits, _ = format_factor(rate, source_decimals=2)
            if not fits:
                continue
            rec = {
                "PLAN": ql_plan.ljust(6)[:6],
                "AGE": str(row["age"]).zfill(2)[:2],
                "CNTL": "00",
                "GENDER": row["gender"],
                "UWCLASS": row["uwclass"],
                "BAND": band_code,
                "ISSCNTRY": "    ",
                "ISSUEST": "  ",
                "EFFDATE": STANDARD_EFFDATE,
            }
            for i in range(10):
                rec[f"GP{i}"] = gp0 if i == 0 else ""
            out.append(rec)
    return out


def emit_quikplgp(ql_plan: str, rows: list[dict[str, str]]) -> list[dict[str, str]]:
    """Rate-key rows — MORT placeholders until OBQ-2 cleared."""
    combos = {(r["gender"], r["uwclass"], b) for r in rows for b in ("01", "02")}
    keys: list[dict[str, str]] = []
    for gender, uwclass, band in sorted(combos):
        keys.append(
            {
                "PLAN": ql_plan.ljust(6)[:6],
                "GENDER": gender,
                "UWCLASS": uwclass,
                "BAND": band,
                "ISSCNTRY": "    ",
                "ISSUEST": "  ",
                "EFFDATE": STANDARD_EFFDATE,
                "MORT": "  ",
                "ETIMORT": "  ",
                "NFOINT": " ",
                "INTMETHCV": " ",
            }
        )
    return keys


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", default="P7MN")
    args = parser.parse_args()

    staging = load_staging(args.plan.upper())
    if not staging:
        raise SystemExit(f"No staging for {args.plan}")

    ql_plan = staging[0]["ql_plan"]
    gps = emit_quikgps(staging, ql_plan)
    plgp = emit_quikplgp(ql_plan, staging)

    gp_fields = [f[0] for f in factor_table_fields("QuikGps")]
    plgp_fields = [f[0] for f in key_table_fields("QuikPlGp")]

    write_csv(OUT_DIR / "quikgps.csv", gp_fields, gps)
    write_csv(OUT_DIR / "quikplgp.csv", plgp_fields, plgp)
    print(f"Wrote {len(gps)} QuikGps rows, {len(plgp)} QuikPlGp rows -> {OUT_DIR}")
    print("NOTE: QuikPlGp MORT/assumption fields are placeholders (OBQ-2).")


if __name__ == "__main__":
    main()
