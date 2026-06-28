# Issue #21D — Client Acceptance Checklist

**Date:** 2026-06-27  
**Converter version:** v57.36  
**Issue:** Interest Crediting Rate / Blank Owner Name  
**UAT scope:** Track A + Track B1

---

## Pre-UAT (QLAdmin — complete)

| # | Item | Status |
|---|------|--------|
| P1 | v57.36 batch output available | ✅ |
| P2 | QLAdmin UAT environment load path documented | ✅ |
| P3 | `Issue_21D_Client_UAT_Package.md` distributed | ✅ |
| P4 | Test scenarios documented | ✅ |
| P5 | B2 exclusion documented | ✅ |
| P6 | Automated validators PASS (Track A + B1) | ✅ |

---

## Track A acceptance criteria

| # | Criterion | Client verify | Pass |
|---|-----------|---------------|------|
| A1 | 010713704C Dividend Accum Int Rate = 4.50% | ☐ | ☐ |
| A2 | 010818663C Dividend Accum Int Rate = 4.50% | ☐ | ☐ |
| A3 | Client-selected ISWL policy = 4.50% | ☐ | ☐ |
| A4 | Non-ISWL sample #1 = 4.00% | ☐ | ☐ |
| A5 | Non-ISWL sample #2 = 4.00% | ☐ | ☐ |
| A6 | No unexpected ISWL-family product at wrong rate | ☐ | ☐ |

**Track A acceptance:** All A1–A6 checked PASS → **Track A ACCEPTED**

---

## Track B1 acceptance criteria

| # | Criterion | Client verify | Pass |
|---|-----------|---------------|------|
| B1 | 010766896C — JOHNSON, PENNY visible | ☐ | ☐ |
| B2 | 011080481C — YOUNTS, JOSHUA (insured) visible | ☐ | ☐ |
| B3 | 010464869C — ULMER, ARTHUR visible | ☐ | ☐ |
| B4 | 010464870C — ULMER, IRENE visible | ☐ | ☐ |
| B5 | 010872417C — EPLEY, JOHN visible | ☐ | ☐ |
| B6 | 011047402C — ULMER, IRENE visible | ☐ | ☐ |
| B7 | 011047403C — ULMER, ARTHUR visible | ☐ | ☐ |
| B8 | No wrong-person or duplicate name observed | ☐ | ☐ |
| B9 | No "I" type-flag displayed as client ID | ☐ | ☐ |

**Track B1 acceptance:** All B1–B9 checked PASS → **Track B1 ACCEPTED**

---

## Track B2 acknowledgment (not acceptance — client action)

| # | Item | Client acknowledge | Done |
|---|------|-------------------|------|
| C1 | Nine policies remain blank due to RNA gap | ☐ | ☐ |
| C2 | B2 is client PRELSA re-extract — not converter defect | ☐ | ☐ |
| C3 | `Issue_21D_B2_Client_Action_Register.md` received | ☐ | ☐ |
| C4 | Client will deliver updated RNA extract (EXT-B1) | ☐ | ☐ |

**Track B2:** Acknowledgment only — **does not block Track A/B1 acceptance**

---

## Overall issue acceptance

| Scope | Can close after client sign-off? |
|-------|-------------------------------|
| **Track A** | ✅ Yes — independent closure |
| **Track B1** | ✅ Yes — independent closure |
| **Track B2** | 🔲 No — remains open until RNA + revalidation |
| **Full Issue #21D** | 🔲 Partial close only (A + B1) |

---

## Sign-off block

| Role | Name | Date | Track A | Track B1 | B2 ack |
|------|------|------|---------|----------|--------|
| Client UAT tester | | | ☐ PASS | ☐ PASS | ☐ |
| Client business owner | | | ☐ APPROVE | ☐ APPROVE | ☐ |
| QLAdmin conversion lead | | | ☐ READY | ☐ READY | ☐ |

---

*Acceptance checklist — pending client execution.*
