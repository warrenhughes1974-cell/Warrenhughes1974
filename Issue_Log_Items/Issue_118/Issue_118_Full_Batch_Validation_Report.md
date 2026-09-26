# Issue #118 — Full Batch Validation Report

**Date:** 2026-08-09  
**Engine:** v58.85 (batch ran on v58.84; membership emit fix bumped to v58.85)  
**Source:** `PPOLC_PolicyMaster_Extract_20260630.csv`  
**Valuation:** `QLA_VALUATION_DATE=20260630`  
**Runner:** `tools/batch_tests/run_full_batch_test.py` (UAT, rates ON, Append GUI OFF)  
**Log:** `QLA_Migration/Logs/_full_batch_test_log.txt`

---

## Batch result

| Check | Result |
|-------|--------|
| Full batch complete | **PASS** (exit 0) |
| Claims UAT DBF alignment | **PASS** (QUIKCLMS 6044 / QUIKCLMP 6536) |
| Post-check CLNT-RJ (client-ID width-12) | **PASS** |
| Post-check CLNT-HW (quikclnt high-water) | **PASS** |

---

## Issue #118 Output proof (after batch)

| Check | Result |
|-------|--------|
| `validate_issue118_uwclass.py` | **PASS** — 6,934 rows; domain `{00,BL,NT,PQ,PR,SM,ST}`; QuikUwpo no NS; L10 family covers all 15 crosswalk plans |
| `validate_issue59_muwclass.py` | **PASS** |
| UAT / smoke screen (11 policies) | **PASS** — see below |
| Membership A–D (after QuikPlUw sync) | **0 / 0 / 0 / 0** |

### MUWCLASS distribution (full Output)

| Code | Rows |
|------|-----:|
| PR | 2,269 |
| 00 | 1,706 |
| ST | 1,523 |
| BL | 840 |
| SM | 384 |
| PQ | 111 |
| NT | 101 |

---

## Smoke screen vs Output

Script: `Issue_Log_Items/Issue_118/tools/validate_issue118_uat_smoke.py`  
Source list: `Issue_118_UAT_Example_Policies.md`

| Policy | Plan | Expect | Got | Result |
|--------|------|--------|-----|--------|
| 9011189929C | 1L1095 | BL | BL | PASS |
| 9011190516C | 1L1095 | SM | SM | PASS |
| 9011193156C | 1L1095 | PR | PR | PASS |
| 9011059291C | 5L0110 | ST | ST | PASS |
| 9011052719C | 5L0110 | PR | PR | PASS |
| 9011206462C | 1L14SC | NT | NT | PASS |
| 9011208194C | 1L14SC | ST | ST | PASS |
| 9011207210C | 1L14SC | PQ | PQ | PASS |
| 9011215903C | 1L14SC | PR | PR | PASS |
| 9010360290C | 170858 | 00 | 00 | PASS |
| 9010713704C | 1659C2 | PR | PR | PASS |

**Smoke RESULT: PASS**

---

## QuikPlUw membership note (important)

Straight out of the rate stage, QuikPlUw was built from **rate keys only**. That left **734** policy rows whose MUWCLASS was not on the plan dropdown (riders, discount riders, PA plans with no rates).

| Action | Detail |
|--------|--------|
| Immediate | Rebuilt QuikPlUw from live rate keys **+** `quikridr.MUWCLASS` → **247** rows / **147** plans; membership A–D all zero |
| Lasting fix | `ensure_members_for_rider_uw` in `qla_core/rate_member_setup.py`, called from `rate_emit.py` before CSV emit (v58.85) so the next full batch does this automatically |

Policy MUWCLASS values themselves were already correct from the batch; only the dropdown membership table needed the sync.

---

## Client deliverables

| File | Purpose |
|------|---------|
| `evidence/Issue_118_Plan_Underwriting_Classes.xlsx` | Every plan × every UW class (for Eric approval) |
| `Issue_118_Open_Questions_for_Eric.md` | Remaining Eric decisions (Q1–Q3) |
| `Output/Test_Validation/` | Published remapped tables for partial UAT reload |

---

## Verdict

**Batch + Issue #118 validation: PASS** for policy underwriting classes and smoke screen.  
Plan membership table synced and production emit patched for next run.  
Ready for Eric to review the plan × class workbook and answer the three open questions.
