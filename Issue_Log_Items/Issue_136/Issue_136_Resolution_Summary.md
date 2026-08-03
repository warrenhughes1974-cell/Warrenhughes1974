# Issue #136 — Resolution Summary

**Issue:** #136 — QuikPlan PVO Flags (Real Variation Only)  
**Framework stage:** Closure  
**Final status:** **Closed**  
**Engine version:** v58.62  
**Closed date:** 2026-08-02  
**Owner:** Conversion (Warren) / Issue Owner Eric  
**Commit:** `cccf858`  

---

## Resolution (issue log — paste-ready)

```text
08/02/2026 Resolution: Plan Values Options now turn on Gender/UW/Band/State/Dividend checkboxes only when that plan family actually has varying rates; default Band 00, ALL state, and missing dividends no longer show as variances. Examples: 1658C1 Band/State/Dividend off with Gross Premium Gender and UW still on; fleet Band and State variance counts 0; plans without dividend rates have all DV flags off.
```

---

## Problem Statement

QLAdmin Plan Values Options showed Band, State, and Dividend variation selected for plans that only had default structural keys (Band 00 / ALL state) or no dividend factor rates loaded (example: 1658C1).

---

## Root Cause

**Category:** [x] Mapping / flag enrichment error  

1. Issue #77 set `BDVARY*=Y` whenever a family had any real row (including Band 00 only) and `STVARYGP=Y` whenever GP was present.  
2. Issue #96 forced Band/Gender from mere QuikCvs/QuikTvs presence.  
3. QuikPlDb/QuikPlDv keys with F/M but empty QuikDbs/QuikDvs still activated DB/DV flags.  
4. Stale `emitted_dbf` Band 01 merged with CSV Band 00 inventing false multi-band.

---

## Resolution

- Band/State flags require multi-value real differentiation.  
- Family factor-presence gate clears VARY when QuikGps/Dbs/Cvs/Tvs/Dvs has no rows for that family.  
- Issue #96 no longer invents Band/Gender.  
- Prefer Output/rates QuikPl CSV keys over stale emitted_dbf.  
- Validated on full Output; published Test_Validation; deployed `quikplan.dbf` to Q UAT.

### Files changed (primary)

| File | Change |
|------|--------|
| `qla_core/quikplan_rate_variation_flags.py` | Real-rate-only flag rules |
| `app.py` / `QLA_Migration/app.py` | v58.62 |
| `tools/validators/validate_issue136_pvo_flags.py` | Output validator |
| `tools/validators/validate_issue_log_accountability.py` | `#136` IN_DATA |
| `tests/test_a11h_real_rate_only_flags.py` | Unit tests |
| `Issue_Log_Items/Issue_136/**` | Framework package |

---

## Evidence (G7 Output gate)

| Check | Result |
|-------|--------|
| `tools/validators/validate_issue136_pvo_flags.py` on full Output | **PASS** |
| Accountability `#136` spot-check | **IN_DATA** |
| 1658C1 gold | Band/State/DV/DB N; GP Gender/UW Y |
| Fleet Band Y / State Y | 0 / 0 |
| `Output/Test_Validation/quikplan.csv` | Published |
| Q UAT `quikplan.dbf` | Deployed; operator confirmed looks good |

Residual (documented, not blocking): Gender/UW still driven by distinct segmentation codes when factors exist, not a full factor-value equality matrix (Luna PASS-WITH-NOTES).

---

## Explicitly Not Changed

- Claims tables  
- Rate factor generation (keys/factors retained)  
- LOANINTX / QuikLoan  
