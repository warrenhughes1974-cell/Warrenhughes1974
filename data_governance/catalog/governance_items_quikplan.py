"""DG-QUIKPLAN — Plan Setup governance item and rule catalog."""

from __future__ import annotations

from data_governance.catalog.governance_items import GovernanceItem, RuleDefinition

# Verified physical field aliases (business name → physical name)
# PAYYRS, MAXUNIT (MAXUNITS), RRULE (ROUNDING)

_RATE_KEY_TABLES = (
    "QuikGps",
    "QuikCvs",
    "QuikDbs",
    "QuikNps",
    "QuikTvs",
    "QuikNff",
    "QuikPlGp",
    "QuikPlCv",
    "QuikPlDb",
    "QuikPlDv",
    "QuikPlTv",
    "QuikPlGd",
    "QuikPlUw",
    "QuikPlBd",
    "QuikPlSt",
    "QuikPlNb",
    "QuikUint",
    "QuikAint",
    "QuikAing",
    "QuikAexp",
    "QuikAinf",
    "QuikIssc",
)

_COMPANY_BEARING_TABLES = (
    "QuikAgts",
    "QuikActg",
    "QuikList",
    "QuikChrt",
)

_DATE_FIELD_TABLES = (
    "QuikPlCv",
    "QuikPlTv",
    "QuikPlGp",
    "QuikPlDb",
    "QuikPlDv",
    "QuikPlNb",
    "QuikDate",
    "QuikComm",
    "QuikAint",
    "QuikUint",
)

_TRADITIONAL_VALUE_TABLES = (
    "QuikPlCv",
    "QuikPlTv",
    "QuikCvs",
    "QuikTvs",
    "QuikNps",
)

_ANNUITY_SUPPORT_TABLES = (
    "QuikAint",
    "QuikAing",
    "QuikAexp",
    "QuikAinf",
)

GOVERNANCE_ITEM_QUIKPLAN = GovernanceItem(
    item_id="DG-QUIKPLAN",
    item_number=7,
    name="Plan Setup",
    description=(
        "Validate that plans are configured with valid plan codes, approved default "
        "values, appropriate payment and insurance periods, valid related setup "
        "references, and the supporting rate and value records required for the plan."
    ),
)

RULE_DG_QUIKPLAN_001 = RuleDefinition(
    rule_id="DG-QUIKPLAN-001",
    governance_item_id="DG-QUIKPLAN",
    technical_name="Validate Plan Code Length",
    business_name="Plan Code Must Contain Six Characters",
    purpose="Ensure every plan code contains exactly six meaningful characters.",
    source_tables=("QuikPlan",),
    source_fields=("PLAN",),
    business_rule=(
        "Source PLAN C(6). After trim-only normalization preserving leading zeros, "
        "each plan code must contain exactly six characters. Blank and null fail."
    ),
    severity="Critical",
    failure_conditions=(
        "PLAN is blank.",
        "PLAN is null.",
        "PLAN contains fewer than six characters.",
        "PLAN contains more than six characters.",
    ),
)

RULE_DG_QUIKPLAN_002 = RuleDefinition(
    rule_id="DG-QUIKPLAN-002",
    governance_item_id="DG-QUIKPLAN",
    technical_name="Validate Plan Code Characters",
    business_name="Plan Code May Contain Only Letters and Numbers",
    purpose="Ensure plan codes contain only letters and numbers with no spaces or special characters.",
    source_tables=("QuikPlan",),
    source_fields=("PLAN",),
    business_rule=(
        "Source PLAN C(6). Exactly six characters; each character must be A–Z or 0–9 "
        "after uppercase normalization. Spaces, punctuation, and special characters fail."
    ),
    severity="Critical",
    failure_conditions=(
        "PLAN does not contain exactly six characters.",
        "PLAN contains a space.",
        "PLAN contains a special character or punctuation.",
    ),
)

RULE_DG_QUIKPLAN_003 = RuleDefinition(
    rule_id="DG-QUIKPLAN-003",
    governance_item_id="DG-QUIKPLAN",
    technical_name="Validate Plan Code PUA Suffix",
    business_name="Plan Code May Not Use a Reserved PUA Suffix",
    purpose="Ensure plan codes do not end with suffixes reserved for paid-up additions.",
    source_tables=("QuikPlan",),
    source_fields=("PLAN",),
    business_rule=(
        "Source PLAN C(6). Case-insensitive comparison. The final two characters must "
        "not be PA, XP, XF, or XS."
    ),
    severity="Critical",
    failure_conditions=(
        "PLAN ends with PA, XP, XF, or XS (case-insensitive).",
    ),
)

RULE_DG_QUIKPLAN_004 = RuleDefinition(
    rule_id="DG-QUIKPLAN-004",
    governance_item_id="DG-QUIKPLAN",
    technical_name="Validate Participating Plan Setting",
    business_name="PAR Must Be 0 or 1",
    purpose="Ensure the participating-plan setting is valid.",
    source_tables=("QuikPlan",),
    source_fields=("PAR",),
    business_rule=(
        "Source PAR. Allowed values after trim are 0 or 1 only."
    ),
    severity="Critical",
    failure_conditions=(
        "PAR is not 0 or 1.",
    ),
)

RULE_DG_QUIKPLAN_005 = RuleDefinition(
    rule_id="DG-QUIKPLAN-005",
    governance_item_id="DG-QUIKPLAN",
    technical_name="Validate Annuity Basis",
    business_name="Annuity Basis Must Match the Plan Type",
    purpose=(
        "Ensure annuity plans use a valid annuity basis and non-annuity plans leave "
        "the basis blank."
    ),
    source_tables=("QuikPlan",),
    source_fields=("PLAN", "BASIS"),
    business_rule=(
        "Annuity plans begin with A. For A plans, BASIS must be exactly one of "
        "NONQ, QUAL, NQIA, QLIA, or TXBL (case-sensitive). For non-A plans, BASIS "
        "must be blank."
    ),
    severity="Critical",
    failure_conditions=(
        "An annuity plan has a blank or invalid BASIS.",
        "A non-annuity plan has a populated BASIS.",
    ),
)

RULE_DG_QUIKPLAN_006 = RuleDefinition(
    rule_id="DG-QUIKPLAN-006",
    governance_item_id="DG-QUIKPLAN",
    technical_name="Validate Loan Interest Option",
    business_name="Loan Interest Option Must Be A or R",
    purpose="Ensure the loan interest option is valid.",
    source_tables=("QuikPlan",),
    source_fields=("LOANINTX",),
    business_rule=(
        "Source LOANINTX. Allowed values are A or R after casefold normalization. "
        "Expected default is A. Any other value fails."
    ),
    severity="Critical",
    failure_conditions=(
        "LOANINTX is blank or null.",
        "LOANINTX is not A or R.",
    ),
)

RULE_DG_QUIKPLAN_007 = RuleDefinition(
    rule_id="DG-QUIKPLAN-007",
    governance_item_id="DG-QUIKPLAN",
    technical_name="Validate MYGA Deposit Interest",
    business_name="MYGA Plans Must Have Positive Deposit Interest",
    purpose="Ensure confirmed MYGA plans have a deposit interest value greater than zero.",
    source_tables=("QuikPlan",),
    source_fields=("PLAN", "DEPINT"),
    business_rule=(
        "Uses plan_classification.csv to identify MYGA plans. For confirmed MYGA plans, "
        "DEPINT must be greater than zero. Non-MYGA plans are not evaluated. When "
        "classification is unavailable, the rule reports Could Not Be Checked."
    ),
    severity="Error",
    failure_conditions=(
        "A confirmed MYGA plan has DEPINT less than or equal to zero.",
        "DEPINT is null, blank, or unreadable for a confirmed MYGA plan.",
        "Plan classification config is unavailable.",
    ),
)

RULE_DG_QUIKPLAN_008 = RuleDefinition(
    rule_id="DG-QUIKPLAN-008",
    governance_item_id="DG-QUIKPLAN",
    technical_name="Validate Low and High Age",
    business_name="Issue Age Range Must Be Valid",
    purpose=(
        "Ensure plan issue ages (LOAGE/HIAGE) are readable and the low age is "
        "less than the high age. LOAGE may be any valid minimum issue age "
        "(DG-R-007: former Age-1 must-be-zero requirement removed)."
    ),
    source_tables=("QuikPlan",),
    source_fields=("LOAGE", "HIAGE"),
    business_rule=(
        "Source LOAGE and HIAGE (QLAdmin Issue Ages — lowest and highest age "
        "for which the plan may be issued). Both must be readable numerics. "
        "LOAGE must be less than HIAGE. LOAGE is not required to be zero."
    ),
    severity="Critical",
    failure_conditions=(
        "LOAGE or HIAGE is null, blank, or unreadable.",
        "LOAGE is greater than or equal to HIAGE.",
    ),
)

RULE_DG_QUIKPLAN_009 = RuleDefinition(
    rule_id="DG-QUIKPLAN-009",
    governance_item_id="DG-QUIKPLAN",
    technical_name="Validate Renewal Setting",
    business_name="Renewal Setting Must Be Valid",
    purpose="Ensure the renewal setting matches the plan type.",
    source_tables=("QuikPlan",),
    source_fields=("PLAN", "RENEW"),
    business_rule=(
        "Source RENEW. Plans beginning with 5 may use N or Y. All other plans must "
        "use N. Expected default is N."
    ),
    severity="Critical",
    failure_conditions=(
        "RENEW is blank, null, or unreadable.",
        "RENEW is not N for a plan that does not begin with 5.",
        "RENEW is not N or Y for a plan beginning with 5.",
    ),
)

RULE_DG_QUIKPLAN_010 = RuleDefinition(
    rule_id="DG-QUIKPLAN-010",
    governance_item_id="DG-QUIKPLAN",
    technical_name="Validate Payment Period",
    business_name="Payment Years and Payment Age Cannot Both Be Zero",
    purpose="Ensure the payment period is populated for applicable plans.",
    source_tables=("QuikPlan",),
    source_fields=("PLAN", "PAYYRS", "PAYAGE"),
    business_rule=(
        "Physical field PAYYRS (business PAYRS) and PAYAGE. For plans not beginning "
        "with 5, at least one of PAYYRS or PAYAGE must be greater than zero. Plans "
        "beginning with 5 may have both zero."
    ),
    severity="Critical",
    failure_conditions=(
        "PAYYRS and PAYAGE are both zero for a plan not beginning with 5.",
        "PAYYRS or PAYAGE is unreadable for an evaluated plan.",
    ),
)

RULE_DG_QUIKPLAN_011 = RuleDefinition(
    rule_id="DG-QUIKPLAN-011",
    governance_item_id="DG-QUIKPLAN",
    technical_name="Validate Insurance Period",
    business_name="Insurance Years and Insurance Age Cannot Both Be Zero",
    purpose="Ensure the insurance period is populated for applicable plans.",
    source_tables=("QuikPlan",),
    source_fields=("PLAN", "INSYRS", "INSAGE"),
    business_rule=(
        "Source INSYRS and INSAGE. For plans not beginning with 5, at least one of "
        "INSYRS or INSAGE must be greater than zero. Plans beginning with 5 may have "
        "both zero."
    ),
    severity="Critical",
    failure_conditions=(
        "INSYRS and INSAGE are both zero for a plan not beginning with 5.",
        "INSYRS or INSAGE is unreadable for an evaluated plan.",
    ),
)

RULE_DG_QUIKPLAN_012 = RuleDefinition(
    rule_id="DG-QUIKPLAN-012",
    governance_item_id="DG-QUIKPLAN",
    technical_name="Validate Single-Premium Settings",
    business_name="Single-Premium Plans Must Use Single-Premium Settings",
    purpose="Ensure confirmed single-premium plans use required payment settings.",
    source_tables=("QuikPlan",),
    source_fields=("PLAN", "PAYYRS", "PAYAGE", "SEMI", "QTRL", "MTHD", "MTHB"),
    business_rule=(
        "Uses plan_classification.csv to identify single-premium plans. For confirmed "
        "single-premium plans: PAYYRS (business PAYRS) must be 1; PAYAGE, SEMI, QTRL, "
        "MTHD, and MTHB must be 0. When classification is unavailable, the rule "
        "reports Could Not Be Checked."
    ),
    severity="Error",
    failure_conditions=(
        "A confirmed single-premium plan has an incorrect PAYYRS, PAYAGE, SEMI, QTRL, "
        "MTHD, or MTHB value.",
        "Plan classification config is unavailable.",
    ),
)

RULE_DG_QUIKPLAN_013 = RuleDefinition(
    rule_id="DG-QUIKPLAN-013",
    governance_item_id="DG-QUIKPLAN",
    technical_name="Validate Payment Age Maximum",
    business_name="Payment Age May Not Exceed 125",
    purpose="Ensure the payment age does not exceed 125.",
    source_tables=("QuikPlan",),
    source_fields=("PAYAGE",),
    business_rule=(
        "Source PAYAGE. When populated and readable, PAYAGE must be 125 or less."
    ),
    severity="Critical",
    failure_conditions=(
        "PAYAGE is greater than 125.",
    ),
)

RULE_DG_QUIKPLAN_014 = RuleDefinition(
    rule_id="DG-QUIKPLAN-014",
    governance_item_id="DG-QUIKPLAN",
    technical_name="Validate Insurance Age Maximum",
    business_name="Insurance Age May Not Exceed 125",
    purpose="Ensure the insurance age does not exceed 125.",
    source_tables=("QuikPlan",),
    source_fields=("INSAGE",),
    business_rule=(
        "Source INSAGE. When populated and readable, INSAGE must be 125 or less."
    ),
    severity="Critical",
    failure_conditions=(
        "INSAGE is greater than 125.",
    ),
)

RULE_DG_QUIKPLAN_015 = RuleDefinition(
    rule_id="DG-QUIKPLAN-015",
    governance_item_id="DG-QUIKPLAN",
    technical_name="Validate Initial Value Default",
    business_name="Initial Value Must Use the Approved Default",
    purpose="Ensure INITVAL uses the approved default unless a transformation exception applies.",
    source_tables=("QuikPlan",),
    source_fields=("PLAN", "INITVAL"),
    business_rule=(
        "Source INITVAL. Expected default is 1000. Plans listed in plan_classification.csv "
        "as INITVAL exceptions pass with non-default values. Other non-default values "
        "generate warnings, not hard failures."
    ),
    severity="Advisory",
    failure_conditions=(
        "INITVAL is null, blank, or unreadable.",
        "INITVAL differs from 1000 and no approved transformation exception applies.",
    ),
)

RULE_DG_QUIKPLAN_016 = RuleDefinition(
    rule_id="DG-QUIKPLAN-016",
    governance_item_id="DG-QUIKPLAN",
    technical_name="Validate Commission ID Reference",
    business_name="Commission ID Must Exist or Be Blank",
    purpose="Ensure populated commission IDs exist exactly once in Commission Setup.",
    source_tables=("QuikPlan", "QuikComm"),
    source_fields=("COMMID", "QuikComm.COMMID"),
    business_rule=(
        "Source COMMID on QuikPlan. Blank passes. A populated value must match exactly "
        "one QuikComm.COMMID. When QuikComm is missing, one Could Not Be Checked item "
        "is reported."
    ),
    severity="Critical",
    failure_conditions=(
        "COMMID is populated and does not exist in QuikComm.",
        "COMMID matches more than one QuikComm record.",
        "QuikComm is not available in the data region.",
    ),
)

RULE_DG_QUIKPLAN_017 = RuleDefinition(
    rule_id="DG-QUIKPLAN-017",
    governance_item_id="DG-QUIKPLAN",
    technical_name="Validate Maximum and Minimum Units",
    business_name="Maximum Units Must Not Be Below Minimum Units",
    purpose="Ensure maximum units are not less than minimum units.",
    source_tables=("QuikPlan",),
    source_fields=("MAXUNIT", "MINUNIT"),
    business_rule=(
        "Physical field MAXUNIT (business MAXUNITS) and MINUNIT. MAXUNIT must be "
        "greater than or equal to MINUNIT."
    ),
    severity="Critical",
    failure_conditions=(
        "MAXUNIT or MINUNIT is null, blank, or unreadable.",
        "MAXUNIT is less than MINUNIT.",
    ),
)

RULE_DG_QUIKPLAN_018 = RuleDefinition(
    rule_id="DG-QUIKPLAN-018",
    governance_item_id="DG-QUIKPLAN",
    technical_name="Validate Rounding Rule Default",
    business_name="Rounding Rule Must Default to B",
    purpose="Ensure the rounding rule uses the approved default.",
    source_tables=("QuikPlan",),
    source_fields=("RRULE",),
    business_rule=(
        "Physical field RRULE (business ROUNDING). Required value is B after "
        "casefold normalization."
    ),
    severity="Error",
    failure_conditions=(
        "RRULE is blank, null, or not B.",
    ),
)

RULE_DG_QUIKPLAN_019 = RuleDefinition(
    rule_id="DG-QUIKPLAN-019",
    governance_item_id="DG-QUIKPLAN",
    technical_name="Validate Automatic NFO Default",
    business_name="Automatic NFO Must Default to 0",
    purpose="Ensure the automatic nonforfeiture setting uses the approved default.",
    source_tables=("QuikPlan",),
    source_fields=("AUTONFO",),
    business_rule=(
        "Source AUTONFO. Required value is 0 after trim."
    ),
    severity="Error",
    failure_conditions=(
        "AUTONFO is blank, null, or not 0.",
    ),
)

RULE_DG_QUIKPLAN_020 = RuleDefinition(
    rule_id="DG-QUIKPLAN-020",
    governance_item_id="DG-QUIKPLAN",
    technical_name="Validate Deficiency Setting",
    business_name="Deficiency Must Be N for Alphabetic or 9-Series Plans",
    purpose="Ensure deficiency is N for plans whose first character is A–Z or 9.",
    source_tables=("QuikPlan",),
    source_fields=("PLAN", "DEFICIENCY"),
    business_rule=(
        "When the first plan-code character is alphabetic or 9, DEFICIENCY must equal N "
        "after casefold normalization. Plans beginning with 0–8 are not evaluated."
    ),
    severity="Critical",
    failure_conditions=(
        "An alphabetic or 9-series plan has DEFICIENCY other than N.",
    ),
)

RULE_DG_QUIKPLAN_021 = RuleDefinition(
    rule_id="DG-QUIKPLAN-021",
    governance_item_id="DG-QUIKPLAN",
    technical_name="Validate New-Business Status",
    business_name="Active Plan Status Must Use a Valid Logical Value",
    purpose="Ensure the new-business status contains a valid yes-or-no value.",
    source_tables=("QuikPlan",),
    source_fields=("BACTIVE",),
    business_rule=(
        "Source BACTIVE. Accepts T/F, Y/N, or 1/0 logical representations. True means "
        "eligible for new business; false means closed. This rule validates storage "
        "format only, not whether the plan should be open or closed."
    ),
    severity="Critical",
    failure_conditions=(
        "BACTIVE is null, blank, or an unreadable logical value.",
    ),
)

# DG-QUIKPLAN-022 retired 2026-07-18 (DG-R-006): PLANVALOPT is the QLAdmin PVO /
# rate-file lookup switch and is not constrained by BACTIVE (closed-to-new-business).

RULE_DG_QUIKPLAN_023 = RuleDefinition(
    rule_id="DG-QUIKPLAN-023",
    governance_item_id="DG-QUIKPLAN",
    technical_name="Validate MLAPSE Default",
    business_name="MLAPSE Must Default to 0",
    purpose="Ensure the lapse setting uses the approved default.",
    source_tables=("QuikPlan",),
    source_fields=("MLAPSE",),
    business_rule=(
        "Source MLAPSE. Required numeric value is 0."
    ),
    severity="Error",
    failure_conditions=(
        "MLAPSE is null, blank, unreadable, or not zero.",
    ),
)

RULE_DG_QUIKPLAN_024 = RuleDefinition(
    rule_id="DG-QUIKPLAN-024",
    governance_item_id="DG-QUIKPLAN",
    technical_name="Validate MNAICLOB Default",
    business_name="MNAICLOB Must Default to NAPLAN",
    purpose="Ensure the NAIC line-of-business setting uses the approved default.",
    source_tables=("QuikPlan",),
    source_fields=("MNAICLOB",),
    business_rule=(
        "Source MNAICLOB. Required value is NAPLAN after casefold normalization."
    ),
    severity="Error",
    failure_conditions=(
        "MNAICLOB is blank, null, or not NAPLAN.",
    ),
)

RULE_DG_QUIKPLAN_025 = RuleDefinition(
    rule_id="DG-QUIKPLAN-025",
    governance_item_id="DG-QUIKPLAN",
    technical_name="Validate Gross Premium Supporting Tables",
    business_name="Gross Premium Supporting Tables Must Exist",
    purpose=(
        "Ensure plans that use variable gross premium setup have required supporting "
        "records."
    ),
    source_tables=("QuikPlan", "QuikGps", "QuikPlGp"),
    source_fields=("PLAN", "VARGP"),
    business_rule=(
        "When VARGP is not 4, the plan must exist in both QuikGps and QuikPlGp. "
        "When a supporting table is missing, one Could Not Be Checked item is reported."
    ),
    severity="Critical",
    failure_conditions=(
        "VARGP is not 4 and the plan is missing from QuikGps.",
        "VARGP is not 4 and the plan is missing from QuikPlGp.",
        "A required supporting table is not available.",
    ),
)

RULE_DG_QUIKPLAN_026 = RuleDefinition(
    rule_id="DG-QUIKPLAN-026",
    governance_item_id="DG-QUIKPLAN",
    technical_name="Validate Death Benefit Supporting Tables",
    business_name="Death Benefit Supporting Tables Must Exist",
    purpose=(
        "Ensure plans with varying death-benefit schedules (VARDB 1/2/3) have required "
        "supporting records. Level (VARDB 0 / INITVAL) and not-on-file (VARDB 4) skip."
    ),
    source_tables=("QuikPlan", "QuikDbs", "QuikPlDb"),
    source_fields=("PLAN", "VARDB"),
    business_rule=(
        "When VARDB is 1, 2, or 3, the plan must exist in both QuikDbs and QuikPlDb. "
        "VARDB 0 (level) and VARDB 4 (not on file) do not require those tables. "
        "When a supporting table is missing, one Could Not Be Checked item is reported."
    ),
    severity="Critical",
    failure_conditions=(
        "VARDB is 1, 2, or 3 and the plan is missing from QuikDbs.",
        "VARDB is 1, 2, or 3 and the plan is missing from QuikPlDb.",
        "A required supporting table is not available.",
    ),
)

RULE_DG_QUIKPLAN_027 = RuleDefinition(
    rule_id="DG-QUIKPLAN-027",
    governance_item_id="DG-QUIKPLAN",
    technical_name="Validate Traditional Plan Value Tables",
    business_name="Traditional Plans Should Have Required Value Tables",
    purpose=(
        "Warn when traditional plans (first character 0–8) are missing expected value "
        "and reserve tables."
    ),
    source_tables=("QuikPlan",) + _TRADITIONAL_VALUE_TABLES,
    source_fields=("PLAN",),
    business_rule=(
        "Traditional plans begin with 0–8. Issue a warning when the plan is missing "
        "from any of QuikPlCv, QuikPlTv, QuikCvs, QuikTvs, or QuikNps."
    ),
    severity="Advisory",
    failure_conditions=(
        "A traditional plan is missing from an expected value or reserve table.",
        "A required supporting table is not available.",
    ),
)

RULE_DG_QUIKPLAN_028 = RuleDefinition(
    rule_id="DG-QUIKPLAN-028",
    governance_item_id="DG-QUIKPLAN",
    technical_name="Validate Annuity Supporting Tables",
    business_name="Annuity Plans Should Have Required Annuity Tables",
    purpose=(
        "Warn when annuity plans are missing expected annuity setup records. "
        "QuikAing and QuikAinf are interchangeable (DG-R-012)."
    ),
    source_tables=("QuikPlan",) + _ANNUITY_SUPPORT_TABLES,
    source_fields=("PLAN", "MPLAN"),
    business_rule=(
        "Annuity plans begin with A. Warn when missing QuikAint or QuikAexp, or when "
        "missing both QuikAing and QuikAinf (either one satisfies the guarantee/"
        "information pair)."
    ),
    severity="Advisory",
    failure_conditions=(
        "An annuity plan is missing QuikAint or QuikAexp.",
        "An annuity plan has neither QuikAing nor QuikAinf.",
        "A required supporting table is not available.",
    ),
)

RULE_DG_QUIKPLAN_029 = RuleDefinition(
    rule_id="DG-QUIKPLAN-029",
    governance_item_id="DG-QUIKPLAN",
    technical_name="Validate Universal Life Interest Record",
    business_name="UL Plans Must Exist in QuikUint",
    purpose="Ensure confirmed Universal Life plans have a Universal Life interest record.",
    source_tables=("QuikPlan", "QuikUint"),
    source_fields=("PLAN", "QuikUint.MPLAN"),
    business_rule=(
        "Uses plan_classification.csv to identify UL plans. Confirmed UL plans must "
        "exist in QuikUint. When classification is unavailable, the rule reports "
        "Could Not Be Checked."
    ),
    severity="Error",
    failure_conditions=(
        "A confirmed UL plan is missing from QuikUint.",
        "Plan classification config is unavailable.",
        "QuikUint is not available in the data region.",
    ),
)

RULE_DG_QUIKPLAN_030 = RuleDefinition(
    rule_id="DG-QUIKPLAN-030",
    governance_item_id="DG-QUIKPLAN",
    technical_name="Validate MEDS Plan Flags",
    business_name="MEDS Plan Flags Must Match the Plan Type",
    purpose="Ensure MEDS plans use required commission and rating-key settings.",
    source_tables=("QuikPlan",),
    source_fields=("PLANTYPE", "HCOMMIP", "HRIGPKEY"),
    business_rule=(
        "When PLANTYPE is MEDS, HCOMMIP and HRIGPKEY must be true. For all other plan "
        "types, both must be false."
    ),
    severity="Critical",
    failure_conditions=(
        "PLANTYPE is MEDS and HCOMMIP or HRIGPKEY is false.",
        "PLANTYPE is not MEDS and HCOMMIP or HRIGPKEY is true.",
        "HCOMMIP or HRIGPKEY is an unreadable logical value.",
    ),
)

RULE_DG_QUIKPLAN_031 = RuleDefinition(
    rule_id="DG-QUIKPLAN-031",
    governance_item_id="DG-QUIKPLAN",
    technical_name="Validate Rate Key Plan References",
    business_name="Rate and Key Table Plan Codes Must Exist in QuikPlan",
    purpose=(
        "Ensure every plan code used in approved rate and key tables exists exactly "
        "once in Plan Setup."
    ),
    source_tables=("QuikPlan",) + _RATE_KEY_TABLES,
    source_fields=("PLAN", "MPLAN", "QuikPlan.PLAN"),
    business_rule=(
        "Cross-table reference check using the approved rate and key table inventory. "
        "Each populated plan code in those tables must match exactly one QuikPlan.PLAN."
    ),
    severity="Critical",
    failure_conditions=(
        "A populated plan code in an approved rate or key table does not exist in QuikPlan.",
        "A populated plan code matches more than one QuikPlan record.",
    ),
)

RULE_DG_QUIKPLAN_032 = RuleDefinition(
    rule_id="DG-QUIKPLAN-032",
    governance_item_id="DG-QUIKPLAN",
    technical_name="Validate Company Code References",
    business_name="Company Codes Must Exist in Company Setup",
    purpose=(
        "Ensure company codes used in approved tables exist exactly once in Company Setup."
    ),
    source_tables=("QuikComp",) + _COMPANY_BEARING_TABLES,
    source_fields=("MCOMP", "QuikComp.MCOMP"),
    business_rule=(
        "Cross-table reference check using the approved company-bearing table inventory. "
        "Each populated company code must match exactly one QuikComp.MCOMP."
    ),
    severity="Critical",
    failure_conditions=(
        "A populated company code does not exist in QuikComp.",
        "A populated company code matches more than one QuikComp record.",
        "QuikComp is not available in the data region.",
    ),
)

RULE_DG_QUIKPLAN_033 = RuleDefinition(
    rule_id="DG-QUIKPLAN-033",
    governance_item_id="DG-QUIKPLAN",
    technical_name="Validate Conversion Date Range",
    business_name="Conversion Dates Outside the Approved Range Must Be Warned",
    purpose=(
        "Warn when conversion dates fall outside the approved date range."
    ),
    source_tables=_DATE_FIELD_TABLES,
    source_fields=(
        "EFFDATE",
        "PACBILL",
        "DIRBILL",
        "REINBILL",
        "MEFFDATE",
    ),
    business_rule=(
        "Approved date fields across conversion tables. Inclusive bounds: minimum "
        "1900-01-01; maximum = add_calendar_months(governance run date, 12). Dates "
        "outside the range generate warnings. Source values are not modified."
    ),
    severity="Advisory",
    failure_conditions=(
        "A populated date is earlier than January 1, 1900.",
        "A populated date is later than the governance run date plus 12 calendar months.",
    ),
)

ALL_QUIKPLAN_RULES = (
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
)
