# Issue #27 — Client UAT Package

**Issue:** SL Phase of Insurance (Duplicate Face Amount)  
**Date:** 2026-06-28  
**Engine version:** v57.39  
**Validation status:** ✅ PASS

---

## 1. What was fixed

LifePRO benefit type **SL (Substandard Life)** was incorrectly converted as a separate coverage row in QLAdmin, causing **duplicate face amounts** on 46 policies.

**Fix:** SL rows are no longer emitted to Coverage (`quikridr`). Substandard Life is handled by QLAdmin's rating structure — not as an additional death benefit.

---

## 2. Client-visible change

### Before (v57.38) — Policy `010448806C`

| Coverage row | Plan | Face amount |
|--------------|------|------------:|
| Base | 170858 | 5,778.00 |
| PUA | 1708PA | 5,752.96 |
| **SL (duplicate)** | **170858** | **5,778.00** ← defect |

### After (v57.39) — Policy `010448806C`

| Coverage row | Plan | Face amount |
|--------------|------|------------:|
| Base | 170858 | 5,778.00 |
| PUA | 1708PA | 5,752.96 |

**Mode premium:** 62.40 (unchanged)

---

## 3. UAT test script

### Test 1 — Duplicate face eliminated (46 policies)

1. Open QLAdmin Coverage tab for any policy in `Issue_27_SL_Suppression_Audit.csv`.
2. Confirm **no SL coverage row** appears.
3. Confirm base face amount appears **once** per plan (not duplicated).

**Pass criteria:** No duplicate amount insured for same MPLAN.

### Test 2 — Trace policy `010448806C`

| Check | Expected |
|-------|----------|
| Coverage rows | 2 (Base + PUA) |
| Duplicate 170858 @ 5,778 | Absent |
| Mode premium | 62.40 |

### Test 3 — Premium-bearing policy `010799083C`

| Check | Expected |
|-------|----------|
| Mode premium (policy master) | 175.73 |
| No duplicate 25,000 face row | Confirmed |

### Test 4 — PUA policy with SL `010497264C`

| Check | Expected |
|-------|----------|
| Two SL rows suppressed (audit) | 2 audit entries |
| Coverage shows base + riders only | No SL phases |

---

## 4. Population scope

| Metric | Count |
|--------|------:|
| Policies affected | 67 |
| Duplicate face policies fixed | 46 |
| Coverage rows removed | 68 |

**Fleet impact:** 1.32% of policies — surgical fix.

---

## 5. What did NOT change

- Policy modal premium (`MMODEPREM`)
- Product setup / rate tables
- Memos (`quikmemo`)
- Beneficiary / client records
- Dividend / loan / accounting tables

---

## 6. Supporting artifacts for UAT

| Artifact | Purpose |
|----------|---------|
| `Issue_27_SL_Suppression_Audit.csv` | Full list of suppressed SL rows |
| `Issue_27_SL_Impact_Population.csv` | Planning population detail |
| `Issue_27_Final_Validation_Report.md` | Validation evidence |

---

## 7. Sign-off checklist

| # | Item | Client sign-off |
|---|------|:---------------:|
| 1 | No duplicate face on `010448806C` | ☐ |
| 2 | Mode premium unchanged on sample policies | ☐ |
| 3 | SL policies show correct base + PUA only | ☐ |
| 4 | Acceptable that SL table rating not shown as coverage row | ☐ |

---

**UAT package status:** ✅ READY FOR CLIENT REVIEW
