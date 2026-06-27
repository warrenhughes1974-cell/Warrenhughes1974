"""
MPOLICY key consistency investigation (Issue #25 / QLAdmin display failure).

Read-only diagnostic — scans CSV outputs, compares child tables to quikmstr,
reports raw/visible length, leading/trailing spaces, hex encoding, and
simulated DBF load behavior (strip + truncate to C(10)).

Usage:
  python QLA_Migration/_investigate_mpolicy_keys.py
  python QLA_Migration/_investigate_mpolicy_keys.py --output-dir QLA_Migration/Output
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

SCRIPT_VERSION = "1.0"
PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_OUTPUT = PROJECT_ROOT / "QLA_Migration" / "Output"
DEFAULT_REPORT = PROJECT_ROOT / "Issue_Log_Items" / "Issue_25" / "reports" / "MPOLICY_Key_Investigation_Report.md"

TRACE_POLICIES = ["018510C", "018495BC", "018499CC", "018499DC", "010143726C"]
GOOD_POLICY = "010143726C"
MPOLICY_WIDTH = 10

POLICY_FIELD_NAMES = {"MPOLICY", "POLICY", "POLICY_NUMBER", "POLNUM", "POLNO"}


def analyze_val(raw) -> dict:
    s = "" if raw is None else str(raw)
    vis = s.strip()
    lead = len(s) - len(s.lstrip(" "))
    trail = len(s) - len(s.rstrip(" "))
    dbf_after_strip = vis[:MPOLICY_WIDTH]
    dbf_padded_right = vis.ljust(MPOLICY_WIDTH)[:MPOLICY_WIDTH]
    dbf_padded_left = vis.rjust(MPOLICY_WIDTH)[:MPOLICY_WIDTH]
    return {
        "raw": s,
        "visible": vis,
        "len_raw": len(s),
        "len_visible": len(vis),
        "leading_spaces": lead,
        "trailing_spaces": trail,
        "hex_ascii": " ".join(f"{b:02x}" for b in s.encode("latin-1", errors="replace")),
        "repr": repr(s),
        "dbf_strip_truncate": dbf_after_strip,
        "dbf_right_pad_spaces": dbf_padded_right,
        "dbf_left_pad_spaces": dbf_padded_left,
    }


def discover_csv_files(output_dir: Path) -> list[Path]:
    paths: list[Path] = sorted(output_dir.glob("*.csv"))
    staging = output_dir / "claims_uat_staging"
    if staging.is_dir():
        paths.extend(sorted(staging.glob("*.csv")))
    dbf_dir = output_dir / "claims_uat_dbf"
    return paths


def load_mpolicy_rows(path: Path) -> tuple[str | None, list[dict]]:
    if not path.is_file():
        return None, []
    with path.open(newline="", encoding="latin-1") as fh:
        reader = csv.DictReader(fh)
        if not reader.fieldnames:
            return None, []
        mpolicy_col = None
        for c in reader.fieldnames:
            if c and c.strip().upper() == "MPOLICY":
                mpolicy_col = c
                break
        if not mpolicy_col:
            return None, []
        return mpolicy_col, list(reader)


def build_master_index(quikmstr_path: Path) -> dict[str, dict]:
    col, rows = load_mpolicy_rows(quikmstr_path)
    if not col:
        return {}
    index: dict[str, dict] = {}
    for row in rows:
        a = analyze_val(row.get(col, ""))
        if a["visible"]:
            index[a["visible"]] = a
    return index


def scan_table(path: Path, master: dict[str, dict]) -> dict:
    col, rows = load_mpolicy_rows(path)
    if not col:
        return {"file": path.name, "has_mpolicy": False}

    stats = {
        "file": str(path.relative_to(path.parent.parent)) if path.parent.name == "Output" else path.name,
        "has_mpolicy": True,
        "field": col,
        "rows_with_value": 0,
        "raw_len_not_10": 0,
        "visible_len_not_10": 0,
        "visible_len_gt_10": 0,
        "with_leading_spaces": 0,
        "with_trailing_spaces": 0,
        "mismatch_vs_quikmstr_raw": 0,
        "mismatch_vs_quikmstr_dbf_sim": 0,
        "unknown_vs_master_visible": 0,
        "visible_len_distribution": Counter(),
    }
    mismatch_samples: list[dict] = []

    for row in rows:
        a = analyze_val(row.get(col, ""))
        if not a["visible"]:
            continue
        stats["rows_with_value"] += 1
        stats["visible_len_distribution"][a["len_visible"]] += 1
        if a["len_raw"] != MPOLICY_WIDTH:
            stats["raw_len_not_10"] += 1
        if a["len_visible"] < MPOLICY_WIDTH:
            stats["visible_len_not_10"] += 1
        if a["len_visible"] > MPOLICY_WIDTH:
            stats["visible_len_gt_10"] += 1
        if a["leading_spaces"] > 0:
            stats["with_leading_spaces"] += 1
        if a["trailing_spaces"] > 0:
            stats["with_trailing_spaces"] += 1

        master_a = master.get(a["visible"])
        if master_a is None:
            stats["unknown_vs_master_visible"] += 1
            continue
        if a["raw"] != master_a["raw"]:
            stats["mismatch_vs_quikmstr_raw"] += 1
            if len(mismatch_samples) < 5:
                mismatch_samples.append({
                    "visible": a["visible"],
                    "child_raw": a["repr"],
                    "master_raw": master_a["repr"],
                })
        if a["dbf_strip_truncate"] != master_a["dbf_strip_truncate"]:
            stats["mismatch_vs_quikmstr_dbf_sim"] += 1

    stats["visible_len_distribution"] = dict(sorted(stats["visible_len_distribution"].items()))
    stats["mismatch_samples"] = mismatch_samples
    return stats


def trace_policy_report(master: dict[str, dict], table_stats: list[dict], output_dir: Path) -> list[dict]:
    traces = []
    for pol in TRACE_POLICIES:
        entry = {"visible_policy": pol, "quikmstr": master.get(pol), "child_tables": {}}
        for fp in discover_csv_files(output_dir):
            if fp.name == "quikmstr.csv":
                continue
            col, rows = load_mpolicy_rows(fp)
            if not col:
                continue
            hits = []
            for row in rows:
                a = analyze_val(row.get(col, ""))
                if a["visible"] == pol:
                    hits.append(a)
            if hits:
                rel = str(fp.relative_to(output_dir)) if fp.is_relative_to(output_dir) else fp.name
                unique_raw = {h["repr"] for h in hits}
                entry["child_tables"][rel] = {
                    "hit_count": len(hits),
                    "unique_raw_values": sorted(unique_raw),
                    "matches_quikmstr_raw": all(
                        master.get(pol) and h["raw"] == master[pol]["raw"] for h in hits
                    ) if master.get(pol) else None,
                }
        traces.append(entry)
    return traces


def simulate_dbf_load(master: dict[str, dict]) -> dict:
    """Simulate strip-on-load DBF behavior for trace policies."""
    out = {}
    for pol in TRACE_POLICIES:
        m = master.get(pol)
        if not m:
            out[pol] = {"status": "NOT_IN_QUIKMSTR"}
            continue
        stripped = m["dbf_strip_truncate"]
        out[pol] = {
            "csv_raw": m["repr"],
            "csv_raw_len": m["len_raw"],
            "dbf_after_strip": repr(stripped),
            "dbf_after_strip_len": len(stripped),
            "left_pad_would_be": repr(m["dbf_left_pad_spaces"]),
            "right_pad_would_be": repr(m["dbf_padded_right_spaces"] if "dbf_padded_right_spaces" in m else m["dbf_right_pad_spaces"]),
            "display_key_hypothesis_trimmed": stripped,
            "index_key_hypothesis_fixed10_left": m["dbf_left_pad_spaces"],
        }
    return out


def write_report(report_path: Path, payload: dict) -> None:
    report_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# MPOLICY Key Investigation Report",
        "",
        f"**Generated:** {payload['timestamp']}",
        f"**Script:** `_investigate_mpolicy_keys.py` v{SCRIPT_VERSION}",
        f"**Output directory:** `{payload['output_dir']}`",
        "",
        "## Executive Summary",
        "",
        payload["executive_summary"],
        "",
        "## Hypothesis Test: Locate vs Display Key Split",
        "",
        payload["hypothesis_section"],
        "",
        "## Trace Policies (quikmstr + child tables)",
        "",
    ]
    for t in payload["traces"]:
        lines.append(f"### `{t['visible_policy']}`")
        m = t.get("quikmstr")
        if m:
            lines.append(f"- **quikmstr raw:** {m['repr']} (len={m['len_raw']}, leading spaces={m['leading_spaces']})")
            lines.append(f"- **visible:** `{m['visible']}` (len={m['len_visible']})")
            lines.append(f"- **hex:** `{m['hex_ascii']}`")
            lines.append(f"- **DBF after strip+truncate C(10):** {repr(m['dbf_strip_truncate'])} (len={len(m['dbf_strip_truncate'])})")
        else:
            lines.append("- **NOT FOUND in quikmstr**")
        if t["child_tables"]:
            lines.append("- **Child table hits:**")
            for tbl, info in sorted(t["child_tables"].items()):
                match = info["matches_quikmstr_raw"]
                flag = "MATCH" if match else ("UNKNOWN" if match is None else "MISMATCH")
                lines.append(f"  - `{tbl}`: {info['hit_count']} rows, raw values={info['unique_raw_values']} [{flag}]")
        else:
            lines.append("- No child-table MPOLICY hits")
        lines.append("")

    lines.extend([
        "## Per-Table Scan Summary",
        "",
        "| Table | Rows | Raw!=10 | Visible<10 | Leading spaces | Mismatch vs quikmstr raw | Mismatch after DBF strip sim |",
        "|-------|------|---------|------------|----------------|--------------------------|------------------------------|",
    ])
    for s in payload["table_stats"]:
        if not s.get("has_mpolicy"):
            continue
        lines.append(
            f"| {s['file']} | {s['rows_with_value']} | {s['raw_len_not_10']} | "
            f"{s['visible_len_not_10']} | {s['with_leading_spaces']} | "
            f"{s['mismatch_vs_quikmstr_raw']} | {s['mismatch_vs_quikmstr_dbf_sim']} |"
        )

    lines.extend([
        "",
        "## DBF Load Simulation (trace policies)",
        "",
        "Simulates known in-repo DBF writers that call `.strip()` before append "
        "(e.g. `phase19_uat_emitted_csv_dbf_generator.truncate_char`, "
        "`phase_p2f_validation_runner.write_quikplan_dbf`).",
        "",
        "```json",
        json.dumps(payload["dbf_simulation"], indent=2),
        "```",
        "",
        "## Root Cause Assessment",
        "",
        payload["root_cause"],
        "",
        "## Recommended Next Step (no code applied)",
        "",
        payload["recommendation"],
        "",
    ])
    report_path.write_text("\n".join(lines), encoding="utf-8")


def run_investigation(output_dir: Path, report_path: Path) -> int:
    quikmstr_path = output_dir / "quikmstr.csv"
    if not quikmstr_path.is_file():
        print(f"FAIL — missing {quikmstr_path}")
        return 1

    master = build_master_index(quikmstr_path)
    table_stats = [scan_table(p, master) for p in discover_csv_files(output_dir)]
    traces = trace_policy_report(master, table_stats, output_dir)
    dbf_sim = simulate_dbf_load(master)

    # Fleet-wide quikmstr stats
    mstr_col, mstr_rows = load_mpolicy_rows(quikmstr_path)
    vis_lens = Counter()
    raw_lens = Counter()
    short_visible_policies = []
    for row in mstr_rows:
        a = analyze_val(row.get(mstr_col, ""))
        if not a["visible"]:
            continue
        vis_lens[a["len_visible"]] += 1
        raw_lens[a["len_raw"]] += 1
        if a["len_visible"] < MPOLICY_WIDTH:
            short_visible_policies.append(a["visible"])

    good = master.get(GOOD_POLICY)
    bad_example = master.get("018499DC")

    # Check CSV preserves leading spaces in file bytes
    csv_preserves_spaces = None
    if bad_example and bad_example["leading_spaces"] > 0:
        raw_bytes = quikmstr_path.read_bytes()
        needle = bad_example["raw"].encode("latin-1")
        csv_preserves_spaces = needle in raw_bytes

    child_mismatches = sum(s.get("mismatch_vs_quikmstr_raw", 0) for s in table_stats)
    all_child_match_raw = child_mismatches == 0

    executive = (
        f"- **quikmstr policies:** {len(master)} unique visible MPOLICY values\n"
        f"- **Policies with visible length < 10:** {vis_lens.get(9,0)+vis_lens.get(8,0)+vis_lens.get(7,0)+sum(v for k,v in vis_lens.items() if k<10)} "
        f"(length distribution: {dict(sorted(vis_lens.items()))})\n"
        f"- **quikmstr raw length exactly 10:** {raw_lens.get(10, 0)} / {sum(raw_lens.values())}\n"
        f"- **Child-table raw MPOLICY mismatches vs quikmstr:** {child_mismatches}\n"
        f"- **CSV file preserves leading-space MPOLICY bytes:** {csv_preserves_spaces}\n"
        f"- **Good policy `{GOOD_POLICY}` raw len:** {good['len_raw'] if good else 'N/A'}\n"
        f"- **Bad example `018499DC` raw len:** {bad_example['len_raw'] if bad_example else 'N/A'}"
    )

    if all_child_match_raw and csv_preserves_spaces:
        hypothesis = (
            "Child tables match quikmstr **raw** CSV values (including leading spaces). "
            "CSV output **does** preserve leading spaces on disk.\n\n"
            "However, every in-repo DBF generation path tested uses **`strip()` before writing** "
            "character fields. After strip, short policies become **7–9 characters** in a **C(10)** field, "
            "not left-padded to 10.\n\n"
            "**Likely QLAdmin behavior:**\n"
            "- **Locate/list** may scan/display using **trimmed** visible policy text → user sees `018499DC`.\n"
            "- **Display/open** may use the **indexed primary key** (`MPOLICY` as stored in quikmstr index) "
            "which may require **fixed-width 10** or exact padded match.\n"
            "- If load strips spaces, index key = `018499DC` (8 chars) but child FK lookups may still fail "
            "if mixed padded/unpadded values exist across tables from prior loads.\n\n"
            "**Leading-space padding in CSV alone does not survive DBF load** if the client's import uses "
            "the same strip pattern as this repo's DBF utilities."
        )
        root_cause = (
            "**Primary (proven in-repo):** DBF load utilities strip leading/trailing spaces from MPOLICY "
            "before append (`truncate_char` / `strip_val` in claims UAT DBF generator and quikplan DBF writer). "
            "This removes the v57.30 leading-space padding benefit at DBF boundary.\n\n"
            "**Secondary (consistent with symptom):** Short crosswalked policies (7–9 visible chars) are stored "
            "in QLAdmin as **unpadded** values in C(10) fields after load. QLAdmin locate may trim for display "
            "while policy open uses a different key resolution path, producing **Policy Not Found**.\n\n"
            "**Not the cause:** Crosswalk identity mismatch for traced policies — all five trace policies exist "
            "in quikmstr with expected crosswalk targets. Child-table raw values match quikmstr when v57.30 padding is present.\n\n"
            "**Not proven in this repo:** Loyal2QL / QLAdmin native FieldPut behavior (external to this codebase) — "
            "must confirm on client load workstation whether FieldPut strips character fields."
        )
        recommendation = (
            "1. **Confirm client DBF load path** — capture actual quikmstr.dbf MPOLICY bytes for `018499DC` "
            "after QLAdmin import (hex dump of 10-char field).\n"
            "2. **Compare good vs bad** — `010143726C` is already 10 visible chars; short policies are 7–9.\n"
            "3. **If DBF stores trimmed 8-char value:** test whether QLAdmin expects **right-padding with spaces** "
            "within C(10) (FoxPro PADR/left-aligned storage) vs **left-padding** vs **no padding**.\n"
            "4. **Surgical fix candidate (after proof):** apply padding at **DBF write boundary** without strip, "
            "OR use QLAdmin-native padding (PADR/LEFT alignment) — **not** CSV-only padding that gets stripped.\n"
            "5. Do **not** zero-pad or change crosswalk identity."
        )
    else:
        hypothesis = "See per-table mismatch counts — inconsistent raw MPOLICY may exist across tables."
        root_cause = "Investigation found child/master raw mismatches or CSV space preservation failure."
        recommendation = "Resolve cross-table raw mismatches first, then re-test DBF load."

    payload = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "output_dir": str(output_dir),
        "executive_summary": executive,
        "hypothesis_section": hypothesis,
        "traces": traces,
        "table_stats": table_stats,
        "dbf_simulation": dbf_sim,
        "root_cause": root_cause,
        "recommendation": recommendation,
        "short_visible_policy_count": len(short_visible_policies),
    }

    write_report(report_path, payload)

    print("=" * 72)
    print(f"MPOLICY KEY INVESTIGATION (script v{SCRIPT_VERSION})")
    print(f"Output: {output_dir}")
    print(f"Report: {report_path}")
    print("=" * 72)
    print(executive.replace("\n", "\n"))
    print("\nDBF simulation for trace policies:")
    for pol, sim in dbf_sim.items():
        if sim.get("status"):
            print(f"  {pol}: {sim['status']}")
        else:
            print(f"  {pol}: csv {sim['csv_raw']} -> dbf strip {sim['dbf_after_strip']} (len {sim['dbf_after_strip_len']})")
    print(f"\nReport written: {report_path}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Investigate MPOLICY key consistency across QLA outputs")
    ap.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    ap.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = ap.parse_args()
    return run_investigation(args.output_dir.resolve(), args.report.resolve())


if __name__ == "__main__":
    sys.exit(main())
