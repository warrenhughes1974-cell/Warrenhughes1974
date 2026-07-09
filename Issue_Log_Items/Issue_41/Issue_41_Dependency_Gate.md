# Issue #41 — Dependency Gate

**Issue:** #41 — CV Age/Duration Endpoint Off by One (`1960PO`)  
**Framework stage:** Dependency Gate (G2)  
**Date:** 2026-07-06  
**Planning reference:** `Issue_41_Planning_Report.md`

---

## 1. Checklist

### Source data and artifacts

| Check | Status | Notes |
|-------|--------|-------|
| Client LifePRO screenshot for `960 PO` / M / age `26` | **Met** | Shows value sequence and reported duration expectation. |
| QLAdmin screenshot for same slice | **Met** | Shows same value sequence one duration early per client report. |
| Prior Issue #37 documentation | **Met** | Confirms current endpoint rule is `100 - issue_age`. |
| Current `QuikCvs.csv` available in repo output | **Partial** | Output root currently does not contain `Output/rates/QuikCvs.csv`; regenerate during development validation. |
| Re-extract required? | **No at intake** | This appears to be placement / endpoint behavior, not missing source rates. |

### Target behavior

| Check | Status | Notes |
|-------|--------|-------|
| QLAdmin target table | **Met** | `QuikCvs` / QuikPlCv CV factor grid. |
| QLAdmin duration convention confirmed | **Missing** | Need final confirmation that CV grids must include age 100. |
| Corrected endpoint formula confirmed | **Missing** | Candidate is age-100 inclusive, likely one terminal duration beyond current rule. |
| Product-specific exceptions confirmed | **Missing** | Prior Issue #37 deferred PCOVR maturity overrides; revisit only if needed. |

### Regression guards

| Check | Status |
|-------|--------|
| Issue #37 first-rate placement preserved | Required |
| Issue #37 proof matrix rerun with new age `26` case | Required |
| QuikCvs values preserved | Required |
| Non-CV rate tables unchanged | Required |
| Issue #31 QuikCvs baseline updated only for intentional endpoint delta | Required |
| Issue #25 MPOLICY padding preserved | Required |
| Issue #26 MPREM preserved | Required |

---

## 2. Gate decision

| Track | Scope | G2 result |
|-------|-------|-----------|
| **Track A — CV endpoint correction** | QuikCvs duration endpoint should include age 100 | **BLOCKED — Awaiting target duration convention confirmation** |
| **Track B — `1960PO` proof-only patch** | Correct only client example | **Not recommended** unless client narrows scope |
| **Track C — Non-CV rate endpoint review** | NP/GP/DB/DV/TV tables | **Deferred** — no evidence currently |

**Overall G2:** **FAIL (conditional)** — research is sufficient to define the issue, but development should wait for confirmation of the QLAdmin age-100-inclusive duration convention.

---

## 3. Unblock actions

| Action | Owner | Deliverable |
|--------|-------|-------------|
| Confirm QLAdmin CV duration endpoint should be age 100 inclusive | Client / QLAdmin SME | Written confirmation or authoritative screenshot/spec |
| Confirm formula: age-100 inclusive endpoint vs PCOVR maturity metadata | Conversion + Client | Implementation decision |
| Add `1960PO` Male issue age `26` to proof matrix | Conversion | Validator update during development |
| Regenerate and validate `QuikCvs.csv` | Conversion | G5 validation artifacts |

---

## 4. Proceed when

- [ ] Client / SME confirms age-100-inclusive endpoint for CV grids
- [ ] Scope confirmed as CV-only
- [ ] Risk Agent (G3) completes blast-radius review
- [ ] Validation plan includes the new `1960PO` M/26 example

**Next stage after unblock:** Risk Agent -> Development Agent.
