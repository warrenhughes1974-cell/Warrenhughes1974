# Issue #108G — Status Consistency Governance Checks

**Track:** **Internal only** — not on the CSO / client issue log. See `Issue_108G_Internal_Track.md`.

**Date:** 2026-07-25
**Framework stage:** Development (stage 5), part 1 of 2
**Scope delivered:** Robert's four consistency checks + election review + NFO field completeness
**Scope deferred:** retiring the in-program status forcing (needs #108E answered)
**Production conversion code touched:** none — `app.py` is untouched, no version bump

## What Robert asked for

> "For conversion purposes, I do not think we should put rules in the generic conversion
> program to force the policy and rider statuses. There should be a crosswalk... After that
> is done, in the data governance or data validation program, I would add something to check
> for inconsistencies."

Before this change, `DG-QUIKMSTR` had 26 rules and none of them compared policy status to
coverage status. There was no QuikRidr-aware status rule anywhere.

## What was built

Six new rules in a new module,
`data_governance/rules/policy_master_integrity/dg_quikmstr_027_032_status_consistency.py`.

| Rule | Check | Severity | Result on current Output |
|---|---|---|---|
| 027 | Terminated policy must not have in-force coverage | Critical | PASS — 2,497 evaluated, 0 findings |
| 028 | ETI/RPU phase 1 status must match policy status | Critical | PASS — 400 evaluated, 0 findings |
| 029 | ETI/RPU should not have other in-force coverages | Advisory | PASS — 5 warnings, 77 excluded |
| 030 | Active policy must have an in-force coverage | Critical | PASS — 2,186 evaluated, 0 findings |
| 031 | ETI/RPU election should match policy status | Advisory | PASS — 277 warnings |
| 032 | ETI/RPU field completeness | Error | PASS — 400 evaluated, 0 findings |

Every count reconciles to the hand analysis in `Issue_108_Validation_Report.md` §4. Rule 029's
5 warnings are exactly the genuine leftovers identified for 108E (`9010779553C`,
`9010820645C`, `9011001302C`, `9011136641C`), and its 77 exclusions are exactly the
`1SALMI` rows.

## Design decisions worth recording

**The status boundary.** In force below 50, terminated at 50 or above. Robert wrote the rules
as "> 50". 50 itself is included because 15 policies carry `MSTATUS` 50 and excluding them
would leave a silent gap. Verified both readings give identical results today.

**Unreadable `MPHSTAT` is unknown, not terminated.** The first draft folded an unparseable
status into "terminated" via `or 99`. That was wrong in a way worth flagging: it would have
manufactured an "active policy with no in-force coverage" failure out of a missing field,
while the mirror-image rule 027 would have passed the same row. It also surfaced a real gap
in the shared test fixture, whose QuikRidr rows carried no `MPHSTAT` at all. The rules now
use an explicit three-state helper, and rule 030 reports Could Not Be Checked when no
coverage row on a policy has a readable status.

**Advisory rules emit WARN and stay PASS.** 029 and 031 raise questions for the source system
rather than rejecting data, which is exactly how Robert framed them — "might be good to at
least check for and question". A governance run does not fail on them, but the findings appear
in `2_Items_Needing_Attention.csv`.

**Why 028 reads zero.** The converter still forces phase 1 `MPHSTAT` from the policy status,
so phase 1 and policy status cannot disagree. The check is not redundant: it is the safety net
that has to exist *before* the force is retired. Standing it up first is the whole point of
sequencing 108G this way.

**`1SALML`/`1SALMI` exclusion.** Hard-coded in the rule with the reason in a comment and in
the catalog, and instrumented via `summary_metrics["zero_unit_base_rows_excluded"]` so the
exclusion is visible rather than invisible. Revisit when 108E is answered.

## Files changed

```text
data_governance/rules/policy_master_integrity/dg_quikmstr_027_032_status_consistency.py  new
data_governance/tests/test_dg_quikmstr_status_consistency.py                             new (26 tests)
data_governance/catalog/governance_items_policy_data.py   +6 RuleDefinition, ALL_POLICY_MSTR_RULES
data_governance/catalog/governance_items.py               re-export the 6 new rule names
data_governance/catalog/registry.py                       imports + 6 RegisteredRule entries
data_governance/reporting/business_descriptions.py        +6 plain-language descriptions
data_governance/docs/RULE_CATALOG.md                      item 2 summary + 027-032 section
data_governance/tests/test_framework.py                   rule count 100 -> 106
data_governance/tests/conftest.py                         clean fixture QuikRidr rows gain MPHSTAT
```

## Verification

```text
python -m pytest data_governance/tests -q
243 passed
```

Registry reports 106 rules. All six new rules execute against
`QLA_Migration/Output/` and reconcile to the hand analysis.

Two test-support changes were needed and are legitimate rather than accommodations:

1. `test_framework.py` asserted a hard rule count of 100. Now 106.
2. `conftest.py`'s `clean_company_tables` fixture described two active policies whose only
   coverage row had no `MPHSTAT`. A fixture claiming to be clean should carry the field, so
   it now does. No assertion was weakened.

## Remaining for 108G

Retiring the in-program forcing, which is the second half of the track:

1. Phase 1 `MPHSTAT` inherit (`app.py`, "Prefer Issue #13 provisional status" block). Issue
   #109 confirmed this is functioning correctly and choosing the right status, so the
   question is purely whether governance should own the rule instead.
2. The Issue #59 hard-coded seven-policy allowlist.

Both need Robert's 108E answer first, because check 029 has to be trusted before removing
the code that currently keeps 2b artificially quiet. Removing the forcing requires an `app.py`
change, a version bump, a full batch and a regression pass — a separate release from this one.

## Related

- `Issue_108_Resolution_Summary.md`
- `Issue_108_Validation_Report.md` §4 — the four checks measured by hand
- `Issue_Log_Items/Issue_109/Issue_109_Planning_Report.md` — phase 1 inherit is healthy
- `data_governance/docs/RULE_CATALOG.md` — DG-QUIKMSTR-027 to 032
