# Issue #151 — Intake Summary

**Issue:** #151 — Val X Modal Prem Outlier (9010969231C former-vanish 0561 leftover)  
**Framework stage:** Intake Agent (G0)  
**Status recommendation:** Intake Complete → Planning → Dependency Gate → Risk  
**Generated:** 2026-09-22  
**Owner:** Conversion  
**Priority:** Go  
**Stage model:** Cursor Grok 4.6 (Warren override 2026-09-22; locked Grok 4.5 unavailable)

---

## Client symptom (verbatim + normalized)

**Verbatim (08/18):** Interest-sensitive / Val X life modal premium is way off. LifePRO / Val X shows **$188.10**. QLAdmin evaluation shows **$2,899.79**. Policy is billing suspended. Eric said the conversion file is coming over correctly. Question for Robert.

**Normalized (09/22):** This is **one policy**, `9010969231C`. LifePRO bills **$188.10** a year. Conversion `quikmstr.MMODEPREM` is **$163.10** because Closed **#139** withholds the $25 ISWL fee — that load is correct and must not be changed to chase $2,899.79. Current `docs/Valuation/QuikValf.dbf` (valuation date 2026-06-30) shows **$2,899.79** on `MPREM1` / `MANNLZD` after QLAdmin treated eight anniversary PACT 0561 rows as partial surrenders and cut units from **5.0000 to 3.4952**. Those 0561s are the same former-vanish fingerprint Closed **#146** already excluded on 20 policies. Warren approved **2026-09-22** adding this 21st key to that allowlist.

## Example policies

| QLA policy | Role | Current state | After this issue |
|------------|------|---------------|------------------|
| **9010969231C** | Only in-scope policy | 8 × $188.10 QuikIsrr; units 5.00000 on load; QuikValf MUNIT 3.4952, MEXTCODE 4, MPREM1 $2,899.79 | **0** QuikIsrr / PS- / phase-0 / type-8; load units stay 5.00000; premium fields unchanged |
| 9010817956C | #146 allowlist control | 0 QuikIsrr; QuikValf MUNIT 5.0, MEXTCODE 1, MPREM1 $148.70 | **Unchanged** |
| 9010943849C | #146 allowlist control | 0 QuikIsrr; QuikValf MUNIT 15.0, MEXTCODE 1, MPREM1 $570.90 | **Unchanged** |
| 9010761639C | #146 keep gold | 1 × $271.00 QuikIsrr | **Unchanged** — real surrender |
| 9010760840C | #146 keep gold | 2 × $716.40 QuikIsrr | **Unchanged** — real surrender |

## Suspected domain

ISWL partial-surrender history — `QuikIsrr` plus the Closed **#34** PR-7 companions from the same unreversed PACT 0561 events (`quikclms` PS- / phase 0, `quikclmp` phase 0, `quikbenh` type 8). Not a billed-premium remap.

## In scope (first pass)

- Add source key **9010969231** to `qla_core/issue146_pc_isrr.py` `ALLOWLIST_SOURCE` (20 → 21). Warren written approval 2026-09-22.
- Existing #146 filter (`filter_issue146_events` after #145B VB filter) and Output stripper then drop this policy’s eight 0561 events from the four #34 tables.
- Leave LifePRO PACTG, `quikridr` phase-1 units / MPREM / MCV0, and `quikmstr.MMODEPREM` **163.10** untouched.
- Leave `quikspec.VANISH=F`.
- Named fail-closed **#151** always-on smoke at Closure (extend #146 validator **and** register a distinct `SMOKE_JOBS` job). Update Closed **#146** guide/docs from “20 policies” to “21” in the same later Development/Closure set — do not silently conflict.

## Out of scope (first pass)

- Remapping `quikmstr.MMODEPREM` to $188.10 or $2,899.79 (do **not** undo **#139**).
- Changing `quikridr.MUNIT` / `MPREM` / `MCV0` (`5.00000` / `37.62` / `-812.49000`).
- Filtering all `BILLING_REASON=PC` (171 PC policies on the 20260831 PPOLC).
- Stripping all leftover 0561s, or touching keep golds **9010761639** / **9010760840**.
- Setting `VANISH=TRUE`.
- Reopening Closed **#34** source rule or Closed **#145B** VB exclude.
- Claiming a **fresh** QLAdmin valuation has already passed (current QuikValf is 2026-06-30). That is a UAT criterion after Development.

## Related issues

| ID | Relationship |
|----|----------------|
| **#146** | Closed. Same four-table exclude. This issue adds one leftover `146_OTHER` policy to the locked allowlist with Warren’s 2026-09-22 written OK. Guide currently says 20. |
| **#145B** | Closed. VB 0561s already out. `issue145b_vpunit_listing_join.csv` tags 9010969231 as `146_OTHER` (8 × $1,504.80, counterfactual units 3.4952). |
| **#34** | Closed 0561 → QuikIsrr source. #151 is an allowlist membership change on that emit, not a new source rule. |
| **#139** | Closed. ISWL $25 fee withheld; load stays **$163.10**. Do not put the fee back. |
| **#128** | Umbrella Val X modal premiums. Keep open; this split now has a conversion cause. |
| **#154** | GP / bill hold / negative fund. Controls also have negative `MCV0` and still valued premium-paying after #146. Do not treat #154 as this emit. |
| **#25 / #26** | MPOLICY padding and MPREM mapping — preserve. |

## Immediate blockers at intake

None. Source 20260831 PPOLC/PACTG, current Output, Closed #146 helper/stripper/validator, and Warren’s allowlist-expansion approval are all in hand.

**Closed-issue notice:** expanding #146 from 20 to 21 **would conflict** with the current Completed Issues guide row (“locked 20 policies”) if done silently. Warren approved that expansion in writing **2026-09-22**. Pre-Development does **not** edit #146 Closed docs. Development/Closure must update the #146 guide row, helper comments, and smoke wording to 21 policies and name 9010969231C.

## Artifact inventory

| Artifact | Status |
|----------|--------|
| Discovery notes | `Issue_151_Discovery_Notes.md` (08/18; superseded 09/22 — this is conversion history exclude, not a premium remap) |
| Tracking row | `Issue_151_Tracking_Sheet_Row.tsv` |
| #145B fingerprint | `Issue_145B/evidence/issue145b_vpunit_listing_join.csv` row 134, bucket `146_OTHER` |
| #146 allowlist / filter | `qla_core/issue146_pc_isrr.py` (9010969231 **not** present) |
| Current Output | `QuikIsrr.csv` 8 rows; matching 8 on clms / clmp / benh type 8 |
| QuikValf (6/30) | `docs/Valuation/QuikValf.dbf` MEXTCODE 4, MUNIT 3.4952, MPREM1/MANNLZD 2899.79 |
| Source | `PPOLC_PolicyMaster_Extract_20260831.csv`; `PACTG_Accounting_Extract20260831.csv` |

## Severity / owner

- **Severity:** High on this one policy — anniversary cuts face by $1,504.80 / 1,000 and valuation premium becomes $2,899.79.
- **Owner:** Conversion (Warren). Sheet owner Eric.
