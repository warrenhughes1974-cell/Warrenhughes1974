# Issue #27 — Client Questions

**Issue:** SL Phase of Insurance  
**Date:** 2026-06-28  
**Contact:** Eric  
**Purpose:** Minimum questions required before Development Authorization

---

## Context for client

Research confirmed:

- LifePRO `SL` rows are **Substandard Life / table rating**, not separate death benefits.
- The converter creates **duplicate coverage rows** in QLAdmin (46 policies).
- **`quikmstr.MMODEPREM` already holds total policy premium** from LifePRO for most policies.
- **No conversion mapping exists** for `PPBENTYP.SL_TABLE_CODE`.
- QLAdmin schema has **unused** candidate fields (`quikridr.MSPCODE`, `quikmstr.MISSCLASS`) but **we cannot assume** they display table rating without QLAdmin SME confirmation.

---

## Required questions

### Q1 — Substandard Life semantics (confirm)

**LifePRO benefit type `SL` represents Substandard Life (table rating), not an additional death benefit. Correct?**

- [ ] Yes — SL is rating metadata only  
- [ ] No — explain: _______________

---

### Q2 — Duplicate coverage fix (recommended)

**We recommend removing SL from converted coverage rows (`quikridr`) so QLAdmin shows one base face amount per plan, not a duplicate SL phase. Approve?**

- [ ] Yes — suppress SL coverage rows  
- [ ] No — explain desired display: _______________

**Example:** Policy `010448806C` would show **2** coverage rows (Base + PUA), not **3**.

---

### Q3 — Table rating destination (BLOCKING for table-rating mapping)

**Where should LifePRO `SL_TABLE_CODE` (e.g. Table 32 on `010448806C`) appear in QLAdmin?**

| Option | Description |
|--------|-------------|
| A | `quikridr.MSPCODE` (4-char, currently unused) |
| B | `quikridr.MUWCLASS` (2-char — **currently used for different LifePRO field**) |
| C | `quikmstr.MISSCLASS` (2-char, currently unused) |
| D | Underwriting tab / separate table (not in current conversion) |
| E | Not displayed — suppress SL row only |
| F | Other — specify: _______________ |

**Client answer:** ___

**QLAdmin SME consulted:** [ ] Yes  [ ] No  **Name:** _______________

---

### Q4 — Premium-bearing SL rows (28 policies)

Research shows SL row premium is usually the **substandard extra** added to base premium; **`PPOLC.MODE_PREMIUM` total is already on the policy master**.

**If SL coverage rows are suppressed, how should substandard extra premium be handled in QLAdmin?**

- [ ] **No action** — `MMODEPREM` total is sufficient; per-phase SL premium display not needed  
- [ ] **Add SL premium to base phase `MPREM`** for display  
- [ ] **Memo / audit only** — document table code and extra premium  
- [ ] Other: _______________

---

### Q5 — Visibility preference

**Should Substandard Life remain visible to operators after conversion?**

- [ ] No — underwriting metadata only; no SL row or memo required  
- [ ] Yes — via memo on policy (`quikmemo`)  
- [ ] Yes — via mapped table rating field (Q3)  
- [ ] Yes — other: _______________

---

## Optional review (non-blocking)

**21 SL rows** do not exactly duplicate base face amount (see `Issue_27_SL_Impact_Population.csv`). Please confirm none represent legitimate separate coverage.

---

## Recommended default (if client defers)

If client approves Q2 only:

- **Proceed with SL suppression** to resolve duplicate face No-Go.
- **Defer Q3–Q5** to a follow-on enhancement.
- Table rating remains in LifePRO source / audit CSV only until Q3 answered.

---

**Document status:** ✅ READY FOR CLIENT — Eric
