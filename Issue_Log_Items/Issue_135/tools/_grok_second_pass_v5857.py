#!/usr/bin/env python3
"""Grok second-pass validation for Issue #135 v58.57 (#134-after-#135 ordering fix)."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from qla_core.issue134_claim_memo_overlay import load_pnote_b_memos_by_mpolicy  # noqa: E402
from qla_core.issue135_cso_claims_expansion import CSO_NO_PACTG_MARKER  # noqa: E402
from qla_core.lifepro_source_resolver import resolve_quikmemo_sources  # noqa: E402

OUT = ROOT / "QLA_Migration" / "Output"
EVID = ROOT / "Issue_Log_Items" / "Issue_135" / "evidence"
ANALYSIS = EVID / "issue135_459_analysis_per_policy.csv"
OPTION3 = EVID / "issue135_option3_quikclms_overlay.csv"
HOLD = EVID / "issue135_option3_hold_unresolved.csv"
TOL = 0.01


def _ver(path: Path) -> str:
    m = re.search(r'APP_VERSION\s*=\s*"([^"]+)"', path.read_text(encoding="utf-8", errors="replace"))
    return m.group(1) if m else ""


def main() -> int:
    fails: list[str] = []
    clms = pd.read_csv(OUT / "quikclms.csv", dtype=str).fillna("")
    clmp = pd.read_csv(OUT / "quikclmp.csv", dtype=str).fillna("")
    analysis = pd.read_csv(ANALYSIS, dtype=str, keep_default_na=False)
    o3 = pd.read_csv(OPTION3, dtype=str, keep_default_na=False)

    v_root = _ver(ROOT / "app.py")
    v_mig = _ver(ROOT / "QLA_Migration" / "app.py")
    if v_root != "v58.57" or v_mig != "v58.57":
        fails.append(f"APP_VERSION root={v_root} mig={v_mig} expected v58.57")

    # Ordering comment present in both apps
    for p in (ROOT / "app.py", ROOT / "QLA_Migration" / "app.py"):
        text = p.read_text(encoding="utf-8", errors="replace")
        idx135 = text.find("issue135_cso_expansion")
        idx134 = text.find("issue134_claim_memos")
        # In emit block, first occurrence of expansion emit key should precede first memo key
        # after the locked-order comment.
        marker = "Order locked v58.57"
        if marker not in text:
            fails.append(f"{p.name}: missing order-lock comment")
        else:
            tail = text.split(marker, 1)[1]
            if tail.find("_apply_issue135_cso_claims_expansion") > tail.find(
                "_apply_issue134_claim_memos"
            ):
                fails.append(f"{p.name}: #134 still before #135 in emit order")

    mint_nz = int((pd.to_numeric(clms["MINTAMT"], errors="coerce").fillna(0).abs() > TOL).sum())
    if mint_nz:
        fails.append(f"MINTAMT nonzero={mint_nz}")

    marker_n = int(clms["MEMOTEXT"].astype(str).str.contains(CSO_NO_PACTG_MARKER, regex=False).sum())
    if marker_n != 308:
        fails.append(f"marker count={marker_n} expected 308")

    clmp_pols = set(clmp["MPOLICY"].astype(str).str.strip())
    marker_payee = int(
        clms[clms["MEMOTEXT"].astype(str).str.contains(CSO_NO_PACTG_MARKER, regex=False)][
            "MPOLICY"
        ]
        .astype(str)
        .str.strip()
        .isin(clmp_pols)
        .sum()
    )
    if marker_payee:
        fails.append(f"marker rows with payees={marker_payee}")

    derived = analysis[analysis["category"].astype(str).str.strip() == "DERIVED_HIGH"]
    derived_pols = set(derived["mpolicy"].astype(str).str.strip())
    if len(derived_pols) != 142:
        fails.append(f"derived analysis pols={len(derived_pols)}")
    present = clms[clms["MPOLICY"].astype(str).str.strip().isin(derived_pols)]
    if len(present["MPOLICY"].astype(str).str.strip().unique()) != 142:
        fails.append("derived headers missing from Output")

    pnote, _, _, _ = resolve_quikmemo_sources(str(ROOT / "QLA_Migration" / "Source"))
    b_memos = load_pnote_b_memos_by_mpolicy(pnote) if pnote else {}
    deathish = clms[
        clms["MEMOTEXT"].astype(str).str.contains("DEATH_CLAIM", regex=False)
        | clms["MEMOTEXT"].astype(str).str.contains("[PNOTE-B]", regex=False)
        | clms["CLAIMSTAT"].astype(str).str.strip().isin(["1", "2"])
    ]
    death_with_b = deathish[deathish["MPOLICY"].astype(str).str.strip().isin(b_memos.keys())]
    missing_b = death_with_b[
        ~death_with_b["MEMOTEXT"].astype(str).str.contains("[PNOTE-B]", regex=False)
    ]
    if len(missing_b):
        fails.append(f"death+B missing [PNOTE-B]={len(missing_b)}")

    # Option-3 count
    o3_pols = set(o3["MPOLICY"].astype(str).str.strip())
    if len(o3_pols) != 43:
        fails.append(f"option3 overlay pols={len(o3_pols)}")

    hold_a = analysis[analysis["category"].astype(str).str.strip() == "HOLD_INCOMPLETE_SOURCE"]
    hold_a_pols = sorted(set(hold_a["mpolicy"].astype(str).str.strip()) - {""})
    if len(hold_a_pols) != 9:
        fails.append(f"hold analysis={len(hold_a_pols)}")
    present_holds = [
        p for p in hold_a_pols if p in set(clms["MPOLICY"].astype(str).str.strip())
    ]
    if present_holds:
        fails.append(f"holds present in clms={present_holds}")

    leftovers = sorted(
        p.name
        for p in OUT.iterdir()
        if p.is_file() and not p.name.lower().startswith("quik")
    )
    if leftovers:
        fails.append(f"Output non-quik leftovers={leftovers}")

    for name in (
        "Migration_Audit_Log.txt",
        "cso_mortality_crosswalk_qa.csv",
        "variation_code_audit.csv",
    ):
        if (OUT / name).exists():
            fails.append(f"still in Output: {name}")

    report = {
        "overall": "PASS" if not fails else "FAIL",
        "engine": "v58.57",
        "app_version_root": v_root,
        "app_version_mig": v_mig,
        "fails": fails,
        "clms": int(len(clms)),
        "clmp": int(len(clmp)),
        "counts": {
            "derived_in_output": 142,
            "no_pactg_marker": marker_n,
            "marker_with_payee": marker_payee,
            "option3_pols": len(o3_pols),
            "holds_analysis": len(hold_a_pols),
            "holds_in_output": len(present_holds),
            "death_with_b": int(len(death_with_b)),
            "missing_pnote_b": int(len(missing_b)),
            "mintamt_nonzero": mint_nz,
        },
        "moved_artifacts_expected": {
            "Migration_Audit_Log.txt": "QLA_Migration/Logs/",
            "cso_mortality_crosswalk_qa.csv": "QLA_Migration/Reports/",
            "variation_code_audit.csv": "QLA_Migration/Reports/",
        },
    }
    out = EVID / "issue135_v5857_grok_second_pass.json"
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    print(f"wrote {out}")
    return 0 if not fails else 1


if __name__ == "__main__":
    raise SystemExit(main())
