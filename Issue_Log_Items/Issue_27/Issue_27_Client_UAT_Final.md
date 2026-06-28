# Issue #27 — Client UAT Final

**Issue:** SL Phase of Insurance — Duplicate Face Amount Fix  
**Version:** v57.39  
**Date:** 2026-06-28  
**Contact:** Eric  
**Status:** Ready for Client UAT

---

## 1. What to verify

LifePRO **SL (Substandard Life)** rows no longer appear as separate coverage in QLAdmin. Duplicate face amounts on **46 policies** should be resolved. Policy premiums and values are unchanged.

---

## 2. Primary test — Policy `010448806C`

This is the client-reported example policy.

### Expected Coverage tab (after fix)

| Row | Type | Plan | Face amount |
|-----|------|------|------------:|
| 1 | Base Coverage | 170858 | 5,778.00 |
| 2 | Paid-Up Additions | 1708PA | 5,752.96 |

### Must NOT appear

| Row | Plan | Face | Why wrong |
|-----|------|-----:|-----------|
| ~~SL duplicate~~ | ~~170858~~ | ~~5,778.00~~ | Was duplicate death benefit |

### Policy master checks

| Field | Expected |
|-------|----------|
| Mode Premium | **62.40** (unchanged) |
| Policy status | Unchanged |

**Pass:** 2 coverage rows only; no duplicate 170858 @ 5,778; premium 62.40.

---

## 3. Additional validation sample (10 policies)

Random sample from SL population (seed=27). Verify each in QLAdmin Coverage tab:

| Policy | Expected quikridr rows | Key check |
|--------|----------------------:|-----------|
| 010397318C | 2 | No duplicate base face |
| 010449050C | 2 | Base + PUA only |
| 010464265C | 2 | No SL phase |
| 010495122C | 2 | Premium unchanged |
| 010771662C | 1 | Single base row |
| 010773109C | 2 | No duplicate face |
| 010782078C | 1 | Zero-face SL was rating-only |
| 011110271C | 1 | No SL coverage row |
| 011201237C | 1 | MMODEPREM = 83.17 |
| 011201621C | 1 | MMODEPREM = 684.59 |

Full audit list: `Issue_27_SL_Suppression_Audit.csv` (68 suppressed rows / 67 policies).

---

## 4. Premium-bearing policies (optional spot check)

If time permits, verify mode premium on high-premium SL policies:

| Policy | Expected MMODEPREM |
|--------|-----------------:|
| 010799083C | 175.73 |
| 010886099C | 1,536.23 |
| 010921853C | 384.61 |

---

## 5. What should NOT change

- Product setup / rate tables
- Policy memos
- Beneficiary designations
- Client/owner records
- Dividend, loan, accounting balances
- Total policy values (except removal of phantom duplicate coverage)

---

## 6. Sign-off form

| # | Statement | Agree? | Initials | Date |
|---|-----------|:------:|----------|------|
| 1 | Duplicate face removed on `010448806C` | ☐ | | |
| 2 | Base coverage face amount correct | ☐ | | |
| 3 | PUA coverage correct where applicable | ☐ | | |
| 4 | Mode premium unchanged on tested policies | ☐ | | |
| 5 | Acceptable that SL is not shown as coverage row | ☐ | | |
| 6 | Issue #27 ready for production deployment | ☐ | | |

**Client approver:** _________________________ **Date:** __________

---

## 7. Supporting documents

| Document | Purpose |
|----------|---------|
| `Issue_27_Final_Validation_Report.md` | Technical validation evidence |
| `Issue_27_SL_Suppression_Audit.csv` | Full suppressed row list |
| `Issue_27_Release_Note.md` | Release summary |

---

**UAT package status:** ✅ FINAL — ready for client review
