"""Confirm the 15 'absent' BA keys are Issue #2 join artifacts, unchanged vs baseline."""
from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "QLA_Migration" / "Source"
OUT = ROOT / "QLA_Migration" / "Output"
EVID = Path(__file__).resolve().parent / "evidence"
BASE = EVID / "quikridr_pre_issue143_20260818T130527Z.csv"
CUT = "20260630"

ABSENT_SRC = [
    "901222DC",
    "9014100C",
    "9018166C",
    "9018167C",
    "9018236C",
    "9018237C",
    "9018258C",
    "9018284C",
    "9018330C",
    "9018465C",
    "9018495C",
    "9018645C",
    "9018845C",
    "901ML4140C",
    "901ML8378C",
]


def load(path):
    by = {}
    with path.open(newline="", encoding="latin1", errors="replace") as fh:
        for row in csv.DictReader(fh):
            by[(str(row.get("MPOLICY") or "").strip(), str(row.get("MPHASE") or "").strip())] = row
    return by


def main():
    post = load(OUT / "quikridr.csv")
    pre = load(BASE)
    # What is the raw PPOLC POLICY_NUMBER?
    ppolc = {}
    with (SRC / f"PPOLC_PolicyMaster_Extract_{CUT}.csv").open(newline="", encoding="latin1", errors="replace") as fh:
        for row in csv.DictReader(fh):
            keys = {str(k).strip().upper(): k for k in row if k}
            pol = str(row.get(keys.get("POLICY_NUMBER"), "")).strip()
            put = str(row.get(keys.get("PAID_UP_TYPE"), "")).strip().upper()
            if put == "RU":
                ppolc[pol] = put

    report = []
    all_unchanged = True
    for src in ABSENT_SRC:
        # Issue #2: if source already ends with C but is not width 11, converter appends another C
        expected_emit = src + "C" if src.endswith("C") and len(src) != 11 else (src if src.endswith("C") else src + "C")
        post_row = post.get((expected_emit, "1")) or post.get((src, "1"))
        # collect all phase-1 rows whose MPOLICY startswith stem
        stem = src[:-1] if src.endswith("C") else src
        phase1 = []
        for (pol, ph), row in post.items():
            if ph == "1" and (pol == expected_emit or pol.startswith(stem)):
                pre_row = pre.get((pol, ph), {})
                munit_same = (row.get("MUNIT") == pre_row.get("MUNIT"))
                if not munit_same:
                    all_unchanged = False
                phase1.append(
                    {
                        "mpolicy": pol,
                        "munit": row.get("MUNIT"),
                        "baseline_munit": pre_row.get("MUNIT"),
                        "munit_unchanged": munit_same,
                    }
                )
        report.append(
            {
                "source_policy": src,
                "in_ppolc_ru": src in ppolc,
                "issue2_expected_mpolicy": expected_emit,
                "exact_constructed_in_output": (src, "1") in post,
                "issue2_key_in_output": (expected_emit, "1") in post,
                "issue2_key_in_baseline": (expected_emit, "1") in pre,
                "phase1_hits": phase1,
            }
        )
    out = {
        "all_related_output_munit_unchanged_vs_baseline": all_unchanged,
        "rows": report,
    }
    path = EVID / "issue143_ba_absent_join.json"
    path.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(json.dumps({
        "all_related_output_munit_unchanged_vs_baseline": all_unchanged,
        "sample": [
            {
                "source": r["source_policy"],
                "issue2": r["issue2_expected_mpolicy"],
                "constructed_in_output": r["exact_constructed_in_output"],
                "issue2_in_output": r["issue2_key_in_output"],
                "issue2_in_baseline": r["issue2_key_in_baseline"],
            }
            for r in report
        ],
    }, indent=2))
    print("wrote", path)


if __name__ == "__main__":
    main()
