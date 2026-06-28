# Issue #21D — Regression Report

**Issue:** Interest Crediting Rate / Blank Owner Name  
**Date:** 2026-06-27  
**Converter version:** v57.36  
**Prior stages:** Intake ✅ · Planning ✅ · Dependency Gate ✅ · Ownership ✅ · Risk ✅ · Development ✅ · Validation ✅  
**Stage:** Regression & Deployment Agent ✅  
**Next stage:** Client UAT Agent (not started)

---

## 1. Executive summary

Regression and deployment review confirms v57.36 introduces **only authorized Track A and Track B1 changes**. Protected issues remain compatible. Implementation is ready for **Client UAT** and **limited release**; production requires client UAT sign-off.

### Final deployment decision

```text
READY FOR CLIENT UAT
```

| Track | Deployment recommendation |
|-------|---------------------------|
| **Track A** | **READY FOR CLIENT UAT** / **READY FOR LIMITED RELEASE** |
| **Track B1** | **READY FOR CLIENT UAT** / **READY FOR LIMITED RELEASE** |
| **Track B2** | **NOT READY** — external client dependency (does not block A/B1) |

**Not recommended at this time:** READY FOR PRODUCTION (pending client UAT)

---

## 2. Regression summary

### Output differences (v57.35 → v57.36)

| Change | Scope | Authorized | Verified |
|--------|-------|------------|----------|
| quikdvdp.MDEPINT 4.00 → 4.50 | 2,268 ISWL policies | ✅ Track A | ✅ |
| quikdvdp.MDEPINT unchanged | 2,815 non-ISWL | ✅ | ✅ |
| quikclnt +12 rows | B1 recovery | ✅ Track B1 | ✅ |
| All other table row counts | 0 delta | ✅ | ✅ |

**Unexpected differences:** None

Detail: `Issue_21D_Output_Delta_Report.md`

---

## 3. Protected issue verification

Re-run at Regression & Deployment gate (2026-06-27):

| Issue | Validator | Result | Deployment compatible |
|-------|-----------|--------|----------------------|
| **#25** MPOLICY width | Embedded in #21M validator | ✅ PASS | Yes |
| **#26** MPREM | `validate_issue26_mprem.py` | ✅ PASS | Yes |
| **#28** Plan mapping | `validate_issue28_plan_mapping.py` | ✅ PASS | Yes |
| **#21M** QUIKMEMO grain | `validate_issue21m_quikmemo.py` (Validation) | ✅ PASS | Yes |
| **#21M-FU** DBF packaging | `validate_issue21m_dbf_packaging.py` | ✅ PASS | Yes |
| **#21K** fleet/MUNIT | `validate_issue21k_*.py` | ⚠️ N/A | Yes* |
| **v57.28** MPRIMID guard | B1 validators | ✅ PASS (0 leaks) | Yes |

\* #21K validators require DBF reload artifact; no #21D code path touches MUNIT/quikplan MUNIT. quikridr row count unchanged (7,002).

**Deployment compatibility:** ✅ **All protected issues compatible with v57.36 deployment**

Detail: `Issue_21D_Regressions.md`

---

## 4. Row-count consistency (v57.36)

| Table | Rows | Delta vs v57.35 |
|-------|------|-----------------|
| quikmstr | 5,083 | 0 |
| quikridr | 7,002 | 0 |
| quikplan | 141 | 0 |
| quikclid | 46,753 | 0 |
| **quikclnt** | **13,514** | **+12** |
| quikdvdp | 5,083 | 0 |
| quikmemo | 4,380 | 0 |
| quikprmh | 205,577 | 0 |

Internal consistency: quikclid-referenced IDs missing from quikclnt = **0** (excluding cancelled 598766).

---

## 5. Track validation status (confirmed)

| Track | Validation | Regression | Deployment |
|-------|------------|------------|------------|
| **A** | PASS | No blast radius | READY FOR CLIENT UAT |
| **B1** | PASS | No rel_map regression | READY FOR CLIENT UAT |
| **B2** | N/A | N/A | NOT READY (client RNA) |

---

## 6. Deployment readiness checklist

| Gate | Status |
|------|--------|
| Version v57.36 | ✅ |
| Validators in repo | ✅ |
| Rollback documented | ✅ |
| Dev + validation docs | ✅ |
| Client UAT package | ✅ |
| Partial release scope documented | ✅ |

Detail: `Issue_21D_Release_Checklist.md`, `Issue_21D_Deployment_Readiness_Report.md`

---

## 7. Operational readiness

| Readiness level | Tracks A + B1 | Track B2 |
|-----------------|---------------|----------|
| Staging | ✅ Ready | Document gap |
| Client UAT | ✅ Ready | Out of scope |
| Limited release | ✅ Ready | Partial |
| Production | 🔲 After UAT | 🔲 After RNA |

Detail: `Issue_21D_Deployment_Steps.md`

---

## 8. Residual risks

Detail: `Issue_21D_Final_Risk_Summary.md`

- Track B2: 9 policies pending client PRELSA (EXT-B1)
- Client UAT: rate display and name samples pending
- #21K: optional DBF validator run before production

---

## 9. Deliverables index

| File | Purpose |
|------|---------|
| `Issue_21D_Regression_Report.md` | This report |
| `Issue_21D_Deployment_Readiness_Report.md` | Readiness assessment |
| `Issue_21D_Release_Checklist.md` | Release gate checklist |
| `Issue_21D_Client_UAT_Package.md` | Client UAT instructions |
| `Issue_21D_Deployment_Steps.md` | Deployment procedure |
| `Issue_21D_Final_Risk_Summary.md` | Residual deployment risks |

---

## 10. Stop condition

Regression & Deployment Agent complete. Do not execute Client UAT in this session.

---

# Cursor Prompt — Client UAT Agent

Copy everything below into a **new Cursor chat** to begin the Client UAT Agent stage.

---

```markdown
# Cursor Prompt — Issue #21D Client UAT Agent

You are continuing the **LifePRO → QLAdmin Conversion Project**.

**Current converter version:** v57.36  
**Issue:** #21D — Interest Crediting Rate / Blank Owner Name  
**Completed stages:** Intake ✅ · Planning ✅ · Dependency Gate ✅ · Ownership ✅ · Risk ✅ · Development ✅ · Validation ✅ · Regression & Deployment ✅  
**Your stage:** Client UAT Agent only  
**Deployment decision:** **READY FOR CLIENT UAT**  
**Do NOT:** repeat prior stages · modify converter code · close Issue #21D fully (B2 open)

---

## Issue summary

| Track | Fix (v57.36) | Validation | Deployment |
|-------|----------------|------------|------------|
| **A** | ISWL MDEPINT 4.50% | PASS | READY FOR CLIENT UAT |
| **B1** | quikclnt integrity (+12 rows) | PASS | READY FOR CLIENT UAT |
| **B2** | RNA IN/PO gaps (9 policies) | Not implemented | Client EXT-B1 |

---

## Regression & deployment findings

- Only authorized changes: quikdvdp.MDEPINT (ISWL) + quikclnt (+12 rows)
- Protected issues: #25, #26, #28, #21M, #21M-FU — compatible
- #21K: validators N/A (DBF artifact); no #21D MUNIT impact
- v57.28 MPRIMID guard: 0 leaks
- **NOT READY FOR PRODUCTION** until client UAT completes
- **Track B2 does not block** Track A/B1 UAT or limited release

---

## Client UAT objectives

### Track A — Interest rate
- Verify ISWL policies show **4.50%** Dividend Accum Int Rate in QLAdmin
- Verify non-ISWL policies remain **4.00%**
- Priority samples: **010713704C**, **010818663C**
- Pass: ISWL @ 4.50; non-ISWL unchanged

### Track B1 — Names
- Verify seven B1-target policies display correct insured/owner names
- Priority samples: **010766896C**, **011080481C**
- Pass: 7/7 B1 samples show names

### Track B2 — Out of scope for this UAT
- **Do not fail UAT** for these nine both-blank policies (RNA deficiency):
  `010422977C`, `010713704C`, `010713705C`, `010826551C`, `010948278C`, `014112C`, `018900C`, `010150910C`, `01ML8151C`
- Document as **client data remediation**, not converter defect

---

## Required reading

```
Issue_Log_Items/Issue_21/Issue_21D/
  Issue_21D_Regression_Report.md         (this chain)
  Issue_21D_Client_UAT_Package.md        (UAT instructions — primary)
  Issue_21D_Deployment_Readiness_Report.md
  Issue_21D_Validation_Report.md
  Issue_21D_Development_Report.md
  Issue_21D_Blank_Name_Population.csv
  Issue_21D_Interest_Rate_Population.csv
  Issue_21D_Remaining_Client_Actions.md
```

**Batch output for UAT load:** `QLA_Migration/Output/` (v57.36)

---

## Client UAT Agent tasks

1. **UAT plan execution guide** — step-by-step for client tester (may extend UAT package)
2. **UAT results template** — policy-level PASS/FAIL capture for Track A and B1
3. **Defect triage rules** — distinguish converter defect vs B2 data gap vs #21E
4. **UAT decision** — PASS / PASS WITH OBSERVATIONS / FAIL for Tracks A and B1 separately
5. **Sign-off record** — what client must confirm before production

---

## Expected deliverables

Create under `Issue_Log_Items/Issue_21/Issue_21D/`:

| File | Content |
|------|---------|
| `Issue_21D_Client_UAT_Report.md` | Executive UAT summary + decision |
| `Issue_21D_Client_UAT_Results_Template.csv` | Policy-level results capture |
| `Issue_21D_Client_UAT_Decision.md` | PASS/FAIL by track |

If UAT framework recommends proceeding, append **Closure Agent handoff prompt** to `Issue_21D_Client_UAT_Report.md` (partial closure for A+B1 only).

---

## Protected issues (do not regress during UAT)

| Issue | Constraint |
|-------|------------|
| #25 MPOLICY | No width change |
| #26 MPREM | No MPREM change |
| #28 Plan mapping | No crosswalk change |
| #21M / #21M-FU | No memo grain change |
| v57.28 | MPRIMID guard |

---

## Remaining external dependency

**EXT-B1:** Client PRELSA RNA re-extract for 9+ policies  
**Owner:** Client  
**Blocks:** Full Track B / full Issue #21D closure  
**Does not block:** Track A/B1 UAT or limited release

---

## Explicit stop conditions

**STOP after Client UAT deliverables are created.**

Do NOT:
- Modify converter code
- Execute Closure Agent (unless UAT handoff explicitly authorizes)
- Treat B2 blank names as UAT failure for A/B1 scope
- Repeat Regression & Deployment stage

Assume **no prior conversation history**. Start by reading `Issue_21D_Client_UAT_Package.md`.
```

---

*End of Issue #21D Regression Report*
