"""
Issue #50 — Risk review simulation (read-only).

Simulates fixed-width PNOTE parse (header-derived widths) vs current
pandas on_bad_lines='skip', then compares quikmemo MEMOTEXT impact.

No production code changes.
  python Issue_Log_Items/Issue_50/scripts/risk_review_issue50_pnote_parse.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from qla_core.normalize_utils import format_qladmin_mpolicy  # noqa: E402
from qla_core.quikmemo_converter import (  # noqa: E402
    QUIKMEMO_SCHEMA,
    _format_pnote_memotext,
    _is_blank_text,
    _merge_segments_by_memokey,
    _pnote_sort_key,
    _read_csv,
    _text_blob,
    convert_quikmemo_from_pnote_pense,
    PNOTE_LINE_COLS,
)

SRC = ROOT / "QLA_Migration" / "Source"
OUT = ROOT / "QLA_Migration" / "Output"
MAP = ROOT / "QLA_Migration" / "Mapping" / "Master_Crosswalk.csv"
EVID = Path(__file__).resolve().parents[1] / "evidence"

PNOTE = SRC / "PNOTE_PolicyNotes_Extract_20260630.csv"
PENSE = SRC / "PENSE_ENSData_Extract_20260630.csv"
EXAMPLE = "018495BC"
CONTROL = "010335038C"
SAL_PLANS = {"1SALML", "1SALMI", "1SALOL", "9SLADB"}


def load_cw() -> dict[str, str]:
    cw = pd.read_csv(MAP, dtype=str).fillna("")
    return dict(
        zip(
            cw["Old_Value"].astype(str).str.strip(),
            cw["New_Value"].astype(str).str.strip(),
        )
    )


def header_widths(header_line: str) -> list[tuple[str, int]]:
    """Derive fixed field widths from padded header names + inter-field commas."""
    # Header is: name1,name2,... where each name may be space-padded to field width
    cols: list[tuple[str, int]] = []
    i = 0
    while i < len(header_line):
        if header_line[i] == ",":
            i += 1
            continue
        # read until comma or end
        j = i
        while j < len(header_line) and header_line[j] != ",":
            j += 1
        name = header_line[i:j]
        cols.append((name.strip(), len(name)))
        i = j
    return cols


def read_pnote_fixed_width(path: Path) -> pd.DataFrame:
    with open(path, "r", encoding="latin1", newline="") as f:
        header_line = f.readline().rstrip("\r\n")
        widths = header_widths(header_line)
        rows: list[dict[str, str]] = []
        for line in f:
            raw = line.rstrip("\r\n")
            if not raw or raw.lstrip().startswith("---"):
                continue
            # Parse: field + optional trailing comma for all but last
            pos = 0
            rec: dict[str, str] = {}
            ok = True
            for idx, (name, width) in enumerate(widths):
                if pos + width > len(raw):
                    # pad short lines
                    chunk = raw[pos:].ljust(width)
                else:
                    chunk = raw[pos : pos + width]
                rec[name] = chunk
                pos += width
                if idx < len(widths) - 1:
                    if pos < len(raw) and raw[pos] == ",":
                        pos += 1
                    else:
                        # tolerate missing comma on short/malformed
                        ok = False
                        break
            if not ok and len(raw) < sum(w for _, w in widths) + (len(widths) - 1) - 5:
                continue
            rows.append({k: (v or "").strip() for k, v in rec.items()})
    return pd.DataFrame(rows)


def convert_from_pnote_df(
    pnote: pd.DataFrame,
    pense_path: str,
    cw_map: dict[str, str],
) -> tuple[pd.DataFrame, dict]:
    """Subset of convert_quikmemo_from_pnote_pense using a preloaded PNOTE frame."""
    # Reuse full converter for PENSE + merge by writing temp is heavy;
    # call official convert after monkeypatching read — instead inline PNOTE emit
    # then merge with official PENSE path via convert on pense-only + manual merge.
    from qla_core.quikmemo_converter import _exact_dup_key, _format_pense_memotext, _pense_sort_key

    stats = {
        "pnote_source_rows": len(pnote),
        "skipped_blank_pnote": 0,
        "emitted_pnote": 0,
        "skipped_orphan": 0,
    }
    memo_records: list[dict] = []
    seen: set[str] = set()

    for _, row in pnote.iterrows():
        text = _text_blob(row, PNOTE_LINE_COLS)
        if _is_blank_text(text):
            stats["skipped_blank_pnote"] += 1
            continue
        lp = str(row.get("POLICY_NUMBER", "")).strip()
        if not lp:
            stats["skipped_blank_pnote"] += 1
            continue
        qla = cw_map.get(lp, "")
        if not qla:
            stats["skipped_orphan"] += 1
            continue
        memotext = _format_pnote_memotext(row)
        dup = _exact_dup_key("PNOTE", lp, row, memotext, "PNOTE")
        if dup in seen:
            continue
        seen.add(dup)
        sk = _pnote_sort_key(row)
        memo_records.append(
            {
                "MEMOKEY": format_qladmin_mpolicy(qla),
                "MEMOTEXT": memotext,
                "_sort_a": sk[0],
                "_sort_b": sk[1],
                "_sort_c": sk[2],
                "_src_order": 0,
                "_source": "PNOTE",
            }
        )
        stats["emitted_pnote"] += 1

    # PENSE via official reader
    pense_df, _, pense_stats = convert_quikmemo_from_pnote_pense(None, pense_path, cw_map)
    # Official with pnote=None still processes pense into merged output — but we need
    # segments before merge. Simpler: run official full convert with current reader
    # for pense-only keys, and separately build pnote segments then combine.

    # Reload pense segments by calling convert with empty pnote file trick:
    # Use official convert_quikmemo on pense only (pnote_path=None) — returns merged
    # ENS-only. Then we need raw segments... Easiest path: full official after
    # temporary fixed-width file.

    return pd.DataFrame(), stats  # placeholder — replaced below


def emit_segments_from_pnote(pnote: pd.DataFrame, cw_map: dict[str, str]) -> tuple[list[dict], dict]:
    from qla_core.quikmemo_converter import _exact_dup_key

    stats = {
        "pnote_source_rows": len(pnote),
        "skipped_blank_pnote": 0,
        "emitted_pnote": 0,
        "skipped_orphan": 0,
        "skipped_exact_dup": 0,
    }
    records: list[dict] = []
    seen: set[str] = set()
    for _, row in pnote.iterrows():
        text = _text_blob(row, PNOTE_LINE_COLS)
        if _is_blank_text(text):
            stats["skipped_blank_pnote"] += 1
            continue
        lp = str(row.get("POLICY_NUMBER", "")).strip()
        if not lp:
            stats["skipped_blank_pnote"] += 1
            continue
        qla = cw_map.get(lp, "")
        if not qla:
            stats["skipped_orphan"] += 1
            continue
        memotext = _format_pnote_memotext(row)
        dup = _exact_dup_key("PNOTE", lp, row, memotext, "PNOTE")
        if dup in seen:
            stats["skipped_exact_dup"] += 1
            continue
        seen.add(dup)
        sk = _pnote_sort_key(row)
        records.append(
            {
                "MEMOKEY": format_qladmin_mpolicy(qla),
                "MEMOTEXT": memotext,
                "_sort_a": sk[0],
                "_sort_b": sk[1],
                "_sort_c": sk[2],
                "_src_order": 0,
                "_source": "PNOTE",
            }
        )
        stats["emitted_pnote"] += 1
    return records, stats


def emit_segments_from_pense(pense_path: str, cw_map: dict[str, str]) -> tuple[list[dict], dict]:
    from qla_core.quikmemo_converter import (
        _exact_dup_key,
        _format_pense_memotext,
        _pense_sort_key,
        PENSE_LINE_COLS,
    )

    pense = _read_csv(pense_path)
    stats = {
        "pense_source_rows": len(pense),
        "skipped_non_p_ens": 0,
        "skipped_blank_pense": 0,
        "emitted_pense": 0,
        "skipped_orphan": 0,
        "skipped_exact_dup": 0,
    }
    records: list[dict] = []
    seen: set[str] = set()
    for _, row in pense.iterrows():
        ens_type = str(row.get("ENS_KEY_TYPE", "")).strip().upper()
        if ens_type != "P":
            stats["skipped_non_p_ens"] += 1
            continue
        text = _text_blob(row, PENSE_LINE_COLS)
        if _is_blank_text(text):
            stats["skipped_blank_pense"] += 1
            continue
        lp = str(row.get("POLICY_NUMBER", "")).strip()
        if not lp:
            stats["skipped_blank_pense"] += 1
            continue
        qla = cw_map.get(lp, "")
        if not qla:
            stats["skipped_orphan"] += 1
            continue
        memotext = _format_pense_memotext(row)
        dup = _exact_dup_key("PENSE", lp, row, memotext, "PENSE")
        if dup in seen:
            stats["skipped_exact_dup"] += 1
            continue
        seen.add(dup)
        sk = _pense_sort_key(row)
        records.append(
            {
                "MEMOKEY": format_qladmin_mpolicy(qla),
                "MEMOTEXT": memotext,
                "_sort_a": sk[0],
                "_sort_b": sk[1] if len(sk) > 1 else 0,
                "_sort_c": 0,
                "_src_order": 1,
                "_source": "PENSE",
            }
        )
        stats["emitted_pense"] += 1
    return records, stats


def merge_records(records: list[dict]) -> pd.DataFrame:
    if not records:
        return pd.DataFrame(columns=QUIKMEMO_SCHEMA)
    memo_df = pd.DataFrame(records)
    memo_df = memo_df.sort_values(
        ["MEMOKEY", "_sort_a", "_sort_b", "_sort_c", "_src_order"],
        ascending=[True, False, False, False, True],
    )
    return _merge_segments_by_memokey(memo_df)


def strip_conversion(text: str) -> str:
    """Remove leading [CONVERSION] segment for fair PNOTE/ENS compare."""
    if not text.startswith("[CONVERSION]"):
        return text
    parts = text.split("\n---\n", 1)
    if len(parts) == 2:
        return parts[1]
    return ""


def main() -> int:
    EVID.mkdir(parents=True, exist_ok=True)
    cw_map = load_cw()

    with open(PNOTE, "r", encoding="latin1", newline="") as f:
        header_line = f.readline().rstrip("\r\n")
    widths = header_widths(header_line)
    expected_len = sum(w for _, w in widths) + (len(widths) - 1)

    pnote_fw = read_pnote_fixed_width(PNOTE)
    pnote_pd = _read_csv(str(PNOTE))

    # Validate Bauerly LINE_1 under fixed-width
    ex_lp = "9018495B"
    fw_ex = pnote_fw[pnote_fw["POLICY_NUMBER"].astype(str).str.strip() == ex_lp]
    pd_ex = pnote_pd[pnote_pd["POLICY_NUMBER"].astype(str).str.strip() == ex_lp]

    # Build before (pandas PNOTE) and after (fixed-width PNOTE) merged memos
    before_recs, before_pstats = emit_segments_from_pnote(pnote_pd, cw_map)
    after_recs, after_pstats = emit_segments_from_pnote(pnote_fw, cw_map)
    pense_recs, pense_stats = emit_segments_from_pense(str(PENSE), cw_map)

    before_df = merge_records(before_recs + pense_recs)
    after_df = merge_records(after_recs + pense_recs)

    before_map = {
        str(r["MEMOKEY"]).strip(): str(r["MEMOTEXT"])
        for _, r in before_df.iterrows()
    }
    after_map = {
        str(r["MEMOKEY"]).strip(): str(r["MEMOTEXT"])
        for _, r in after_df.iterrows()
    }

    all_keys = set(before_map) | set(after_map)
    changed = []
    new_keys = []
    removed_keys = []
    unchanged = 0
    for k in sorted(all_keys):
        b = before_map.get(k, "")
        a = after_map.get(k, "")
        if b == a:
            unchanged += 1
        elif not b and a:
            new_keys.append(k)
            changed.append({"QLA": k, "CLASS": "NEW_MEMOKEY", "BEFORE_LEN": 0, "AFTER_LEN": len(a), "DELTA_LEN": len(a)})
        elif b and not a:
            removed_keys.append(k)
            changed.append({"QLA": k, "CLASS": "REMOVED", "BEFORE_LEN": len(b), "AFTER_LEN": 0, "DELTA_LEN": -len(b)})
        else:
            changed.append(
                {
                    "QLA": k,
                    "CLASS": "MEMOTEXT_CHANGED",
                    "BEFORE_LEN": len(b),
                    "AFTER_LEN": len(a),
                    "DELTA_LEN": len(a) - len(b),
                    "GAINED_BAUERLY_PATTERN": str("Bauerly" in a and "Bauerly" not in b),
                    "BEFORE_HAS_PNOTE": str("[PNOTE]" in b),
                    "AFTER_HAS_PNOTE": str("[PNOTE]" in a),
                }
            )

    qridr = pd.read_csv(OUT / "quikridr.csv", dtype=str).fillna("")
    sal = set(
        qridr.loc[qridr["MPLAN"].isin(SAL_PLANS), "MPOLICY"].astype(str).str.strip().unique()
    )
    changed_keys = {c["QLA"] for c in changed}
    sal_changed = sorted(sal & changed_keys)

    # Current output (with CONVERSION) vs after PNOTE/ENS body
    qm = pd.read_csv(OUT / "quikmemo.csv", dtype=str).fillna("")
    cur_body = {
        str(r["MEMOKEY"]).strip(): strip_conversion(str(r["MEMOTEXT"]))
        for _, r in qm.iterrows()
    }

    # Control stability: before pandas path vs after FW for control key
    control_before = before_map.get(CONTROL, "")
    control_after = after_map.get(CONTROL, "")
    example_before = before_map.get(EXAMPLE, "")
    example_after = after_map.get(EXAMPLE, "")

    # Fixed-width row length audit
    len_ok = len_short = len_long = 0
    with open(PNOTE, "r", encoding="latin1", newline="") as f:
        f.readline()
        for line in f:
            raw = line.rstrip("\r\n")
            if not raw or "---" in raw[:20]:
                continue
            if len(raw) == expected_len:
                len_ok += 1
            elif len(raw) < expected_len:
                len_short += 1
            else:
                len_long += 1

    # FW Bauerly LINE_1
    fw_line1 = ""
    if len(fw_ex):
        seq1 = fw_ex[fw_ex["RECORD_SEQ"].astype(str).str.strip() == "1"]
        if len(seq1):
            fw_line1 = str(seq1.iloc[0].get("LINE_1", ""))

    summary = {
        "header_expected_line_len": expected_len,
        "pnote_fw_rows": len(pnote_fw),
        "pnote_pandas_rows": len(pnote_pd),
        "pnote_rows_recovered": len(pnote_fw) - len(pnote_pd),
        "line_len_exact": len_ok,
        "line_len_short": len_short,
        "line_len_long": len_long,
        "before_emitted_pnote_segments": before_pstats["emitted_pnote"],
        "after_emitted_pnote_segments": after_pstats["emitted_pnote"],
        "pense_emitted_segments": pense_stats["emitted_pense"],
        "before_memokeys": len(before_map),
        "after_memokeys": len(after_map),
        "memokeys_unchanged": unchanged,
        "memokeys_changed": len(changed),
        "memokeys_new": len(new_keys),
        "memokeys_removed": len(removed_keys),
        "sal_memokeys_changed": len(sal_changed),
        "control_010335038C_stable": control_before == control_after,
        "example_gained_bauerly": ("Bauerly" in example_after) and ("Bauerly" not in example_before),
        "example_keeps_last_known": "Last Known" in example_after,
        "fw_bauerly_line1_prefix": fw_line1[:80],
        "before_total_memotext_chars": sum(len(v) for v in before_map.values()),
        "after_total_memotext_chars": sum(len(v) for v in after_map.values()),
        "delta_total_memotext_chars": sum(len(v) for v in after_map.values())
        - sum(len(v) for v in before_map.values()),
        "current_output_rows": len(qm),
        "current_body_matches_before_sim": sum(
            1 for k, b in before_map.items() if cur_body.get(k, "") == b
        ),
    }

    pd.DataFrame([summary]).to_csv(EVID / "issue50_risk_simulation_summary.csv", index=False)
    pd.DataFrame(changed).sort_values("DELTA_LEN", ascending=False).to_csv(
        EVID / "issue50_risk_memotext_changes.csv", index=False
    )
    pd.DataFrame({"QLA": sal_changed}).to_csv(EVID / "issue50_risk_sal_changed_keys.csv", index=False)

    traces = [
        {
            "QLA": EXAMPLE,
            "ROLE": "client_example",
            "BEFORE_HAS_BAUERLY": "Bauerly" in example_before,
            "AFTER_HAS_BAUERLY": "Bauerly" in example_after,
            "BEFORE_HAS_LAST_KNOWN": "Last Known" in example_before,
            "AFTER_HAS_LAST_KNOWN": "Last Known" in example_after,
            "BEFORE_LEN": len(example_before),
            "AFTER_LEN": len(example_after),
            "AFTER_PREVIEW": example_after[:240].replace("\n", " | "),
        },
        {
            "QLA": CONTROL,
            "ROLE": "21m_control",
            "STABLE": control_before == control_after,
            "BEFORE_LEN": len(control_before),
            "AFTER_LEN": len(control_after),
        },
    ]
    # add one SAL only-malformed if present
    only_mal = pd.read_csv(EVID / "issue50_sal_malformed_impact.csv", dtype=str)
    only = only_mal[only_mal["LOSS_CLASS"] == "ONLY_MALFORMED"]
    if len(only):
        k = str(only.iloc[0]["QLA"]).strip()
        traces.append(
            {
                "QLA": k,
                "ROLE": "sal_only_malformed",
                "BEFORE_HAS_PNOTE": "[PNOTE]" in before_map.get(k, ""),
                "AFTER_HAS_PNOTE": "[PNOTE]" in after_map.get(k, ""),
                "BEFORE_LEN": len(before_map.get(k, "")),
                "AFTER_LEN": len(after_map.get(k, "")),
            }
        )
    pd.DataFrame(traces).to_csv(EVID / "issue50_risk_traces.csv", index=False)

    print("Issue #50 Risk simulation")
    for k, v in summary.items():
        print(f"  {k}: {v}")
    print(f"  widths: {[(n, w) for n, w in widths]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
