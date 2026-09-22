# Issue #152 — Planning Report

**Issue:** #152 — Val X Modal Includes Rider  
**Framework stage:** Planning Agent  
**Status:** Planning  
**Generated:** 2026-09-22  
**Agent/script:** Cursor Grok 4.6 (Warren stage-model override 2026-09-22; Grok 4.5 unavailable) · read-only PPBEN / VALXLIFE / Output / QuikValf / comparison workbook (no production code)

---

## 1. Executive Finding

LifePRO already stores rider modal premium on the rider row. On interest-sensitive (BF) base coverage, `ANN_PREM_PER_UNIT` is often blank, so the Closed **#88 / #137** fallback annualizes the **entire** base `MODE_PREMIUM` — which still includes those riders — and writes that into `quikridr.MPREM`. QLAdmin valuation multiplies Prem/Unit × units on the base **and** still values the rider, so the rider is counted twice.

On PPBEN **20260630** that structural population is **exactly 35** BF policies with blank/zero base ANN and at least one active `SU`/`SL`/`OR` rider with `MODE_PREMIUM` > 0. Rider-premium total **$319.61**. For all 35, `base MODE_PREMIUM − sum(active rider MODE_PREMIUM)` equals Val X base `MODAL_PREMIUM` within **$0.02** (max residual is floating-point noise). On PPBEN **20260831** the same structure is **33**. Dropped: **9010815117** (base ANN now 2.020, rider terminated) and **9011000026** (base ANN now 5.070, riders terminated). Do not hardcode 35.

**Direction:** on phase-1 BF blank/zero ANN only, subtract the active rider modal sum from base `MODE_PREMIUM`, then call existing `blank_ann_annual_ppu`. Do not change rider rows, `MMODEPREM`, fees, units, or `VANISH`. This **narrows** the Closed **#88** MODE input. That is a written conflict until Warren approves the exception. Development is **not** approved.

---

## 2. Confirmed LifePRO Source Table/File(s)

| Source table | File pattern | In Source/ package? | Row count |
|--------------|--------------|---------------------|----------:|
| PPBEN 20260630 | `PPBEN_PolicyBenefit_Extract_20260630.csv` | Yes | 11,698; **35** in-scope candidates; rider modal **$319.61** |
| PPBEN 20260831 | `PPBEN_PolicyBenefit_Extract_20260831.csv` | Yes (current batch extract) | 11,698; **33** in-scope candidates; rider modal **$303.02** |
| PPOLC 20260831 | `PPOLC_PolicyMaster_Extract_20260831.csv` | Yes | Billing mode / form / policy fee for #137 and #139; not remapped here |
| VALXLIFE | `docs/Valuation/VALXLIFE.TXT` | Yes | 3,152 rows, valuation date 2026-06-30 |

### Available source fields

| Field | Column / source | Populated % | Notes |
|-------|-----------------|------------:|-------|
| Base identity | PPBEN `BENEFIT_TYPE=BF`, `BENEFIT_SEQ=1` | All candidates | ISWL base only |
| Blank ANN | `ANN_PREM_PER_UNIT` blank/zero | Required for in-scope | If populated, **#26** path — out of scope |
| Base modal | `MODE_PREMIUM` | 33 / 33 > 0 | Includes rider modal today |
| Active rider modal | `SU`/`SL`/`OR`, `STATUS_CODE=A`, `MODE_PREMIUM` > 0 | 35 SU + 1 SL + 2 OR on 8/31 candidates | Sum **all** qualifying riders |
| Terminated riders | `STATUS_CODE=T` | Excluded from the subtract | 9010815117 / 9011000026 dropped on 8/31 this way |
| Negative rider modal | 9010779727 seq-4 `SU` −169.50 | Out of the `> 0` filter | Closed **#88** gold stays 5.8615 |
| Policy key | `POLICY_NUMBER` | 100% | Existing `#2` / `#25` → `…C` |

Nine other 8/31 BF policies have active premium riders **and** populated base ANN (9010767171, 9010779552, 9010782078, 9010833382, 9010841793, 9010847571, 9010880362, 9011028990, 9011129883). Out of scope.

---

## 3. Confirmed QLAdmin Target Structure

| Table | Field | Type | Length | Source (Help / schema) |
|-------|-------|------|--------|------------------------|
| quikridr | MPREM | numeric Prem/Unit | existing | QLAdmin Help: annual premium **per unit**. Valuation × units. |
| quikridr | MPHASE / MPLAN / MUNIT / MVPU | existing | — | Rider rows including `9SUBLF` stay |
| quikmstr | MMODEPREM | numeric billed mode | existing | Closed **#139** — **do not touch** |

**Repo references** (population paths only):

| Location | Role |
|----------|------|
| `app.py` / `QLA_Migration/app.py` **9102–9146** | `Issue 26/88/137` blank-ANN `MPREM` interceptor. **Insertion point** after `mode_prem` is read (~9111–9115), before `blank_ann_annual_ppu(...)`. |
| `app.py` ~8634–8704 | Existing PPOLC billing-mode / form / fee caches for the same interceptor. Build the rider-modal sum from the in-memory PPBEN `source` here (or immediately after). |
| `qla_core/modal_premium_factors.py` `blank_ann_annual_ppu` | Keep as-is. Pass the **reduced** mode premium in. |
| `QLA_Migration/Configs/Sync_Rulebook_quikridr.csv` line 16 | Comment-only #26/#88/#137 note. Comment update at Development if the exception is approved; no mapping-column change. |
| `tools/validators/validate_issue26_mprem.py` | Populated ANN golds. Must still PASS. Docstring still describes the pre-#88 fallback — do not “fix” it by reopening #26. |
| `tools/validators/validate_issue137_modalized_mprem.py` | Gold 9010722550C. Must still PASS. |
| `tools/validators/validate_issue139_policy_fee_suppression.py` | MMODEPREM / ISWL fees. Must still PASS. |
| `tools/validators/validate_issue142_sl_rider.py` | `9SUBLF` rows. Must still PASS. |
| `tools/validators/validate_release_closed_issues.py` `SMOKE_JOBS` | Named **#152** fail-closed job at **Closure**, not now. |

---

## 4. Required Source-to-Target Field Mapping

| LifePRO source | LifePRO field | QLAdmin target | Transformation | Change? |
|----------------|---------------|----------------|----------------|---------|
| PPBEN BF seq 1, ANN populated | `ANN_PREM_PER_UNIT` | quikridr.MPREM | Closed **#26** as-is | **No** |
| PPBEN BF seq 1, ANN blank, **no** positive active SU/SL/OR | `MODE_PREMIUM` | quikridr.MPREM | Existing #88/#137 `blank_ann_annual_ppu(MODE, units, …)` | **No** |
| PPBEN BF seq 1, ANN blank, **with** positive active SU/SL/OR | `MODE_PREMIUM − Σ rider MODE` | quikridr.MPREM | Same helper, **narrowed MODE input** | **Yes** — this issue |
| PPBEN SU/SL/OR (active) | `ANN_PREM_PER_UNIT` / own `MODE_PREMIUM` | rider-phase MPREM | Existing #26/#88/#137 on **that** row | **No** |
| PPBEN SL active | existing #142 | MPLAN `9SUBLF`, MVPU 0 | Preserve | **No** |
| PPOLC | `MODE_PREMIUM` − ISWL fee | quikmstr.MMODEPREM | Closed **#139** | **No** |

Proposed formula (phase-1 BF only):

```text
if ANN_PREM_PER_UNIT is blank/zero
   and units > 0
   and Σ(active SU/SL/OR MODE_PREMIUM where MODE > 0) > 0:
       mode_in = max(0, base MODE_PREMIUM − that sum)
else:
       mode_in = base MODE_PREMIUM   # today’s #88/#137 input

MPREM = blank_ann_annual_ppu(mode_in, units, bill_mode, bill_form, plan_factors)
```

### Fields that must remain unchanged

| Target | Current source | Touch this issue? |
|--------|----------------|-------------------|
| quikmstr.MMODEPREM | PPOLC after #139 (9010723388C = **857.00**) | **No** |
| Rider-phase MPREM | Rider ANN / own MODE (977ADB 1.00; 9SUBLF 0.19520) | **No** |
| quikridr.MUNIT / MVPU | PPBEN units / VPU | **No** |
| quikridr.MANNLFEE and modal fees | #139 zeros on ISWL | **No** |
| Populated-ANN MPREM | #26 | **No** |
| #88 gold 9010779727C MPREM | 5.8615 | **No** |
| #137 gold 9010722550C MPREM | 8.71966 | **No** |
| MPOLICY padding | format_qladmin_mpolicy | **No** |
| quikspec.VANISH | #145 | **No** |

---

## 5. Open Client Questions

None that block Planning **research**. One **Development-entry** question is **not** answered and is **not** implied by “go through the development process”:

1. **Warren — Closed #88 written exception.** May Issue 152 subtract separately loaded active rider `MODE_PREMIUM` from the blank-ANN `MODE_PREMIUM` **before** the Closed #88/#137 per-unit division, and may Closure then update the #88 guide How-clause to say so? Until that written exception exists, Development must not start.

Accepted for this issue (evidence, not a new client ask):

- Structural population, not a frozen 35.
- Subtract all active SU **and** SL **and** OR with MODE > 0.
- Fresh QLAdmin valuation is **UAT after Development**, not a pre-dev gap.
- Do not reopen #128. Do not undo #139. Do not fold #153.

---

## 6. Recommended Formatting Rules

| Rule | Recommendation |
|------|----------------|
| Policy key | Existing `format_qladmin_mpolicy()` only |
| Money / Prem/Unit | Keep `format_mprem_ppu` (strip trailing zeros) |
| Blanks / zeros | ANN blank/zero both trigger the fallback today; keep that |
| Rider filter | `STATUS_CODE=A` and `MODE_PREMIUM` > 0 only (terminated and negative stay out) |
| Identity | Recompute from the extract being converted. Never freeze 35 or 33 |

---

## 7. Memo / Text / Special Handling

N/A.

---

## 8. Policy Number Key Handling

1. LifePRO `POLICY_NUMBER` → existing `#2` / `#25` → 11-character `…C`.  
2. Rider-sum map keys on normalized LifePRO policy number (same `self.normalize` as `_billing_mode_map`).  
3. No new crosswalk. No MPOLICY rewrite.

---

## 9. Estimated Record Counts

Read 2026-09-22 against current Source / Output:

| Metric | Count | Basis |
|--------|------:|-------|
| 6/30 structural candidates | **35** | BF seq-1 blank ANN + active SU/SL/OR MODE>0 |
| 6/30 vs Val X base modal | **35 / 35** within $0.02 | All match |
| 8/31 structural candidates | **33** | Same rule; dropped 9010815117 and 9011000026 |
| 8/31 vs Val X 6/30 modal | **33 / 33** within $0.02 | Remaining premiums unchanged |
| 8/31 rider modal total | **$303.02** | 6/30 was $319.61; dropped riders $16.59 |
| 8/31 billing mix | 18 monthly / 7 annual / 6 quarterly / 2 semi | All still go through #137 factors after the subtract |
| 8/31 multi-rider policies | 5 | 9010811318, 9010811319, 9010817242, 9010987095, 9011061723 |
| 8/31 populated-ANN + active premium rider (out of scope) | **9** | #26 path |
| Phase-1 rows that would change on current Output | **33** | Only those BF blank-ANN bases |
| Rider rows / MMODEPREM / fees | 0 intended | Preserve |

Current Output package valuation date: **20260831** (`newest_plan_rate_package.json`). Engine **v59.18**.

---

## 10. Sample Trace (policies)

| Policy (QLA) | LifePRO | Before phase-1 MPREM | After (proposed) | Status |
|--------------|---------|---------------------:|-----------------:|--------|
| 9010723388C | BF MODE 882 − SU 100 = 782; units 100; annual | 8.82 | **7.82** | In scope |
| 9010723386C | 852 − 100 = 752 | 8.52 | **7.52** | In scope |
| 9011069655C | 869 − 22 = 847 | 8.69 | **8.47** | In scope |
| 9010987095C | 52.93 − 1.22 − 1.22 = 50.49; quarterly 27% / 25 units | 7.841481 | **7.48** | Both riders subtracted |
| 9010779552C | Base ANN 7.73000; active ADB $25 | 7.73000 | 7.73000 | Out — #26 |
| 9010767171C | Base ANN 2.16800; active SU $5 | 2.16800 | 2.16800 | Out — #26 |
| 9010722550C | Blank ANN but riders **terminated** | 8.71966 | 8.71966 | #137 gold — not a candidate |
| 9010779727C | Blank ANN; active SU is **−169.50** | 5.8615 | 5.8615 | #88 gold — MODE>0 filter excludes it |

`quikmstr.MMODEPREM` on the golds (must stay): 9010723388C **857.00**; 9010723386C **827.00**; 9011069655C **844.00**; 9010987095C **46.18**.

Rider rows on 9010723388C: phase 2 `977ADB` MPREM **1.00** stays. On 9010987095C: phase 2 `976659` MPREM **0.18000** and phase 3 `9SUBLF` MPREM **0.19520** / MVPU **0** stay.

Current `QuikValf.dbf` (2026-06-30, before-state only): base `MPREM1` 882 / 852 / 869 / 52.92. That is the doubled load, not a passed fresh valuation.

---

## 11. Risks and Unknowns

| Risk | Severity | Mitigation |
|------|----------|------------|
| Written conflict with Closed **#88** How-clause | **High** | Stop. Warren must approve the exception in writing. “Go through the development process” is not that approval. Update the #88 guide row only after that approval, at Development/Closure. |
| Frozen 35-policy list | High | Structural rule from the active extract |
| Subtracting on rider rows too | High | Gate on BF + BENEFIT_SEQ 1 (phase 1) only |
| Undoing #139 / mixing #153 | High | Do not touch MMODEPREM or fees |
| Dropping #142 `9SUBLF` | High | Preserve rider emit; only change base MODE input |
| Changing #137 gold 9010722550C | Medium | Not a candidate (terminated riders). Validator must still PASS |
| Changing #88 gold 9010779727C | Medium | Negative rider excluded by MODE>0 |
| Quarterly 27% vs Val X 25% annualized | Low | Existing #21J/#137; Issue 152 still aligns **modal** 50.49 after the subtract |
| Claiming current QuikValf is fixed | Medium | File date 2026-06-30; UAT later |

---

## 12. Dependency Gate Preview

| Check | Met? |
|-------|------|
| Source file present | Yes — both PPBEN cuts + VALXLIFE + current Output |
| Field definitions confirmed | Yes — MPREM = annual Prem/Unit; Val X MODAL_PREMIUM on BF seq 1 |
| Client scope clear | Yes — structural BF blank-ANN + active SU/SL/OR; 9 ANN policies out |
| Example policies available | Yes — Eric three + 9010987095 + non-candidates |
| Closed #88 written exception | **Missing for Development** — not a missing extract. Recorded as Development-entry hold |
| Fresh QLAdmin valuation | **UAT later** |

---

## 13. Recommended Risk Agent Prompt

Quantify 33 (8/31) vs 35 (6/30). Confirm Val X match, proposed MPREM on golds 7.82 / 7.52 / 8.47 / 7.48, MMODEPREM and rider rows unchanged, #88/#137 golds unchanged. Issue **GO** on evidence. Do **not** treat this as Development approval or as the Closed #88 exception.

---

## 14. Recommended Development Task (Do Not Implement)

Development is **not** approved. If later approved **and** Warren writes the #88 exception:

1. In root `app.py` **and** `QLA_Migration/app.py` (keep in sync), during quikridr convert (~8634+), build `_issue152_rider_modal_sum[policy] = Σ MODE_PREMIUM` for `STATUS_CODE=A`, `BENEFIT_TYPE in {SU,SL,OR}`, `MODE_PREMIUM > 0` from the in-memory PPBEN source.  
2. In the existing interceptor at **~9102–9146**, after `mode_prem` is read from the current row and **only** when `BENEFIT_SEQ` is 1 and `BENEFIT_TYPE` is `BF`, subtract that sum (`max(0, mode_prem − sum)`). Then call existing `blank_ann_annual_ppu`.  
3. Do **not** change `blank_ann_annual_ppu` itself. Do **not** hardcode 33/35. Do **not** subtract on rider rows.  
4. Dual `APP_VERSION` bump from **v59.18**.  
5. New fail-closed validator `tools/validators/validate_issue152_mprem_rider.py`: structural join to the active PPBEN (not a frozen list); golds 9010723388C **7.82**, 9010723386C **7.52**, 9011069655C **8.47**, 9010987095C **7.48**; non-candidates 9010779552C / 9010767171C / 9010722550C / 9010779727C unchanged; rider MPREM and `MMODEPREM` unchanged.  
6. At Closure: register that validator in `SMOKE_JOBS`; add the #152 Completed Issues guide row; update the **#88** How-clause citing Warren’s exception date; publish `quikridr.csv` to `Test_Validation/`; G7 Output accountability **IN_DATA**.  
7. Do not change `quikmstr`, fees, units, `VANISH`, or #142 rows.

### Locked do-not-touch

MMODEPREM, rider MPREM, MANNLFEE, MUNIT, MVPU, VANISH, populated-ANN MPREM, #88 gold 5.8615, #137 gold 8.71966.
