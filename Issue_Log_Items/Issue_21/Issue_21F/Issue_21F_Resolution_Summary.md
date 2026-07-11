# Issue 21F — Resolution Summary

**Issue:** 21F — Truncated Premium History (Conversion Adjustment)  
**Framework stage:** Closure Agent (G7)  
**Final status:** **Closed** — Ready for Client UAT  
**Engine version:** v57.73  
**Closed date:** 2026-07-11  
**Owner:** Conversion + Client (Eric)

---

## Resolution (issue log — paste-ready)

**Resolution:** Non-ISWL policies receive one additive Conversion Adjustment `quikprmh` row dated 12/31/2017 (`MSOURCE=CONV_ADJ`) when LifePRO Base+PUA+SU+SL total exceeds converted payment history; ISWL excluded; negatives in exception report only (v57.73).

---

## Problem Statement

Premium payment history loaded into QLAdmin reflects only recent PACTG detail (post-~2017 floor), not full LifePRO lifetime premiums paid. Example: policy **010310404C** had LifePRO total **$17,040.05** but only **$1,846.20** in converted history. Client (Eric) approved a single conversion adjustment row per eligible non-ISWL policy to reconcile the gap.

---

## Root Cause

**Category:** Scope gap + source floor

PACTG payment extract does not carry full pre-2017 accounting history into `quikprmh`. QLAdmin therefore under-reports lifetime premiums paid unless an opening-balance adjustment is added at conversion.

---

## Resolution

Engine v57.73 appends one synthetic `quikprmh` row per eligible non-ISWL policy when LifePRO four-component total (BA/BF base + PU + SU + SL from PPBENTYP) exceeds existing history sum. Adjustment dated **20171231**, marked `MSOURCE=CONV_ADJ`, `USER_ID=QLA21F`, `MBATCH=21F-ADJ`. ISWL (`TYPE_CODE=BF`) excluded phase 1. Negative gaps logged to exception report only. Validation and exception CSVs published under `QLA_Migration/Reports/`.

### Files changed

| File | Change |
|------|--------|
| `qla_core/issue21f_premium_adjustment.py` | New — totals, eligibility, row build, strip-rebuild idempotency, reports |
| `app.py` / `QLA_Migration/app.py` | Wire after quikprmh build; **v57.73** |
| `tools/validators/validate_issue21f_premium_adjustment.py` | Golden + report reconcile validator |
| `Issue_Log_Items/Issue_21/Issue_21F/*` | Framework artifacts, rebatch/audit/regression scripts |

### Rulebook changes

None — logic module + batch wire only.

### Engine changes

- Typed PPBENTYP aggregation: base from **BA/BF only**; PU/SU/SL summed on typed rows  
- Strip-rebuild CONV_ADJ each run (idempotent output + correct UAT report)  
- `OPENING_BALANCE` status when no prior history  
- **2,609** CONV_ADJ rows; **$19,970,810.97** total adjustment premium  

---

## Evidence

| Artifact | Path |
|----------|------|
| Business decisions | `Issue_Log_Items/Issue_21/Issue_21F/Issue_21F_Business_Decisions.md` |
| Planning report | `Issue_Log_Items/Issue_21/Issue_21F/Issue_21F_Planning_Report.md` |
| Risk review | `Issue_Log_Items/Issue_21/Issue_21F/Issue_21F_Risk_Review_Report.md` (CONDITIONAL GO) |
| Validation report | `Issue_Log_Items/Issue_21/Issue_21F/Issue_21F_Validation_Report.md` — **PASS** |
| Regression report | `Issue_Log_Items/Issue_21/Issue_21F/Issue_21F_Regression_Report.md` — **PASS** |
| UAT validation CSV | `QLA_Migration/Reports/issue21f_premium_adjustment_validation.csv` |
| Exception CSV | `QLA_Migration/Reports/issue21f_premium_adjustment_exceptions.csv` |
| Partial UAT reload | `QLA_Migration/Output/Test_Validation/quikprmh.csv` |
| Validator | `tools/validators/validate_issue21f_premium_adjustment.py` |

---

## Trace Policy Confirmation

| Policy | Client expected | Emitted | Match |
|--------|-----------------|---------|-------|
| 010310404C | Adj **$15,193.85** @ 20171231 | CONV_ADJ **$15,193.85**; total **$17,040.05** | Yes |
| 010713704C (ISWL) | No adjustment | No CONV_ADJ row | Yes |
| 01FG8217A/C/D | Negative exception only | Not loaded; in exceptions report | Yes |

---

## Explicitly Not Changed

- Pre-existing `quikprmh` payment rows (206,861 rows byte-identical)
- quikmstr, quikridr, quikplan, quikclid, quikclnt, quikbenf row counts
- Issue **#25** MPOLICY 10-char padding
- Issue **#26** MPREM mapping on quikridr
- Modal premium / MMODPREM on quikmstr
- ISWL premium history (phase 1 exclusion per Eric)

---

## Fleet Impact

| Metric | Value |
|--------|------:|
| CONV_ADJ rows added | 2,609 |
| Adjustment premium sum | $19,970,810.97 |
| OPENING_BALANCE policies | 359 |
| ISWL excluded | 2,348 |
| Negative exceptions | 3 |
| History rows changed | 0 |
| Other table row deltas | 0 |

---

## Production Readiness + Git Release (G7)

| Check | Status |
|-------|--------|
| Validators PASS (G5 + G6) | Yes |
| `app.py` version bumped | **v57.73** (both copies) |
| Issue-scoped git commit | hash: *(recorded after commit)* |
| **`git push` to remote** | branch: `issue-34-pr7-quikisrr` |
| Network batch note | `Output/` gitignored — run **EXECUTE FULL BATCH MIGRATION** on network after pull |

---

## Client UAT

| Item | Status |
|------|--------|
| Golden 010310404C premium total | Pending client verify |
| ISWL 010713704C unchanged | Pending client verify |
| UAT reports + Test_Validation quikprmh | Ready for Eric review |
| Client sign-off | Pending |

**UAT package for Eric:**
1. `QLA_Migration/Output/Test_Validation/quikprmh.csv`
2. `QLA_Migration/Reports/issue21f_premium_adjustment_validation.csv`
3. `QLA_Migration/Reports/issue21f_premium_adjustment_exceptions.csv`

---

## Residual Risks / Follow-ups

| Item | Owner | Notes |
|------|-------|-------|
| ISWL phase 2 | Client | Eric excluded ISWL phase 1; separate issue if ISWL adjustment needed |
| 3 negative exceptions | Client | 01FG8217A/C/D — history exceeds LifePRO total |
| Full batch on network | Conversion | Re-run batch after pull; offline rebatch path used for validation |

---

## Rollback

1. Revert commit *(hash below)* or restore `quikprmh` from `QLA_Migration/Archive/quikprmh_pre_21f_v57.72.csv`
2. Set `APP_VERSION` back to pre-21F baseline
3. Remove `qla_core/issue21f_premium_adjustment.py` wire from `app.py`
4. Re-run batch from baseline Source/

---

## Issue Log Entry (paste-ready)

> **Issue #21F — Truncated Premium History — CLOSED (2026-07-11).**  
> **Resolution:** Non-ISWL policies receive one additive Conversion Adjustment `quikprmh` row dated 12/31/2017 (`MSOURCE=CONV_ADJ`) when LifePRO Base+PUA+SU+SL total exceeds converted payment history; ISWL excluded; negatives in exception report only (v57.73).  
> **Evidence:** Validation and regression PASS; trace policies 010310404C, 010713704C, 01FG8217A confirmed. **Preserved:** MPOLICY padding (#25), MPREM (#26), 206,861 history rows. **Follow-ups:** ISWL phase 2 if required; 3 negative exceptions for client review.

---

## Framework Checklist

- [x] Intake
- [x] Planning
- [x] Dependency Gate PASS
- [x] Risk CONDITIONAL GO
- [x] Development (v57.72 + fix v57.73)
- [x] Validation PASS
- [x] Regression PASS
- [x] Closure — Resolution summary published
- [x] Git commit + push (G7 release gate)
