#!/usr/bin/env python3
"""Grok second-pass — Issue #135 surgical 9011156655C payee backfill."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from qla_core.issue135_match_cso_zero_payee_backfill import ALLOWLIST, REASON  # noqa: E402

OUT = ROOT / "QLA_Migration" / "Output"
EVID = ROOT / "Issue_Log_Items" / "Issue_135" / "evidence"
RESULT = EVID / "issue135_9011156655C_grok_second_pass.json"
POL = "9011156655C"
TOL = 0.01


def _ver(path: Path) -> str:
    m = re.search(r'APP_VERSION\s*=\s*"([^"]+)"', path.read_text(encoding="utf-8", errors="replace"))
    return m.group(1) if m else ""


def _strip(v) -> str:
    return "" if v is None else str(v).strip()


def _money(v) -> float:
    try:
        return float(str(v).replace(",", "").strip() or 0)
    except (TypeError, ValueError):
        return 0.0


def main() -> int:
    fails: list[str] = []
    clms = pd.read_csv(OUT / "quikclms.csv", dtype=str).fillna("")
    clmp = pd.read_csv(OUT / "quikclmp.csv", dtype=str).fillna("")

    v_root = _ver(ROOT / "app.py")
    v_mig = _ver(ROOT / "QLA_Migration" / "app.py")
    if v_root != v_mig:
        fails.append(f"APP_VERSION mismatch root={v_root} mig={v_mig}")
    if v_root != "v58.60":
        fails.append(f"APP_VERSION={v_root} expected v58.60")

    # Golden policy must remain on SAFE allowlist (cohort may include additional SAFE keys)
    if POL not in ALLOWLIST:
        fails.append(f"allowlist missing golden {POL}; keys={list(ALLOWLIST.keys())[:5]}")

    mod = (ROOT / "qla_core" / "issue135_match_cso_zero_payee_backfill.py").read_text(
        encoding="utf-8", errors="replace"
    )
    if REASON not in mod:
        fails.append("missing reason constant in backfill module")
    exp_path = ROOT / "qla_core" / "issue135_cso_claims_expansion.py"
    exp_txt = exp_path.read_text(encoding="utf-8", errors="replace")
    if "apply_match_cso_zero_payee_backfill" not in exp_txt:
        fails.append("backfill not wired into issue135 expansion")

    hdr = clms[clms["MPOLICY"].map(_strip) == POL]
    pay = clmp[clmp["MPOLICY"].map(_strip) == POL]
    if len(hdr) != 1:
        fails.append(f"header_rows={len(hdr)}")
    else:
        h = hdr.iloc[0]
        if abs(_money(h["MPAID"]) - 5145.67) > TOL:
            fails.append(f"MPAID={h['MPAID']}")
        if abs(_money(h["MFACE"]) - 5000.0) > TOL or abs(_money(h["NETDB"]) - 5000.0) > TOL:
            fails.append(f"MFACE/NETDB={h['MFACE']}/{h['NETDB']}")
        if abs(_money(h["MINTAMT"])) > TOL or abs(_money(h["PREMIUM"])) > TOL:
            fails.append(f"MINTAMT/PREMIUM={h['MINTAMT']}/{h['PREMIUM']}")

    if len(pay) != 4:
        fails.append(f"payees={len(pay)}")
    else:
        if abs(round(pay["MAMOUNT"].map(_money).sum(), 2) - 5145.67) > TOL:
            fails.append("payee_sum!=5145.67")
        names = sorted(pay["MPAYNAME"].map(_strip).str.upper())
        expect_names = sorted(
            [
                "LINVILLE L BRASWELL",
                "CHERI ROSE BRASWELL",
                "DANIEL L BRASWELL JR",
                "ROBERT C BRASWELL",
            ]
        )
        if names != expect_names:
            fails.append(f"names={names}")

    # Screenshot alignment: Net Payment = MPAID; Amount Ins = MFACE; payee amounts present
    screenshot_align = (
        len(hdr) == 1
        and abs(_money(hdr.iloc[0]["MPAID"]) - 5145.67) <= TOL
        and abs(_money(hdr.iloc[0]["MFACE"]) - 5000.0) <= TOL
        and len(pay) == 4
        and abs(round(pay["MAMOUNT"].map(_money).sum(), 2) - 5145.67) <= TOL
    )
    if not screenshot_align:
        fails.append("screenshot_values_not_aligned")

    audit = EVID / "issue135_9011156655C_zero_payee_backfill_audit.csv"
    if not audit.is_file():
        fails.append("missing_backfill_audit")

    result = {
        "policy": POL,
        "reason": REASON,
        "app_version": v_root,
        "pass": bool(len(fails) == 0),
        "fails": fails,
        "screenshot_aligned": bool(screenshot_align),
        "payee_count": int(len(pay)),
        "confidence": 0.95 if not fails else 0.4,
        "followup": (
            "Broader MATCH_CSO existing-header zero-payee cohort (~140) remains "
            "follow-up analysis — not mass-applied by this change."
        ),
    }
    RESULT.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))
    print("Wrote", RESULT)
    return 0 if not fails else 1


if __name__ == "__main__":
    raise SystemExit(main())
