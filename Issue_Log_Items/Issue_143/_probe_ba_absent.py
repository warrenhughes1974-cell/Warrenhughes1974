"""Read-only: why 15 BA RPU source policies appear absent from Output."""
from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "QLA_Migration" / "Output"
EVID = Path(__file__).resolve().parent / "evidence"
BASE = EVID / "quikridr_pre_issue143_20260818T130527Z.csv"

ABSENT_SRC = [
    "901222D",
    "9014100",
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


def load_keys(path):
    keys = set()
    rows = {}
    with path.open(newline="", encoding="latin1", errors="replace") as fh:
        for row in csv.DictReader(fh):
            pol = str(row.get("MPOLICY") or "").strip()
            ph = str(row.get("MPHASE") or "").strip()
            keys.add(pol)
            rows[(pol, ph)] = row
    return keys, rows


def main():
    post_keys, post_rows = load_keys(OUT / "quikridr.csv")
    pre_keys, pre_rows = load_keys(BASE)
    findings = []
    for src in ABSENT_SRC:
        hits_post = sorted(k for k in post_keys if src in k or k in src or src.rstrip("C") in k)
        hits_pre = sorted(k for k in pre_keys if src in k or k in src or src.rstrip("C") in k)
        # also search without trailing C
        core = src[:-1] if src.endswith("C") else src
        extra_post = sorted(k for k in post_keys if core in k)
        extra_pre = sorted(k for k in pre_keys if core in k)
        findings.append(
            {
                "source_policy": src,
                "exact_in_output": src in post_keys,
                "exact_in_baseline": src in pre_keys,
                "output_substring_hits": extra_post,
                "baseline_substring_hits": extra_pre,
                "same_hits_pre_post": extra_pre == extra_post,
            }
        )
    outp = EVID / "issue143_ba_absent_probe.json"
    outp.write_text(json.dumps(findings, indent=2), encoding="utf-8")
    for f in findings:
        print(f["source_policy"], "out=", f["output_substring_hits"], "pre=", f["baseline_substring_hits"])
    print("wrote", outp)


if __name__ == "__main__":
    main()
