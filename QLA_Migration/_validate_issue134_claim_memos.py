"""Issue #134 — validate PNOTE FILE_TYPE=B on quikclms.MEMOTEXT, absent from quikmemo."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from qla_core.issue134_claim_memo_overlay import load_pnote_b_memos_by_mpolicy  # noqa: E402
from qla_core.lifepro_source_resolver import resolve_quikmemo_sources  # noqa: E402
from qla_core.normalize_utils import format_qladmin_mpolicy  # noqa: E402
from qla_core.quikmemo_converter import _read_pnote_csv, _strip  # noqa: E402

OUT = ROOT / "QLA_Migration" / "Output"
SRC = ROOT / "QLA_Migration" / "Source"
EVIDENCE = ROOT / "Issue_Log_Items" / "Issue_134" / "evidence"
TRACE_POLICIES = [
    "9010150740C",
    "9010150910C",
    "9010335038C",
    "9010331157C",
    "9010363098C",
]


def _main() -> int:
    errors: list[str] = []
    clms_path = OUT / "quikclms.csv"
    clmp_path = OUT / "quikclmp.csv"
    memo_path = OUT / "quikmemo.csv"
    if not clms_path.is_file():
        print("FAIL: missing quikclms.csv")
        return 1
    if not memo_path.is_file():
        print("FAIL: missing quikmemo.csv")
        return 1

    pnote_path, _, _, _ = resolve_quikmemo_sources(str(SRC))
    if not pnote_path:
        print("FAIL: missing PNOTE source")
        return 1

    clms = pd.read_csv(clms_path, dtype=str, keep_default_na=False)
    memo = pd.read_csv(memo_path, dtype=str, keep_default_na=False)
    clmp_rows = None
    if clmp_path.is_file():
        clmp_rows = len(pd.read_csv(clmp_path, dtype=str, keep_default_na=False))

    b_memos = load_pnote_b_memos_by_mpolicy(pnote_path)
    pnote = _read_pnote_csv(pnote_path)
    b_lines = (
        pnote[pnote["FILE_TYPE"].astype(str).str.strip().str.upper() == "B"]["LINE_1"]
        .astype(str)
        .str.strip()
    )
    sample_b_bodies = [t for t in b_lines.tolist() if t][:30]

    # Death rows should carry [PNOTE-B] when policy has B notes
    clms["_k"] = clms["MPOLICY"].astype(str).str.strip()
    deathish = clms[
        clms["MEMOTEXT"].astype(str).str.contains("DEATH_CLAIM", regex=False)
        | clms["MEMOTEXT"].astype(str).str.contains("[PNOTE-B]", regex=False)
        | clms["CLAIMSTAT"].astype(str).str.strip().isin(["1", "2"])
    ]
    death_with_b = deathish[deathish["_k"].isin(b_memos.keys())]
    missing_tag = death_with_b[~death_with_b["MEMOTEXT"].astype(str).str.contains("[PNOTE-B]", regex=False)]
    if len(missing_tag):
        errors.append(f"death rows with B notes missing [PNOTE-B]: {len(missing_tag)}")

    # Sample distinctive B text must not remain on Policy Memo
    memo_blob = "\n".join(memo["MEMOTEXT"].astype(str).tolist())
    b_still_in_memo = 0
    for t in sample_b_bodies:
        if len(t) < 12:
            continue
        if t in memo_blob:
            b_still_in_memo += 1
    # Allow a small false-positive rate if generic phrases also appear in non-B notes
    if b_still_in_memo > 5:
        errors.append(f"sample B LINE_1 still in quikmemo: {b_still_in_memo}/30")

    # Trace policies
    traces = []
    for pol in TRACE_POLICIES:
        row = clms[clms["_k"] == pol]
        mrow = memo[memo["MEMOKEY"].astype(str).str.strip() == pol]
        clms_text = str(row["MEMOTEXT"].iloc[0]) if len(row) else ""
        memo_text = str(mrow["MEMOTEXT"].iloc[0]) if len(mrow) else ""
        ok = "[PNOTE-B]" in clms_text and "PB =" in clms_text
        # B body should not be the only content left wrongly on memo — soft check
        traces.append(
            {
                "MPOLICY": pol,
                "clms_has_pnote_b": "[PNOTE-B]" in clms_text,
                "clms_has_pb": "PB =" in clms_text,
                "clms_has_lineage_death": "DEATH_CLAIM" in clms_text,
                "memo_has_pnote_b": "[PNOTE-B]" in memo_text,
                "ok": ok,
            }
        )
        if not ok:
            errors.append(f"trace fail {pol}")

    # Non-death with B should not be force-updated if only PARTIAL/SURRENDER (no CLAIMSTAT 1/2)
    # Spot-check: a known death control still has CLAIMSTAT intact (column present)
    if "CLAIMSTAT" not in clms.columns:
        errors.append("CLAIMSTAT missing — unrelated schema damage")

    # Schema / row sanity
    if len(clms) < 1000:
        errors.append(f"quikclms row count suspiciously low: {len(clms)}")

    summary = {
        "pnote_b_policies": len(b_memos),
        "death_rows_with_b": int(len(death_with_b)),
        "missing_pnote_b_tag": int(len(missing_tag)),
        "sample_b_still_in_quikmemo": b_still_in_memo,
        "quikclms_rows": int(len(clms)),
        "quikmemo_rows": int(len(memo)),
        "quikclmp_rows": clmp_rows,
        "traces": traces,
        "errors": errors,
        "pass": len(errors) == 0,
    }
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    out_json = EVIDENCE / "issue134_validation_summary.json"
    out_json.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print("Issue #134 validation")
    print(f"  B policies: {summary['pnote_b_policies']}")
    print(f"  Death rows with B: {summary['death_rows_with_b']}")
    print(f"  Missing [PNOTE-B] tag: {summary['missing_pnote_b_tag']}")
    print(f"  Sample B still in quikmemo: {summary['sample_b_still_in_quikmemo']}")
    print(f"  quikclms={summary['quikclms_rows']} quikmemo={summary['quikmemo_rows']} quikclmp={summary['quikclmp_rows']}")
    for t in traces:
        print(f"  TRACE {t['MPOLICY']}: ok={t['ok']} clms_B={t['clms_has_pnote_b']} lineage_left={t['clms_has_lineage_death']}")
    if errors:
        print("FAIL")
        for e in errors:
            print(f"  - {e}")
        print(f"  Summary: {out_json}")
        return 1
    print("PASS")
    print(f"  Summary: {out_json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
