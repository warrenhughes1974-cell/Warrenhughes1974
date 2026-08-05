"""Cut Remediation Wave 1 — claims CC join, 21F Issue #2 pad, #114 baseline."""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from qla_core.issue21f_premium_adjustment import (
    _emit_issue2_mpolicy,
    build_conversion_adjustment_row,
)
from qla_core.issue78_quikclmp_recovery import recover_missing_quikclmp_payments
from qla_core.normalize_utils import format_qladmin_mpolicy
from tools.validators import validate_issue114_dividend_history as v114


def test_emit_issue2_mpolicy_pads_short_keys():
    assert _emit_issue2_mpolicy("9018253C") == "   9018253C"
    assert _emit_issue2_mpolicy("9018253AC") == "  9018253AC"
    assert _emit_issue2_mpolicy("901ML4054C") == " 901ML4054C"
    assert _emit_issue2_mpolicy("9010310404C") == "9010310404C"


def test_21f_adj_row_preserves_width11():
    row = build_conversion_adjustment_row("9018253C", 272.08, None)
    assert row["MPOLICY"] == "   9018253C"
    assert len(row["MPOLICY"]) == 11
    golden = build_conversion_adjustment_row("9010310404C", 15193.85, None)
    assert golden["MPOLICY"] == "9010310404C"
    assert golden["PREMIUM"] == "15193.85"


def test_issue78_does_not_double_append_c(tmp_path):
    clms = pd.DataFrame(
        [
            {
                "MPOLICY": "   9018253C",
                "MPHASE": "1",
                "CLAIMSTAT": "99",
                "MPAID": "14.32",
            }
        ]
    )
    clmp = pd.DataFrame(columns=["MPOLICY", "MPHASE", "MAMOUNT", "MSEQ"])
    # Empty pactg/rel → no rows recovered, but exercise path with missing payee pol
    pactg = tmp_path / "pactg.csv"
    pactg.write_text(
        "POLICY_NUMBER,CREDIT_CODE,DEBIT_CODE,TRANS_AMOUNT,EFFECTIVE_DATE,REVERSAL_CODE,CONTROL_NUMBER\n"
        "9018253,90,,14.32,20220331,,1\n",
        encoding="latin1",
    )
    rel = tmp_path / "rel.csv"
    rel.write_text(
        "POLICY_NUMBER,RELATE_CODE,NAME_ID,NAME_BUSINESS,INDIVIDUAL_FIRST,INDIVIDUAL_MIDDLE,"
        "INDIVIDUAL_LAST,ADDR_LINE_1,ADDR_LINE_2,CITY,STATE,ZIP,ZIP_EXTENSION,KEY_NAME\n"
        "9018253,IN,1,,BRENDA,,HAASE,ADDR,,,,,\n",
        encoding="latin1",
    )
    cw = tmp_path / "cw.csv"
    cw.write_text("old,new\n9018253,018253C\n", encoding="utf-8")

    out, audit = recover_missing_quikclmp_payments(
        clms,
        clmp,
        str(pactg),
        str(rel),
        str(cw),
        format_mpolicy=format_qladmin_mpolicy,
    )
    assert not out.empty
    keys = out["MPOLICY"].astype(str).tolist()
    assert "   9018253C" in keys
    assert not any(str(k).strip() == "9018253CC" for k in keys)
    # Prove the bug pattern
    assert format_qladmin_mpolicy("9018253C") == "  9018253CC"


def test_issue114_baseline_includes_issue54_seeds():
    assert v114.ISSUE54_SEED_DELTA == 556
    assert v114.BASELINE_PRESERVED["10"] == 4118
    assert v114.BASELINE_PRESERVED["8"] == 3657
    assert v114.BASELINE_TOTAL_ROWS == 41066
    # Additive identity used by validator
    div = 3079
    ledger = 867
    assert v114.BASELINE_TOTAL_ROWS + div + ledger == 45012
