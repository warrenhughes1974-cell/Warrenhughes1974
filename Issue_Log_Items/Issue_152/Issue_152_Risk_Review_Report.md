# Issue #152 — Risk Review Report

**Issue:** #152 — Val X Modal Includes Rider  
**Framework stage:** Risk Agent  
**Status:** **GO — Ready for Development** (after **separate** user Development approval **and** Closed #88 written exception)  
**Fallback simulated:** structural rider-modal subtract vs frozen 35 vs billed-premium remap vs dropping rider rows vs mixing #153 fees  
**Generated:** 2026-09-22  
**Agent/script:** Cursor Grok 4.6 (Warren stage-model override 2026-09-22; Grok 4.5 unavailable) · read-only PPBEN 20260630/20260831, VALXLIFE, `QLA_Migration/Output/`, `docs/Valuation/QuikValf.dbf`, comparison workbook

**Status note:** Risk analysis only — no production code changes unless later approved. **Development is not approved.**

---

## Go / No-Go Recommendation

**GO** — On phase-1 BF rows with blank/zero `ANN_PREM_PER_UNIT`, subtract active `SU`/`SL`/`OR` `MODE_PREMIUM` (> 0) from the base `MODE_PREMIUM`, then keep the existing Closed **#88 / #137** `blank_ann_annual_ppu` calculation. On the current **20260831** extract that is **33** policies (rider modal **$303.02**). The 6/30 comparison cut was **35** (rider modal **$319.61**); do not hardcode either count. For all 35 on 6/30 and all 33 remaining on 8/31, base MODE minus rider MODE equals Val X base `MODAL_PREMIUM` within $0.02.

**Development is not approved.** Closed **#88** is a written conflict until Warren approves the exception in writing. “Go through the development process” is not that exception and is not Development approval.

**Conditions before any code:**

1. Warren writes the Closed **#88** exception (narrow the MODE **input**; do not put full modal premium back into Prem/Unit).  
2. Separate user **Approved for Development**.  
3. Structural rule only — never freeze 35 or 33.  
4. Phase-1 BF only. Do not subtract on rider rows.  
5. Subtract **every** qualifying active rider (9010987095 both $1.22).  
6. Do **not** change `quikmstr.MMODEPREM`, rider `MPREM`, fees, units, `MVPU`, or `VANISH`.  
7. Do **not** undo **#139** or fold **#153**.  
8. Do **not** drop **#142** `9SUBLF` rows.  
9. Do **not** reopen **#128**.  
10. Do **not** change `blank_ann_annual_ppu` itself.  
11. Fresh QLAdmin valuation is **UAT**, not proof on the current 2026-06-30 `QuikValf.dbf`.

---

## 1. Current vs Proposed Mapping

| Field | Current | Proposed | Change? |
|-------|---------|----------|---------|
| quikridr.MPREM, BF seq-1, ANN > 0 | ANN_PREM_PER_UNIT (#26) | Unchanged | **No** |
| quikridr.MPREM, BF seq-1, ANN blank, no positive active SU/SL/OR | `blank_ann_annual_ppu(full MODE, …)` (#88/#137) | Unchanged | **No** |
| quikridr.MPREM, BF seq-1, ANN blank, **with** positive active SU/SL/OR | Same helper on **full** base MODE | Same helper on **MODE − Σ rider MODE** | **Yes** |
| Rider-phase MPREM | Existing #26/#88/#137 / #142 | Unchanged | **No** |
| quikmstr.MMODEPREM | PPOLC after #139 | Unchanged | **No** |

---

## 2. Premium / Related Fields Untouched

| Target | Source | Touched? |
|--------|--------|----------|
| quikmstr.MMODEPREM | #139 (9010723388C **857.00**) | **No** |
| Rider MPREM | 977ADB **1.00**; 9SUBLF **0.19520** | **No** |
| quikridr.MUNIT / MVPU | PPBEN | **No** |
| quikridr.MANNLFEE | 0.0000 on ISWL (#139) | **No** |
| Populated-ANN MPREM | #26 (9010779552C **7.73000**) | **No** |
| #88 gold MPREM | 9010779727C **5.8615** | **No** |
| #137 gold MPREM | 9010722550C **8.71966** | **No** |
| MPOLICY padding | #2 / #25 | **No** |
| quikspec.VANISH | #145 | **No** |

---

## 3. Repo References

| Location | Role |
|----------|------|
| `app.py` / `QLA_Migration/app.py` **9102–9146** | Subtract after `mode_prem` is read (~9111), before `blank_ann_annual_ppu` (~9128). Gate on BF + seq 1 |
| `app.py` ~8634–8704 | Build `_issue152_rider_modal_sum` from in-memory PPBEN alongside existing billing caches |
| `qla_core/modal_premium_factors.py` `blank_ann_annual_ppu` | **Do not edit** |
| `QLA_Migration/Configs/Sync_Rulebook_quikridr.csv` MPREM comment | Comment-only after the #88 exception |
| `tools/validators/validate_issue26_mprem.py` | Must still PASS |
| `tools/validators/validate_issue137_modalized_mprem.py` | Must still PASS |
| `tools/validators/validate_issue139_policy_fee_suppression.py` | Must still PASS |
| `tools/validators/validate_issue142_sl_rider.py` | Must still PASS |
| `tools/validators/validate_release_closed_issues.py` | Named **#152** `SMOKE_JOBS` entry at Closure |
| `Issue_Log_Items/Completed_Issues_Release_Validation_Guide.md` #88 row | How-clause update **only after** Warren’s written exception |

---

## 4. Population Analysis

| Metric | Count |
|--------|------:|
| 6/30 in-scope policies | **35** |
| 6/30 vs Val X within $0.02 | **35 / 35** |
| 6/30 rider modal total | **$319.61** |
| 8/31 in-scope policies | **33** |
| 8/31 vs Val X 6/30 within $0.02 | **33 / 33** |
| 8/31 rider modal total | **$303.02** |
| 8/31 phase-1 MPREM that would change | **33** |
| 8/31 populated-ANN + active premium rider (out) | **9** |
| Dropped 6/30 → 8/31 | **2** (9010815117, 9011000026) |

### Breakdown (8/31 candidates)

| Dimension | policies | would_change |
|-----------|---------:|-------------:|
| Billing mode 1 (monthly) | 18 | 18 |
| Billing mode 12 (annual) | 7 | 7 |
| Billing mode 3 (quarterly) | 6 | 6 |
| Billing mode 6 (semi) | 2 | 2 |
| Multi-rider | 5 | 5 |
| SL in the subtract | 1 (9010987095) | 1 |
| OR in the subtract | 2 (9010718309, 9010818663) | 2 |

---

## 5. Fallback Recommendation (if applicable)

| Option | Rows changed | Assessment |
|--------|-------------:|------------|
| A. Structural: MODE − Σ active SU/SL/OR MODE, then existing #88/#137 | 33 on 8/31 | **Recommended** |
| B. Frozen 35-policy list from 6/30 | 35 forever | **Reject** — 9010815117 / 9011000026 now have ANN and terminated riders |
| C. Remap `MMODEPREM` down by the rider | billed premium | **Reject** — undoes billed total; #139 stays |
| D. Drop rider rows so valuation cannot double-count | rider phases | **Reject** — undoes #142 and hides the rider |
| E. Wait for QLAdmin valuation programming only | 0 conversion | **Reject** — load Prem/Unit is already wrong (8.82 vs 7.82) |
| F. Fold #153 fee into this subtract | fees / MMODEPREM | **Reject** |

**Recommended fallback:** Option A, **after** the #88 exception and Development approval.

---

## 6. Trace Policies

| Policy | Before MPREM | Proposed | MMODEPREM (stay) | Pass? |
|--------|-------------:|---------:|------------------:|-------|
| 9010723388C | 8.82 | **7.82** | 857.00 | Yes — in scope |
| 9010723386C | 8.52 | **7.52** | 827.00 | Yes — in scope |
| 9011069655C | 8.69 | **8.47** | 844.00 | Yes — Val X 847, not 827 |
| 9010987095C | 7.841481 | **7.48** | 46.18 | Yes — both riders |
| 9010779552C | 7.73000 | 7.73000 | 193.25 | Yes — out (#26) |
| 9010767171C | 2.16800 | 2.16800 | 54.25 | Yes — out (#26) |
| 9010722550C | 8.71966 | 8.71966 | 37.81 | Yes — #137 gold |
| 9010779727C | 5.8615 | 5.8615 | (unchanged) | Yes — #88 gold |

9010987095C riders that **stay**: `976659` 0.18000; `9SUBLF` 0.19520 / MVPU 0.

---

## 7. Top largest Prem/Unit changes (8/31)

| Policy | Before | After | Delta | Rider modal |
|--------|-------:|------:|------:|------------:|
| 9011061723 | 8.052261 | 6.791378 | 1.261 | 2.90 |
| 9010811319 | 8.048354 | 6.789520 | 1.259 | 2.77 |
| 9010811318 | 9.775273 | 8.566430 | 1.209 | 2.66 |
| 9010718309 | 5.570017 | 4.369622 | 1.200 | 2.64 |
| 9010817242 | 9.466246 | 8.266491 | 1.200 | 2.64 |
| 9010818663 | 9.557136 | 8.357381 | 1.200 | 2.64 |
| 9010781047 | 8.240762 | 7.240381 | 1.000 | 13.13 |
| 9011109258 | 4.192291 | 3.191961 | 1.000 | 2.20 |

Eric annual golds move by **1.00** Prem/Unit ($100 / 100 units) or **0.22** ($22 / 100 units). Those are the client-visible dollars.

---

## 8. Material Calculation Impact

**Intentional on blank-ANN BF Prem/Unit only.** We are not changing billed mode premium. We are stopping QLAdmin from valuing the same rider dollars on the base Prem/Unit and again on the rider row.

Workbook notes match: 882 with SU $100 → Val X 782; 852 with SU $100 → 752; 869 with SU $22 → 847. Current conversion and current QuikValf still show 882 / 852 / 869 on the base. After the fix, annual golds become 782 / 752 / 847 in Prem/Unit × units.

Residual on quarterly 9010987095: Val X annualizes 50.49 at 25%; QLAdmin plan factor is 27% (#21J). After this issue, QuikValf **modal** `MPREM1` is expected to be **50.49** (7.48 × 25 × 0.27). The annualized 187 vs 201.96 gap is **not** Issue 152.

---

## 9. Prior Fix Preservation

| Check | Result |
|-------|--------|
| Issue #25 MPOLICY padding | Preserved |
| Issue #26 populated ANN → MPREM | Preserved — 9 out-of-scope policies |
| Issue #88 annualized MODE ÷ units | **Written conflict on the MODE input** — method (÷ units, not full modal into Prem/Unit) stays; input is narrowed. **Requires Warren’s written exception before code.** Gold 9010779727C stays 5.8615 |
| Issue #137 modal-factor helper | Preserved — helper not edited; gold 9010722550C not a candidate |
| Issue #128 umbrella | Stays **Closed**. Do not reopen |
| Issue #139 ISWL fee withhold | Preserved — MMODEPREM 857.00 / 827.00 / 844.00 / 46.18 |
| Issue #142 active SL as 9SUBLF | Preserved — 9010987095C phase 3 stays |

---

## 10. Regression Testing Checklist (for Validation Agent)

- [ ] 9010723388C phase-1 MPREM **7.82**; phase-2 977ADB still **1.00**; MMODEPREM still **857.00**
- [ ] 9010723386C phase-1 MPREM **7.52**; 977ADB **1.00**; MMODEPREM **827.00**
- [ ] 9011069655C phase-1 MPREM **8.47**; 976659 **0.22000**; MMODEPREM **844.00**
- [ ] 9010987095C phase-1 MPREM **7.48**; 976659 **0.18000**; 9SUBLF **0.19520** / MVPU **0**; MMODEPREM **46.18**
- [ ] 9010779552C / 9010767171C MPREM unchanged (ANN path)
- [ ] 9010722550C MPREM still **8.71966** (#137)
- [ ] 9010779727C MPREM still **5.8615** (#88)
- [ ] Structural count equals active-extract join (not hardcoded 33/35)
- [ ] `quikridr` / `quikmstr` row counts unchanged
- [ ] #26 / #137 / #139 / #142 smokes still PASS
- [ ] Named **#152** fail-closed smoke PASS before Closure
- [ ] **UAT (not claimed here):** fresh QLAdmin valuation — base `MPREM1` 782 / 752 / 847, rider rows still present. Current 2026-06-30 QuikValf is before-state only

---

## 11. Recommended Development Agent Task

**Do not run until Warren (1) writes the Closed #88 exception and (2) says Approved for Development.**

1. Dual `app.py` + `QLA_Migration/app.py`: build rider-modal sum map from PPBEN; subtract only on BF seq-1 blank-ANN interceptor path (~9111 before `blank_ann_annual_ppu`).  
2. Do **not** edit `blank_ann_annual_ppu`. Do **not** hardcode policies.  
3. Dual `APP_VERSION` bump from **v59.18**.  
4. Add `tools/validators/validate_issue152_mprem_rider.py` (structural + named golds + non-candidates + rider/MMODEPREM unchanged).  
5. At Closure: `SMOKE_JOBS` entry; Completed Issues **#152** row; **#88** How-clause update citing Warren’s exception date; `Test_Validation/quikridr.csv`; G7 validator PASS on full Output + accountability **IN_DATA**.  
6. Do **not** change `quikmstr`, fees, units, VANISH, #142 rows, or #153.

### Rollback

Revert the interceptor subtract + map + version bump. `blank_ann_annual_ppu` never changed, so prior Prem/Unit returns. Do not wipe DBFs; APPEND-only remains.

---

## Appendix

- Comparison workbook: `docs/Valuation File Comparison Research.xlsx` sheet `Mode Premium & Gr Ann Prem `  
- Val X: `docs/Valuation/VALXLIFE.TXT`  
- Before-state valuation: `docs/Valuation/QuikValf.dbf` (MVALDATE 2026-06-30 — **not** a fresh PASS)  
- Closed #88 guide row: `Issue_Log_Items/Completed_Issues_Release_Validation_Guide.md`  
- Stage-model override dated **2026-09-22:** Cursor Grok 4.6 (Grok 4.5 unavailable; same-day as Issue 151)  
- **Still required from Warren:** Closed #88 written exception **and** Development approval
