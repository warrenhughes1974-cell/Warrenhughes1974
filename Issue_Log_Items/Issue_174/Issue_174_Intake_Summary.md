# Issue #174 — Intake Summary

**Issue:** #174 — Pending Death Benefit Policies
**Framework stage:** Intake
**Date:** 2026-09-28
**Status after intake:** Planning
**Owner:** Conversion (Warren)
**Priority:** No Go
**Raised:** 2026-09-25, Eric. Diagnosed by Brianna.

---

## Client symptom

Sheet, verbatim:

> Policies in Pending Death Benefit status are not calculating return of premium or allowing edits to items such as beneficiaries.

Brianna, on `9011085655C`, verbatim in substance:

The policy and the phase are both status 50. The user cannot edit the beneficiary. QLAdmin says the policy status is not in sync with the coverage status, even though both are 50. When she adds a pending claim herself, the policy is 50 and the phase stays Active (22), and she can edit the beneficiary. These policies need to convert with an active phase of coverage.

**Normalized:** Keep the policy at Death Claim Pending (50). Leave the coverage phase at Active (22). That is what unlocks the beneficiary edit. Return of premium is Eric's sheet symptom. No return-of-premium amount exists to load. It is a QLAdmin calculation that should be rechecked after the phase is Active. It is out of the conversion change.

## Example policies

| Policy | Role |
|---|---|
| `9011085655C` | Brianna's example. Century SR, plan `1659CR`. |
| `9010521213C` | Only pending-death policy on the 6/30 extract that also has a paid-up addition. |
| `9010439999C` | The paid-up-addition case on the 8/31 extract. Still Active in the current 6/30 Output. |

Full lists: `evidence/issue174_pending_death_population.csv`.

## Domain

Policy status and coverage-phase status. Tables: `quikmstr.MSTATUS` (do not change the 50) and `quikridr.MPHSTAT` / `MSAVESTAT` (stop copying 50 onto the phase).

Not claims, not beneficiaries as a missing table, not premium.

## In scope

- Policies whose LifePRO contract is Suspended / Death Pending (`CONTRACT_CODE=S`, `CONTRACT_REASON=DP`), which translates to status 50.
- Phase 1 must keep the benefit's own Active status (22). `MSAVESTAT` follows it.
- The one paid-up addition on that same contract must also stay Active (22), not be rewritten to Paid Up (41) or to 50.
- The policy header stays 50. Issue #49 must not put it back to 22.

## Out of scope

- Surrendered, lapsed, matured, and actual death (`T`/`DC` → 53). Those phases keep following the policy.
- Return of premium as a loaded amount.
- Beneficiary rows already on the policy. The block is the status pair, not a missing beneficiary.

## Related issues

| Issue | Relationship |
|---|---|
| #13 / `ST_S_DP` | Header 50 is correct. Keep it. |
| #49 | Must not promote the header to 22 when the phase is left Active. |
| #59 | Named death-claim policy follows the current extract: 50 while `S`/`DP`, 53 once `T`/`DC`. Do not freeze 50. |
| Closed #160 | PUA copies a terminal base, including 50. This issue stops the base from being 50, so that copy must not be how a pending-death PUA gets its status. |
| #60 | Active base normally forces the PUA to Paid Up (41). That must not run when the policy is 50. |
| #108 | Status 50-and-above ends the coverages. Status 50 is the exception Brianna stated. |
| #133-PS | Header stays 50 when a PUA is still Active in LifePRO. That header result stays. The base phase does not stay 50. |

## Blockers visible at intake

None that stop Planning. The closed-issue exception (#160, #60, #108) is a Development-approval condition, not a missing extract.

## Artifact inventory

| Have | Missing |
|---|---|
| Brianna's written rule and example policy | Screenshot of her test claim (described, not filed) |
| 6/30 and 8/31 `PPOLC` / `PPBEN` | A return-of-premium field. None expected. |
| Current Output (6/30 valuation) showing both sides at 50 | |

## G0

- [x] Issue folder exists
- [x] Intake summary written
- [x] Example policies listed
- [x] Owner Warren, priority No Go
- [x] No code or rulebook changes
