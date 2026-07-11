"""
Issue #50 — validate PNOTE fixed-width parse restores dropped policy notes.

Checks converter output from Source extracts and optional batch quikmemo.csv.

Usage:
  python tools/validators/validate_issue50_pnote_parse.py
  python tools/validators/validate_issue50_pnote_parse.py --output-dir QLA_Migration/Output
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

SCRIPT_VERSION = "1.1"
ENGINE_VERSION = "v57.75"
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SRC = PROJECT_ROOT / "QLA_Migration" / "Source"
DEFAULT_OUT = PROJECT_ROOT / "QLA_Migration" / "Output"
CW = PROJECT_ROOT / "QLA_Migration" / "Mapping" / "Master_Crosswalk.csv"

EXAMPLE_QLA = "018495BC"
CONTROL_QLA = "010335038C"
CONVERSION_TAG = "[CONVERSION]"
MEMO_SEPARATOR = "\n---\n"

# Risk simulation baselines (PNOTE+PENSE merge before #21J prepend)
EXPECTED_PNOTE_SOURCE_ROWS = 7976
EXPECTED_PNOTE_EMITTED_MIN = 7940
EXPECTED_MEMOKEYS_MIN = 4520
EXPECTED_EXAMPLE_BAUERLY = "Bauerly"
EXPECTED_EXAMPLE_LAST_KNOWN = "Last Known"


def _load_cw() -> dict[str, str]:
    cw = pd.read_csv(CW, dtype=str).fillna("")
    return dict(
        zip(
            cw["Old_Value"].astype(str).str.strip(),
            cw["New_Value"].astype(str).str.strip(),
        )
    )


def _strip_conversion(text: str) -> str:
    if not text.startswith(CONVERSION_TAG):
        return text
    parts = text.split(MEMO_SEPARATOR, 1)
    return parts[1] if len(parts) == 2 else ""


def validate(src_dir: Path, output_dir: Path | None) -> int:
    sys.path.insert(0, str(PROJECT_ROOT))
    from qla_core.quikmemo_converter import convert_quikmemo_from_pnote_pense

    print("=" * 72)
    print(f"ISSUE #50 PNOTE PARSE VALIDATION (script v{SCRIPT_VERSION}, engine {ENGINE_VERSION})")
    print("=" * 72)

    errors: list[str] = []
    warnings: list[str] = []

    pnote = src_dir / "PNOTE_PolicyNotes_Extract_20260630.csv"
    pense = src_dir / "PENSE_ENSData_Extract_20260630.csv"
    if not pnote.exists():
        errors.append(f"Missing PNOTE source: {pnote}")
    if not pense.exists():
        errors.append(f"Missing PENSE source: {pense}")
    if errors:
        for e in errors:
            print(f"FAIL: {e}")
        return 1

    cw_map = _load_cw()
    out_df, orphan_df, stats = convert_quikmemo_from_pnote_pense(
        str(pnote), str(pense), cw_map
    )

    print(f"PNOTE source rows read: {stats.get('pnote_source_rows')}")
    print(f"PNOTE segments emitted: {stats.get('emitted_pnote')}")
    print(f"PENSE segments emitted: {stats.get('emitted_pense')}")
    print(f"Merged MEMOKEY rows: {stats.get('emitted_rows')}")
    print(f"Orphan rows: {len(orphan_df)}")

    if stats.get("pnote_source_rows", 0) < EXPECTED_PNOTE_SOURCE_ROWS:
        errors.append(
            f"PNOTE source rows {stats.get('pnote_source_rows')} < expected {EXPECTED_PNOTE_SOURCE_ROWS}"
        )
    if stats.get("emitted_pnote", 0) < EXPECTED_PNOTE_EMITTED_MIN:
        errors.append(
            f"PNOTE emitted {stats.get('emitted_pnote')} < expected min {EXPECTED_PNOTE_EMITTED_MIN}"
        )
    if stats.get("emitted_rows", 0) < EXPECTED_MEMOKEYS_MIN:
        errors.append(
            f"Merged rows {stats.get('emitted_rows')} < expected min {EXPECTED_MEMOKEYS_MIN}"
        )

    memo_map = {
        str(r["MEMOKEY"]).strip(): str(r["MEMOTEXT"])
        for _, r in out_df.iterrows()
    }

    ex_text = memo_map.get(EXAMPLE_QLA, "")
    if EXPECTED_EXAMPLE_BAUERLY not in ex_text:
        errors.append(f"{EXAMPLE_QLA} missing '{EXPECTED_EXAMPLE_BAUERLY}' in MEMOTEXT")
    if EXPECTED_EXAMPLE_LAST_KNOWN not in ex_text:
        errors.append(f"{EXAMPLE_QLA} missing '{EXPECTED_EXAMPLE_LAST_KNOWN}' in MEMOTEXT")
    if "[PNOTE]" not in ex_text:
        errors.append(f"{EXAMPLE_QLA} missing [PNOTE] segment")

    ctrl_text = memo_map.get(CONTROL_QLA, "")
    if not ctrl_text or "[PNOTE]" not in ctrl_text:
        errors.append(f"{CONTROL_QLA} missing [PNOTE] (control policy)")

    bad_width = [str(k) for k in out_df["MEMOKEY"].tolist() if len(str(k)) != 10]
    if bad_width:
        errors.append(f"MEMOKEY width != 10 for {len(bad_width)} keys (Issue #25)")

    # Optional: compare batch output body if present
    batch_path = (output_dir or DEFAULT_OUT) / "quikmemo.csv"
    if batch_path.exists():
        qm = pd.read_csv(batch_path, dtype=str).fillna("")
        batch_ex = qm[qm["MEMOKEY"].str.strip() == EXAMPLE_QLA]
        if len(batch_ex):
            batch_text = str(batch_ex["MEMOTEXT"].iloc[0])
            if EXPECTED_EXAMPLE_BAUERLY not in batch_text:
                warnings.append(
                    f"Batch quikmemo.csv for {EXAMPLE_QLA} still missing Bauerly — re-run batch"
                )
            else:
                print(f"Batch quikmemo.csv: {EXAMPLE_QLA} contains Bauerly")
        else:
            warnings.append(f"Batch quikmemo.csv missing {EXAMPLE_QLA}")
    else:
        warnings.append(f"No batch quikmemo.csv at {batch_path} (converter-only validation)")

    # Issue #50 UAT: DBF MEMOKEY must be left-padded like quikmstr (not right-padded by dbf lib)
    dbf_path = (output_dir or DEFAULT_OUT) / "quikmemo_uat_dbf" / "quikmemo.dbf"
    if dbf_path.exists():
        import struct

        data = dbf_path.read_bytes()
        header_len = struct.unpack_from("<H", data, 8)[0]
        rec_len = struct.unpack_from("<H", data, 10)[0]
        num_recs = struct.unpack_from("<I", data, 4)[0]
        found_key = None
        for i in range(num_recs):
            off = header_len + i * rec_len
            mk = data[off + 1 : off + 11]
            if b"018495BC" in mk:
                found_key = mk
                break
        if found_key is None:
            errors.append(f"DBF missing MEMOKEY for {EXAMPLE_QLA}")
        elif found_key != b"  018495BC":
            errors.append(
                f"DBF MEMOKEY padding wrong for {EXAMPLE_QLA}: {found_key!r} "
                f"(expected b'  018495BC') — Memo tab SEEK will miss"
            )
        else:
            print(f"DBF MEMOKEY left-pad OK: {found_key!r}")
    else:
        warnings.append(f"No UAT DBF at {dbf_path}")

    print("-" * 72)
    print("TRACE SAMPLES")
    print(f"  {EXAMPLE_QLA} preview: {ex_text[:200].replace(chr(10), ' | ')}")
    print(f"  {CONTROL_QLA} len: {len(ctrl_text)}")

    if warnings:
        print("-" * 72)
        print("WARNINGS")
        for w in warnings:
            print(f"  WARN: {w}")

    print("=" * 72)
    if errors:
        print("RESULT: FAIL")
        for e in errors:
            print(f"  FAIL: {e}")
        return 1

    print("RESULT: PASS")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Issue #50 PNOTE parse validation")
    parser.add_argument("--src-dir", type=Path, default=DEFAULT_SRC)
    parser.add_argument("--output-dir", type=Path, default=None)
    args = parser.parse_args()
    return validate(args.src_dir, args.output_dir)


if __name__ == "__main__":
    raise SystemExit(main())
