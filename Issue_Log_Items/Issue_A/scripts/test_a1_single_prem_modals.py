"""Issue A A1 — SP modal zeros must survive Issue #21J overlay."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[3]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from qla_core.modal_premium_factors import apply_modal_factors_to_quikplan
from qla_core.quikplan_converter import (
    apply_single_premium_payment_settings,
    load_single_premium_plans,
)


def test_load_single_premium_plans_four_descr_plans():
    plans = load_single_premium_plans(str(REPO))
    assert plans == {"1668SP", "10L171", "10L172", "1L17SP"}
    assert "117JPO" not in plans
    assert "17MJPO" not in plans


def test_sp_modals_zero_after_21j_overlay():
    repo_root = str(REPO)
    df = pd.DataFrame(
        [
            {
                "PLAN": "10L171",
                "PAYYRS": "0",
                "PAYAGE": "0",
                "SEMI": "99",
                "QTRL": "99",
                "MTHD": "99",
                "MTHB": "99",
                "ANNL": "100",
            },
            {
                "PLAN": "NOTMAP1",
                "PAYYRS": "0",
                "PAYAGE": "0",
                "SEMI": "50.0000",
                "QTRL": "25.0035",
                "MTHD": "8.3298",
                "MTHB": "8.3298",
                "ANNL": "100",
            },
        ]
    )
    df = apply_single_premium_payment_settings(df, repo_root=repo_root)
    df, _ = apply_modal_factors_to_quikplan(df, repo_root=repo_root)
    df = apply_single_premium_payment_settings(df, repo_root=repo_root)

    sp = df.loc[df["PLAN"] == "10L171"].iloc[0]
    assert sp["PAYYRS"] == "1"
    assert sp["PAYAGE"] == "0"
    for col in ("SEMI", "QTRL", "MTHD", "MTHB"):
        assert float(sp[col]) == 0.0

    non_sp = df.loc[df["PLAN"] == "NOTMAP1"].iloc[0]
    assert float(non_sp["SEMI"]) == 50.0
    assert float(non_sp["QTRL"]) == 25.0035
