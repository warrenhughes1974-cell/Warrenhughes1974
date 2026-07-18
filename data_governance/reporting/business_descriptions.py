"""Centralized plain-English descriptions for governance reports.

Keep report wording here — not scattered across rule validators.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

_LOG = logging.getLogger(__name__)

# Friendly display names for logical tables (report text only)
FRIENDLY_TABLE_NAMES: dict[str, str] = {
    "QuikComp": "Company Setup",
    "QuikAgts": "Agents",
    "QuikMstr": "Policies",
    "QuikActg": "Accounting",
    "QuikList": "Group Billing",
    "QuikDate": "Processing Dates",
    "QuikQxs": "Mortality Table Setup",
    "QuikPlan": "Plan Setup",
    "QuikPlGd": "Gender Setup",
    "QuikPlUw": "Underwriting Class Setup",
    "QuikPlBd": "Band Setup",
    "QuikPlCv": "Cash Values",
    "QuikPlTv": "Tabular Values",
    "QuikPlGp": "Guaranteed Premiums",
    "QuikPlDb": "Death Benefits",
    "QuikPlDv": "Dividends",
    "QuikComm": "Commission Setup",
    "QuikGps": "Gross Premium Setup",
    "QuikDbs": "Death Benefit Setup",
    "QuikCvs": "Cash Value Setup",
    "QuikTvs": "Terminal Reserve Setup",
    "QuikNps": "Net Premium Setup",
    "QuikAint": "Annuity Interest Setup",
    "QuikAing": "Annuity Guarantee Setup",
    "QuikAexp": "Annuity Expense Setup",
    "QuikAinf": "Annuity Information Setup",
    "QuikUint": "Universal Life Interest Setup",
    "QuikNff": "Nonforfeiture Factor Setup",
    "QuikPlSt": "State Setup",
    "QuikPlNb": "New Business Setup",
    "QuikIssc": "Issue Charge Setup",
}


@dataclass(frozen=True)
class AreaDescription:
    item_id: str
    area_name: str
    summary_what_checked: str
    sort_order: int


@dataclass(frozen=True)
class RuleDescription:
    rule_id: str
    area_name: str
    check_description: str
    required_value: str
    # How to pick Record column: company_code | policy_number | group_number |
    # agent_number | company_plan | record_number | plan | plan_detail | key_value
    record_strategy: str
    subsection: str = ""
    # Short problem builders use failure_category / message when needed
    problem_default: str = ""


AREA_DESCRIPTIONS: dict[str, AreaDescription] = {
    "DG-QUIKCOMP": AreaDescription(
        item_id="DG-QUIKCOMP",
        area_name="Company Setup",
        summary_what_checked=(
            "Company codes are present, unique, and used consistently"
        ),
        sort_order=1,
    ),
    "DG-QUIKMSTR": AreaDescription(
        item_id="DG-QUIKMSTR",
        area_name="Policies",
        summary_what_checked=(
            "Policy numbers meet the required format and use valid company codes"
        ),
        sort_order=2,
    ),
    "DG-ACCOUNTING": AreaDescription(
        item_id="DG-ACCOUNTING",
        area_name="Accounting",
        summary_what_checked=(
            "Company and plan assignments are unique and company codes are valid"
        ),
        sort_order=3,
    ),
    "DG-QUIKLIST": AreaDescription(
        item_id="DG-QUIKLIST",
        area_name="Group Billing",
        summary_what_checked=(
            "Group numbers, company codes, billing names, and billing defaults are valid"
        ),
        sort_order=4,
    ),
    "DG-QUIKDATE": AreaDescription(
        item_id="DG-QUIKDATE",
        area_name="Processing Dates",
        summary_what_checked=(
            "Billing dates use the previous month end and required defaults are correct"
        ),
        sort_order=5,
    ),
    "DG-PLANVALUES": AreaDescription(
        item_id="DG-PLANVALUES",
        area_name="Plan Values",
        summary_what_checked=(
            "Plans, mortality tables, classes, bands, states, and effective dates are valid"
        ),
        sort_order=6,
    ),
    "DG-QUIKPLAN": AreaDescription(
        item_id="DG-QUIKPLAN",
        area_name="Plan Setup",
        summary_what_checked=(
            "Plan codes, settings, payment and insurance periods, related setup "
            "references, and supporting rate and value records are valid"
        ),
        sort_order=7,
    ),
}


RULE_DESCRIPTIONS: dict[str, RuleDescription] = {
    "DG-QUIKCOMP-001": RuleDescription(
        rule_id="DG-QUIKCOMP-001",
        area_name="Company Setup",
        check_description="Company codes are present and are not duplicated.",
        required_value="A unique company code",
        record_strategy="company_code",
        problem_default="The company code is missing or duplicated in Company Setup.",
    ),
    "DG-QUIKCOMP-002": RuleDescription(
        rule_id="DG-QUIKCOMP-002",
        area_name="Company Setup",
        check_description="Every agent uses a company code that exists in Company Setup.",
        required_value="A valid company code",
        record_strategy="agent_number",
        problem_default="The agent company code was not found in Company Setup.",
    ),
    "DG-QUIKCOMP-003": RuleDescription(
        rule_id="DG-QUIKCOMP-003",
        area_name="Policies",
        check_description=(
            "The company code at the end of each policy number exists in Company Setup."
        ),
        required_value="A valid company code",
        record_strategy="policy_number",
        problem_default="The policy company code was not found in Company Setup.",
    ),
    "DG-QUIKMSTR-001": RuleDescription(
        rule_id="DG-QUIKMSTR-001",
        area_name="Policies",
        check_description="Policy numbers are between 4 and 11 characters after trimming.",
        required_value="A policy number 4 to 11 characters long",
        record_strategy="policy_number",
        problem_default="The policy number length is not within the required range.",
    ),
    "DG-QUIKACTG-001": RuleDescription(
        rule_id="DG-QUIKACTG-001",
        area_name="Accounting",
        check_description="Each company and plan combination appears only once in Accounting.",
        required_value="A unique company and plan combination",
        record_strategy="company_plan",
        problem_default="The company and plan combination is duplicated in Accounting.",
    ),
    "DG-QUIKACTG-002": RuleDescription(
        rule_id="DG-QUIKACTG-002",
        area_name="Accounting",
        check_description="Every accounting company code exists in Company Setup.",
        required_value="A valid company code",
        record_strategy="company_plan",
        problem_default="The accounting company code was not found in Company Setup.",
    ),
    "DG-QUIKLIST-001": RuleDescription(
        rule_id="DG-QUIKLIST-001",
        area_name="Group Billing",
        check_description="Every group number is unique.",
        required_value="A unique group number",
        record_strategy="group_number",
        problem_default="The group number is missing or duplicated.",
    ),
    "DG-QUIKLIST-002": RuleDescription(
        rule_id="DG-QUIKLIST-002",
        area_name="Group Billing",
        check_description="Every group uses a valid company code.",
        required_value="A valid company code",
        record_strategy="group_number",
        problem_default="The group company code was not found in Company Setup.",
    ),
    "DG-QUIKLIST-003": RuleDescription(
        rule_id="DG-QUIKLIST-003",
        area_name="Group Billing",
        check_description="Every group has a billing name.",
        required_value="A billing name",
        record_strategy="group_number",
        problem_default="The group billing name is blank.",
    ),
    "DG-QUIKLIST-004": RuleDescription(
        rule_id="DG-QUIKLIST-004",
        area_name="Group Billing",
        check_description="Billing sort is set to N.",
        required_value="N",
        record_strategy="group_number",
        problem_default="The billing sort setting is incorrect.",
    ),
    "DG-QUIKLIST-005": RuleDescription(
        rule_id="DG-QUIKLIST-005",
        area_name="Group Billing",
        check_description="The life lapse value is set to 0.",
        required_value="0",
        record_strategy="group_number",
        problem_default="The life lapse value is incorrect.",
    ),
    "DG-QUIKLIST-006": RuleDescription(
        rule_id="DG-QUIKLIST-006",
        area_name="Group Billing",
        check_description="The health/accident lapse value is set to 0.",
        required_value="0",
        record_strategy="group_number",
        problem_default="The health/accident lapse value is incorrect.",
    ),
    "DG-QUIKLIST-007": RuleDescription(
        rule_id="DG-QUIKLIST-007",
        area_name="Group Billing",
        check_description="Group status is set to A.",
        required_value="A",
        record_strategy="group_number",
        problem_default="The group status setting is incorrect.",
    ),
    "DG-QUIKLIST-008": RuleDescription(
        rule_id="DG-QUIKLIST-008",
        area_name="Group Billing",
        check_description="Billing day is set to 0.",
        required_value="0",
        record_strategy="group_number",
        problem_default="The billing day setting is incorrect.",
    ),
    "DG-QUIKLIST-009": RuleDescription(
        rule_id="DG-QUIKLIST-009",
        area_name="Group Billing",
        check_description="Billing mode is set to 0.",
        required_value="0",
        record_strategy="group_number",
        problem_default="The billing mode setting is incorrect.",
    ),
    "DG-QUIKDATE-001": RuleDescription(
        rule_id="DG-QUIKDATE-001",
        area_name="Processing Dates",
        check_description="The PAC billing date is set to the end of the previous month.",
        required_value="The end of the previous month",
        record_strategy="record_number",
        problem_default="The PAC billing date is not set to the end of the previous month.",
    ),
    "DG-QUIKDATE-002": RuleDescription(
        rule_id="DG-QUIKDATE-002",
        area_name="Processing Dates",
        check_description="The direct billing date is set to the end of the previous month.",
        required_value="The end of the previous month",
        record_strategy="record_number",
        problem_default="The direct billing date is not set to the end of the previous month.",
    ),
    "DG-QUIKDATE-003": RuleDescription(
        rule_id="DG-QUIKDATE-003",
        area_name="Processing Dates",
        check_description=(
            "The reinsurance billing date is set to the end of the previous month."
        ),
        required_value="The end of the previous month",
        record_strategy="record_number",
        problem_default=(
            "The reinsurance billing date is not set to the end of the previous month."
        ),
    ),
    "DG-QUIKDATE-004": RuleDescription(
        rule_id="DG-QUIKDATE-004",
        area_name="Processing Dates",
        check_description="The ACH file ID is set to 0.",
        required_value="0",
        record_strategy="record_number",
        problem_default="The ACH file ID is incorrect.",
    ),
    "DG-QUIKDATE-005": RuleDescription(
        rule_id="DG-QUIKDATE-005",
        area_name="Processing Dates",
        check_description="The secondary ACH file ID is set to A.",
        required_value="A",
        record_strategy="record_number",
        problem_default="The secondary ACH file ID is incorrect.",
    ),
    "DG-QUIKDATE-006": RuleDescription(
        rule_id="DG-QUIKDATE-006",
        area_name="Processing Dates",
        check_description="The escrow date is blank.",
        required_value="Blank",
        record_strategy="record_number",
        problem_default="The escrow date should be blank.",
    ),
    "DG-PLANVALUES-001": RuleDescription(
        rule_id="DG-PLANVALUES-001",
        area_name="Plan Values",
        check_description="The mortality table exists in Mortality Table Setup.",
        required_value="A mortality table defined in Mortality Table Setup",
        record_strategy="plan_detail",
        problem_default="The mortality table was not found in Mortality Table Setup.",
    ),
    "DG-PLANVALUES-002": RuleDescription(
        rule_id="DG-PLANVALUES-002",
        area_name="Plan Values",
        check_description="The ETI mortality table exists in Mortality Table Setup.",
        required_value="A mortality table defined in Mortality Table Setup",
        record_strategy="plan_detail",
        problem_default="The ETI mortality table was not found in Mortality Table Setup.",
    ),
    "DG-PLANVALUES-003": RuleDescription(
        rule_id="DG-PLANVALUES-003",
        area_name="Plan Values",
        check_description="The plan exists in Plan Setup.",
        required_value="A plan defined in Plan Setup",
        record_strategy="plan",
        problem_default="The plan was not found in Plan Setup.",
    ),
    "DG-PLANVALUES-004": RuleDescription(
        rule_id="DG-PLANVALUES-004",
        area_name="Plan Values",
        check_description="Gender is 0 or a valid gender code for the plan.",
        required_value="0 or a valid gender code",
        record_strategy="plan_detail",
        problem_default="The gender code is not 0 and is not defined for this plan.",
    ),
    "DG-PLANVALUES-005": RuleDescription(
        rule_id="DG-PLANVALUES-005",
        area_name="Plan Values",
        check_description="Underwriting class is 00 or a valid class for the plan.",
        required_value="00 or a valid underwriting class",
        record_strategy="plan_detail",
        problem_default=(
            "The underwriting class is not 00 and is not defined for this plan."
        ),
    ),
    "DG-PLANVALUES-006": RuleDescription(
        rule_id="DG-PLANVALUES-006",
        area_name="Plan Values",
        check_description="Band is 00 or a valid band for the plan.",
        required_value="00 or a valid band",
        record_strategy="plan_detail",
        problem_default="The band is not 00 and is not defined for this plan.",
    ),
    "DG-PLANVALUES-007": RuleDescription(
        rule_id="DG-PLANVALUES-007",
        area_name="Plan Values",
        check_description="Issue state is 00 or a valid United States state abbreviation.",
        required_value="A valid state abbreviation or 00",
        record_strategy="plan_detail",
        problem_default="The issue state is not 00 and is not a valid state abbreviation.",
    ),
    "DG-PLANVALUES-008": RuleDescription(
        rule_id="DG-PLANVALUES-008",
        area_name="Plan Values",
        check_description=(
            "The effective date is between January 1, 1900 and 12 months after the review date."
        ),
        required_value="A date within the approved range",
        record_strategy="plan_detail",
        problem_default="The effective date is outside the approved date range.",
    ),
    "DG-QUIKPLAN-001": RuleDescription(
        rule_id="DG-QUIKPLAN-001",
        area_name="Plan Setup",
        check_description="Every plan code contains exactly six characters.",
        required_value="A six-character plan code",
        record_strategy="plan",
        subsection="Plan Code and Basic Setup",
        problem_default="The plan code does not contain exactly six characters.",
    ),
    "DG-QUIKPLAN-002": RuleDescription(
        rule_id="DG-QUIKPLAN-002",
        area_name="Plan Setup",
        check_description=(
            "Plan codes contain only letters and numbers with no spaces or special characters."
        ),
        required_value="Six letters or numbers with no spaces or special characters",
        record_strategy="plan",
        subsection="Plan Code and Basic Setup",
        problem_default="The plan code contains a space or special character.",
    ),
    "DG-QUIKPLAN-003": RuleDescription(
        rule_id="DG-QUIKPLAN-003",
        area_name="Plan Setup",
        check_description=(
            "Plan codes do not end with suffixes reserved for paid-up additions."
        ),
        required_value="A plan code that does not end in PA, XP, XF, or XS",
        record_strategy="plan",
        subsection="Plan Code and Basic Setup",
        problem_default=(
            "The plan code ends with a suffix reserved for paid-up additions."
        ),
    ),
    "DG-QUIKPLAN-004": RuleDescription(
        rule_id="DG-QUIKPLAN-004",
        area_name="Plan Setup",
        check_description="The participating-plan setting is 0 or 1.",
        required_value="0 or 1",
        record_strategy="plan",
        subsection="Plan Code and Basic Setup",
        problem_default="The participating-plan setting is invalid.",
    ),
    "DG-QUIKPLAN-005": RuleDescription(
        rule_id="DG-QUIKPLAN-005",
        area_name="Plan Setup",
        check_description=(
            "Annuity plans use a valid annuity basis and non-annuity plans leave the basis blank."
        ),
        required_value="NONQ, QUAL, NQIA, QLIA, or TXBL for annuity plans; blank for others",
        record_strategy="plan",
        subsection="Plan Code and Basic Setup",
        problem_default="The annuity basis does not match the plan type.",
    ),
    "DG-QUIKPLAN-006": RuleDescription(
        rule_id="DG-QUIKPLAN-006",
        area_name="Plan Setup",
        check_description="The loan interest option is A or R.",
        required_value="A or R",
        record_strategy="plan",
        subsection="Plan Code and Basic Setup",
        problem_default="The loan interest option is invalid.",
    ),
    "DG-QUIKPLAN-007": RuleDescription(
        rule_id="DG-QUIKPLAN-007",
        area_name="Plan Setup",
        check_description="MYGA plans have a deposit interest value greater than zero.",
        required_value="A value greater than zero",
        record_strategy="plan",
        subsection="Plan-Type Rules",
        problem_default=(
            "This MYGA plan does not have a deposit interest value greater than zero."
        ),
    ),
    "DG-QUIKPLAN-008": RuleDescription(
        rule_id="DG-QUIKPLAN-008",
        area_name="Plan Setup",
        check_description=(
            "The low age is zero for the Age 1 row and is less than the high age."
        ),
        required_value="A low age below the high age, with zero used for the Age 1 row",
        record_strategy="plan",
        subsection="Payment, Insurance, and Age Rules",
        problem_default="The low age is not valid for this plan.",
    ),
    "DG-QUIKPLAN-009": RuleDescription(
        rule_id="DG-QUIKPLAN-009",
        area_name="Plan Setup",
        check_description="The renewal setting matches the plan type.",
        required_value="N for most plans; N or Y for plans beginning with 5",
        record_strategy="plan",
        subsection="Payment, Insurance, and Age Rules",
        problem_default="The renewal setting is invalid for this plan.",
    ),
    "DG-QUIKPLAN-010": RuleDescription(
        rule_id="DG-QUIKPLAN-010",
        area_name="Plan Setup",
        check_description=(
            "Payment years and payment age are not both zero for applicable plans."
        ),
        required_value="At least one value greater than zero",
        record_strategy="plan",
        subsection="Payment, Insurance, and Age Rules",
        problem_default="Both the payment years and payment age are zero.",
    ),
    "DG-QUIKPLAN-011": RuleDescription(
        rule_id="DG-QUIKPLAN-011",
        area_name="Plan Setup",
        check_description=(
            "Insurance years and insurance age are not both zero for applicable plans."
        ),
        required_value="At least one value greater than zero",
        record_strategy="plan",
        subsection="Payment, Insurance, and Age Rules",
        problem_default="Both the insurance years and insurance age are zero.",
    ),
    "DG-QUIKPLAN-012": RuleDescription(
        rule_id="DG-QUIKPLAN-012",
        area_name="Plan Setup",
        check_description="Single-premium plans use the required payment settings.",
        required_value="Single-premium settings",
        record_strategy="plan",
        subsection="Plan-Type Rules",
        problem_default="A single-premium plan does not use the required payment settings.",
    ),
    "DG-QUIKPLAN-013": RuleDescription(
        rule_id="DG-QUIKPLAN-013",
        area_name="Plan Setup",
        check_description="Payment age does not exceed 125.",
        required_value="125 or less",
        record_strategy="plan",
        subsection="Payment, Insurance, and Age Rules",
        problem_default="The payment age is greater than 125.",
    ),
    "DG-QUIKPLAN-014": RuleDescription(
        rule_id="DG-QUIKPLAN-014",
        area_name="Plan Setup",
        check_description="Insurance age does not exceed 125.",
        required_value="125 or less",
        record_strategy="plan",
        subsection="Payment, Insurance, and Age Rules",
        problem_default="The insurance age is greater than 125.",
    ),
    "DG-QUIKPLAN-015": RuleDescription(
        rule_id="DG-QUIKPLAN-015",
        area_name="Plan Setup",
        check_description="The initial value uses the approved default.",
        required_value="1000 unless an approved transformation applies",
        record_strategy="plan",
        subsection="Related Setup References",
        problem_default="The initial value differs from the expected default of 1000.",
    ),
    "DG-QUIKPLAN-016": RuleDescription(
        rule_id="DG-QUIKPLAN-016",
        area_name="Plan Setup",
        check_description=(
            "Commission IDs exist in Commission Setup when populated."
        ),
        required_value="A valid commission ID or blank",
        record_strategy="plan_detail",
        subsection="Related Setup References",
        problem_default="The commission ID was not found in Commission Setup.",
    ),
    "DG-QUIKPLAN-017": RuleDescription(
        rule_id="DG-QUIKPLAN-017",
        area_name="Plan Setup",
        check_description="Maximum units are not less than minimum units.",
        required_value="A value greater than or equal to the minimum units",
        record_strategy="plan",
        subsection="Related Setup References",
        problem_default="The maximum units are less than the minimum units.",
    ),
    "DG-QUIKPLAN-018": RuleDescription(
        rule_id="DG-QUIKPLAN-018",
        area_name="Plan Setup",
        check_description="The rounding rule is set to B.",
        required_value="B",
        record_strategy="plan",
        subsection="Related Setup References",
        problem_default="The rounding rule is not set to B.",
    ),
    "DG-QUIKPLAN-019": RuleDescription(
        rule_id="DG-QUIKPLAN-019",
        area_name="Plan Setup",
        check_description="The automatic nonforfeiture setting is set to 0.",
        required_value="0",
        record_strategy="plan",
        subsection="Related Setup References",
        problem_default="The automatic nonforfeiture setting is not set to 0.",
    ),
    "DG-QUIKPLAN-020": RuleDescription(
        rule_id="DG-QUIKPLAN-020",
        area_name="Plan Setup",
        check_description=(
            "The deficiency setting is N for alphabetic and 9-series plans."
        ),
        required_value="N",
        record_strategy="plan",
        subsection="Plan-Type Rules",
        problem_default="The deficiency setting must be N for this plan.",
    ),
    "DG-QUIKPLAN-021": RuleDescription(
        rule_id="DG-QUIKPLAN-021",
        area_name="Plan Setup",
        check_description=(
            "The new-business status contains a valid yes-or-no value."
        ),
        required_value="A valid yes-or-no value",
        record_strategy="plan",
        subsection="Related Setup References",
        problem_default="The new-business status is not a valid yes-or-no value.",
    ),
    "DG-QUIKPLAN-022": RuleDescription(
        rule_id="DG-QUIKPLAN-022",
        area_name="Plan Setup",
        check_description="Closed plans do not have the plan-value option enabled.",
        required_value="Plan-value option turned off",
        record_strategy="plan",
        subsection="Related Setup References",
        problem_default=(
            "This plan is closed to new business, but the plan-value option is still enabled."
        ),
    ),
    "DG-QUIKPLAN-023": RuleDescription(
        rule_id="DG-QUIKPLAN-023",
        area_name="Plan Setup",
        check_description="The lapse setting is set to 0.",
        required_value="0",
        record_strategy="plan",
        subsection="Related Setup References",
        problem_default="The lapse setting is not set to 0.",
    ),
    "DG-QUIKPLAN-024": RuleDescription(
        rule_id="DG-QUIKPLAN-024",
        area_name="Plan Setup",
        check_description="The NAIC line-of-business setting is set to N.",
        required_value="N",
        record_strategy="plan",
        subsection="Related Setup References",
        problem_default="The NAIC line-of-business setting is not set to N.",
    ),
    "DG-QUIKPLAN-025": RuleDescription(
        rule_id="DG-QUIKPLAN-025",
        area_name="Plan Setup",
        check_description=(
            "Plans that use variable gross premium setup have the required supporting records."
        ),
        required_value="A supporting record for the plan",
        record_strategy="plan_detail",
        subsection="Supporting Rate and Value Tables",
        problem_default="The plan was not found in a required gross premium table.",
    ),
    "DG-QUIKPLAN-026": RuleDescription(
        rule_id="DG-QUIKPLAN-026",
        area_name="Plan Setup",
        check_description=(
            "Plans that use variable death-benefit setup have the required supporting records."
        ),
        required_value="A supporting record for the plan",
        record_strategy="plan_detail",
        subsection="Supporting Rate and Value Tables",
        problem_default="The plan was not found in a required death-benefit table.",
    ),
    "DG-QUIKPLAN-027": RuleDescription(
        rule_id="DG-QUIKPLAN-027",
        area_name="Plan Setup",
        check_description=(
            "Traditional plans have the expected value and reserve tables."
        ),
        required_value="A supporting record for the plan",
        record_strategy="plan_detail",
        subsection="Supporting Rate and Value Tables",
        problem_default="The plan does not have a required value or reserve record.",
    ),
    "DG-QUIKPLAN-028": RuleDescription(
        rule_id="DG-QUIKPLAN-028",
        area_name="Plan Setup",
        check_description="Annuity plans have the expected annuity setup records.",
        required_value="A supporting record for the plan",
        record_strategy="plan_detail",
        subsection="Supporting Rate and Value Tables",
        problem_default="The annuity plan does not have a required annuity setup record.",
    ),
    "DG-QUIKPLAN-029": RuleDescription(
        rule_id="DG-QUIKPLAN-029",
        area_name="Plan Setup",
        check_description="Universal Life plans have a Universal Life interest record.",
        required_value="A Universal Life interest record",
        record_strategy="plan_detail",
        subsection="Plan-Type Rules",
        problem_default=(
            "The Universal Life plan was not found in Universal Life Interest Setup."
        ),
    ),
    "DG-QUIKPLAN-030": RuleDescription(
        rule_id="DG-QUIKPLAN-030",
        area_name="Plan Setup",
        check_description="MEDS plan flags match the plan type.",
        required_value="Enabled for MEDS plans and disabled for other plans",
        record_strategy="plan",
        subsection="Plan-Type Rules",
        problem_default="The MEDS plan flags do not match the plan type.",
    ),
    "DG-QUIKPLAN-031": RuleDescription(
        rule_id="DG-QUIKPLAN-031",
        area_name="Plan Setup",
        check_description=(
            "Every plan code used in approved rate and key tables exists in Plan Setup."
        ),
        required_value="A plan defined in Plan Setup",
        record_strategy="plan_detail",
        subsection="Supporting Rate and Value Tables",
        problem_default="The plan code was not found in Plan Setup.",
    ),
    "DG-QUIKPLAN-032": RuleDescription(
        rule_id="DG-QUIKPLAN-032",
        area_name="Plan Setup",
        check_description=(
            "Company codes used in approved tables exist in Company Setup."
        ),
        required_value="A valid company code",
        record_strategy="company_code",
        subsection="Supporting Rate and Value Tables",
        problem_default="The company code was not found in Company Setup.",
    ),
    "DG-QUIKPLAN-033": RuleDescription(
        rule_id="DG-QUIKPLAN-033",
        area_name="Plan Setup",
        check_description="Conversion dates fall within the approved date range.",
        required_value="A date from January 1, 1900 through the calculated maximum date",
        record_strategy="plan",
        subsection="Conversion Date Warnings",
        problem_default="The date is outside the approved conversion date range.",
    ),
}


def get_area(item_id: str) -> AreaDescription:
    if item_id in AREA_DESCRIPTIONS:
        return AREA_DESCRIPTIONS[item_id]
    return AreaDescription(
        item_id=item_id or "UNKNOWN",
        area_name=item_id or "Other",
        summary_what_checked="Configured governance checks for this area",
        sort_order=99,
    )


def get_rule_description(rule_id: str, *, business_name: str = "") -> RuleDescription:
    if rule_id in RULE_DESCRIPTIONS:
        return RULE_DESCRIPTIONS[rule_id]
    _LOG.warning(
        "Business description mapping missing for rule %s; using fallback.",
        rule_id,
    )
    area = "Other"
    if rule_id.startswith("DG-"):
        # Best-effort area from prefix
        parts = rule_id.rsplit("-", 1)
        if len(parts) == 2 and parts[0] in AREA_DESCRIPTIONS:
            area = AREA_DESCRIPTIONS[parts[0]].area_name
        elif rule_id.startswith("DG-QUIKACTG") or rule_id.startswith("DG-ACCOUNTING"):
            area = "Accounting"
    return RuleDescription(
        rule_id=rule_id,
        area_name=area,
        check_description=business_name or rule_id,
        required_value="The value required by this check",
        record_strategy="key_value",
        problem_default=business_name or "This check found a problem.",
    )


def friendly_table_name(logical_or_physical: str) -> str:
    if not logical_or_physical:
        return ""
    key = logical_or_physical.strip()
    if key in FRIENDLY_TABLE_NAMES:
        return FRIENDLY_TABLE_NAMES[key]
    # Multi-table strings from ERROR findings
    if "," in key:
        parts = [friendly_table_name(p.strip()) for p in key.split(",")]
        return ", ".join(p for p in parts if p)
    return key
