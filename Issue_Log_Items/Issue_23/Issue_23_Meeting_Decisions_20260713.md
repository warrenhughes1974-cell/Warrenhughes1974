# Issue #23 — ISWL Premium Expense Charge (3.5%)

**Issue:** #23 — Expense charge (ISWL plans)  
**Date opened (client log):** 2026-06-23  
**Updated:** 2026-07-13 (meeting / Eric email)  
**Owner:** Warren · **Assigned:** Sujitha  
**Priority:** No-Go → **Go for plan setup** (decisions locked; programming pending)  
**Companion:** #43 (policy fee / monthly expense discovery)

---

## Business requirement

For all ISWL policies (**excluding the single premium plan**), implement a **3.5% gross premium expense charge** when setting up those plans in QLAdmin.

---

## Meeting decisions (2026-07-13)

**Source:** Eric Scow + annual statement Censi I (`9010817956`)

| Item | Decision |
|------|----------|
| 3.5% premium expense | **Confirmed** — all ISWL contracts have 3.5% documented |
| How it appears on statement | Premium Charge = 3.5% of premiums received (e.g. $5.21 on $148.70) |
| Frequency | **Percent of premium when premium is received** (not a one-time annual charge) |
| Single premium plan | **Excluded** (original #23 scope) |

**Evidence:** `Annual_Statement_Censi_I_9010817956.pdf` (copy in this folder and under `Issue_43/evidence/`)

**Full write-up:** `../Issue_43/Issue_43_Meeting_Decisions_20260713.md` (D2)

---

## Related decision (#43) — $25 monthly expense

Eric also confirmed the **$25 policy fee is taken monthly** (statement: **$2.08/month** × 12 ≈ $25/year). That answers Sujitha’s #43 question on Policy fee vs Monthly expense per policy.

---

## Still open

Eric asked whether **U6 Curr COI** tables provide these expense charges.  
**Research answer:** **No** — U6 is **Current COI**, not expense. Expenses = contract 3.5% + $25 annual fee monthly amort. (UF / U2 candidates).

---

## Next steps

1. Reply to Eric on U6 (COI ≠ expense).  
2. Sujitha programs ISWL plan expense setup: **3.5% premium** + **monthly per-policy ~$2.08** (from $25).  
3. Planning/Development: freeze mapping to QLAdmin expense fields; exclude single premium.  
4. Do **not** change conversion `app.py` until plan-setup approach is agreed with New Era / Sujitha.
