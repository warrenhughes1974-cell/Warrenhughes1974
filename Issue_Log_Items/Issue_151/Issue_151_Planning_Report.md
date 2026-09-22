# Issue #151 — Planning Report

**Issue:** #151 — Val X Modal Prem Outlier (9010969231C former-vanish 0561 leftover)  
**Framework stage:** Planning Agent  
**Status:** Planning  
**Generated:** 2026-09-22  
**Agent/script:** Cursor Grok 4.6 (Warren stage-model override 2026-09-22; Grok 4.5 unavailable) · read-only Output / Source / QuikValf traces (no production code)

---

## 1. Executive Finding

`9010969231C` is not a billed-premium mapping error. LifePRO PPOLC/PPBEN 20260831 show plan **659 CEN SR**, status Active, billing code **S**, reason **PC**, `MODE_PREMIUM` = `ANNUAL_PREMIUM` = **188.10**, units **5.00000**. Conversion already loads QLA plan **1659CR**, status **22**, `MMODEPREM` **163.10** (188.10 − $25 ISWL fee per Closed **#139**), rider phase 1 **MUNIT 5.00000 / MPREM 37.62 / MCV0 -812.49000**.

Current Output still emits **eight** unreversed PACT 0561 rows (2018–2025, each **$188.10**) to QuikIsrr and the matching #34 companions. Valuation-unit math is exact: `5.0000 − (8 × 188.10 / 1000) = 3.4952`, which is `docs/Valuation/QuikValf.dbf` `MUNIT`. That same QuikValf row is **MEXTCODE 4** (Extended Term) with `MPREM1`/`MANNLZD` **2899.79**. The $2,899.79 figure is valuation output after those false surrenders, not a conversion premium.

**Direction:** surgical membership add — put `9010969231` on the Closed **#146** allowlist (20 → 21). Warren approved that expansion **2026-09-22**. Existing `filter_issue146_events` and `apply_issue146_pc_isrr_exclude.py` then drop the eight events from four tables. Do not remap premiums. Do not claim a fresh QLAdmin valuation has passed. Ready for Dependency Gate.

---

## 2. Confirmed LifePRO Source Table/File(s)

| Source table | File pattern | In Source/ package? | Row count |
|--------------|--------------|---------------------|----------:|
| PPOLC | `PPOLC_PolicyMaster_Extract_20260831.csv` | Yes | 5,084; 171 `BILLING_REASON=PC`; this policy = S / PC / MODE_PREMIUM 188.10 / POLICY_FEE 25.00 |
| PPBEN | `PPBEN_PolicyBenefit_Extract_20260831.csv` | Yes | Phase/seq 1 BF Active; `PLAN_CODE` 659 CEN SR; `NUMBER_OF_UNITS` 5.00000; `MODE_PREMIUM` 188.10 |
| PACTG | `PACTG_Accounting_Extract20260831.csv` | Yes | **8** unreversed DEBIT_CODE 561, TRANS_AMOUNT 188.10, EFFECTIVE_DATE 20180221–20250221 |

### Available source fields

| Field | Column / source | Populated % | Notes |
|-------|-----------------|------------:|-------|
| Identity | Locked policy key `9010969231` | 1 / 1 in scope | PC is evidence, not the emit key (171 PC policies) |
| Event | PACTG.DEBIT_CODE 561/0561 | 8 / 8 | #34 candidate rule unchanged for non-allowlist |
| Reversal | PACTG.REVERSAL_CODE | blank | Unreversed; do not reopen #34 |
| Amount | PACTG.TRANS_AMOUNT | 8 / 8 = 188.10 | Equals annual premium; fingerprint match |
| Policy key | POLICY_NUMBER | 100% | Existing `#2` / `#25` `format_qladmin_mpolicy` → `9010969231C` |

Do **not** treat `BILLING_REASON=PC` as a fleet exclude.

---

## 3. Confirmed QLAdmin Target Structure

| Table | Field | Type | Length | Source (Help / schema) |
|-------|-------|------|--------|------------------------|
| QuikIsrr | MPOLICY / MSURRDATE / MSURRAMT | C / D / N | #34 | Help §7.143 |
| quikclms | CLAIMNUM / CAUSE / MPHASE | — | — | PR-7 PS- / SRR / phase 0 |
| quikclmp | MPHASE / MAMOUNT | — | — | PR-7 phase 0 companions |
| quikbenh | MBENTYP / MBEN / MDATE | — | — | Type **8** only (ISRR). Types 10/11/12 are #54 loans. |

**Repo references** (population paths only):

| Location | Role |
|----------|------|
| `qla_core/issue146_pc_isrr.py` `ALLOWLIST_SOURCE` | Add `9010969231` (currently 20 keys; this policy absent) |
| `qla_core/quikisrr_loader.py` `filter_issue146_events` | Already called after `filter_vb_events` — no new branch needed |
| `Issue_Log_Items/Issue_146/tools/apply_issue146_pc_isrr_exclude.py` | Strip current Output once the key is on the allowlist |
| `Issue_Log_Items/Issue_34/tools/quikisrr_pr7_emit.py` | Already fails on `issue146_leak_policies` |
| `tools/validators/validate_issue146_pc_isrr.py` | Iterates `ALLOWLIST_SOURCE` — will cover the 21st key automatically |
| `tools/validators/validate_release_closed_issues.py` `SMOKE_JOBS` | #146 job exists; **#151 still needs its own named job at Closure** |

---

## 4. Required Source-to-Target Field Mapping

| LifePRO source | LifePRO field | QLAdmin target | Transformation | Change? |
|----------------|---------------|----------------|----------------|---------|
| Locked allowlist | 20 keys + **9010969231** | (filter) | Drop all #34 0561 events for those policies | **Yes** — membership only |
| PACTG | 0561 unreversed, not allowlist | QuikIsrr + companions | Existing #34 + #145B + #146 | **No** |
| PACTG | 0561 on 9010969231 | (none) | Do not emit; strip the eight already written | **Yes** |
| PPOLC | MODE_PREMIUM 188.10 − fee 25.00 | quikmstr.MMODEPREM 163.10 | Closed #139 | **No** |
| PPBEN | NUMBER_OF_UNITS 5 / MODE_PREMIUM | quikridr.MUNIT / MPREM | Existing | **No** |
| PACTG extract | all rows | LifePRO file | Never delete source | **No** |

### Fields that must remain unchanged

| Target | Current source | Touch this issue? |
|--------|----------------|-------------------|
| quikmstr.MMODEPREM | 163.10 after #139 (not 188.10, not 2899.79) | **No** |
| quikridr.MPREM | 37.62 (#26 family) | **No** |
| quikridr.MUNIT | 5.00000 | **No** |
| quikridr.MCV0 | -812.49000 | **No** |
| quikridr.MANNLFEE | 0.0000 (#139) | **No** |
| MPOLICY padding | format_qladmin_mpolicy | **No** |
| quikspec.VANISH / VANISHDT / RESRVCAT / SOR_POL | F / blank / 16 / 9010969231 | **No** |
| QuikIsrr #146 keep golds | 9010761639C $271; 9010760840C $716.40 | **No** |
| quikbenh MBENTYP 10/11/12 | #54 | **No** |

---

## 5. Open Client Questions

None that block Planning. Locked **2026-09-22** by Warren:

1. In-scope identity is **only** `9010969231` / `9010969231C`.  
2. Expand Closed #146 allowlist 20 → 21 (written approval).  
3. Keep 9010761639 and 9010760840.  
4. Do not set VANISH. Do not filter all PC or all 0561s.  
5. Do not undo #139.  
6. Fresh QLAdmin valuation is **UAT after Development**, not a Planning gap.

---

## 6. Recommended Formatting Rules

| Rule | Recommendation |
|------|----------------|
| Policy key | Existing `format_qladmin_mpolicy()` only. Match allowlist on digit / C keys. |
| Dates | Unchanged on leftover rows |
| Money | Unchanged on leftover rows; do not rewrite 188.10 into MMODEPREM |
| Blanks / zeros | This policy may have **zero** QuikIsrr rows after. That is success. |
| Identity | Hard allowlist add, not `BILLING_REASON=PC` |

---

## 7. Memo / Text / Special Handling

PR-7 `MEMOTEXT` on the eight PS- claim rows is generated from the same 0561 events. Those rows come out with the claim companions. No memo concatenation change.

---

## 8. Policy Number Key Handling

1. LifePRO `POLICY_NUMBER` `9010969231` → existing `#2` / `#25` formatter → `9010969231C`.  
2. Allowlist test: policy in the locked **21** keys (with/without C).  
3. Unknown / not on list: **keep** the 0561.  
4. Crosswalk also has `9010969231,010969231C` as a historical alias; conversion Output uses `9010969231C`. Do not retarget the key.

---

## 9. Estimated Record Counts

Current 20260831 Output (read 2026-09-22):

| Metric | Count | Basis |
|--------|------:|-------|
| QuikIsrr leftover now | 110 / 31 policies | After #145B + #146 |
| This policy QuikIsrr | 8 | $1,504.80; dates 20180221–20250221 |
| Companion rows to remove (each of clms / clmp / benh-8) | 8 | This policy has only those 8 on each table |
| QuikIsrr rows after | 102 | 30 policies |
| Keep golds | 1 + 2 rows | $271.00 and $716.40 still present |
| Current #146 allowlist still in leftover | 0 | Filter already holding |

Gold after: `9010969231C` QuikIsrr = **0**. `MUNIT` stays **5.00000**. `MPREM` stays **37.62**. `MCV0` stays **-812.49000**. `MMODEPREM` stays **163.10**.

---

## 10. Sample Trace (5 policies)

| Policy (QLA) | Before QuikIsrr | After (proposed) | Status |
|--------------|----------------:|------------------|--------|
| 9010969231C | 8 / $1,504.80 | 0 | Add to allowlist — remove |
| 9010817956C | 0 | 0 | #146 control — already clean |
| 9010943849C | 0 | 0 | #146 control — already clean |
| 9010761639C | 1 / $271.00 | 1 / $271.00 | Keep — real surrender |
| 9010760840C | 2 / $716.40 | 2 / $716.40 | Keep — real surrender |

Valuation-unit identity on the in-scope policy: `5.0000 − 1.5048 = 3.4952` (current QuikValf). After history is gone, conversion units stay 5.00000. **Whether a later QLAdmin valuation then shows MUNIT 5.0000, MEXTCODE 1, and a ~$188.10 premium (not $2,899.79) is UAT — not proven on this 2026-06-30 QuikValf file.**

Natural controls 9010817956C / 9010943849C also carry negative `MCV0` (-496.10 / -1154.33) yet valued premium-paying at full units after #146. That supports the same exclude here; it does not replace a fresh valuation run.

---

## 11. Risks and Unknowns

| Risk | Severity | Mitigation |
|------|----------|------------|
| Silent conflict with Closed #146 “20 policies” guide row | High | Warren approved 20→21 on 2026-09-22. Development/Closure must update #146 guide/docs in the same change set. This pre-dev chain does not edit #146 files. |
| Using `BILLING_REASON=PC` as the filter | High | Add one hard key only (171 PC on 8/31) |
| Closing #151 without its own `SMOKE_JOBS` entry | High | Extend #146 validator **and** register a named #151 fail-closed smoke |
| Undoing #139 to make MMODEPREM 188.10 | High | Forbidden. $2,899.79 is not the conversion target |
| Strip `quikbenh` wholesale | High | Type **8** on this policy only (it has no other benh types today) |
| Claiming current QuikValf already “fixed” | Medium | File date is 2026-06-30; fresh valuation is UAT |
| True surrender hiding on this policy | Low | 8/8 amounts = annual premium; #145B join already tagged `146_OTHER` |

---

## 12. Dependency Gate Preview

| Check | Met? |
|-------|------|
| Source file present | Yes — PPOLC / PPBEN / PACTG 20260831 |
| Field definitions confirmed | Yes — same four #34 tables as #146 |
| Client scope clear | Yes — one policy; Warren 20→21 approval 2026-09-22 |
| Example policies available | Yes — 9010969231C plus #146 controls and keep golds |
| Fresh QLAdmin valuation | **UAT later** — not a pre-dev blocker |

---

## 13. Recommended Risk Agent Prompt

Quantify 8-row × 4-table remove vs 102-row leftover. Confirm keep golds, #146 allowlist still 0, #139 MMODEPREM 163.10, rider 5.00000 / 37.62 / -812.49. Recommend named #151 smoke vs relying only on #146. Do not treat 2026-06-30 QuikValf as a passed fresh valuation.

---

## 14. Recommended Development Task (do not implement)

1. Add `"9010969231"` to `ALLOWLIST_SOURCE` in `qla_core/issue146_pc_isrr.py`. Update the “20-policy” comments there to 21 and cite Warren 2026-09-22.  
2. Do **not** add a new filter branch in `quikisrr_loader.py` unless a dry-run proves the existing `filter_issue146_events` call misses the key.  
3. After approval, strip current Output with the existing #146 apply tool (do not blindly re-run PR-7 append).  
4. Extend `validate_issue146_pc_isrr.py` comments/docstring 20 → 21 (it already loops `ALLOWLIST_SOURCE`).  
5. Add a **named #151** fail-closed validator (thin gold on `9010969231C`: 0 ISRR / 0 PS- / 0 phase-0 / 0 type-8; MUNIT 5.00000; MPREM 37.62; MCV0 -812.49000; MMODEPREM 163.10) and register it in `SMOKE_JOBS` at Closure.  
6. Dual `APP_VERSION` bump (currently **v59.17**) — no other `app.py` logic.  
7. At Closure: update Completed Issues guide **#151 new row** and **#146 row 20→21** with Warren 2026-09-22 approval; publish the four tables to `Test_Validation/`.  
8. Do not change `quikridr`, `quikmstr` premiums, `quikspec`, PACTG, or keep-gold rows.

### Locked add (1)

**9010969231**

### Locked keep (2) — do not filter

9010761639, 9010760840.
