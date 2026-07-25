"""DG-QUIKMSTR (002–026), DG-QUIKCLNT, and DG-QUIKCLID — Policy Data Governance catalog."""

from __future__ import annotations

from data_governance.catalog.governance_items import GovernanceItem, RuleDefinition

# Parent governance_items.py owns GOVERNANCE_ITEM_QUIKMSTR and RULE_DG_QUIKMSTR_001.
# Apply this description when expanding item 2 to full Policy Master scope.
GOVERNANCE_ITEM_QUIKMSTR_POLICY_DESCRIPTION = (
    "Validate policy master records for unique policy numbers, status and dates, "
    "billing setup, client references, approved defaults, and forced blank beneficiary IDs."
)

_GOVERNANCE_ITEM_ID_QUIKMSTR = "DG-QUIKMSTR"
_GOVERNANCE_ITEM_ID_QUIKCLNT = "DG-QUIKCLNT"
_GOVERNANCE_ITEM_ID_QUIKCLID = "DG-QUIKCLID"

RULE_DG_QUIKMSTR_002 = RuleDefinition(
    rule_id="DG-QUIKMSTR-002",
    governance_item_id=_GOVERNANCE_ITEM_ID_QUIKMSTR,
    technical_name="Validate Policy Status",
    business_name="Policy Status Is Required And Valid",
    purpose="Ensure every policy has a populated status in the approved policy-status code list.",
    source_tables=("QuikMstr",),
    source_fields=("MPOLICY", "MSTATUS"),
    business_rule=(
        "MSTATUS must be nonblank after trim and must exist in policy_code_authorities "
        "MSTATUS. Do not invent status codes."
    ),
    severity="Critical",
    failure_conditions=(
        "MSTATUS is null or blank.",
        "MSTATUS is not in the approved policy-status code list.",
    ),
)

RULE_DG_QUIKMSTR_003 = RuleDefinition(
    rule_id="DG-QUIKMSTR-003",
    governance_item_id=_GOVERNANCE_ITEM_ID_QUIKMSTR,
    technical_name="Validate Status Date",
    business_name="Status Date Is Required",
    purpose="Ensure every policy has a valid status date within the approved date range.",
    source_tables=("QuikMstr",),
    source_fields=("MPOLICY", "MSTATDATE"),
    business_rule=(
        "MSTATDATE must decode to a valid calendar date on or after 1900-01-01 and on or "
        "before the governance run date plus 12 calendar months."
    ),
    severity="Critical",
    failure_conditions=(
        "MSTATDATE is null or blank.",
        "MSTATDATE is invalid or unreadable.",
        "MSTATDATE is outside the approved date range.",
    ),
)

RULE_DG_QUIKMSTR_004 = RuleDefinition(
    rule_id="DG-QUIKMSTR-004",
    governance_item_id=_GOVERNANCE_ITEM_ID_QUIKMSTR,
    technical_name="Validate Issue Date",
    business_name="Issue Date Is Required",
    purpose="Ensure every policy has a valid issue date (physical field MISSDT).",
    source_tables=("QuikMstr",),
    source_fields=("MPOLICY", "MISSDT"),
    business_rule=(
        "MISSDT must decode to a valid calendar date on or after 1900-01-01 and on or "
        "before the governance run date plus 12 calendar months."
    ),
    severity="Critical",
    failure_conditions=(
        "MISSDT is null or blank.",
        "MISSDT is invalid or unreadable.",
        "MISSDT is outside the approved date range.",
    ),
)

RULE_DG_QUIKMSTR_005 = RuleDefinition(
    rule_id="DG-QUIKMSTR-005",
    governance_item_id=_GOVERNANCE_ITEM_ID_QUIKMSTR,
    technical_name="Validate Paid-To Versus Issue Date",
    business_name="Paid-To Date Cannot Be Before Issue Date",
    purpose="Ensure the paid-to date is not earlier than the issue date.",
    source_tables=("QuikMstr",),
    source_fields=("MPOLICY", "MPAIDTO", "MISSDT"),
    business_rule=(
        "When MPAIDTO and MISSDT are both valid dates, MPAIDTO must be on or after MISSDT."
    ),
    severity="Critical",
    failure_conditions=(
        "MPAIDTO is earlier than MISSDT when both dates are valid.",
        "MPAIDTO is required but null, blank, or unreadable.",
    ),
)

RULE_DG_QUIKMSTR_006 = RuleDefinition(
    rule_id="DG-QUIKMSTR-006",
    governance_item_id=_GOVERNANCE_ITEM_ID_QUIKMSTR,
    technical_name="Validate Bill-To Versus Issue Date",
    business_name="Bill-To Date Cannot Be Before Issue Date",
    purpose="Ensure the bill-to date is not earlier than the issue date.",
    source_tables=("QuikMstr",),
    source_fields=("MPOLICY", "MBILLTO", "MISSDT"),
    business_rule=(
        "When MBILLTO and MISSDT are both valid dates, MBILLTO must be on or after MISSDT."
    ),
    severity="Critical",
    failure_conditions=(
        "MBILLTO is earlier than MISSDT when both dates are valid.",
        "MBILLTO is required but null, blank, or unreadable.",
    ),
)

RULE_DG_QUIKMSTR_007 = RuleDefinition(
    rule_id="DG-QUIKMSTR-007",
    governance_item_id=_GOVERNANCE_ITEM_ID_QUIKMSTR,
    technical_name="Validate Bill-To Versus Paid-To Date",
    business_name="Bill-To Date Cannot Be Before Paid-To Date",
    purpose="Ensure the bill-to date is not earlier than the paid-to date.",
    source_tables=("QuikMstr",),
    source_fields=("MPOLICY", "MBILLTO", "MPAIDTO"),
    business_rule=(
        "When MBILLTO and MPAIDTO are both valid dates, MBILLTO must be on or after MPAIDTO."
    ),
    severity="Critical",
    failure_conditions=(
        "MBILLTO is earlier than MPAIDTO when both dates are valid.",
    ),
)

RULE_DG_QUIKMSTR_008 = RuleDefinition(
    rule_id="DG-QUIKMSTR-008",
    governance_item_id=_GOVERNANCE_ITEM_ID_QUIKMSTR,
    technical_name="Validate Nonforfeiture Option Default",
    business_name="Nonforfeiture Option Must Default To Zero",
    purpose="Ensure MNFOPT is populated with the approved default when blank.",
    source_tables=("QuikMstr",),
    source_fields=("MPOLICY", "MNFOPT"),
    business_rule=(
        "Blank or null MNFOPT must default to 0 in converted output. Populated values must "
        "be approved MNFOPT codes; invalid populated values fail. Do not replace valid "
        "nonzero options with 0."
    ),
    severity="Error",
    failure_conditions=(
        "MNFOPT is populated with an unapproved value.",
        "MNFOPT remains blank in converted output when a default was required.",
    ),
)

RULE_DG_QUIKMSTR_009 = RuleDefinition(
    rule_id="DG-QUIKMSTR-009",
    governance_item_id=_GOVERNANCE_ITEM_ID_QUIKMSTR,
    technical_name="Validate Dividend Option",
    business_name="Dividend Option Governance Deferred",
    purpose=(
        "Deferred: dividend-option values and default behavior require additional "
        "business direction. Do not fail on MDIVOPT."
    ),
    source_tables=("QuikMstr",),
    source_fields=("MPOLICY", "MDIVOPT"),
    business_rule=(
        "Deferred rule — do not validate MDIVOPT or generate failures until approved "
        "dividend-option values are defined."
    ),
    severity="Advisory",
    failure_conditions=(),
    implementation_status="Deferred",
)

RULE_DG_QUIKMSTR_010 = RuleDefinition(
    rule_id="DG-QUIKMSTR-010",
    governance_item_id=_GOVERNANCE_ITEM_ID_QUIKMSTR,
    technical_name="Validate Billing Form",
    business_name="Billing Form Is Required And Valid",
    purpose="Ensure every policy has a valid billing-form code.",
    source_tables=("QuikMstr",),
    source_fields=("MPOLICY", "MBILLFRM"),
    business_rule=(
        "MBILLFRM must be nonblank after trim and must exist in policy_code_authorities "
        "MBILLFRM. Do not default unknown billing forms."
    ),
    severity="Critical",
    failure_conditions=(
        "MBILLFRM is null or blank.",
        "MBILLFRM is not in the approved billing-form code list.",
    ),
)

RULE_DG_QUIKMSTR_011 = RuleDefinition(
    rule_id="DG-QUIKMSTR-011",
    governance_item_id=_GOVERNANCE_ITEM_ID_QUIKMSTR,
    technical_name="Validate Billing Day From Issue Date",
    business_name="Billing Day Defaults From Issue Date",
    purpose="Ensure MBILLDAY is valid, deriving from MISSDT when blank or zero.",
    source_tables=("QuikMstr",),
    source_fields=("MPOLICY", "MBILLDAY", "MISSDT"),
    business_rule=(
        "When MBILLDAY is blank or zero and MISSDT is valid, set MBILLDAY to the calendar "
        "day of MISSDT. Validate MBILLDAY is within the allowed application range. Do not "
        "derive when MISSDT is missing or invalid."
    ),
    severity="Error",
    failure_conditions=(
        "MBILLDAY is outside the allowed range.",
        "MBILLDAY remains blank or zero when MISSDT was valid and derivation was required.",
        "MISSDT is invalid — billing-day derivation could not be checked.",
    ),
)

RULE_DG_QUIKMSTR_012 = RuleDefinition(
    rule_id="DG-QUIKMSTR-012",
    governance_item_id=_GOVERNANCE_ITEM_ID_QUIKMSTR,
    technical_name="Validate Bank Account For Bank Draft",
    business_name="Bank Account Is Required For Bank Draft",
    purpose="Ensure bank-draft policies have a populated bank account number.",
    source_tables=("QuikMstr",),
    source_fields=("MPOLICY", "MBILLFRM", "MBANKNO"),
    business_rule=(
        "When MBILLFRM equals 2 (bank draft / PAC), MBANKNO must be populated after trim. "
        "Do not invent bank account numbers."
    ),
    severity="Critical",
    failure_conditions=(
        "MBILLFRM is 2 and MBANKNO is null or blank.",
    ),
)

RULE_DG_QUIKMSTR_013 = RuleDefinition(
    rule_id="DG-QUIKMSTR-013",
    governance_item_id=_GOVERNANCE_ITEM_ID_QUIKMSTR,
    technical_name="Validate Payment Mode",
    business_name="Payment Mode Is Required And Valid",
    purpose="Ensure every policy has a valid payment-mode code.",
    source_tables=("QuikMstr",),
    source_fields=("MPOLICY", "MMODE"),
    business_rule=(
        "MMODE must be nonblank after trim and must exist in policy_code_authorities "
        "MMODE. Do not guess payment modes."
    ),
    severity="Critical",
    failure_conditions=(
        "MMODE is null or blank.",
        "MMODE is not in the approved payment-mode code list.",
    ),
)

RULE_DG_QUIKMSTR_014 = RuleDefinition(
    rule_id="DG-QUIKMSTR-014",
    governance_item_id=_GOVERNANCE_ITEM_ID_QUIKMSTR,
    technical_name="Validate Issue State",
    business_name="Issue State Is Required And Valid",
    purpose="Ensure every policy has a valid United States issue state code.",
    source_tables=("QuikMstr",),
    source_fields=("MPOLICY", "MISSUEST"),
    business_rule=(
        "MISSUEST must be populated and must be an approved two-character United States "
        "state or DC abbreviation. Valid lowercase values may be normalized to uppercase "
        "in converted output. Do not guess missing states."
    ),
    severity="Critical",
    failure_conditions=(
        "MISSUEST is null or blank.",
        "MISSUEST is not an approved state abbreviation.",
    ),
)

RULE_DG_QUIKMSTR_015 = RuleDefinition(
    rule_id="DG-QUIKMSTR-015",
    governance_item_id=_GOVERNANCE_ITEM_ID_QUIKMSTR,
    technical_name="Validate Group Number Reference",
    business_name="Group Number Must Exist When Populated",
    purpose="Ensure a populated group number exists in Group Billing Setup.",
    source_tables=("QuikMstr", "QuikList"),
    source_fields=("MPOLICY", "MGROUP", "QuikList.MGROUP"),
    business_rule=(
        "Blank MGROUP passes. A populated normalized MGROUP must match a group number in "
        "QuikList. Do not create group records automatically."
    ),
    severity="Critical",
    failure_conditions=(
        "MGROUP is populated and does not exist in QuikList.",
        "QuikList is not available — report Could Not Be Checked once.",
    ),
)

RULE_DG_QUIKMSTR_016 = RuleDefinition(
    rule_id="DG-QUIKMSTR-016",
    governance_item_id=_GOVERNANCE_ITEM_ID_QUIKMSTR,
    technical_name="Validate Primary Insured Client Reference",
    business_name="Primary Insured Client Must Exist",
    purpose="Ensure a populated primary insured client ID exists in Client Setup.",
    source_tables=("QuikMstr", "QuikClnt"),
    source_fields=("MPOLICY", "MPRIMID", "MCLIENTID"),
    business_rule=(
        "When MPRIMID is populated after trim, it must match exactly one QuikClnt "
        "MCLIENTID. Blank passes when the role is not applicable. Do not create clients."
    ),
    severity="Critical",
    failure_conditions=(
        "MPRIMID is populated and does not exist in QuikClnt.",
        "QuikClnt is not available — report Could Not Be Checked once.",
    ),
)

RULE_DG_QUIKMSTR_017 = RuleDefinition(
    rule_id="DG-QUIKMSTR-017",
    governance_item_id=_GOVERNANCE_ITEM_ID_QUIKMSTR,
    technical_name="Validate Owner Client Reference",
    business_name="Owner Client Must Exist",
    purpose="Ensure a populated owner client ID exists in Client Setup.",
    source_tables=("QuikMstr", "QuikClnt"),
    source_fields=("MPOLICY", "MOWNRID", "MCLIENTID"),
    business_rule=(
        "When MOWNRID is populated after trim, it must match exactly one QuikClnt "
        "MCLIENTID. Blank passes. Do not substitute another client role."
    ),
    severity="Critical",
    failure_conditions=(
        "MOWNRID is populated and does not exist in QuikClnt.",
        "QuikClnt is not available — report Could Not Be Checked once.",
    ),
)

RULE_DG_QUIKMSTR_018 = RuleDefinition(
    rule_id="DG-QUIKMSTR-018",
    governance_item_id=_GOVERNANCE_ITEM_ID_QUIKMSTR,
    technical_name="Validate Assignee Client Reference",
    business_name="Assignee Client Must Exist",
    purpose="Ensure a populated assignee client ID exists in Client Setup.",
    source_tables=("QuikMstr", "QuikClnt"),
    source_fields=("MPOLICY", "MASGNID", "MCLIENTID"),
    business_rule=(
        "When MASGNID is populated after trim, it must match exactly one QuikClnt "
        "MCLIENTID. Blank passes."
    ),
    severity="Critical",
    failure_conditions=(
        "MASGNID is populated and does not exist in QuikClnt.",
        "QuikClnt is not available — report Could Not Be Checked once.",
    ),
)

RULE_DG_QUIKMSTR_019 = RuleDefinition(
    rule_id="DG-QUIKMSTR-019",
    governance_item_id=_GOVERNANCE_ITEM_ID_QUIKMSTR,
    technical_name="Validate Payer Client Reference",
    business_name="Payer Client Must Exist",
    purpose="Ensure a populated payer client ID exists in Client Setup.",
    source_tables=("QuikMstr", "QuikClnt"),
    source_fields=("MPOLICY", "MPAYRID", "MCLIENTID"),
    business_rule=(
        "When MPAYRID is populated after trim, it must match exactly one QuikClnt "
        "MCLIENTID. Blank passes."
    ),
    severity="Critical",
    failure_conditions=(
        "MPAYRID is populated and does not exist in QuikClnt.",
        "QuikClnt is not available — report Could Not Be Checked once.",
    ),
)

RULE_DG_QUIKMSTR_020 = RuleDefinition(
    rule_id="DG-QUIKMSTR-020",
    governance_item_id=_GOVERNANCE_ITEM_ID_QUIKMSTR,
    technical_name="Validate Owner-Company Client Reference",
    business_name="Owner-Company Client Must Exist",
    purpose="Ensure a populated owner-company client ID exists in Client Setup.",
    source_tables=("QuikMstr", "QuikClnt"),
    source_fields=("MPOLICY", "MOWNCID", "MCLIENTID"),
    business_rule=(
        "When MOWNCID is populated after trim, it must match exactly one QuikClnt "
        "MCLIENTID. Blank passes."
    ),
    severity="Critical",
    failure_conditions=(
        "MOWNCID is populated and does not exist in QuikClnt.",
        "QuikClnt is not available — report Could Not Be Checked once.",
    ),
)

RULE_DG_QUIKMSTR_021 = RuleDefinition(
    rule_id="DG-QUIKMSTR-021",
    governance_item_id=_GOVERNANCE_ITEM_ID_QUIKMSTR,
    technical_name="Validate Primary Beneficiary ID Blank",
    business_name="Primary Beneficiary ID Must Be Blank",
    purpose="Ensure beneficiary IDs are not stored on Policy Master.",
    source_tables=("QuikMstr",),
    source_fields=("MPOLICY", "MBENPID"),
    business_rule=(
        "MBENPID must be blank in converted output. Clear populated values and record a "
        "transformation note. Do not delete client or relationship records."
    ),
    severity="Error",
    failure_conditions=(
        "MBENPID is populated in converted output.",
    ),
)

RULE_DG_QUIKMSTR_022 = RuleDefinition(
    rule_id="DG-QUIKMSTR-022",
    governance_item_id=_GOVERNANCE_ITEM_ID_QUIKMSTR,
    technical_name="Validate Contingent Beneficiary ID Blank",
    business_name="Contingent Beneficiary ID Must Be Blank",
    purpose="Ensure contingent beneficiary IDs are not stored on Policy Master.",
    source_tables=("QuikMstr",),
    source_fields=("MPOLICY", "MBENCID"),
    business_rule=(
        "MBENCID must be blank in converted output. Clear populated values and record a "
        "transformation note."
    ),
    severity="Error",
    failure_conditions=(
        "MBENCID is populated in converted output.",
    ),
)

RULE_DG_QUIKMSTR_023 = RuleDefinition(
    rule_id="DG-QUIKMSTR-023",
    governance_item_id=_GOVERNANCE_ITEM_ID_QUIKMSTR,
    technical_name="Validate Application Versus Issue Date",
    business_name="Application Date Cannot Be After Issue Date",
    purpose="Ensure the application date is not later than the issue date.",
    source_tables=("QuikMstr",),
    source_fields=("MPOLICY", "MAPPDATE", "MISSDT"),
    business_rule=(
        "When MAPPDATE and MISSDT are both valid dates, MAPPDATE must be on or before "
        "MISSDT. Do not change dates without an approved source."
    ),
    severity="Critical",
    failure_conditions=(
        "MAPPDATE is later than MISSDT when both dates are valid.",
    ),
)

RULE_DG_QUIKMSTR_024 = RuleDefinition(
    rule_id="DG-QUIKMSTR-024",
    governance_item_id=_GOVERNANCE_ITEM_ID_QUIKMSTR,
    technical_name="Validate Issue Country Default",
    business_name="Issue Country Must Default To 0000",
    purpose="Ensure MISSCNTRY is populated with the approved default when blank.",
    source_tables=("QuikMstr",),
    source_fields=("MPOLICY", "MISSCNTRY"),
    business_rule=(
        "Blank or null MISSCNTRY must default to 0000 in converted output. Populated "
        "values must be approved country codes when a reference list exists."
    ),
    severity="Error",
    failure_conditions=(
        "MISSCNTRY is populated with an unapproved value.",
        "MISSCNTRY remains blank in converted output when a default was required.",
    ),
)

RULE_DG_QUIKMSTR_025 = RuleDefinition(
    rule_id="DG-QUIKMSTR-025",
    governance_item_id=_GOVERNANCE_ITEM_ID_QUIKMSTR,
    technical_name="Validate Residence State",
    business_name="Residence State Governance Deferred",
    purpose=(
        "Deferred: business has not decided whether MRESSTATE is required or how it is "
        "derived. Do not fail on MRESSTATE."
    ),
    source_tables=("QuikMstr",),
    source_fields=("MPOLICY", "MRESSTATE"),
    business_rule=(
        "Deferred rule — do not validate or populate MRESSTATE until business direction "
        "is complete. Do not generate failures."
    ),
    severity="Advisory",
    failure_conditions=(),
    implementation_status="Deferred",
)

RULE_DG_QUIKMSTR_026 = RuleDefinition(
    rule_id="DG-QUIKMSTR-026",
    governance_item_id=_GOVERNANCE_ITEM_ID_QUIKMSTR,
    technical_name="Validate Issue Class Default",
    business_name="Issue Class Must Default To 00",
    purpose="Ensure MISSCLASS is populated with the approved default when blank.",
    source_tables=("QuikMstr",),
    source_fields=("MPOLICY", "MISSCLASS"),
    business_rule=(
        "Blank or null MISSCLASS must default to 00 in converted output. Preserve "
        "approved nonblank issue classes; validate populated values when a reference exists."
    ),
    severity="Error",
    failure_conditions=(
        "MISSCLASS is populated with an unapproved value.",
        "MISSCLASS remains blank in converted output when a default was required.",
    ),
)

# --- Issue #108G: cross-table policy/coverage status consistency (Robert, 2026-07-25) ---
# These compare QuikMstr policy status against QuikRidr coverage status. They exist so the
# converter can stop forcing statuses and let governance report inconsistencies instead.

RULE_DG_QUIKMSTR_027 = RuleDefinition(
    rule_id="DG-QUIKMSTR-027",
    governance_item_id=_GOVERNANCE_ITEM_ID_QUIKMSTR,
    technical_name="Validate Terminated Policy Has No In-Force Coverage",
    business_name="Terminated Policy Must Not Have In-Force Coverage",
    purpose=(
        "Ensure a terminated policy carries no coverage that is still in force. If the "
        "policy is terminated, every coverage should be terminated too."
    ),
    source_tables=("QuikMstr", "QuikRidr"),
    source_fields=("MPOLICY", "MSTATUS", "MPHASE", "MPHSTAT"),
    business_rule=(
        "When QuikMstr MSTATUS is 50 or greater, no QuikRidr row for that policy may carry "
        "MPHSTAT below 50. Report the coverage rows, do not change them."
    ),
    severity="Critical",
    failure_conditions=(
        "Policy MSTATUS is 50 or greater and a coverage MPHSTAT is below 50.",
    ),
)

RULE_DG_QUIKMSTR_028 = RuleDefinition(
    rule_id="DG-QUIKMSTR-028",
    governance_item_id=_GOVERNANCE_ITEM_ID_QUIKMSTR,
    technical_name="Validate NFO Phase 1 Status Matches Policy Status",
    business_name="ETI Or RPU Phase 1 Coverage Must Match Policy Status",
    purpose=(
        "Ensure the base coverage on a nonforfeiture policy carries the same status as the "
        "policy. When a policy goes to ETI or RPU, phase 1 moves with it."
    ),
    source_tables=("QuikMstr", "QuikRidr"),
    source_fields=("MPOLICY", "MSTATUS", "MPHASE", "MPHSTAT"),
    business_rule=(
        "When QuikMstr MSTATUS is 44 (ETI) or 45 (RPU), the QuikRidr phase 1 row must carry "
        "the same MPHSTAT value."
    ),
    severity="Critical",
    failure_conditions=(
        "Policy MSTATUS is 44 or 45 and the phase 1 MPHSTAT differs.",
        "Policy MSTATUS is 44 or 45 and no phase 1 coverage row exists.",
    ),
)

RULE_DG_QUIKMSTR_029 = RuleDefinition(
    rule_id="DG-QUIKMSTR-029",
    governance_item_id=_GOVERNANCE_ITEM_ID_QUIKMSTR,
    technical_name="Review NFO Policy Later Phase Coverages",
    business_name="ETI Or RPU Policy Should Not Have Other In-Force Coverages",
    purpose=(
        "Flag coverages beyond phase 1 that are still in force on a nonforfeiture policy. "
        "Normally all other coverages terminate, so these need source confirmation."
    ),
    source_tables=("QuikMstr", "QuikRidr"),
    source_fields=("MPOLICY", "MSTATUS", "MPHASE", "MPLAN", "MPHSTAT"),
    business_rule=(
        "When QuikMstr MSTATUS is 44 or 45, report any QuikRidr row with MPHASE above 1 and "
        "MPHSTAT below 50. Plans 1SALML and 1SALMI are excluded: on those policies the phase "
        "1 base carries zero units and the phase 2 rider holds the entire face amount, so an "
        "in-force later phase is the expected structure rather than a defect. Advisory only "
        "— confirm against the source system before acting."
    ),
    severity="Advisory",
    failure_conditions=(
        "Policy MSTATUS is 44 or 45 and a phase 2 or later coverage has MPHSTAT below 50.",
    ),
)

RULE_DG_QUIKMSTR_030 = RuleDefinition(
    rule_id="DG-QUIKMSTR-030",
    governance_item_id=_GOVERNANCE_ITEM_ID_QUIKMSTR,
    technical_name="Validate Active Policy Has In-Force Coverage",
    business_name="Active Policy Must Have At Least One In-Force Coverage",
    purpose=(
        "Ensure an active policy carries at least one coverage that is still in force. A "
        "policy cannot be in force with no in-force coverage."
    ),
    source_tables=("QuikMstr", "QuikRidr"),
    source_fields=("MPOLICY", "MSTATUS", "MPHASE", "MPHSTAT"),
    business_rule=(
        "When QuikMstr MSTATUS is below 44, at least one QuikRidr row for that policy must "
        "carry MPHSTAT below 50."
    ),
    severity="Critical",
    failure_conditions=(
        "Policy MSTATUS is below 44 and every coverage MPHSTAT is 50 or greater.",
        "Policy MSTATUS is below 44 and the policy has no coverage rows at all.",
    ),
)

RULE_DG_QUIKMSTR_031 = RuleDefinition(
    rule_id="DG-QUIKMSTR-031",
    governance_item_id=_GOVERNANCE_ITEM_ID_QUIKMSTR,
    technical_name="Review NFO Election Against Policy Status",
    business_name="ETI Or RPU Election Should Match Policy Status",
    purpose=(
        "Flag nonforfeiture policies whose recorded election disagrees with the policy "
        "status so the source system can be checked."
    ),
    source_tables=("QuikMstr", "QuikRidr"),
    source_fields=("MPOLICY", "MSTATUS", "MNFOPT"),
    business_rule=(
        "When QuikMstr MSTATUS is 44 the election MNFOPT is expected to be 2 (ETI); when "
        "MSTATUS is 45 it is expected to be 3 (RPU). Report disagreements for source review. "
        "Do not overwrite the election — it carries the source value on purpose (Issue #72 "
        "downgrade, Issue #108F)."
    ),
    severity="Advisory",
    failure_conditions=(
        "MSTATUS is 44 and MNFOPT is not 2.",
        "MSTATUS is 45 and MNFOPT is not 3.",
    ),
)

RULE_DG_QUIKMSTR_032 = RuleDefinition(
    rule_id="DG-QUIKMSTR-032",
    governance_item_id=_GOVERNANCE_ITEM_ID_QUIKMSTR,
    technical_name="Validate NFO Policy Field Completeness",
    business_name="ETI Or RPU Policy Fields Must Be Complete",
    purpose=(
        "Ensure the nonforfeiture field set is internally consistent on every ETI and RPU "
        "policy, so a later change cannot quietly undo the Issue #108 conversion rules."
    ),
    source_tables=("QuikMstr", "QuikRidr"),
    source_fields=(
        "MPOLICY",
        "MSTATUS",
        "MPAIDTO",
        "MPHASE",
        "MPLAN",
        "MAGE",
        "MPAYUP",
        "MPREM",
        "MPHSTAT",
        "MSAVESTAT",
    ),
    business_rule=(
        "On a policy with MSTATUS 44 or 45: phase 1 MPAYUP must equal MPAIDTO; phase 1 MAGE "
        "must be populated and nonzero; the phase 1 save fields MSAVEAGE, MSAVEUNIT, "
        "MSAVEVPU, MSAVEPREM and MSAVESTAT must be blank; MPREM must be zero when MSTATUS is "
        "44; and any paid-up addition coverage must carry MPHSTAT 54."
    ),
    severity="Error",
    failure_conditions=(
        "Phase 1 MPAYUP does not equal policy MPAIDTO.",
        "Phase 1 MAGE is blank or zero.",
        "A phase 1 save field is populated.",
        "MSTATUS is 44 and phase 1 MPREM is not zero.",
        "A paid-up addition coverage is not terminated at 54.",
    ),
)

GOVERNANCE_ITEM_QUIKCLNT = GovernanceItem(
    item_id=_GOVERNANCE_ITEM_ID_QUIKCLNT,
    item_number=8,
    name="Client Setup",
    description=(
        "Validate client records for unique client IDs, required names and codes, "
        "contact information, and approved defaults for type, tax-ID type, and language."
    ),
)

RULE_DG_QUIKCLNT_001 = RuleDefinition(
    rule_id="DG-QUIKCLNT-001",
    governance_item_id=_GOVERNANCE_ITEM_ID_QUIKCLNT,
    technical_name="Validate Unique Client ID",
    business_name="Client ID Must Be Unique",
    purpose="Ensure each client ID appears only once in Client Setup.",
    source_tables=("QuikClnt",),
    source_fields=("MCLIENTID",),
    business_rule=(
        "After standard DBF character normalization, each nonblank MCLIENTID must occur "
        "exactly once. Blank or null MCLIENTID fails. Do not merge or reassign IDs."
    ),
    severity="Critical",
    failure_conditions=(
        "The same normalized MCLIENTID occurs more than once.",
        "MCLIENTID is null or blank.",
    ),
)

RULE_DG_QUIKCLNT_002 = RuleDefinition(
    rule_id="DG-QUIKCLNT-002",
    governance_item_id=_GOVERNANCE_ITEM_ID_QUIKCLNT,
    technical_name="Validate Client Type",
    business_name="Client Type Is Required",
    purpose="Ensure every client has a valid client type, defaulting to Individual.",
    source_tables=("QuikClnt",),
    source_fields=("MCLIENTID", "MTYPE"),
    business_rule=(
        "Blank MTYPE must default to I in converted output. Populated values must be "
        "approved client-type codes. Do not replace valid organization or trust types with I."
    ),
    severity="Error",
    failure_conditions=(
        "MTYPE is populated with an unapproved value.",
        "MTYPE remains blank in converted output when a default was required.",
    ),
)

RULE_DG_QUIKCLNT_003 = RuleDefinition(
    rule_id="DG-QUIKCLNT-003",
    governance_item_id=_GOVERNANCE_ITEM_ID_QUIKCLNT,
    technical_name="Validate Tax ID Type Default",
    business_name="Tax ID Type Must Default To S",
    purpose="Ensure MTAXIDTYPE is populated with the approved default when blank.",
    source_tables=("QuikClnt",),
    source_fields=("MCLIENTID", "MTAXIDTYPE"),
    business_rule=(
        "Blank MTAXIDTYPE must default to S in converted output. Preserve other approved "
        "tax-ID types. Do not overwrite valid EIN or other types."
    ),
    severity="Error",
    failure_conditions=(
        "MTAXIDTYPE is populated with an unapproved value.",
        "MTAXIDTYPE remains blank in converted output when a default was required.",
    ),
)

RULE_DG_QUIKCLNT_004 = RuleDefinition(
    rule_id="DG-QUIKCLNT-004",
    governance_item_id=_GOVERNANCE_ITEM_ID_QUIKCLNT,
    technical_name="Validate Required Last Name",
    business_name="Last Name Is Required",
    purpose="Ensure individual clients have a populated last name (physical field MLNAME).",
    source_tables=("QuikClnt",),
    source_fields=("MCLIENTID", "MTYPE", "MLNAME"),
    business_rule=(
        "For MTYPE Individual (I), MLNAME must contain a meaningful nonblank value after "
        "trim. Do not invent names."
    ),
    severity="Critical",
    failure_conditions=(
        "MTYPE is Individual and MLNAME is null or blank.",
    ),
)

RULE_DG_QUIKCLNT_005 = RuleDefinition(
    rule_id="DG-QUIKCLNT-005",
    governance_item_id=_GOVERNANCE_ITEM_ID_QUIKCLNT,
    technical_name="Validate Client Contact Information",
    business_name="Client Contact Information Warning",
    purpose="Warn when a client has no usable name or mailing-address information.",
    source_tables=("QuikClnt",),
    source_fields=("MCLIENTID", "MADDR1", "MLNAME", "MFNAME", "MCITY", "MSTATE", "MZIP"),
    business_rule=(
        "When MADDR1, MLNAME, MFNAME, MCITY, MSTATE, and MZIP are all blank, issue a "
        "Warning. Do not fail solely on this rule when MLNAME already satisfies rule 004."
    ),
    severity="Advisory",
    failure_conditions=(
        "All verified name and mailing fields are blank.",
    ),
)

RULE_DG_QUIKCLNT_006 = RuleDefinition(
    rule_id="DG-QUIKCLNT-006",
    governance_item_id=_GOVERNANCE_ITEM_ID_QUIKCLNT,
    technical_name="Validate Date Of Birth",
    business_name="Date Of Birth Must Be Valid",
    purpose="Ensure populated dates of birth are valid and not in the future.",
    source_tables=("QuikClnt",),
    source_fields=("MCLIENTID", "MTYPE", "MDOB"),
    business_rule=(
        "When MDOB is populated, it must decode to a valid date on or after 1900-01-01 "
        "and on or before the governance run date. Individual clients with blank MDOB "
        "generate a Warning. Non-individual clients may have blank MDOB."
    ),
    severity="Error",
    failure_conditions=(
        "MDOB is populated but invalid or unreadable.",
        "MDOB is after the governance run date.",
        "MDOB is before 1900-01-01.",
        "Individual client has blank MDOB (Warning).",
    ),
)

RULE_DG_QUIKCLNT_007 = RuleDefinition(
    rule_id="DG-QUIKCLNT-007",
    governance_item_id=_GOVERNANCE_ITEM_ID_QUIKCLNT,
    technical_name="Validate Sex Code",
    business_name="Sex Code Must Be M Or F",
    purpose="Ensure individual clients have a valid sex code.",
    source_tables=("QuikClnt",),
    source_fields=("MCLIENTID", "MTYPE", "MSEX"),
    business_rule=(
        "For individual clients, MSEX must be M or F after case normalization. Valid "
        "lowercase values may be uppercased in converted output. Do not default blank sex."
    ),
    severity="Error",
    failure_conditions=(
        "Individual client MSEX is blank.",
        "Individual client MSEX is not M or F after normalization.",
    ),
)

RULE_DG_QUIKCLNT_008 = RuleDefinition(
    rule_id="DG-QUIKCLNT-008",
    governance_item_id=_GOVERNANCE_ITEM_ID_QUIKCLNT,
    technical_name="Validate Language Default",
    business_name="Language Must Default To English",
    purpose="Ensure MLANGUAGE is populated with the approved default when blank.",
    source_tables=("QuikClnt",),
    source_fields=("MCLIENTID", "MLANGUAGE"),
    business_rule=(
        "Blank MLANGUAGE must default to E in converted output. Preserve other approved "
        "language codes when populated."
    ),
    severity="Error",
    failure_conditions=(
        "MLANGUAGE is populated with an unapproved value.",
        "MLANGUAGE remains blank in converted output when a default was required.",
    ),
)

GOVERNANCE_ITEM_QUIKCLID = GovernanceItem(
    item_id=_GOVERNANCE_ITEM_ID_QUIKCLID,
    item_number=9,
    name="Policy Relationships",
    description=(
        "Validate policy relationship rows for valid clients, policies, phases, "
        "relationship codes, and insured rider alignment."
    ),
)

RULE_DG_QUIKCLID_001 = RuleDefinition(
    rule_id="DG-QUIKCLID-001",
    governance_item_id=_GOVERNANCE_ITEM_ID_QUIKCLID,
    technical_name="Validate Relationship Client Reference",
    business_name="Client Must Exist",
    purpose="Ensure every relationship client ID exists in Client Setup.",
    source_tables=("QuikClid", "QuikClnt"),
    source_fields=("MCLIENTID", "MPOLICY", "MRELATION"),
    business_rule=(
        "MCLIENTID must be populated and must match a QuikClnt MCLIENTID. Do not create "
        "clients automatically."
    ),
    severity="Critical",
    failure_conditions=(
        "MCLIENTID is null or blank.",
        "MCLIENTID does not exist in QuikClnt.",
        "QuikClnt is not available — report Could Not Be Checked once.",
    ),
)

RULE_DG_QUIKCLID_002 = RuleDefinition(
    rule_id="DG-QUIKCLID-002",
    governance_item_id=_GOVERNANCE_ITEM_ID_QUIKCLID,
    technical_name="Validate Relationship Policy Reference",
    business_name="Policy Must Exist",
    purpose="Ensure every relationship policy number exists in Policy Master.",
    source_tables=("QuikClid", "QuikMstr"),
    source_fields=("MPOLICY", "MCLIENTID", "MRELATION"),
    business_rule=(
        "MPOLICY must be populated and must match a QuikMstr MPOLICY after policy-number "
        "normalization."
    ),
    severity="Critical",
    failure_conditions=(
        "MPOLICY is null or blank.",
        "MPOLICY does not exist in QuikMstr.",
        "QuikMstr is not available — report Could Not Be Checked once.",
    ),
)

RULE_DG_QUIKCLID_003 = RuleDefinition(
    rule_id="DG-QUIKCLID-003",
    governance_item_id=_GOVERNANCE_ITEM_ID_QUIKCLID,
    technical_name="Validate Nonzero Phase Rider Reference",
    business_name="Nonzero Phase Must Exist In Rider Setup",
    purpose="Ensure a nonzero relationship phase exists on the policy in QuikRidr.",
    source_tables=("QuikClid", "QuikRidr"),
    source_fields=("MPOLICY", "MPHASE", "MRELATION"),
    business_rule=(
        "When MPHASE is not zero, the (MPOLICY, MPHASE) pair must exist in QuikRidr."
    ),
    severity="Critical",
    failure_conditions=(
        "MPHASE is not zero and (MPOLICY, MPHASE) does not exist in QuikRidr.",
        "QuikRidr is not available — report Could Not Be Checked once.",
    ),
)

RULE_DG_QUIKCLID_004 = RuleDefinition(
    rule_id="DG-QUIKCLID-004",
    governance_item_id=_GOVERNANCE_ITEM_ID_QUIKCLID,
    technical_name="Validate Policy-Level Relationship Phase",
    business_name="Non-Insured Relationships Must Use Phase Zero",
    purpose="Ensure policy-level relationships use MPHASE zero.",
    source_tables=("QuikClid",),
    source_fields=("MPOLICY", "MCLIENTID", "MRELATION", "MPHASE"),
    business_rule=(
        "When MRELATION is not INSD (including OWNR, OWNC, PAYR, PRIM, ASGN, BENP, BENC), "
        "MPHASE must be 0 in converted output. Force non-INSD phases to 0 and record a "
        "transformation note when changed."
    ),
    severity="Error",
    failure_conditions=(
        "Non-INSD relationship has MPHASE other than 0 in converted output.",
    ),
)

RULE_DG_QUIKCLID_005 = RuleDefinition(
    rule_id="DG-QUIKCLID-005",
    governance_item_id=_GOVERNANCE_ITEM_ID_QUIKCLID,
    technical_name="Validate Insured Relationship Rider Match",
    business_name="Insured Relationship Must Match A Rider",
    purpose="Ensure INSD relationships align with an insured phase on QuikRidr.",
    source_tables=("QuikClid", "QuikRidr"),
    source_fields=("MPOLICY", "MPHASE", "MRELATION", "MCLIENTID"),
    business_rule=(
        "When MRELATION is INSD, MPHASE must not be zero unless the application explicitly "
        "uses phase zero for a base insured. (MPOLICY, MPHASE) must exist in QuikRidr. "
        "QuikClid has no MRIDRID — match on policy and phase only. One unambiguous rider "
        "match may derive phase in conversion; zero matches fail; multiple matches require review."
    ),
    severity="Critical",
    failure_conditions=(
        "INSD relationship has no matching (MPOLICY, MPHASE) in QuikRidr.",
        "INSD relationship has multiple possible rider matches.",
        "QuikRidr is not available — report Could Not Be Checked once.",
    ),
)

RULE_DG_QUIKCLID_006 = RuleDefinition(
    rule_id="DG-QUIKCLID-006",
    governance_item_id=_GOVERNANCE_ITEM_ID_QUIKCLID,
    technical_name="Validate Relationship Code",
    business_name="Relationship Code Must Be Valid",
    purpose="Ensure every relationship uses an approved relationship code.",
    source_tables=("QuikClid",),
    source_fields=("MPOLICY", "MCLIENTID", "MRELATION"),
    business_rule=(
        "MRELATION must be populated and must exist in policy_code_authorities MRELATION. "
        "Use approved source-to-target mapping in conversion; do not guess unknown codes."
    ),
    severity="Critical",
    failure_conditions=(
        "MRELATION is null or blank.",
        "MRELATION is not in the approved relationship-code list.",
    ),
)

ALL_POLICY_MSTR_RULES = (
    RULE_DG_QUIKMSTR_002,
    RULE_DG_QUIKMSTR_003,
    RULE_DG_QUIKMSTR_004,
    RULE_DG_QUIKMSTR_005,
    RULE_DG_QUIKMSTR_006,
    RULE_DG_QUIKMSTR_007,
    RULE_DG_QUIKMSTR_008,
    RULE_DG_QUIKMSTR_009,
    RULE_DG_QUIKMSTR_010,
    RULE_DG_QUIKMSTR_011,
    RULE_DG_QUIKMSTR_012,
    RULE_DG_QUIKMSTR_013,
    RULE_DG_QUIKMSTR_014,
    RULE_DG_QUIKMSTR_015,
    RULE_DG_QUIKMSTR_016,
    RULE_DG_QUIKMSTR_017,
    RULE_DG_QUIKMSTR_018,
    RULE_DG_QUIKMSTR_019,
    RULE_DG_QUIKMSTR_020,
    RULE_DG_QUIKMSTR_021,
    RULE_DG_QUIKMSTR_022,
    RULE_DG_QUIKMSTR_023,
    RULE_DG_QUIKMSTR_024,
    RULE_DG_QUIKMSTR_025,
    RULE_DG_QUIKMSTR_026,
    RULE_DG_QUIKMSTR_027,
    RULE_DG_QUIKMSTR_028,
    RULE_DG_QUIKMSTR_029,
    RULE_DG_QUIKMSTR_030,
    RULE_DG_QUIKMSTR_031,
    RULE_DG_QUIKMSTR_032,
)

ALL_QUIKCLNT_RULES = (
    RULE_DG_QUIKCLNT_001,
    RULE_DG_QUIKCLNT_002,
    RULE_DG_QUIKCLNT_003,
    RULE_DG_QUIKCLNT_004,
    RULE_DG_QUIKCLNT_005,
    RULE_DG_QUIKCLNT_006,
    RULE_DG_QUIKCLNT_007,
    RULE_DG_QUIKCLNT_008,
)

ALL_QUIKCLID_RULES = (
    RULE_DG_QUIKCLID_001,
    RULE_DG_QUIKCLID_002,
    RULE_DG_QUIKCLID_003,
    RULE_DG_QUIKCLID_004,
    RULE_DG_QUIKCLID_005,
    RULE_DG_QUIKCLID_006,
)
