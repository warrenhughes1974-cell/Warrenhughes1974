# Issue #21D — Client Signoff Package

**Date:** 2026-06-27  
**Converter version:** v57.36  
**Release:** Partial Issue #21D (Track A + Track B1)

---

## 1. What client is signing off

| Item | Description |
|------|-------------|
| **Converter version** | v57.36 |
| **Track A** | ISWL Dividend Accum Int Rate corrected to 4.50% |
| **Track B1** | Seven policies + 12 quikclnt rows — name display corrected |
| **Not in scope** | Track B2 — nine RNA-deficient policies |

---

## 2. Pre-UAT evidence summary (QLAdmin automated QA)

Provided for client reference before manual UAT:

| Check | Result |
|-------|--------|
| ISWL policies @ 4.50% | 2,268 / 2,268 ✅ |
| Non-ISWL @ 4.00% | 2,815 / 2,815 ✅ |
| B1-target policies (7) | 7 / 7 names resolved ✅ |
| Both-blank population | 25 → 9 ✅ |
| MPRIMID='I' leak | 0 ✅ |
| Protected regressions (#25/#26/#28/#21M) | PASS ✅ |

---

## 3. Client sign-off form

### Track A — Interest crediting rate

I confirm that ISWL policies in QLAdmin display **4.50%** Dividend Accum Int Rate and non-ISWL policies remain at **4.00%** per the test scenarios in `Issue_21D_Client_Test_Scenarios.md`.

| Field | Entry |
|-------|-------|
| Result | ☐ PASS  ☐ FAIL |
| Tester name | |
| Date | |
| Notes | |

---

### Track B1 — Owner / insured names

I confirm that the seven B1-target policies display correct insured/owner names and no unexpected name regressions were observed.

| Field | Entry |
|-------|-------|
| Result | ☐ PASS  ☐ FAIL |
| Tester name | |
| Date | |
| Notes | |

---

### Track B2 — Acknowledgment (not sign-off of fix)

I acknowledge that **nine policies** remain blank due to missing IN/PO rows in the PRELSA RNA extract. This is a **client data remediation** item (EXT-B1), not a converter defect in v57.36.

| Field | Entry |
|-------|-------|
| Acknowledged | ☐ YES |
| Client action owner | |
| Target delivery date | |
| Notes | |

---

### Production authorization (optional — after UAT pass)

| Field | Entry |
|-------|-------|
| Authorize v57.36 for production conversion | ☐ YES  ☐ NO  ☐ LIMITED |
| Authorized by | |
| Date | |
| Conditions | |

---

## 4. Partial closure recommendation

Upon client sign-off of Track A and Track B1:

| Issue portion | Recommended status |
|---------------|-------------------|
| Issue #21D Track A | **CLOSED** |
| Issue #21D Track B1 | **CLOSED** |
| Issue #21D Track B2 | **OPEN** (client-owned) |
| Issue #21D (full) | **PARTIALLY CLOSED** |

---

## 5. Enclosed documents

| Document | Purpose |
|----------|---------|
| `Issue_21D_Client_UAT_Package.md` | UAT instructions |
| `Issue_21D_Client_Test_Scenarios.md` | Test cases |
| `Issue_21D_Client_Acceptance_Checklist.md` | Acceptance criteria |
| `Issue_21D_B2_Client_Action_Register.md` | B2 action items |
| `Issue_21D_Blank_Name_Population.csv` | Full policy reference |
| `Issue_21D_Interest_Rate_Population.csv` | ISWL rate population |

---

## 6. Contact / escalation

| Role | Action on defect |
|------|------------------|
| Client UAT tester | Log defect with MPOLICY + screenshot |
| QLAdmin conversion | Triage Track A vs B1 vs B2 |
| Client extract team | B2 RNA delivery only |

---

*Signoff package ready for client distribution.*
