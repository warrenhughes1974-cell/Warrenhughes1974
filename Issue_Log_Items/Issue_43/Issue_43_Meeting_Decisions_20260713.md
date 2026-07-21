# Issue #43 — Meeting Decisions (2026-07-13)

**Issue:** #43 — ISWL Expense Charge Source Discovery  
**Companion:** #23 — ISWL 3.5% Premium Expense Charge (plan setup)  
**Status after meeting:** **DECIDED** on fee / % premium · **OPEN** on U6 COI question  
**Source:** Eric Scow email + ISWL annual statement (Censi I)

---

## Decisions locked

### D1 — Policy fee $25 = monthly per-policy expense (amortized)

| Question | Decision |
|----------|----------|
| Is LifePRO `PCOVR.POLICY_FEE` = 25.00 the QLAdmin monthly expense per policy? | **Yes — with monthly amortization** |
| Amount | **$25.00 per year**, taken **monthly** |
| Statement proof | Monthly Charge **$2.08** each month × 12 = **$24.96** ≈ $25.00 |

**Implementation intent (for Sujitha / Development):**  
QLAdmin **UF / Monthly expense per policy** should be set from the $25 annual policy fee on a **monthly** basis (**≈ $2.08 / month**, not $25 charged every month).  
Do **not** treat as a one-time charge.  
Exclude **single premium** ISWL plans (per #23 original scope).

**Evidence:** `evidence/Annual_Statement_Censi_I_9010817956.pdf`  
Policy `9010817956` · Product Interest-Sensitive Whole Life · Period 11/04/2024–11/04/2025  
- Annual line: Monthly Charges **$24.96**  
- Monthly activity grid: Monthly Charge **$2.08** every month

### D2 — 3.5% premium expense charge (all ISWL)

| Question | Decision |
|----------|----------|
| Do ISWL contracts have a premium expense charge? | **Yes — 3.5%** |
| Scope | **All ISWL contracts** (documented); not single-premium plan per #23 |
| Frequency | Applied as **% of premium when premium is received** (not a separate annual lump) |

**Statement proof:**  
Premiums Received **$148.70** · Premium Charge **$5.21** → \(5.21 / 148.70 ≈ **3.503%** ≈ **3.5%**)

**Related:** Closes the open business question on Issue **#23** (3.5% gross premium expense for ISWL plan setup).

### D3 — Still open (Eric question)

> Do the U6 Curr COI Rate tables provide the expense charges you are looking for?

**Preliminary / research answer (not a client decision):** **No.**

| Segment | Product Book meaning | Expense? |
|---------|----------------------|----------|
| **U6** | Current COI Rates Segment → QuikCoi | **No — COI, not expense** |
| **UF** | Per Policy Monthly Expense | Yes — aligns with D1 ($25 → monthly) |
| **U2** | Premium Collection Expenses | Candidate for D2 3.5% premium load |
| **U1 / U3** | Premium fees / per-$1K expense | Not found for ISWL in prior #43 scan |

**Next step:** Reply to Eric that U6 is Current COI; expenses are contract constants (3.5% + $25/mo amort.) and/or UF/U2 setup — then confirm with Sujitha how QLAdmin plan expense fields should be programmed.

---

## Status change

| Before | After |
|--------|--------|
| Investigation Complete / Awaiting Client | **Client decisions received (D1–D2)** · Ready for Planning / Development handoff to Sujitha |
| No Go for expense mapping | **Go for plan expense setup** once D3 reply confirmed and single-premium exclusion frozen |

---

## Related issues

| ID | Update |
|----|--------|
| **#23** | 3.5% confirmed for all ISWL (non–single premium); see `Issue_23/` |
| **#21C** | Still maps policy-level fee → `quikridr.MANNLFEE`; plan UF monthly expense is separate setup work |
| **#22** | Vanish option — **unchanged** (not part of this email) |
