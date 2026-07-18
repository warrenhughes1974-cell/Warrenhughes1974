"""DG-PLANVALUES-004/005/006 — GENDER, UWCLASS, BAND default-or-reference rules."""

from __future__ import annotations

from data_governance.catalog.governance_items import (
    RULE_DG_PLANVALUES_004,
    RULE_DG_PLANVALUES_005,
    RULE_DG_PLANVALUES_006,
)
from data_governance.config.settings import (
    TABLE_QUIKPLBD,
    TABLE_QUIKPLGD,
    TABLE_QUIKPLUW,
)
from data_governance.rules.plan_value_integrity.default_or_ref_rule import (
    run_default_or_composite_reference,
)


def run_dg_planvalues_004(store, *, run_id, run_timestamp):
    return run_default_or_composite_reference(
        store,
        rule=RULE_DG_PLANVALUES_004,
        source_field="GENDER",
        default_value="0",
        ref_table=TABLE_QUIKPLGD,
        ref_plan_field="PLAN",
        ref_code_field="GDCODE",
        label="gender code",
        run_id=run_id,
        run_timestamp=run_timestamp,
        uppercase_code=True,
    )


def run_dg_planvalues_005(store, *, run_id, run_timestamp):
    return run_default_or_composite_reference(
        store,
        rule=RULE_DG_PLANVALUES_005,
        source_field="UWCLASS",
        default_value="00",
        ref_table=TABLE_QUIKPLUW,
        ref_plan_field="PLAN",
        ref_code_field="UWCODE",
        label="underwriting class",
        run_id=run_id,
        run_timestamp=run_timestamp,
        uppercase_code=True,
    )


def run_dg_planvalues_006(store, *, run_id, run_timestamp):
    # Verified band setup table is QuikPlBd.BDCODE (QuikPlVd not present in CSO).
    return run_default_or_composite_reference(
        store,
        rule=RULE_DG_PLANVALUES_006,
        source_field="BAND",
        default_value="00",
        ref_table=TABLE_QUIKPLBD,
        ref_plan_field="PLAN",
        ref_code_field="BDCODE",
        label="band",
        run_id=run_id,
        run_timestamp=run_timestamp,
        uppercase_code=True,
    )
