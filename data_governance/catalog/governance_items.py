"""Governance item and rule catalog metadata."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class GovernanceItem:
    item_id: str
    item_number: int
    name: str
    description: str


@dataclass(frozen=True)
class RuleDefinition:
    rule_id: str
    governance_item_id: str
    technical_name: str
    business_name: str
    purpose: str
    source_tables: tuple[str, ...]
    source_fields: tuple[str, ...]
    business_rule: str
    severity: str
    failure_conditions: tuple[str, ...]
    implementation_status: str = "Implemented"


GOVERNANCE_ITEM_QUIKCOMP = GovernanceItem(
    item_id="DG-QUIKCOMP",
    item_number=1,
    name="QuikComp Company Code Integrity",
    description=(
        "Ensure QuikComp company codes are unique and that agent and policy "
        "company codes reference a valid QuikComp company code."
    ),
)

RULE_DG_QUIKCOMP_001 = RuleDefinition(
    rule_id="DG-QUIKCOMP-001",
    governance_item_id="DG-QUIKCOMP",
    technical_name="Unique Company Code",
    business_name="Unique QuikComp Company Code",
    purpose="Ensure each company code appears only once in QuikComp.",
    source_tables=("QuikComp",),
    source_fields=("MCOMP",),
    business_rule=(
        "After standard DBF character normalization, each nonblank MCOMP "
        "value must occur exactly once in QuikComp. Blank or null MCOMP fails."
    ),
    severity="Critical",
    failure_conditions=(
        "The same normalized MCOMP appears on more than one QuikComp record.",
        "MCOMP is blank or null.",
    ),
)

RULE_DG_QUIKCOMP_002 = RuleDefinition(
    rule_id="DG-QUIKCOMP-002",
    governance_item_id="DG-QUIKCOMP",
    technical_name="Agent Company Code Must Exist",
    business_name="Agent Company Code Must Exist in QuikComp",
    purpose="Ensure every company code assigned to an agent is defined in QuikComp.",
    source_tables=("QuikAgts", "QuikComp"),
    source_fields=("QuikAgts.MCOMP", "QuikComp.MCOMP", "QuikAgts.MAGENT", "QuikAgts.MAGTNAME"),
    business_rule=(
        "Each distinct nonblank normalized QuikAgts.MCOMP value must match "
        "exactly one normalized QuikComp.MCOMP value."
    ),
    severity="Critical",
    failure_conditions=(
        "QuikAgts.MCOMP is blank or null for an agent record.",
        "QuikAgts.MCOMP does not exist in QuikComp.",
        "The matching QuikComp company code is duplicated.",
    ),
)

RULE_DG_QUIKCOMP_003 = RuleDefinition(
    rule_id="DG-QUIKCOMP-003",
    governance_item_id="DG-QUIKCOMP",
    technical_name="Policy Company Code Must Exist",
    business_name="Policy Number Company Code Must Exist in QuikComp",
    purpose=(
        "Ensure the company code represented by the final character of each "
        "policy number exists in QuikComp."
    ),
    source_tables=("QuikMstr", "QuikComp"),
    source_fields=("QuikMstr.MPOLICY", "QuikComp.MCOMP"),
    business_rule=(
        "Business rule (supplied): the final non-space character of MPOLICY "
        "represents the policy company code. That code must match exactly one "
        "normalized QuikComp.MCOMP value. Not represented as a QLAdmin manual rule."
    ),
    severity="Critical",
    failure_conditions=(
        "MPOLICY is blank or null.",
        "A company code cannot be derived from MPOLICY.",
        "The derived company code does not exist in QuikComp.",
        "The matching QuikComp company code is duplicated.",
    ),
)

GOVERNANCE_ITEM_QUIKMSTR = GovernanceItem(
    item_id="DG-QUIKMSTR",
    item_number=2,
    name="QuikMstr Policy Number Integrity",
    description=(
        "Ensure policy numbers stored in QuikMstr meet required format rules, "
        "starting with acceptable character length."
    ),
)

RULE_DG_QUIKMSTR_001 = RuleDefinition(
    rule_id="DG-QUIKMSTR-001",
    governance_item_id="DG-QUIKMSTR",
    technical_name="Validate QuikMstr Policy Number Length",
    business_name="Policy Number Must Contain 4 to 11 Characters",
    purpose="Ensure every policy number stored in QuikMstr contains an acceptable number of characters.",
    source_tables=("QuikMstr",),
    source_fields=("MPOLICY",),
    business_rule=(
        "After safely handling nulls and removing only leading/trailing DBF padding, "
        "MPOLICY must contain between 4 and 11 characters (inclusive). Internal spaces "
        "are retained and counted. Policy numbers are never corrected by this rule."
    ),
    severity="Critical",
    failure_conditions=(
        "MPOLICY is null.",
        "MPOLICY is blank after DBF padding is removed.",
        "Normalized policy number contains fewer than 4 characters.",
        "Normalized policy number contains more than 11 characters.",
    ),
)

GOVERNANCE_ITEM_ACCOUNTING = GovernanceItem(
    item_id="DG-ACCOUNTING",
    item_number=3,
    name="Accounting Company and Account Integrity",
    description=(
        "Ensure QuikActg accounting assignment rows are unique by company and plan, "
        "and that QuikActg company codes exist in QuikComp. QuikChrt is a related "
        "chart-of-accounts table (MCOMP + MACCOUNT) reserved for future rules."
    ),
)

RULE_DG_QUIKACTG_001 = RuleDefinition(
    rule_id="DG-QUIKACTG-001",
    governance_item_id="DG-ACCOUNTING",
    technical_name="Validate Unique QuikActg Company and Account Key",
    business_name="Company and Account Number Combination Must Be Unique",
    purpose=(
        "Ensure QuikActg does not contain duplicate accounting assignment records "
        "for the same company and plan (verified composite key MCOMP + MPLAN)."
    ),
    source_tables=("QuikActg",),
    source_fields=("MCOMP", "MPLAN"),
    business_rule=(
        "Supplied business rule: each normalized company-and-plan combination must "
        "occur at most once. Verified physical fields: MCOMP C(1) + MPLAN C(6). "
        "QuikActg has no MACCOUNT column; QuikChrt uses MCOMP+MACCOUNT for COA. "
        "Multiple plans per company are valid; the same plan under different "
        "companies is valid. Leading zeros in MPLAN are preserved."
    ),
    severity="Critical",
    failure_conditions=(
        "Same normalized MCOMP + MPLAN occurs more than once.",
        "MCOMP is null or blank after trim.",
        "MPLAN is null or blank after trim.",
    ),
)

RULE_DG_QUIKACTG_002 = RuleDefinition(
    rule_id="DG-QUIKACTG-002",
    governance_item_id="DG-ACCOUNTING",
    technical_name="Validate QuikActg Company Reference",
    business_name="QuikActg Company Code Must Exist in QuikComp",
    purpose="Ensure every company code used by QuikActg is defined once in QuikComp.",
    source_tables=("QuikActg", "QuikComp"),
    source_fields=("QuikActg.MCOMP", "QuikComp.MCOMP", "QuikActg.MPLAN"),
    business_rule=(
        "Every distinct nonblank normalized QuikActg.MCOMP must match exactly one "
        "normalized QuikComp.MCOMP. Reuses shared QuikComp company-code index / "
        "normalization from Item 1."
    ),
    severity="Critical",
    failure_conditions=(
        "QuikActg.MCOMP is null or blank.",
        "Normalized company code does not exist in QuikComp.",
        "Matching QuikComp company code is duplicated.",
    ),
)

GOVERNANCE_ITEM_QUIKLIST = GovernanceItem(
    item_id="DG-QUIKLIST",
    item_number=4,
    name="QuikList Group Billing Integrity",
    description=(
        "Ensure QuikList group bill rows have unique group numbers, valid company "
        "codes, populated billing names, and business-supplied default values for "
        "sort, lapse days, status, bill day, and bill mode."
    ),
)

RULE_DG_QUIKLIST_001 = RuleDefinition(
    rule_id="DG-QUIKLIST-001",
    governance_item_id="DG-QUIKLIST",
    technical_name="Validate Unique QuikList Group Number",
    business_name="Group Number Must Be Unique",
    purpose="Ensure each group number appears only once in QuikList.",
    source_tables=("QuikList",),
    source_fields=("MGROUP",),
    business_rule=(
        "After standard DBF character normalization, each nonblank MGROUP value "
        "must occur exactly once in QuikList. MGROUP is never converted to numeric; "
        "leading zeros are preserved."
    ),
    severity="Critical",
    failure_conditions=(
        "The same normalized MGROUP occurs more than once.",
        "MGROUP is null.",
        "MGROUP is blank after normalization.",
    ),
)

RULE_DG_QUIKLIST_002 = RuleDefinition(
    rule_id="DG-QUIKLIST-002",
    governance_item_id="DG-QUIKLIST",
    technical_name="Validate QuikList Company Reference",
    business_name="QuikList Company Code Must Exist in QuikComp",
    purpose="Ensure every company code assigned to a QuikList group is defined in QuikComp.",
    source_tables=("QuikList", "QuikComp"),
    source_fields=("QuikList.MCOMP", "QuikComp.MCOMP", "QuikList.MGROUP"),
    business_rule=(
        "Every nonblank normalized QuikList.MCOMP must match exactly one normalized "
        "QuikComp.MCOMP. Reuses shared QuikComp company-code index / normalization."
    ),
    severity="Critical",
    failure_conditions=(
        "QuikList.MCOMP is null or blank.",
        "QuikList.MCOMP does not exist in QuikComp.",
        "The matching QuikComp company code is duplicated.",
    ),
)

RULE_DG_QUIKLIST_003 = RuleDefinition(
    rule_id="DG-QUIKLIST-003",
    governance_item_id="DG-QUIKLIST",
    technical_name="Validate Required QuikList Billing Name",
    business_name="Group Billing Name Must Be Populated",
    purpose="Ensure every QuikList group has a billing name.",
    source_tables=("QuikList",),
    source_fields=("MBILLNAME", "MGROUP"),
    business_rule=(
        "MBILLNAME must contain a meaningful nonblank value after DBF padding is "
        "removed. Billing names are not required to be unique and are never derived "
        "from another field."
    ),
    severity="Critical",
    failure_conditions=(
        "MBILLNAME is null.",
        "MBILLNAME is blank or whitespace-only after trim.",
    ),
)

RULE_DG_QUIKLIST_004 = RuleDefinition(
    rule_id="DG-QUIKLIST-004",
    governance_item_id="DG-QUIKLIST",
    technical_name="Validate QuikList MSORT Default",
    business_name="Group Bill Sort Must Default to N",
    purpose="Ensure QuikList.MSORT equals the business-supplied default N.",
    source_tables=("QuikList",),
    source_fields=("MSORT", "MGROUP"),
    business_rule=(
        "Business-supplied governance standard (not claimed as a QLAdmin manual "
        "default): after character and case normalization, MSORT must equal 'N'."
    ),
    severity="Error",
    failure_conditions=(
        "MSORT is null or blank.",
        "MSORT contains any value other than N after case normalization.",
    ),
)

RULE_DG_QUIKLIST_005 = RuleDefinition(
    rule_id="DG-QUIKLIST-005",
    governance_item_id="DG-QUIKLIST",
    technical_name="Validate QuikList MLAPSEL Default",
    business_name="Life Lapse Days Must Default to Zero",
    purpose="Ensure QuikList.MLAPSEL equals the business-supplied default 0.",
    source_tables=("QuikList",),
    source_fields=("MLAPSEL", "MGROUP"),
    business_rule=(
        "Business-supplied governance standard: MLAPSEL must decode to numeric zero. "
        "Null and blank are not treated as zero."
    ),
    severity="Error",
    failure_conditions=(
        "MLAPSEL is null, blank, or unreadable.",
        "MLAPSEL contains a numeric value other than zero.",
    ),
)

RULE_DG_QUIKLIST_006 = RuleDefinition(
    rule_id="DG-QUIKLIST-006",
    governance_item_id="DG-QUIKLIST",
    technical_name="Validate QuikList MLAPSEH Default",
    business_name="Health and Accident Lapse Days Must Default to Zero",
    purpose="Ensure QuikList.MLAPSEH equals the business-supplied default 0.",
    source_tables=("QuikList",),
    source_fields=("MLAPSEH", "MGROUP"),
    business_rule=(
        "Business-supplied governance standard: MLAPSEH must decode to numeric zero. "
        "Field name is MLAPSEH (not MLASPEH). Null and blank are not treated as zero."
    ),
    severity="Error",
    failure_conditions=(
        "MLAPSEH is null, blank, or unreadable.",
        "MLAPSEH contains a numeric value other than zero.",
    ),
)

RULE_DG_QUIKLIST_007 = RuleDefinition(
    rule_id="DG-QUIKLIST-007",
    governance_item_id="DG-QUIKLIST",
    technical_name="Validate QuikList MSTATUS Default",
    business_name="Group Status Must Default to Active",
    purpose="Ensure QuikList.MSTATUS equals the business-supplied default A.",
    source_tables=("QuikList",),
    source_fields=("MSTATUS", "MGROUP"),
    business_rule=(
        "Business-supplied governance standard: after character and case "
        "normalization, MSTATUS must equal 'A'."
    ),
    severity="Error",
    failure_conditions=(
        "MSTATUS is null or blank.",
        "MSTATUS contains any value other than A after case normalization.",
    ),
)

RULE_DG_QUIKLIST_008 = RuleDefinition(
    rule_id="DG-QUIKLIST-008",
    governance_item_id="DG-QUIKLIST",
    technical_name="Validate QuikList MBILLDAY Default",
    business_name="Group Bill Day Must Default to Zero",
    purpose="Ensure QuikList.MBILLDAY equals the business-supplied default 0.",
    source_tables=("QuikList",),
    source_fields=("MBILLDAY", "MGROUP"),
    business_rule=(
        "Business-supplied governance standard: MBILLDAY must decode to numeric zero. "
        "Null and blank are not treated as zero."
    ),
    severity="Error",
    failure_conditions=(
        "MBILLDAY is null, blank, or unreadable.",
        "MBILLDAY contains a numeric value other than zero.",
    ),
)

RULE_DG_QUIKLIST_009 = RuleDefinition(
    rule_id="DG-QUIKLIST-009",
    governance_item_id="DG-QUIKLIST",
    technical_name="Validate QuikList MBILLMODE Default",
    business_name="Group Bill Mode Must Default to Zero",
    purpose="Ensure QuikList.MBILLMODE equals the business-supplied default 0.",
    source_tables=("QuikList",),
    source_fields=("MBILLMODE", "MGROUP"),
    business_rule=(
        "Business-supplied governance standard: MBILLMODE must decode to numeric zero. "
        "Null and blank are not treated as zero."
    ),
    severity="Error",
    failure_conditions=(
        "MBILLMODE is null, blank, or unreadable.",
        "MBILLMODE contains a numeric value other than zero.",
    ),
)

GOVERNANCE_ITEM_QUIKDATE = GovernanceItem(
    item_id="DG-QUIKDATE",
    item_number=5,
    name="QuikDate Processing Date Integrity",
    description=(
        "Validate that QuikDate PAC Bill, Direct Bill, and Reinsurance Bill dates "
        "equal the prior-month-end date for the governance run date, and that "
        "ACHFILEID, ACHFILEID2, and ESCDATE (ESC_DATE) match required defaults."
    ),
)

RULE_DG_QUIKDATE_001 = RuleDefinition(
    rule_id="DG-QUIKDATE-001",
    governance_item_id="DG-QUIKDATE",
    technical_name="Validate QuikDate PAC Bill Prior Month End",
    business_name="PAC Bill Date Must Be Set to the Previous Month End",
    purpose=(
        "Ensure the QuikDate PAC Bill date equals the final calendar day of the "
        "month immediately before the governance run date."
    ),
    source_tables=("QuikDate",),
    source_fields=("PACBILL",),
    business_rule=(
        "Verified field PACBILL (D). Decode the DBF date and compare calendar date "
        "only to the dynamically calculated prior-month-end date for the run date."
    ),
    severity="Critical",
    failure_conditions=(
        "PACBILL is null or blank.",
        "PACBILL is invalid or unreadable.",
        "PACBILL is any valid date other than the calculated prior-month-end date.",
    ),
)

RULE_DG_QUIKDATE_002 = RuleDefinition(
    rule_id="DG-QUIKDATE-002",
    governance_item_id="DG-QUIKDATE",
    technical_name="Validate QuikDate Direct Bill Prior Month End",
    business_name="Direct Bill Date Must Be Set to the Previous Month End",
    purpose=(
        "Ensure the QuikDate Direct Bill date equals the final calendar day of the "
        "month immediately before the governance run date."
    ),
    source_tables=("QuikDate",),
    source_fields=("DIRBILL",),
    business_rule=(
        "Verified field DIRBILL (D). Decode the DBF date and compare calendar date "
        "only to the dynamically calculated prior-month-end date for the run date."
    ),
    severity="Critical",
    failure_conditions=(
        "DIRBILL is null or blank.",
        "DIRBILL is invalid or unreadable.",
        "DIRBILL is any valid date other than the calculated prior-month-end date.",
    ),
)

RULE_DG_QUIKDATE_003 = RuleDefinition(
    rule_id="DG-QUIKDATE-003",
    governance_item_id="DG-QUIKDATE",
    technical_name="Validate QuikDate Reinsurance Bill Prior Month End",
    business_name="Reinsurance Bill Date Must Be Set to the Previous Month End",
    purpose=(
        "Ensure the QuikDate Reinsurance Bill date equals the final calendar day of "
        "the month immediately before the governance run date."
    ),
    source_tables=("QuikDate",),
    source_fields=("REINBILL",),
    business_rule=(
        "Verified field REINBILL (D). Business label: Reinsurance Bill. Decode the "
        "DBF date and compare calendar date only to the dynamically calculated "
        "prior-month-end date for the run date."
    ),
    severity="Critical",
    failure_conditions=(
        "REINBILL is null or blank.",
        "REINBILL is invalid or unreadable.",
        "REINBILL is any valid date other than the calculated prior-month-end date.",
    ),
)

RULE_DG_QUIKDATE_004 = RuleDefinition(
    rule_id="DG-QUIKDATE-004",
    governance_item_id="DG-QUIKDATE",
    technical_name="Validate QuikDate ACHFILEID Default",
    business_name="ACH File ID Must Default to Zero",
    purpose="Ensure QuikDate.ACHFILEID equals the business-supplied default 0.",
    source_tables=("QuikDate",),
    source_fields=("ACHFILEID",),
    business_rule=(
        "Verified field ACHFILEID N(1). Must decode to numeric zero. Null and blank "
        "are not treated as zero. Separate from ACHFILEID2."
    ),
    severity="Error",
    failure_conditions=(
        "ACHFILEID is null, blank, or unreadable.",
        "ACHFILEID contains a numeric value other than zero.",
    ),
)

RULE_DG_QUIKDATE_005 = RuleDefinition(
    rule_id="DG-QUIKDATE-005",
    governance_item_id="DG-QUIKDATE",
    technical_name="Validate QuikDate ACHFILEID2 Default",
    business_name="Secondary ACH File ID Must Default to A",
    purpose="Ensure QuikDate.ACHFILEID2 equals the business-supplied default A.",
    source_tables=("QuikDate",),
    source_fields=("ACHFILEID2",),
    business_rule=(
        "Verified field ACHFILEID2 C(1). After trim and case normalization must "
        "equal 'A'. Separate from ACHFILEID."
    ),
    severity="Error",
    failure_conditions=(
        "ACHFILEID2 is null or blank.",
        "ACHFILEID2 contains any normalized value other than A.",
    ),
)

RULE_DG_QUIKDATE_006 = RuleDefinition(
    rule_id="DG-QUIKDATE-006",
    governance_item_id="DG-QUIKDATE",
    technical_name="Validate QuikDate ESCDATE Blank",
    business_name="ESCDATE Must Be Blank",
    purpose=(
        "Ensure the QuikDate ESCDATE value is blank (physical field ESC_DATE)."
    ),
    source_tables=("QuikDate",),
    source_fields=("ESC_DATE",),
    business_rule=(
        "Verified physical field ESC_DATE (D) — business label ESCDATE. Passes when "
        "the value is a supported empty DBF date, null representing no date, or blank "
        "after trim. Populated dates fail."
    ),
    severity="Error",
    failure_conditions=(
        "ESC_DATE contains a populated date.",
        "ESC_DATE contains a nonblank character or unreadable nonblank value.",
    ),
)

_PLANVALUE_SOURCES = (
    "QuikPlCv",
    "QuikPlTv",
    "QuikPlGp",
    "QuikPlDb",
    "QuikPlDv",
)

GOVERNANCE_ITEM_PLANVALUES = GovernanceItem(
    item_id="DG-PLANVALUES",
    item_number=6,
    name="Plan Value Reference Integrity",
    description=(
        "Validate that mortality tables, plans, gender codes, underwriting classes, "
        "bands, issue states, and effective dates used by QuikPlCv, QuikPlTv, QuikPlGp, "
        "QuikPlDb, and QuikPlDv are approved defaults or valid setup references."
    ),
)

RULE_DG_PLANVALUES_001 = RuleDefinition(
    rule_id="DG-PLANVALUES-001",
    governance_item_id="DG-PLANVALUES",
    technical_name="Validate Plan Value Mortality Table Reference",
    business_name="Mortality Table Must Exist in QuikQxs",
    purpose=(
        "Ensure every populated normalized MORT value on applicable plan-value tables "
        "exists exactly once in QuikQxs."
    ),
    source_tables=_PLANVALUE_SOURCES + ("QuikQxs",),
    source_fields=("MORT", "QuikQxs.MORT"),
    business_rule=(
        "Source field MORT C(2) on QuikPlCv and QuikPlTv (verified). After trim-only "
        "normalization preserving leading zeros, each nonblank MORT must match exactly "
        "one QuikQxs.MORT. Null and blank fail. Other plan-value tables without MORT "
        "are NOT_RUN for this rule. Does not confirm actuarial appropriateness."
    ),
    severity="Critical",
    failure_conditions=(
        "MORT is null.",
        "MORT is blank.",
        "MORT does not exist in QuikQxs.",
        "The matching QuikQxs.MORT key is duplicated.",
    ),
)

RULE_DG_PLANVALUES_002 = RuleDefinition(
    rule_id="DG-PLANVALUES-002",
    governance_item_id="DG-PLANVALUES",
    technical_name="Validate Plan Value ETI Mortality Table Reference",
    business_name="ETI Mortality Table Must Exist in QuikQxs",
    purpose=(
        "Ensure every populated normalized ETIMORT value exists exactly once in QuikQxs."
    ),
    source_tables=_PLANVALUE_SOURCES + ("QuikQxs",),
    source_fields=("ETIMORT", "QuikQxs.MORT"),
    business_rule=(
        "Source field ETIMORT C(2) on QuikPlCv only (verified). Same QuikQxs.MORT key "
        "as MORT. Null and blank fail. Tables without ETIMORT are NOT_RUN."
    ),
    severity="Critical",
    failure_conditions=(
        "ETIMORT is null.",
        "ETIMORT is blank.",
        "ETIMORT does not exist in QuikQxs.",
        "The matching QuikQxs.MORT key is duplicated.",
    ),
)

RULE_DG_PLANVALUES_003 = RuleDefinition(
    rule_id="DG-PLANVALUES-003",
    governance_item_id="DG-PLANVALUES",
    technical_name="Validate Plan Value Plan Reference",
    business_name="Plan Must Exist in QuikPlan",
    purpose="Ensure every populated normalized PLAN value exists exactly once in QuikPlan.",
    source_tables=_PLANVALUE_SOURCES + ("QuikPlan",),
    source_fields=("PLAN", "QuikPlan.PLAN"),
    business_rule=(
        "Source field PLAN C(6) on all five plan-value tables. Leading zeros preserved. "
        "Each nonblank PLAN must match exactly one QuikPlan.PLAN. Null and blank fail. "
        "Does not confirm the rate record belongs to the correct plan product."
    ),
    severity="Critical",
    failure_conditions=(
        "PLAN is null.",
        "PLAN is blank.",
        "PLAN does not exist in QuikPlan.",
        "The matching QuikPlan.PLAN is duplicated.",
    ),
)

RULE_DG_PLANVALUES_004 = RuleDefinition(
    rule_id="DG-PLANVALUES-004",
    governance_item_id="DG-PLANVALUES",
    technical_name="Validate Plan Value Gender Code",
    business_name="Gender Must Be Default Zero or a Valid Gender Code",
    purpose=(
        "Ensure GENDER is the approved default 0 or exists once in QuikPlGd for the plan."
    ),
    source_tables=_PLANVALUE_SOURCES + ("QuikPlGd",),
    source_fields=("GENDER", "QuikPlGd.GDCODE", "QuikPlGd.PLAN"),
    business_rule=(
        "Source GENDER C(1). Passes when normalized value is '0', or (PLAN, GENDER) "
        "matches exactly one QuikPlGd (PLAN, GDCODE). Leading zeros preserved. Missing "
        "QuikPlGd does not invent missing-reference findings for nonzero values."
    ),
    severity="Error",
    failure_conditions=(
        "GENDER is null.",
        "GENDER is blank.",
        "GENDER is not 0 and does not exist in QuikPlGd for the plan.",
        "GENDER is not 0 and matches multiple QuikPlGd records.",
    ),
)

RULE_DG_PLANVALUES_005 = RuleDefinition(
    rule_id="DG-PLANVALUES-005",
    governance_item_id="DG-PLANVALUES",
    technical_name="Validate Plan Value Underwriting Class",
    business_name="Underwriting Class Must Be Default 00 or a Valid Class",
    purpose=(
        "Ensure UWCLASS is the approved default '00' or exists once in QuikPlUw for the plan."
    ),
    source_tables=_PLANVALUE_SOURCES + ("QuikPlUw",),
    source_fields=("UWCLASS", "QuikPlUw.UWCODE", "QuikPlUw.PLAN"),
    business_rule=(
        "Source UWCLASS C(2). Passes when normalized value is '00' (not converted to "
        "numeric zero), or (PLAN, UWCLASS) matches exactly one QuikPlUw (PLAN, UWCODE)."
    ),
    severity="Error",
    failure_conditions=(
        "UWCLASS is null.",
        "UWCLASS is blank.",
        "UWCLASS is not '00' and does not exist in QuikPlUw for the plan.",
        "UWCLASS is not '00' and matches multiple QuikPlUw records.",
    ),
)

RULE_DG_PLANVALUES_006 = RuleDefinition(
    rule_id="DG-PLANVALUES-006",
    governance_item_id="DG-PLANVALUES",
    technical_name="Validate Plan Value Band Code",
    business_name="Band Must Be Default 00 or a Valid Band",
    purpose=(
        "Ensure BAND is the approved default '00' or exists once in the verified band "
        "setup table for the plan."
    ),
    source_tables=_PLANVALUE_SOURCES + ("QuikPlBd",),
    source_fields=("BAND", "QuikPlBd.BDCODE", "QuikPlBd.PLAN"),
    business_rule=(
        "Source BAND C(2). QuikPlVd was not present in the inspected CSO region; "
        "verified reference is QuikPlBd.BDCODE scoped by PLAN. Passes when value is "
        "'00' or (PLAN, BAND) matches exactly one QuikPlBd (PLAN, BDCODE). '00' is not "
        "converted to numeric zero."
    ),
    severity="Error",
    failure_conditions=(
        "BAND is null.",
        "BAND is blank.",
        "BAND is not '00' and does not exist in QuikPlBd for the plan.",
        "BAND is not '00' and matches multiple QuikPlBd records.",
    ),
)

RULE_DG_PLANVALUES_007 = RuleDefinition(
    rule_id="DG-PLANVALUES-007",
    governance_item_id="DG-PLANVALUES",
    technical_name="Validate Plan Value Issue State",
    business_name="Issue State Must Be Default 00 or a Valid State Abbreviation",
    purpose=(
        "Ensure ISSUEST is '00' or an approved two-character United States state/DC "
        "abbreviation."
    ),
    source_tables=_PLANVALUE_SOURCES,
    source_fields=("ISSUEST",),
    business_rule=(
        "Source ISSUEST C(2). Uppercase normalization. Passes when value is '00' or in "
        "the approved 50-state + DC list. Territories and military codes are not accepted. "
        "Does not confirm the rate is legally approved for sale in that state."
    ),
    severity="Error",
    failure_conditions=(
        "ISSUEST is null.",
        "ISSUEST is blank.",
        "ISSUEST is not '00' and is not an approved abbreviation.",
        "ISSUEST is not exactly two meaningful characters after normalization.",
    ),
)

RULE_DG_PLANVALUES_008 = RuleDefinition(
    rule_id="DG-PLANVALUES-008",
    governance_item_id="DG-PLANVALUES",
    technical_name="Validate Plan Value Effective Date",
    business_name="Effective Date Must Be Within the Approved Date Range",
    purpose=(
        "Ensure EFFDATE is a valid calendar date on or after 1900-01-01 and on or before "
        "the governance run date plus 12 calendar months."
    ),
    source_tables=_PLANVALUE_SOURCES,
    source_fields=("EFFDATE",),
    business_rule=(
        "Source EFFDATE D(8). Inclusive bounds: minimum 1900-01-01; maximum = "
        "add_calendar_months(run_date, 12) with end-of-month day clamping "
        "(e.g. 2024-02-29 + 12 months → 2025-02-28). Time-of-day is ignored. "
        "Does not confirm the date is the correct product/rate filing effective date."
    ),
    severity="Critical",
    failure_conditions=(
        "EFFDATE is null.",
        "EFFDATE is blank.",
        "EFFDATE is invalid or unreadable.",
        "EFFDATE is earlier than January 1, 1900.",
        "EFFDATE is later than the governance run date plus 12 calendar months.",
    ),
)

ALL_GOVERNANCE_ITEMS = (
    GOVERNANCE_ITEM_QUIKCOMP,
    GOVERNANCE_ITEM_QUIKMSTR,
    GOVERNANCE_ITEM_ACCOUNTING,
    GOVERNANCE_ITEM_QUIKLIST,
    GOVERNANCE_ITEM_QUIKDATE,
    GOVERNANCE_ITEM_PLANVALUES,
)
ALL_RULE_DEFINITIONS = (
    RULE_DG_QUIKCOMP_001,
    RULE_DG_QUIKCOMP_002,
    RULE_DG_QUIKCOMP_003,
    RULE_DG_QUIKMSTR_001,
    RULE_DG_QUIKACTG_001,
    RULE_DG_QUIKACTG_002,
    RULE_DG_QUIKLIST_001,
    RULE_DG_QUIKLIST_002,
    RULE_DG_QUIKLIST_003,
    RULE_DG_QUIKLIST_004,
    RULE_DG_QUIKLIST_005,
    RULE_DG_QUIKLIST_006,
    RULE_DG_QUIKLIST_007,
    RULE_DG_QUIKLIST_008,
    RULE_DG_QUIKLIST_009,
    RULE_DG_QUIKDATE_001,
    RULE_DG_QUIKDATE_002,
    RULE_DG_QUIKDATE_003,
    RULE_DG_QUIKDATE_004,
    RULE_DG_QUIKDATE_005,
    RULE_DG_QUIKDATE_006,
    RULE_DG_PLANVALUES_001,
    RULE_DG_PLANVALUES_002,
    RULE_DG_PLANVALUES_003,
    RULE_DG_PLANVALUES_004,
    RULE_DG_PLANVALUES_005,
    RULE_DG_PLANVALUES_006,
    RULE_DG_PLANVALUES_007,
    RULE_DG_PLANVALUES_008,
)
