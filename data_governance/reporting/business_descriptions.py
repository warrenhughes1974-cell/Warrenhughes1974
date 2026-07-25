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
    "QuikMstr": "Policy Master",
    "QuikClnt": "Clients",
    "QuikClid": "Policy Relationships",
    "QuikRidr": "Riders",
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
        area_name="Policy Master",
        summary_what_checked=(
            "Policy numbers are unique and valid length; status and dates are present "
            "and consistent; billing setup and bank-draft accounts are correct; issue "
            "state, country, and class use approved defaults; group and client references "
            "exist when populated; beneficiary IDs are blank"
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
    "DG-QUIKCLNT": AreaDescription(
        item_id="DG-QUIKCLNT",
        area_name="Client Setup",
        summary_what_checked=(
            "Client IDs are unique; names, type, tax-ID type, sex, and language use "
            "approved values and defaults; contact and date-of-birth information is valid"
        ),
        sort_order=8,
    ),
    "DG-QUIKCLID": AreaDescription(
        item_id="DG-QUIKCLID",
        area_name="Policy Relationships",
        summary_what_checked=(
            "Relationship rows reference valid clients and policies, use approved "
            "relationship codes, and align insured phases with rider setup"
        ),
        sort_order=9,
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
        area_name="Policy Master",
        check_description=(
            "Policy numbers are unique and are between 4 and 11 characters after trimming."
        ),
        required_value="A unique policy number 4 to 11 characters long",
        record_strategy="policy_number",
        problem_default=(
            "The policy number is missing, duplicated, or not within the required length."
        ),
    ),
    "DG-QUIKMSTR-002": RuleDescription(
        rule_id="DG-QUIKMSTR-002",
        area_name="Policy Master",
        check_description="Every policy has a valid policy status code.",
        required_value="A populated approved policy status",
        record_strategy="policy_number",
        problem_default="The policy status is missing or not approved.",
    ),
    "DG-QUIKMSTR-003": RuleDescription(
        rule_id="DG-QUIKMSTR-003",
        area_name="Policy Master",
        check_description="Every policy has a valid status date.",
        required_value="A status date within the approved range",
        record_strategy="policy_number",
        problem_default="The status date is missing, invalid, or out of range.",
    ),
    "DG-QUIKMSTR-004": RuleDescription(
        rule_id="DG-QUIKMSTR-004",
        area_name="Policy Master",
        check_description="Every policy has a valid issue date.",
        required_value="An issue date within the approved range",
        record_strategy="policy_number",
        problem_default="The issue date is missing, invalid, or out of range.",
    ),
    "DG-QUIKMSTR-005": RuleDescription(
        rule_id="DG-QUIKMSTR-005",
        area_name="Policy Master",
        check_description="The paid-to date is not before the issue date.",
        required_value="A paid-to date on or after the issue date",
        record_strategy="policy_number",
        problem_default="The paid-to date is before the issue date or is missing.",
    ),
    "DG-QUIKMSTR-006": RuleDescription(
        rule_id="DG-QUIKMSTR-006",
        area_name="Policy Master",
        check_description="The bill-to date is not before the issue date.",
        required_value="A bill-to date on or after the issue date",
        record_strategy="policy_number",
        problem_default="The bill-to date is before the issue date or is missing.",
    ),
    "DG-QUIKMSTR-007": RuleDescription(
        rule_id="DG-QUIKMSTR-007",
        area_name="Policy Master",
        check_description="The bill-to date is not before the paid-to date.",
        required_value="A bill-to date on or after the paid-to date",
        record_strategy="policy_number",
        problem_default="The bill-to date is before the paid-to date.",
    ),
    "DG-QUIKMSTR-008": RuleDescription(
        rule_id="DG-QUIKMSTR-008",
        area_name="Policy Master",
        check_description="The nonforfeiture option defaults to zero when blank.",
        required_value="0 or an approved nonforfeiture option",
        record_strategy="policy_number",
        problem_default="The nonforfeiture option is blank or not approved.",
    ),
    "DG-QUIKMSTR-009": RuleDescription(
        rule_id="DG-QUIKMSTR-009",
        area_name="Policy Master",
        check_description="Dividend option validation is deferred pending business direction.",
        required_value="Deferred — no check applied",
        record_strategy="policy_number",
        problem_default="Dividend option validation is deferred.",
    ),
    "DG-QUIKMSTR-010": RuleDescription(
        rule_id="DG-QUIKMSTR-010",
        area_name="Policy Master",
        check_description="Every policy has a valid billing form code.",
        required_value="A populated approved billing form",
        record_strategy="policy_number",
        problem_default="The billing form is missing or not approved.",
    ),
    "DG-QUIKMSTR-011": RuleDescription(
        rule_id="DG-QUIKMSTR-011",
        area_name="Policy Master",
        check_description=(
            "Billing day is valid or can be derived from the issue date when blank."
        ),
        required_value="A billing day between 1 and 31",
        record_strategy="policy_number",
        problem_default="The billing day is invalid or could not be derived.",
    ),
    "DG-QUIKMSTR-012": RuleDescription(
        rule_id="DG-QUIKMSTR-012",
        area_name="Policy Master",
        check_description="Bank-draft policies have a bank account number.",
        required_value="A populated bank account when billing form is bank draft",
        record_strategy="policy_number",
        problem_default="Bank draft billing is used but the bank account is missing.",
    ),
    "DG-QUIKMSTR-013": RuleDescription(
        rule_id="DG-QUIKMSTR-013",
        area_name="Policy Master",
        check_description="Every policy has a valid payment mode.",
        required_value="A populated approved payment mode",
        record_strategy="policy_number",
        problem_default="The payment mode is missing or not approved.",
    ),
    "DG-QUIKMSTR-014": RuleDescription(
        rule_id="DG-QUIKMSTR-014",
        area_name="Policy Master",
        check_description="Every policy has a valid United States issue state.",
        required_value="An approved US state abbreviation",
        record_strategy="policy_number",
        problem_default="The issue state is missing or not approved.",
    ),
    "DG-QUIKMSTR-015": RuleDescription(
        rule_id="DG-QUIKMSTR-015",
        area_name="Policy Master",
        check_description="Populated group numbers exist in Group Billing Setup.",
        required_value="A group number defined in Group Billing when populated",
        record_strategy="policy_number",
        problem_default="The group number was not found in Group Billing Setup.",
    ),
    "DG-QUIKMSTR-016": RuleDescription(
        rule_id="DG-QUIKMSTR-016",
        area_name="Policy Master",
        check_description="Populated primary insured client IDs exist in Client Setup.",
        required_value="A client ID defined in Client Setup when populated",
        record_strategy="policy_number",
        problem_default="The primary insured client was not found in Client Setup.",
    ),
    "DG-QUIKMSTR-017": RuleDescription(
        rule_id="DG-QUIKMSTR-017",
        area_name="Policy Master",
        check_description="Populated owner client IDs exist in Client Setup.",
        required_value="A client ID defined in Client Setup when populated",
        record_strategy="policy_number",
        problem_default="The owner client was not found in Client Setup.",
    ),
    "DG-QUIKMSTR-018": RuleDescription(
        rule_id="DG-QUIKMSTR-018",
        area_name="Policy Master",
        check_description="Populated assignee client IDs exist in Client Setup.",
        required_value="A client ID defined in Client Setup when populated",
        record_strategy="policy_number",
        problem_default="The assignee client was not found in Client Setup.",
    ),
    "DG-QUIKMSTR-019": RuleDescription(
        rule_id="DG-QUIKMSTR-019",
        area_name="Policy Master",
        check_description="Populated payer client IDs exist in Client Setup.",
        required_value="A client ID defined in Client Setup when populated",
        record_strategy="policy_number",
        problem_default="The payer client was not found in Client Setup.",
    ),
    "DG-QUIKMSTR-020": RuleDescription(
        rule_id="DG-QUIKMSTR-020",
        area_name="Policy Master",
        check_description="Populated owner-company client IDs exist in Client Setup.",
        required_value="A client ID defined in Client Setup when populated",
        record_strategy="policy_number",
        problem_default="The owner-company client was not found in Client Setup.",
    ),
    "DG-QUIKMSTR-021": RuleDescription(
        rule_id="DG-QUIKMSTR-021",
        area_name="Policy Master",
        check_description="Primary beneficiary IDs are blank on Policy Master.",
        required_value="Blank",
        record_strategy="policy_number",
        problem_default="The primary beneficiary ID should be blank.",
    ),
    "DG-QUIKMSTR-022": RuleDescription(
        rule_id="DG-QUIKMSTR-022",
        area_name="Policy Master",
        check_description="Contingent beneficiary IDs are blank on Policy Master.",
        required_value="Blank",
        record_strategy="policy_number",
        problem_default="The contingent beneficiary ID should be blank.",
    ),
    "DG-QUIKMSTR-023": RuleDescription(
        rule_id="DG-QUIKMSTR-023",
        area_name="Policy Master",
        check_description="The application date is not after the issue date.",
        required_value="An application date on or before the issue date",
        record_strategy="policy_number",
        problem_default="The application date is after the issue date.",
    ),
    "DG-QUIKMSTR-024": RuleDescription(
        rule_id="DG-QUIKMSTR-024",
        area_name="Policy Master",
        check_description="Issue country defaults to 0000 when blank.",
        required_value="0000 or an approved country code",
        record_strategy="policy_number",
        problem_default="The issue country is blank or not approved.",
    ),
    "DG-QUIKMSTR-025": RuleDescription(
        rule_id="DG-QUIKMSTR-025",
        area_name="Policy Master",
        check_description=(
            "Residence state validation is deferred pending business direction."
        ),
        required_value="Deferred — no check applied",
        record_strategy="policy_number",
        problem_default="Residence state validation is deferred.",
    ),
    "DG-QUIKMSTR-027": RuleDescription(
        rule_id="DG-QUIKMSTR-027",
        area_name="Policy Master",
        check_description=(
            "A terminated policy carries no coverage that is still in force."
        ),
        required_value="Every coverage terminated when the policy is terminated",
        record_strategy="policy_number",
        problem_default="The policy is terminated but a coverage is still in force.",
    ),
    "DG-QUIKMSTR-028": RuleDescription(
        rule_id="DG-QUIKMSTR-028",
        area_name="Policy Master",
        check_description=(
            "On an extended term or reduced paid-up policy, the base coverage carries the "
            "same status as the policy."
        ),
        required_value="Phase 1 coverage status equals the policy status",
        record_strategy="policy_number",
        problem_default="The base coverage status does not match the policy status.",
    ),
    "DG-QUIKMSTR-029": RuleDescription(
        rule_id="DG-QUIKMSTR-029",
        area_name="Policy Master",
        check_description=(
            "Coverages beyond the base are normally terminated on an extended term or "
            "reduced paid-up policy. Any still in force are listed for source review."
        ),
        required_value="Other coverages terminated, or confirmed against the source system",
        record_strategy="policy_number",
        problem_default=(
            "A coverage beyond the base is still in force on a nonforfeiture policy."
        ),
    ),
    "DG-QUIKMSTR-030": RuleDescription(
        rule_id="DG-QUIKMSTR-030",
        area_name="Policy Master",
        check_description="An active policy has at least one coverage still in force.",
        required_value="At least one in-force coverage on an active policy",
        record_strategy="policy_number",
        problem_default="The policy is active but every coverage is terminated.",
    ),
    "DG-QUIKMSTR-031": RuleDescription(
        rule_id="DG-QUIKMSTR-031",
        area_name="Policy Master",
        check_description=(
            "The nonforfeiture election agrees with the policy status. Disagreements are "
            "listed for source review rather than corrected."
        ),
        required_value="Election 2 for extended term, 3 for reduced paid-up",
        record_strategy="policy_number",
        problem_default=(
            "The nonforfeiture election does not agree with the policy status."
        ),
    ),
    "DG-QUIKMSTR-032": RuleDescription(
        rule_id="DG-QUIKMSTR-032",
        area_name="Policy Master",
        check_description=(
            "Extended term and reduced paid-up policies carry a complete and consistent "
            "field set: pay-up date, attained age, blank save fields, zero premium on "
            "extended term, and terminated paid-up additions."
        ),
        required_value="Complete nonforfeiture field set",
        record_strategy="policy_number",
        problem_default="A nonforfeiture field is missing or inconsistent.",
    ),
    "DG-QUIKMSTR-026": RuleDescription(
        rule_id="DG-QUIKMSTR-026",
        area_name="Policy Master",
        check_description="Issue class defaults to 00 when blank.",
        required_value="00 or an approved issue class",
        record_strategy="policy_number",
        problem_default="The issue class is blank or not approved.",
    ),
    "DG-QUIKCLNT-001": RuleDescription(
        rule_id="DG-QUIKCLNT-001",
        area_name="Client Setup",
        check_description="Client IDs are present and are not duplicated.",
        required_value="A unique client ID",
        record_strategy="key_value",
        problem_default="The client ID is missing or duplicated.",
    ),
    "DG-QUIKCLNT-002": RuleDescription(
        rule_id="DG-QUIKCLNT-002",
        area_name="Client Setup",
        check_description="Client type defaults to Individual when blank.",
        required_value="I or an approved client type",
        record_strategy="key_value",
        problem_default="The client type is blank or not approved.",
    ),
    "DG-QUIKCLNT-003": RuleDescription(
        rule_id="DG-QUIKCLNT-003",
        area_name="Client Setup",
        check_description="Tax ID type defaults to S when blank.",
        required_value="S or an approved tax ID type",
        record_strategy="key_value",
        problem_default="The tax ID type is blank or not approved.",
    ),
    "DG-QUIKCLNT-004": RuleDescription(
        rule_id="DG-QUIKCLNT-004",
        area_name="Client Setup",
        check_description="Individual clients have a last name.",
        required_value="A populated last name for individual clients",
        record_strategy="key_value",
        problem_default="The last name is missing for an individual client.",
    ),
    "DG-QUIKCLNT-005": RuleDescription(
        rule_id="DG-QUIKCLNT-005",
        area_name="Client Setup",
        check_description="Clients have usable name or mailing-address information.",
        required_value="At least one name or mailing field populated",
        record_strategy="key_value",
        problem_default="No usable name or mailing information was found.",
    ),
    "DG-QUIKCLNT-006": RuleDescription(
        rule_id="DG-QUIKCLNT-006",
        area_name="Client Setup",
        check_description="Dates of birth are valid when populated.",
        required_value="A valid date of birth on or after January 1, 1900",
        record_strategy="key_value",
        problem_default="The date of birth is missing, invalid, or out of range.",
    ),
    "DG-QUIKCLNT-007": RuleDescription(
        rule_id="DG-QUIKCLNT-007",
        area_name="Client Setup",
        check_description="Individual clients have sex code M or F.",
        required_value="M or F for individual clients",
        record_strategy="key_value",
        problem_default="The sex code is missing or not M or F.",
    ),
    "DG-QUIKCLNT-008": RuleDescription(
        rule_id="DG-QUIKCLNT-008",
        area_name="Client Setup",
        check_description="Language defaults to English when blank.",
        required_value="E or an approved language code",
        record_strategy="key_value",
        problem_default="The language is blank or not approved.",
    ),
    "DG-QUIKCLID-001": RuleDescription(
        rule_id="DG-QUIKCLID-001",
        area_name="Policy Relationships",
        check_description="Every relationship client ID exists in Client Setup.",
        required_value="A client ID defined in Client Setup",
        record_strategy="key_value",
        problem_default="The relationship client was not found in Client Setup.",
    ),
    "DG-QUIKCLID-002": RuleDescription(
        rule_id="DG-QUIKCLID-002",
        area_name="Policy Relationships",
        check_description="Every relationship policy number exists in Policy Master.",
        required_value="A policy number defined in Policy Master",
        record_strategy="key_value",
        problem_default="The relationship policy was not found in Policy Master.",
    ),
    "DG-QUIKCLID-003": RuleDescription(
        rule_id="DG-QUIKCLID-003",
        area_name="Policy Relationships",
        check_description="Nonzero relationship phases exist in Rider Setup.",
        required_value="A matching rider when phase is not zero",
        record_strategy="key_value",
        problem_default="No matching rider was found for the relationship phase.",
    ),
    "DG-QUIKCLID-004": RuleDescription(
        rule_id="DG-QUIKCLID-004",
        area_name="Policy Relationships",
        check_description="Non-insured relationships use phase zero.",
        required_value="Phase 0 for non-insured relationships",
        record_strategy="key_value",
        problem_default="A non-insured relationship uses a nonzero phase.",
    ),
    "DG-QUIKCLID-005": RuleDescription(
        rule_id="DG-QUIKCLID-005",
        area_name="Policy Relationships",
        check_description="Insured relationships match a rider on the policy.",
        required_value="Exactly one rider match for insured relationships",
        record_strategy="key_value",
        problem_default="The insured relationship does not match a rider.",
    ),
    "DG-QUIKCLID-006": RuleDescription(
        rule_id="DG-QUIKCLID-006",
        area_name="Policy Relationships",
        check_description="Every relationship uses an approved relationship code.",
        required_value="A populated approved relationship code",
        record_strategy="key_value",
        problem_default="The relationship code is missing or not approved.",
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
        check_description=(
            "When a mortality table is entered, it exists in Mortality Table Setup. "
            "Blank mortality tables are allowed."
        ),
        required_value="A mortality table defined in Mortality Table Setup",
        record_strategy="plan_detail",
        problem_default="The mortality table was not found in Mortality Table Setup.",
    ),
    "DG-PLANVALUES-002": RuleDescription(
        rule_id="DG-PLANVALUES-002",
        area_name="Plan Values",
        check_description=(
            "When an ETI mortality table is entered, it exists in Mortality Table Setup. "
            "Blank ETI mortality tables are allowed."
        ),
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
            "The plan issue-age range is readable and the low age is less than the high age."
        ),
        required_value="A readable low age below the high age (low age may be greater than zero)",
        record_strategy="plan",
        subsection="Payment, Insurance, and Age Rules",
        problem_default="The issue-age range is not valid for this plan.",
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
        check_description="The NAIC line-of-business setting is set to NAPLAN.",
        required_value="NAPLAN",
        record_strategy="plan",
        subsection="Related Setup References",
        problem_default="The NAIC line-of-business setting is not set to NAPLAN.",
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
            "Plans with varying death-benefit schedules (VARDB 1, 2, or 3) have the "
            "required supporting records. Level (VARDB 0) and not-on-file (VARDB 4) skip."
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
        check_description=(
            "Annuity plans have interest and expense setup, plus guarantee or "
            "information setup (QuikAing or QuikAinf)."
        ),
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
