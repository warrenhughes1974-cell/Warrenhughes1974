# Issue 21G — Resolution Summary

**Issue:** #21G — Total Premium / Cost Basis  
**Date:** 2026-07-11  
**Status:** **CLOSED**  
**Authority:** New Era / QLAdmin (product capability) — confirmed not required at conversion  

---

**Resolution:** QLAdmin has no programmed cost basis / taxable-gain field for life policies and does not compute or withhold taxable gains on life surrenders; conversion will not load LifePRO Premiums Paid or Tax Basis into a QLAdmin master field — use premium history and/or the staged report for any manual estimate outside QL.

---

## Client question (closed)

> Where should Total Premium Paid and Cost/Tax Basis appear in QLAdmin? Identify target screen and field or confirm not required at conversion.

**Answer:** **Not required at conversion.** QLAdmin does not accommodate taxable gains on life surrenders or tax withholding on those surrenders. Any such activity is outside QL (accounting / check processing). Premium history in QL can support a rough manual estimate, but it is not always complete — especially on policies converted from another system.

## Source note (unchanged)

LifePRO values (e.g. 010448806C Premiums Paid $6,552.00 / Tax Basis $2,483.97) remain available from Benefit Detail / `PPBENTYP` BA `PREMIUMS_PAID` + `TAX_BASIS`. Informational staging to `Reports/issue21g_premium_basis_totals.csv` may continue for reference; no Output load mapping.

## No further Development

No rulebook or engine change required for a QLAdmin tax-basis/premiums-paid target field.
