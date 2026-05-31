"""
Non-convertible benefit row governance (LifePRO Product Book alignment).

BENEFIT_SEQ = 99 and associated administrative rows (especially BENEFIT_TYPE = UV
with blank PLAN_CODE) are NON-CONVERTIBLE / NON-PRODUCT structures unless business
explicitly overrides.

These rows:
- are NOT authoritative product coverages
- do NOT require authoritative MPLAN resolution
- must NOT be forced into quikplan/quikridr product authority
- must NOT be hard-failed as orphan products
- must remain EXPECTED_NON_PRODUCT_ROW in governance reporting

See: plan_governance/non_product_row_governance_rule.md
"""

from __future__ import annotations

NON_CONVERTIBLE_BENEFIT_SEQ = frozenset({"99"})

# LifePRO BENEFIT_TYPE values treated as non-product when PLAN is blank
NON_PRODUCT_BENEFIT_TYPES_BLANK_PLAN = frozenset({"UV"})

EXPECTED_NON_PRODUCT_ROW = "EXPECTED_NON_PRODUCT_ROW"
UNRESOLVED_PRODUCT = "UNRESOLVED_PRODUCT"
MISSING_CATALOG_PRODUCT = "MISSING_CATALOG_PRODUCT"
PARSER_DROP = "PARSER_DROP"
ROLLBACK_FALLBACK_ONLY = "ROLLBACK_FALLBACK_ONLY"

GOVERNANCE_FAILURE_CLASSIFICATIONS = frozenset({
    UNRESOLVED_PRODUCT,
    PARSER_DROP,
    MISSING_CATALOG_PRODUCT,
})

NON_PRODUCT_GOVERNANCE_STATUSES = frozenset({
    "BLANK_ALLOWED",
    "CLASSIFIED_OK",
})


def _strip(s: str) -> str:
    return s.strip() if isinstance(s, str) else ""


def is_non_convertible_benefit_row(
    *,
    benefit_seq: str,
    source_plan_code: str = "",
    source_benefit_type: str = "",
) -> tuple[bool, str]:
    """
    Return (True, reason) when row must NOT receive authoritative MPLAN mapping.

    Preserves raw values for caller-side reporting; only uses strip for comparison.
    """
    seq = _strip(benefit_seq)
    plan = source_plan_code  # exact — blank PLAN may be spaces
    plan_blank = not _strip(plan)
    btype = _strip(source_benefit_type)

    if seq in NON_CONVERTIBLE_BENEFIT_SEQ:
        if plan_blank:
            return True, "BENEFIT_SEQ 99 with blank PLAN_CODE — non-convertible administrative structure"
        return True, "BENEFIT_SEQ 99 — non-convertible unless business explicitly overrides"

    if plan_blank and btype in NON_PRODUCT_BENEFIT_TYPES_BLANK_PLAN:
        return True, f"BENEFIT_TYPE {btype} with blank PLAN_CODE — non-product value/administrative row"

    if plan_blank and seq and seq not in ("1", "01"):
        return True, "Blank PLAN_CODE on non-base benefit sequence — likely admin/relationship row"

    if plan_blank:
        return True, "Blank PLAN_CODE — non-product or structural row"

    return False, ""


def classify_blank_mplan_governance(
    *,
    benefit_seq: str,
    source_plan_code: str = "",
    source_benefit_type: str = "",
    exists_in_catalog: bool | None = None,
    exists_in_quikplan: bool | None = None,
    parser_dropped: bool = False,
    allow_legacy: bool = False,
    resolution_path: str = "",
    has_product_premium_indicators: bool = False,
) -> tuple[str, str, str]:
    """
    Classify blank MPLAN rows for P3E/P3F/P3G governance layers.

    Returns (classification, blank_reason, recommended_action).
    Only UNRESOLVED_PRODUCT, PARSER_DROP, and MISSING_CATALOG_PRODUCT are failures.
    """
    non_conv, non_conv_reason = is_non_convertible_benefit_row(
        benefit_seq=benefit_seq,
        source_plan_code=source_plan_code,
        source_benefit_type=source_benefit_type,
    )
    if non_conv:
        return (
            EXPECTED_NON_PRODUCT_ROW,
            non_conv_reason,
            "No action — preserve blank MPLAN; non-convertible per Product Book governance",
        )

    if parser_dropped:
        return (
            PARSER_DROP,
            "Source COVERAGE_ID existed in quikplan_source but parser dropped row before emit",
            "Re-run product setup after source loader fix; verify quikplan emit",
        )

    if exists_in_catalog is False:
        return (
            MISSING_CATALOG_PRODUCT,
            "Source PLAN not in authoritative product catalog",
            "Add approved row to product_catalog_crosswalk.csv",
        )

    if allow_legacy and resolution_path == "LEGACY_FALLBACK":
        return (
            ROLLBACK_FALLBACK_ONLY,
            "Legacy fallback enabled — product not in closed authority emit universe",
            "Disable legacy fallback for production; add catalog/quikplan parity",
        )

    if exists_in_catalog and exists_in_quikplan is False:
        return (
            PARSER_DROP,
            "Catalog-authoritative product missing from quikplan PLAN universe",
            "Run product setup conversion; verify quikplan_source ingestion trace",
        )

    if has_product_premium_indicators:
        return (
            UNRESOLVED_PRODUCT,
            "Product indicators present but authoritative MPLAN resolution returned blank",
            "Verify catalog crosswalk_ql_plan_code and quikplan PLAN parity; re-run P3E",
        )

    return (
        UNRESOLVED_PRODUCT,
        "Source PLAN present but authoritative MPLAN resolution returned blank",
        "Verify catalog crosswalk_ql_plan_code and quikplan PLAN parity; re-run P3E",
    )


def governance_status_for_classification(classification: str, *, allow_legacy: bool = False) -> str:
    """Map blank MPLAN classification to governance status."""
    if classification == EXPECTED_NON_PRODUCT_ROW:
        return "BLANK_ALLOWED"
    if classification == ROLLBACK_FALLBACK_ONLY:
        return "LEGACY_FALLBACK_REPORTED" if allow_legacy else "LEGACY_MODE"
    if classification in GOVERNANCE_FAILURE_CLASSIFICATIONS:
        return "GOVERNANCE_ERROR"
    return "REVIEW"


def row_has_product_premium_indicators(row_data: dict) -> bool:
    """Detect quikridr rows with premium/unit signals suggesting true product row."""
    for field in ("MUNIT", "MPREM", "MVPU", "MAGE"):
        val = _strip(str(row_data.get(field, "")))
        if val not in ("", "0", "0.0", "0.00"):
            return True
    return False
