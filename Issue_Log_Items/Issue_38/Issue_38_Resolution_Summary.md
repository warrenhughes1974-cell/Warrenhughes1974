# Issue #38 — Resolution Summary

**Issue:** #38 — Dividend Accumulations  
**Framework stage:** Closure Agent (G7)  
**Final status:** **Closed**  
**Engine version:** **v57.44**  
**Closed date:** 2026-07-04  
**Owner:** Conversion (Warren) · Reporter: Eric

---

## Production Readiness (G7 gate)

| Check | Status |
|-------|--------|
| G5 validation PASS | **Done** |
| G6 regression PASS | **Done** |
| `app.py` / `QLA_Migration/app.py` **v57.44** | **Done** |
| Issue-scoped git commit | **Pending push step** |
| Network batch after pull | Re-run full batch at v57.44 (`Output/` gitignored) |

---

## Problem Statement

Eric reported that **Dividend Accumulations do not appear in QLAdmin** for policies including **010378830C** and **010380808C** (960 PO). LifePRO screenshots confirmed balances exist in source; QLAdmin showed zero or blank dividend deposit values.

---

## Root Cause

**Category:** Mapping / engine enrichment error (not source extract defect)

The rulebook correctly mapped **`PPBENTYP.ACCUM_DIVIDENDS` → `quikdvdp.MDEPOSIT`**, but post-emit **QUIKDVDP ENRICHMENT** forced **`MDEPOSIT = 0.00`** whenever the PACTG transaction cache missed. The cache never built because the code hardcoded **`PACTG_Accounting_Extract20260427.csv`**, which is absent from Source (only **`20260530`** exists). All **5,083** policies were zeroed; **59** had non-zero accumulation balances in LifePRO.

---

## Resolution

**v57.44** preserves **`MDEPOSIT`** from the rulebook (PPBENTYP source data). **MINTYTD** and **MINTDATE** enrich from **PACTG account 641** only when the cache loads. PACTG path resolves dynamically via `_resolve_table_source_path("quikprmh", ...)`. Account **514** sums are no longer used as balance authority.

### Files changed

| File | Change |
|------|--------|
| `app.py` | v57.44; quikdvdp enrichment + PACTG 641 cache |
| `QLA_Migration/app.py` | Mirror |
| `tools/validators/validate_issue38_mdeposit.py` | New validator |
| `QLA_Migration/_research_issue38_quikdvdp.py` | Read-only research |
| `QLA_Migration/_risk_review_issue38_quikdvdp.py` | Risk simulation |
| `Issue_Log_Items/Issue_38/*` | Intake through closure artifacts |

### Rulebook changes

**None** — `Sync_Rulebook_quikdvdp.csv` unchanged.

---

## Evidence

| Artifact | Path |
|----------|------|
| Intake | `Issue_38_Intake_Summary.md` |
| Planning | `Issue_38_Planning_Report.md` |
| Dependency Gate | `Issue_38_Dependency_Gate.md` |
| Risk | `Issue_38_Risk_Review_Report.md` |
| Validation (G5) | `Issue_38_Validation_Report.md` |
| Regression (G6) | `Issue_38_Regression_Report.md` |
| Population | `Issue_38_Population.csv` |
| Validator | `tools/validators/validate_issue38_mdeposit.py` |

---

## Trace Policy Confirmation

| Policy | Source `ACCUM_DIVIDENDS` | Emitted `MDEPOSIT` | Match |
|--------|-------------------------:|-------------------:|-------|
| 010378830C | 9,888.08 | 9,888.08 | Yes |
| 010380808C | 9,220.33 | 9,220.33 | Yes |
| 010435671C | 17,237.02 | 17,237.02 | Yes |
| 010713704C | 0.00 | 0.00 | Yes (ISWL control) |

---

## Explicitly Not Changed

- Issue #25 MPOLICY 10-char padding
- Issue #26 MPREM / quikmstr.MMODPREM
- Issue #21D ISWL MDEPINT 4.50 allowlist
- `Sync_Rulebook_quikdvdp.csv` field mappings
- quikdvdp row count (5,083)
- All other conversion tables

---

## Fleet Impact

| Metric | Value |
|--------|------:|
| Policies with MDEPOSIT corrected | 59 |
| quikdvdp rows with MINTDATE populated (641 cache) | 63 |
| quikdvdp rows with 2026 MINTYTD > 0 | 18 |
| Row count delta (quikdvdp) | 0 |

---

## Git Release

| Item | Value |
|------|-------|
| Commit | *(recorded at G7 push)* |
| Branch | `issue-34-pr7-quikisrr` |

**Network batch:** Pull latest branch, confirm **v57.44** in `app.py`, run **`QLA_Migration/run_converter.bat`** or `tools/batch_tests/run_full_batch_test.py`. `Output/` is gitignored — regenerate `quikdvdp.csv` on the network machine after pull.

---

## Client UAT

| Item | Status |
|------|--------|
| QLAdmin dividend accumulation visible | **Pending client UAT** |
| Sample policies | 010378830C, 010380808C |

---

## Residual Risks / Follow-ups

| Item | Owner | Notes |
|------|-------|-------|
| MINTYTD = 0 for most policies in 2026 | Informational | No 641 credits posted in 2026 in current PACTG extract |
| PEVNTNONFC extract absent | Optional | PACTG 641 fallback in use; deliver PEVNTNONFC if client wants alternate YTD path |

---

## Rollback

1. Revert to **v57.43** (`app.py` quikdvdp enrichment block).
2. Re-run full batch.
3. Confirm `validate_issue38_mdeposit.py` fails (expected).

---

## Issue Log Entry (paste-ready)

> **Issue #38 — Dividend Accumulations — CLOSED (2026-07-04).** QLAdmin showed zero dividend deposit balances because enrichment wiped `quikdvdp.MDEPOSIT` when PACTG cache failed to load. **Fix:** v57.44 preserves PPBENTYP `ACCUM_DIVIDENDS` for 59 policies; PACTG 641 enriches MINTYTD/MINTDATE; dynamic PACTG path. **Evidence:** Validation and regression PASS; trace 010378830C / 010380808C confirmed. **Preserved:** MPOLICY (#25), MPREM (#26), MDEPINT (#21D). **Follow-ups:** Client UAT on sample policies.

---

## Framework Checklist

- [x] Intake
- [x] Planning
- [x] Dependency Gate PASS
- [x] Risk Conditional Go
- [x] Development (v57.44)
- [x] Validation PASS
- [x] Regression PASS
- [x] Closure
- [ ] Git commit + push (G7 — in progress)
