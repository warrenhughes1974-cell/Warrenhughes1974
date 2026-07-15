# Issue #76 — Regression Report

**Issue:** #76 — ETI/RPU phase-1 pay-up + duration for Policy Display cash values  
**Framework stage:** Regression Agent (G6)  
**Engine version:** v57.93  
**Baseline:** `Issue_Log_Items/Issue_76/evidence/issue76_risk_phase1_simulation.csv` (pre-fix MPAYUP/MLASTANN) + schema key set from `Issue_60/evidence/quikridr_pre_v5785_baseline.csv`  
**Output directory:** `QLA_Migration/Output/`  
**Batch:** Scoped rebatch (`Issue_Log_Items/Issue_76/scripts/rebatch_issue76_quikridr.py`, exit 0)  
**Generated:** 2026-07-15  
**Model:** Cursor Grok 4.5 (locked)  
**Verdict:** **PASS**

**Note:** No full pre-v57.93 `quikridr` snapshot was captured. Regression uses risk-backed before values for the 400 ETI/RPU candidates plus fleet non-candidate guards (same pattern as Issue #60 with blocked #26 extract).

---

## 1. Scope of Change (expected)

| Component | Expected impact |
|-----------|-----------------|
| `quikridr` phase-1 @ MSTATUS 44/45 | `MPAYUP`, `MLASTANN` only |
| `quikridr` phase > 1 / PUA (#60) | **No** pay-up override |
| `quikridr` non-ETI/RPU | **No** change |
| `quikmstr` / other tables | **No** #76 hook (rebatch for cache only) |
| Rulebooks / rates | Not modified |

---

## 2. Row Count Comparison

| Table | After | Expected | OK? |
|-------|------:|---------:|:---:|
| quikmstr | 5,083 | 5,083 | **Yes** |
| quikridr | 6,934 | 6,934 | **Yes** |
| quikprmh | 209,470 | 209,470 | **Yes** |
| quikplan | 141 | 141 | **Yes** |
| quikclid | 34,449 | 34,449 | **Yes** |
| quikclnt | 13,597 | 13,597 | **Yes** |
| quikbenf | 5,916 | 5,916 | **Yes** |
| quikdvdp | 5,083 | 5,083 | **Yes** |

Key identity vs v57.85 schema baseline: **0** missing, **0** orphan `(MPOLICY, MPHASE)` keys.

---

## 3. Non-Target Field Diff (`quikridr`)

| Check | Result | OK? |
|-------|--------|:---:|
| Schema headers (40 cols) | Identical to baseline | **Yes** |
| Blank `MRIDRID` | 0 / 6,934 | **Yes** |
| Candidate `MEFFDATE` vs risk before | 0 drift / 400 | **Yes** |
| Candidate `MPLAN` vs risk before | 0 drift / 400 | **Yes** |
| Non-candidate false issue76 override | 0 | **Yes** |
| #60 PUA phase>1 on 44/45 (`MPAYUP=MEFFDATE`) | 0 bad / 27 checked | **Yes** |
| Active control `010367131C` pay-up not forced | PASS | **Yes** |

### Intentional impact (candidates @44/45 phase 1)

| Field | Rows changed (risk simulation) |
|-------|-------------------------------:|
| `MPAYUP` | 223 |
| `MLASTANN` | 400 |

---

## 4. Prior Issue Fix Regression

| Issue | Check | Result |
|-------|-------|--------|
| **#25** | `validate_mpolicy_width.py` | **PASS** |
| **#26** | `validate_issue26_mprem.py` | Blocked — missing `*_20260530` extracts |
| **#26** | MPREM trace decimals (`010310404C`, `010331768C`, `010367131C`) | **PASS** |
| **#60** | PUA sample `010407670C` phase 2 `MPAYUP=MEFFDATE` | **PASS** |
| **#72** | Sample `010407670C` MSTATUS=45 MNFOPT=3 | **PASS** |

---

## 5. Commands Run

```bash
python Issue_Log_Items/Issue_76/scripts/regression_issue76.py
python tools/validators/validate_mpolicy_width.py
python tools/validators/validate_issue76_eti_rpu_payup.py
```

Evidence: `evidence/issue76_regression_checks.csv` (23 checks, 0 failures)

---

## 6. Fleet Impact Summary

| Metric | Value |
|--------|------:|
| ETI/RPU phase-1 policies adjusted | 400 |
| Non-candidate false overrides | 0 |
| Collateral field drift on candidates | 0 |
| PUA regressions | 0 |
| Table row-count drift | 0 |

---

## 7. Client UAT

1. Reload `Output/Test_Validation/quikridr.csv`  
2. Data Admin + Rebuild CV on **`010407670C`**  
3. Confirm Policy Display CV dates ~ **2026**, not **2080**

---

## Gate Criteria (G6 — Regression Pass)

- [x] Row counts stable  
- [x] Unrelated fields unchanged (risk-backed + guards)  
- [x] #25 / #26 preservation verified (MPREM traces + #25 validator)  
- [x] Regression report published  
- [x] No schema integrity violations  

**Status:** **Ready for Client UAT** (Closure after UAT sign-off)

---

## Next step

After client UAT on CV dates, say **“Close Issue 76”** for Closure Agent docs.
