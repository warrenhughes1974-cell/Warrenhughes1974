"""CFIC Issue #01 — read-only risk impact simulation (wave scopes, rollout tiers)."""
from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
EVIDENCE = Path(__file__).resolve().parents[1] / "evidence"

DUR_EST = {
    "age_pdf": 55,
    "other": 55,
    "consolidated": 800,
    "all_ages": 100,
    "expiry_age": 55,
}


def load_csv(name: str) -> list[dict]:
    with (EVIDENCE / name).open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def pdfs_for_products(inv: list[dict], products: set[str]) -> list[dict]:
    return [r for r in inv if r["product"] in products and r["skip_extraction"] != "True"]


def complexity_tier(product_row: dict) -> str:
    name = product_row["product"]
    patterns = set(product_row["naming_patterns"].split(";"))
    if "consolidated" in patterns and product_row["pdf_count"] == "1":
        return "high_consolidated"
    if "expiry_age" in patterns:
        return "high_expiry_age"
    if "all_ages" in patterns:
        return "high_all_ages"
    if name.startswith(("P7", "P8", "P9")):
        return "standard_p7_p9"
    return "standard"


def staging_estimate(pdfs: list[dict]) -> int:
    return sum(DUR_EST.get(r["naming_pattern"], 55) for r in pdfs)


def main() -> None:
    inv = load_csv("cfic_issue01_pdf_inventory.csv")
    prod = load_csv("cfic_issue01_product_summary.csv")
    xwalk = {r["cv_product"]: r for r in load_csv("cfic_issue01_crosswalk_match.csv")}

    wave1 = [r for r in pdfs_for_products(inv, {"P7MN"}) if r["filename"] in {"18.pdf", "30.pdf", "50.pdf"}]
    wave2 = pdfs_for_products(inv, {"P7FN", "P7FS", "P7MN", "P7MS"})
    all_products = {r["cv_product"] for r in load_csv("cfic_issue01_crosswalk_match.csv")} - {"Table of Days", "R69G"}
    wave_full = pdfs_for_products(inv, all_products)

    waves = [
        ("wave1_p7mn_pilot", wave1, "extract_only"),
        ("wave2_p7_family", wave2, "staging_only"),
        ("wave3_full_program", wave_full, "emit_blocked_until_obq"),
    ]
    impact = []
    for wave, pdfs, mode in waves:
        staging = staging_estimate(pdfs)
        impact.append(
            {
                "wave": wave,
                "pdf_count": len(pdfs),
                "est_staging_rows": staging,
                "est_quik_rows_per_family": staging // 10,
                "est_quik_rows_cv_tv_np_combined": (staging // 10) * 3,
                "warren_qla_output_row_delta": 0,
                "qladmin_emit_mode": mode,
            }
        )

    rollout = []
    for p in prod:
        if p["product"] == "Table of Days":
            continue
        tier = complexity_tier(p)
        patterns = p["naming_patterns"]
        rollout.append(
            {
                "product": p["product"],
                "pdf_count": p["pdf_count"],
                "complexity_tier": tier,
                "naming_patterns": patterns,
                "crosswalk_status": xwalk.get(p["product"], {}).get("crosswalk_status", ""),
                "recommended_wave": (
                    "wave1" if p["product"] == "P7MN" else "wave2" if p["product"].startswith("P7") else "wave3+"
                ),
            }
        )

    write_csv(EVIDENCE / "cfic_issue01_risk_impact_summary.csv", impact)
    write_csv(EVIDENCE / "cfic_issue01_risk_rollout_tiers.csv", rollout)
    tiers = Counter(r["complexity_tier"] for r in rollout)
    print(f"Wrote risk evidence to {EVIDENCE}")
    print("Wave1 PDFs:", len(wave1), "staging rows:", staging_estimate(wave1))
    print("Complexity tiers:", dict(tiers))


def write_csv(path: Path, rows: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)


if __name__ == "__main__":
    main()
