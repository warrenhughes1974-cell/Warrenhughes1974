"""Build Issue 145B Control/Test QuikIsrr UAT copies. Does not change converter or Output."""
from __future__ import annotations

import csv
import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUTPUT = ROOT / "QLA_Migration" / "Output"
UAT = Path(__file__).resolve().parent
CONTROL = UAT / "CONTROL"
TEST = UAT / "TEST"
CMP = UAT / "comparison"

GOLD_MPOLICY = ("9010815236C", "9011050114C", "9011069610C")
EXPECTED = {
    "9010815236C": {
        "lp_units": 25.0,
        "munit": 25.0,
        "expected_control": 23.59744,
        "expected_test": 25.0,
        "expected_sum": 1402.56,
        "expected_n": 8,
    },
    "9011050114C": {
        "lp_units": 25.0,
        "munit": 25.0,
        "expected_control": 24.864,
        "expected_test": 25.0,
        "expected_sum": 136.00,
        "expected_n": 1,
    },
    "9011069610C": {
        "lp_units": 50.0,
        "munit": 50.0,
        "expected_control": 49.594,
        "expected_test": 50.0,
        "expected_sum": 406.00,
        "expected_n": 1,
    },
}
HASH_TABLES = (
    "QuikIsrr.csv",
    "quikisrr.csv",
    "quikmstr.csv",
    "quikridr.csv",
    "QuikIswl.csv",
    "quikspec.csv",
    "quikclnt.csv",
    "quikclms.csv",
    "quikclmp.csv",
    "quikbenh.csv",
)


def sha256(path: Path) -> str | None:
    if not path.is_file():
        return None
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> None:
    src = OUTPUT / "QuikIsrr.csv"
    CONTROL.mkdir(exist_ok=True)
    TEST.mkdir(exist_ok=True)
    CMP.mkdir(exist_ok=True)

    shutil.copy2(src, CONTROL / "QuikIsrr.csv")

    removed = []
    kept = 0
    with src.open(newline="", encoding="utf-8-sig") as fin, (
        TEST / "QuikIsrr.csv"
    ).open("w", newline="", encoding="utf-8") as fout:
        reader = csv.DictReader(fin)
        fieldnames = reader.fieldnames or ["MPOLICY", "MSURRDATE", "MSURRAMT"]
        writer = csv.DictWriter(fout, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        for i, row in enumerate(reader, start=2):
            mp = (row.get("MPOLICY") or "").strip()
            if mp in GOLD_MPOLICY:
                amt = float((row.get("MSURRAMT") or "0").replace(",", "") or 0)
                removed.append({
                    "source_line": i,
                    "mpolicy": mp,
                    "msurrdate": (row.get("MSURRDATE") or "").strip(),
                    "msurramt": amt,
                    "reversal_status": "unreversed (Issue 34 already dropped REVERSAL=Y)",
                    "transaction_type": "PACTG 0561 emitted as QuikIsrr",
                })
                continue
            writer.writerow(row)
            kept += 1

    by_pol: dict[str, list] = {k: [] for k in GOLD_MPOLICY}
    for r in removed:
        by_pol[r["mpolicy"]].append(r)

    gold_summary = {}
    for mp, spec in EXPECTED.items():
        rows = by_pol[mp]
        total = round(sum(x["msurramt"] for x in rows), 2)
        gold_summary[mp] = {
            **spec,
            "rows_removed": len(rows),
            "sum_removed": total,
            "sum_matches_expected": abs(total - spec["expected_sum"]) < 0.005,
            "count_matches_expected": len(rows) == spec["expected_n"],
            "rows": rows,
        }

    output_hashes = {}
    for name in HASH_TABLES:
        output_hashes[name] = sha256(OUTPUT / name)

    comparison = {
        "issue": "145B",
        "built_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "converter_changed": False,
        "app_version_changed": False,
        "output_root_modified": False,
        "control": {
            "quikisrr_path": str((CONTROL / "QuikIsrr.csv").relative_to(ROOT)).replace("\\", "/"),
            "quikisrr_sha256": sha256(CONTROL / "QuikIsrr.csv"),
            "identical_to_output_quikisrr": sha256(CONTROL / "QuikIsrr.csv") == output_hashes["QuikIsrr.csv"],
            "other_tables": "Use QLA_Migration/Output/ as-is (not copied).",
        },
        "test": {
            "quikisrr_path": str((TEST / "QuikIsrr.csv").relative_to(ROOT)).replace("\\", "/"),
            "quikisrr_sha256": sha256(TEST / "QuikIsrr.csv"),
            "rows_kept": kept,
            "rows_removed": len(removed),
            "policies_affected": list(GOLD_MPOLICY),
            "other_tables": "Same files as Control: QLA_Migration/Output/ (quikmstr, quikridr, QuikIswl, PACTG, etc.).",
        },
        "delta": {
            "tables_changed": ["QuikIsrr.csv only"],
            "tables_unchanged": [n for n in HASH_TABLES if n.lower() != "quikisrr.csv"],
            "non_gold_policies_changed": False,
            "pactg_changed": False,
            "munit_changed": False,
            "quikiswl_changed": False,
            "removed_row_count": len(removed),
            "removed_amount_total": round(sum(r["msurramt"] for r in removed), 2),
        },
        "output_sha256": output_hashes,
        "gold": gold_summary,
        "removed_rows": removed,
        "guardrail": {
            "vb_only": True,
            "issue_146_non_vb_untouched": True,
            "examples_not_in_this_test": ["9010761639C", "9010760840C"],
        },
    }

    (CMP / "issue145b_control_vs_test.json").write_text(
        json.dumps(comparison, indent=2), encoding="utf-8"
    )

    with (CMP / "issue145b_removed_quikisrr_rows.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(
            f,
            fieldnames=["source_line", "mpolicy", "msurrdate", "msurramt", "reversal_status", "transaction_type"],
        )
        w.writeheader()
        w.writerows(removed)

    print(json.dumps({
        "control_rows": kept + len(removed),
        "test_rows": kept,
        "removed": len(removed),
        "control_sha": comparison["control"]["quikisrr_sha256"],
        "test_sha": comparison["test"]["quikisrr_sha256"],
        "identical_to_output": comparison["control"]["identical_to_output_quikisrr"],
        "gold": {k: {"n": v["rows_removed"], "sum": v["sum_removed"], "ok": v["sum_matches_expected"]} for k, v in gold_summary.items()},
    }, indent=2))


if __name__ == "__main__":
    main()
