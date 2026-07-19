"""Rule registry — add future governance items by registering callables here."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from data_governance.catalog.governance_items import (
    ALL_RULE_DEFINITIONS,
    RULE_DG_PLANVALUES_001,
    RULE_DG_PLANVALUES_002,
    RULE_DG_PLANVALUES_003,
    RULE_DG_PLANVALUES_004,
    RULE_DG_PLANVALUES_005,
    RULE_DG_PLANVALUES_006,
    RULE_DG_PLANVALUES_007,
    RULE_DG_PLANVALUES_008,
    RULE_DG_QUIKPLAN_001,
    RULE_DG_QUIKPLAN_002,
    RULE_DG_QUIKPLAN_003,
    RULE_DG_QUIKPLAN_004,
    RULE_DG_QUIKPLAN_005,
    RULE_DG_QUIKPLAN_006,
    RULE_DG_QUIKPLAN_007,
    RULE_DG_QUIKPLAN_008,
    RULE_DG_QUIKPLAN_009,
    RULE_DG_QUIKPLAN_010,
    RULE_DG_QUIKPLAN_011,
    RULE_DG_QUIKPLAN_012,
    RULE_DG_QUIKPLAN_013,
    RULE_DG_QUIKPLAN_014,
    RULE_DG_QUIKPLAN_015,
    RULE_DG_QUIKPLAN_016,
    RULE_DG_QUIKPLAN_017,
    RULE_DG_QUIKPLAN_018,
    RULE_DG_QUIKPLAN_019,
    RULE_DG_QUIKPLAN_020,
    RULE_DG_QUIKPLAN_021,
    RULE_DG_QUIKPLAN_023,
    RULE_DG_QUIKPLAN_024,
    RULE_DG_QUIKPLAN_025,
    RULE_DG_QUIKPLAN_026,
    RULE_DG_QUIKPLAN_027,
    RULE_DG_QUIKPLAN_028,
    RULE_DG_QUIKPLAN_029,
    RULE_DG_QUIKPLAN_030,
    RULE_DG_QUIKPLAN_031,
    RULE_DG_QUIKPLAN_032,
    RULE_DG_QUIKPLAN_033,
    RULE_DG_QUIKACTG_001,
    RULE_DG_QUIKACTG_002,
    RULE_DG_QUIKCOMP_001,
    RULE_DG_QUIKCOMP_002,
    RULE_DG_QUIKCOMP_003,
    RULE_DG_QUIKDATE_001,
    RULE_DG_QUIKDATE_002,
    RULE_DG_QUIKDATE_003,
    RULE_DG_QUIKDATE_004,
    RULE_DG_QUIKDATE_005,
    RULE_DG_QUIKDATE_006,
    RULE_DG_QUIKLIST_001,
    RULE_DG_QUIKLIST_002,
    RULE_DG_QUIKLIST_003,
    RULE_DG_QUIKLIST_004,
    RULE_DG_QUIKLIST_005,
    RULE_DG_QUIKLIST_006,
    RULE_DG_QUIKLIST_007,
    RULE_DG_QUIKLIST_008,
    RULE_DG_QUIKLIST_009,
    RULE_DG_QUIKMSTR_001,
    RuleDefinition,
)
from data_governance.models.findings import RuleExecutionResult

RuleCallable = Callable[..., RuleExecutionResult]


@dataclass(frozen=True)
class RegisteredRule:
    definition: RuleDefinition
    execute: RuleCallable


def _build_registry() -> dict[str, RegisteredRule]:
    from data_governance.rules.company_code_integrity.dg_quikcomp_001_unique_company_code import (
        run_dg_quikcomp_001,
    )
    from data_governance.rules.company_code_integrity.dg_quikcomp_002_agent_company_code_must_exist import (
        run_dg_quikcomp_002,
    )
    from data_governance.rules.company_code_integrity.dg_quikcomp_003_policy_company_code_must_exist import (
        run_dg_quikcomp_003,
    )
    from data_governance.rules.policy_number_integrity.dg_quikmstr_001_policy_number_length import (
        run_dg_quikmstr_001,
    )
    from data_governance.rules.accounting_integrity.dg_quikactg_001_unique_company_plan import (
        run_dg_quikactg_001,
    )
    from data_governance.rules.accounting_integrity.dg_quikactg_002_company_must_exist import (
        run_dg_quikactg_002,
    )
    from data_governance.rules.group_billing_integrity.dg_quiklist_001_unique_group import (
        run_dg_quiklist_001,
    )
    from data_governance.rules.group_billing_integrity.dg_quiklist_002_company_must_exist import (
        run_dg_quiklist_002,
    )
    from data_governance.rules.group_billing_integrity.dg_quiklist_003_billing_name_required import (
        run_dg_quiklist_003,
    )
    from data_governance.rules.group_billing_integrity.dg_quiklist_004_msort_default import (
        run_dg_quiklist_004,
    )
    from data_governance.rules.group_billing_integrity.dg_quiklist_005_mlapsel_default import (
        run_dg_quiklist_005,
    )
    from data_governance.rules.group_billing_integrity.dg_quiklist_006_mlapseh_default import (
        run_dg_quiklist_006,
    )
    from data_governance.rules.group_billing_integrity.dg_quiklist_007_mstatus_default import (
        run_dg_quiklist_007,
    )
    from data_governance.rules.group_billing_integrity.dg_quiklist_008_mbillday_default import (
        run_dg_quiklist_008,
    )
    from data_governance.rules.group_billing_integrity.dg_quiklist_009_mbillmode_default import (
        run_dg_quiklist_009,
    )
    from data_governance.rules.processing_date_integrity.dg_quikdate_001_pac_bill import (
        run_dg_quikdate_001,
    )
    from data_governance.rules.processing_date_integrity.dg_quikdate_002_direct_bill import (
        run_dg_quikdate_002,
    )
    from data_governance.rules.processing_date_integrity.dg_quikdate_003_reinsurance_bill import (
        run_dg_quikdate_003,
    )
    from data_governance.rules.processing_date_integrity.dg_quikdate_004_achfileid import (
        run_dg_quikdate_004,
    )
    from data_governance.rules.processing_date_integrity.dg_quikdate_005_achfileid2 import (
        run_dg_quikdate_005,
    )
    from data_governance.rules.processing_date_integrity.dg_quikdate_006_escdate import (
        run_dg_quikdate_006,
    )
    from data_governance.rules.plan_value_integrity.dg_planvalues_001_003_refs import (
        run_dg_planvalues_001,
        run_dg_planvalues_002,
        run_dg_planvalues_003,
    )
    from data_governance.rules.plan_value_integrity.dg_planvalues_004_006_codes import (
        run_dg_planvalues_004,
        run_dg_planvalues_005,
        run_dg_planvalues_006,
    )
    from data_governance.rules.plan_value_integrity.dg_planvalues_007_issuest import (
        run_dg_planvalues_007,
    )
    from data_governance.rules.plan_value_integrity.dg_planvalues_008_effdate import (
        run_dg_planvalues_008,
    )
    from data_governance.rules.plan_setup_integrity.dg_quikplan_001_006_plan_code import (
        run_dg_quikplan_001,
        run_dg_quikplan_002,
        run_dg_quikplan_003,
        run_dg_quikplan_004,
        run_dg_quikplan_005,
        run_dg_quikplan_006,
    )
    from data_governance.rules.plan_setup_integrity.dg_quikplan_007_015_plan_type_periods import (
        run_dg_quikplan_007,
        run_dg_quikplan_008,
        run_dg_quikplan_009,
        run_dg_quikplan_010,
        run_dg_quikplan_011,
        run_dg_quikplan_012,
        run_dg_quikplan_013,
        run_dg_quikplan_014,
        run_dg_quikplan_015,
    )
    from data_governance.rules.plan_setup_integrity.dg_quikplan_016_024_defaults_refs import (
        run_dg_quikplan_016,
        run_dg_quikplan_017,
        run_dg_quikplan_018,
        run_dg_quikplan_019,
        run_dg_quikplan_020,
        run_dg_quikplan_021,
        run_dg_quikplan_023,
        run_dg_quikplan_024,
    )
    from data_governance.rules.plan_setup_integrity.dg_quikplan_025_030_supporting import (
        run_dg_quikplan_025,
        run_dg_quikplan_026,
        run_dg_quikplan_027,
        run_dg_quikplan_028,
        run_dg_quikplan_029,
        run_dg_quikplan_030,
    )
    from data_governance.rules.plan_setup_integrity.dg_quikplan_031_033_cross_dates import (
        run_dg_quikplan_031,
        run_dg_quikplan_032,
        run_dg_quikplan_033,
    )

    entries = (
        RegisteredRule(RULE_DG_QUIKCOMP_001, run_dg_quikcomp_001),
        RegisteredRule(RULE_DG_QUIKCOMP_002, run_dg_quikcomp_002),
        RegisteredRule(RULE_DG_QUIKCOMP_003, run_dg_quikcomp_003),
        RegisteredRule(RULE_DG_QUIKMSTR_001, run_dg_quikmstr_001),
        RegisteredRule(RULE_DG_QUIKACTG_001, run_dg_quikactg_001),
        RegisteredRule(RULE_DG_QUIKACTG_002, run_dg_quikactg_002),
        RegisteredRule(RULE_DG_QUIKLIST_001, run_dg_quiklist_001),
        RegisteredRule(RULE_DG_QUIKLIST_002, run_dg_quiklist_002),
        RegisteredRule(RULE_DG_QUIKLIST_003, run_dg_quiklist_003),
        RegisteredRule(RULE_DG_QUIKLIST_004, run_dg_quiklist_004),
        RegisteredRule(RULE_DG_QUIKLIST_005, run_dg_quiklist_005),
        RegisteredRule(RULE_DG_QUIKLIST_006, run_dg_quiklist_006),
        RegisteredRule(RULE_DG_QUIKLIST_007, run_dg_quiklist_007),
        RegisteredRule(RULE_DG_QUIKLIST_008, run_dg_quiklist_008),
        RegisteredRule(RULE_DG_QUIKLIST_009, run_dg_quiklist_009),
        RegisteredRule(RULE_DG_QUIKDATE_001, run_dg_quikdate_001),
        RegisteredRule(RULE_DG_QUIKDATE_002, run_dg_quikdate_002),
        RegisteredRule(RULE_DG_QUIKDATE_003, run_dg_quikdate_003),
        RegisteredRule(RULE_DG_QUIKDATE_004, run_dg_quikdate_004),
        RegisteredRule(RULE_DG_QUIKDATE_005, run_dg_quikdate_005),
        RegisteredRule(RULE_DG_QUIKDATE_006, run_dg_quikdate_006),
        RegisteredRule(RULE_DG_PLANVALUES_001, run_dg_planvalues_001),
        RegisteredRule(RULE_DG_PLANVALUES_002, run_dg_planvalues_002),
        RegisteredRule(RULE_DG_PLANVALUES_003, run_dg_planvalues_003),
        RegisteredRule(RULE_DG_PLANVALUES_004, run_dg_planvalues_004),
        RegisteredRule(RULE_DG_PLANVALUES_005, run_dg_planvalues_005),
        RegisteredRule(RULE_DG_PLANVALUES_006, run_dg_planvalues_006),
        RegisteredRule(RULE_DG_PLANVALUES_007, run_dg_planvalues_007),
        RegisteredRule(RULE_DG_PLANVALUES_008, run_dg_planvalues_008),
        RegisteredRule(RULE_DG_QUIKPLAN_001, run_dg_quikplan_001),
        RegisteredRule(RULE_DG_QUIKPLAN_002, run_dg_quikplan_002),
        RegisteredRule(RULE_DG_QUIKPLAN_003, run_dg_quikplan_003),
        RegisteredRule(RULE_DG_QUIKPLAN_004, run_dg_quikplan_004),
        RegisteredRule(RULE_DG_QUIKPLAN_005, run_dg_quikplan_005),
        RegisteredRule(RULE_DG_QUIKPLAN_006, run_dg_quikplan_006),
        RegisteredRule(RULE_DG_QUIKPLAN_007, run_dg_quikplan_007),
        RegisteredRule(RULE_DG_QUIKPLAN_008, run_dg_quikplan_008),
        RegisteredRule(RULE_DG_QUIKPLAN_009, run_dg_quikplan_009),
        RegisteredRule(RULE_DG_QUIKPLAN_010, run_dg_quikplan_010),
        RegisteredRule(RULE_DG_QUIKPLAN_011, run_dg_quikplan_011),
        RegisteredRule(RULE_DG_QUIKPLAN_012, run_dg_quikplan_012),
        RegisteredRule(RULE_DG_QUIKPLAN_013, run_dg_quikplan_013),
        RegisteredRule(RULE_DG_QUIKPLAN_014, run_dg_quikplan_014),
        RegisteredRule(RULE_DG_QUIKPLAN_015, run_dg_quikplan_015),
        RegisteredRule(RULE_DG_QUIKPLAN_016, run_dg_quikplan_016),
        RegisteredRule(RULE_DG_QUIKPLAN_017, run_dg_quikplan_017),
        RegisteredRule(RULE_DG_QUIKPLAN_018, run_dg_quikplan_018),
        RegisteredRule(RULE_DG_QUIKPLAN_019, run_dg_quikplan_019),
        RegisteredRule(RULE_DG_QUIKPLAN_020, run_dg_quikplan_020),
        RegisteredRule(RULE_DG_QUIKPLAN_021, run_dg_quikplan_021),
        RegisteredRule(RULE_DG_QUIKPLAN_023, run_dg_quikplan_023),
        RegisteredRule(RULE_DG_QUIKPLAN_024, run_dg_quikplan_024),
        RegisteredRule(RULE_DG_QUIKPLAN_025, run_dg_quikplan_025),
        RegisteredRule(RULE_DG_QUIKPLAN_026, run_dg_quikplan_026),
        RegisteredRule(RULE_DG_QUIKPLAN_027, run_dg_quikplan_027),
        RegisteredRule(RULE_DG_QUIKPLAN_028, run_dg_quikplan_028),
        RegisteredRule(RULE_DG_QUIKPLAN_029, run_dg_quikplan_029),
        RegisteredRule(RULE_DG_QUIKPLAN_030, run_dg_quikplan_030),
        RegisteredRule(RULE_DG_QUIKPLAN_031, run_dg_quikplan_031),
        RegisteredRule(RULE_DG_QUIKPLAN_032, run_dg_quikplan_032),
        RegisteredRule(RULE_DG_QUIKPLAN_033, run_dg_quikplan_033),
    )
    return {r.definition.rule_id: r for r in entries}


_REGISTRY: dict[str, RegisteredRule] | None = None


def get_registry() -> dict[str, RegisteredRule]:
    global _REGISTRY
    if _REGISTRY is None:
        _REGISTRY = _build_registry()
    return _REGISTRY


def reset_registry_for_tests() -> None:
    global _REGISTRY
    _REGISTRY = None


def list_rule_definitions() -> list[RuleDefinition]:
    return list(ALL_RULE_DEFINITIONS)


def get_rule(rule_id: str) -> RegisteredRule:
    registry = get_registry()
    key = rule_id.strip().upper()
    if key not in registry:
        raise KeyError(f"Unknown governance rule ID: {rule_id}")
    return registry[key]


def select_rules(
    *,
    rule_id: str | None = None,
    governance_item_id: str | None = None,
) -> list[RegisteredRule]:
    registry = get_registry()
    if rule_id:
        return [get_rule(rule_id)]
    rules = list(registry.values())
    if governance_item_id:
        item = governance_item_id.strip().upper()
        selected = [r for r in rules if r.definition.governance_item_id.upper() == item]
        if not selected:
            raise KeyError(f"Unknown governance item ID: {governance_item_id}")
        return selected
    return rules


def required_tables_for(rules: list[RegisteredRule]) -> list[str]:
    names: list[str] = []
    seen: set[str] = set()
    for rule in rules:
        for table in rule.definition.source_tables:
            if table not in seen:
                seen.add(table)
                names.append(table)
    return names
