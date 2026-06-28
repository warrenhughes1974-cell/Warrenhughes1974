# Issue #21D — Track B2 Client Action Register

**Date:** 2026-06-27  
**Converter version:** v57.36  
**Dependency ID:** EXT-B1  
**Owner:** Client / LifePRO extract team  
**Status:** **OPEN**

---

## 1. Summary

Track B2 is a **client-owned data remediation** activity. The v57.36 converter cannot manufacture missing IN/PO relationship rows. Nine policies remain with blank insured and owner names until PRELSA RNA is re-delivered.

**This is not a converter defect and does not invalidate Track A or Track B1 UAT.**

---

## 2. Required client deliverable

| Field | Specification |
|-------|---------------|
| **Extract** | PRELSA / `RelationshipNameAddress_Extract_*.csv` |
| **Delivery path** | `QLA_Migration/Source/` |
| **Required roles** | `IN`, `PO` (and related roles where present in LifePRO) |
| **Reference list** | `Issue_21D_Blank_Name_Population.csv` |
| **Priority golden policy** | 010713704C (9010713704) |

---

## 3. Nine both-blank policies (RNA missing IN and PO)

| MPOLICY | MPLAN | IS_ISWL | RNA gap |
|---------|-------|---------|---------|
| 010422977C | 1960PO | N | No IN, no PO in extract |
| **010713704C** | 1659C2 | Y | No IN, no PO (SA+BK only) |
| 010713705C | 1659C2 | Y | No IN, no PO |
| 010826551C | 1659CR | Y | No IN, no PO |
| 010948278C | 5667AT | N | No IN, no PO |
| 014112C | 1SALML | N | No IN, no PO |
| 018900C | 1SALML | N | No IN, no PO |
| 010150910C | 221END | N | No IN, no PO |
| 01ML8151C | 1SALML | N | No IN, no PO |

---

## 4. Additional policies (partial blank — may also benefit from RNA)

These policies had partial name display issues beyond the nine both-blank set. RNA re-extract may resolve remaining owner or insured gaps:

| MPOLICY | Gap type |
|---------|----------|
| 010774773C | Missing IN |
| 010816156C | Missing IN |
| 010877890C | Missing IN |
| 011188773C | Missing PO |
| 010397945C | Missing PO |
| 010790779C | Missing PO |
| 010834096C | Missing PO |
| 011062307C | Missing PO |
| 011064567C | Missing PO |

---

## 5. Evidence of gap (010713704C)

LifePRO hierarchy includes IN|PA|PO|B1|B2|BK|SA roles; current RNA extract contains **SA + BK only**. See `Issue_21D_Trace_Samples.md`.

---

## 6. QLAdmin actions after client delivery

| Step | Owner | Action |
|------|-------|--------|
| 1 | Client | Deliver updated PRELSA extract |
| 2 | QLAdmin | Drop file into `QLA_Migration/Source/` |
| 3 | QLAdmin | Re-run full batch (v57.36 — no code change expected) |
| 4 | QLAdmin | Run `validate_issue21d_blank_names.py` — target 0 both-blank |
| 5 | Client | UAT full Track B name display |
| 6 | Both | Close Track B2 / full Issue #21D |

---

## 7. Acceptance criteria (B2 completion)

| Criterion | Target |
|-----------|--------|
| Both-blank population | 0 (or documented client-approved exceptions) |
| 010713704C names | Populated if IN/PO exist in LifePRO |
| quikclid IN/PO rows | Present for listed policies |
| Client UAT Track B | PASS |

---

## 8. Timeline tracking

| Milestone | Owner | Target date | Status |
|-----------|-------|-------------|--------|
| Action register issued | QLAdmin | 2026-06-27 | ✅ |
| Client acknowledges B2 scope | Client | | 🔲 |
| PRELSA re-extract delivered | Client | | 🔲 |
| Re-batch + validation | QLAdmin | | 🔲 |
| Track B2 UAT | Client | | 🔲 |
| Track B2 closure | Both | | 🔲 |

---

*Track B2 client action register — remains open.*
