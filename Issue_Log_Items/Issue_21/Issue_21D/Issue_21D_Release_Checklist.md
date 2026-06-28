# Issue #21D — Release Checklist

**Date:** 2026-06-27  
**Converter version:** v57.36  
**Release type:** Partial (#21D Track A + Track B1)

---

## A. Implementation complete

| # | Item | Status |
|---|------|--------|
| A1 | Track A MDEPINT ISWL allowlist implemented | ✅ |
| A2 | Track B1 quikclnt CANCEL_DATE NULL fix implemented | ✅ |
| A3 | Version bumped to v57.36 | ✅ |
| A4 | Both app.py copies updated | ✅ |
| A5 | Track B2 not implemented (by design) | ✅ |

---

## B. Validation complete

| # | Item | Status |
|---|------|--------|
| B1 | Full v57.36 batch completed | ✅ |
| B2 | `validate_issue21d_mdepint.py` PASS | ✅ |
| B3 | `validate_issue21d_blank_names.py` PASS | ✅ |
| B4 | Output delta documented (v57.35 → v57.36) | ✅ |
| B5 | Validation decision: PASS WITH OBSERVATIONS | ✅ |

---

## C. Regression gate

| # | Issue | Status |
|---|-------|--------|
| C1 | #25 MPOLICY | ✅ PASS |
| C2 | #26 MPREM | ✅ PASS |
| C3 | #28 Plan mapping | ✅ PASS |
| C4 | #21M QUIKMEMO | ✅ PASS |
| C5 | #21M-FU DBF packaging | ✅ PASS |
| C6 | #21K fleet/MUNIT | ⚠️ N/A (DBF artifact) |
| C7 | v57.28 MPRIMID guard | ✅ PASS |

---

## D. Documentation complete

| # | Artifact | Status |
|---|----------|--------|
| D1 | Development Report | ✅ |
| D2 | Validation Report + track validations | ✅ |
| D3 | Regression Report | ✅ |
| D4 | Rollback Strategy | ✅ |
| D5 | Client UAT Package | ✅ |
| D6 | Deployment Steps | ✅ |
| D7 | Remaining Client Actions (B2) | ✅ |

---

## E. Validators in repo

| # | Validator | Status |
|---|-----------|--------|
| E1 | `tools/validators/validate_issue21d_mdepint.py` | ✅ |
| E2 | `tools/validators/validate_issue21d_blank_names.py` | ✅ |
| E3 | `validate_insured_owner_golden.py` v1.2 | ✅ |

---

## F. Client / release gates (pending)

| # | Item | Status |
|---|------|--------|
| F1 | Client UAT Track A | 🔲 Pending |
| F2 | Client UAT Track B1 | 🔲 Pending |
| F3 | Non-ISWL 4.00% confirmation (recommended) | 🔲 Pending |
| F4 | RNA re-extract EXT-B1 (full #21D) | 🔲 Pending |
| F5 | Production deployment approval | 🔲 Pending |

---

## G. Release authorization

| Scope | Authorized? |
|-------|-------------|
| Client UAT (A + B1) | ✅ **YES** |
| Limited / staging release (A + B1) | ✅ **YES** |
| Production release | 🔲 After UAT |
| Full Issue #21D closure | 🔲 After B2 |

---

*Release checklist complete.*
