# Issue 21F — Intake Summary

**Issue:** #21F — Truncated Premium History (conversion premium adjustment)  
**Date:** 2026-07-11  
**Framework stage:** Business decisions locked · Planning complete · awaiting Risk / Dev Auth  
**Owner:** Conversion (Warren) · **Business confirm:** Eric  

---

## 1. Client / business symptom

Premium payment history in QLAdmin is truncated relative to LifePRO lifetime accounting. Converted `quikprmh` reflects the extract floor (~2017 forward); LifePRO screens and premium-paid totals show lifetime amounts back to issue (often 2001/2002+).

**Client annotation:** history may cut off around Jan 2018 (extract floor is ~2017-01-01).

**Approved remedy (not re-extract):** one **Conversion Adjustment** `quikprmh` row per eligible non-ISWL policy so QLAdmin cumulative premiums paid equals LifePRO total, without rewriting existing history rows.

---

## 2. Suspected domain

| Layer | Path / table | Role |
|---|---|---|
| Source totals | `PPBENTYP_BenefitType_Extract_*.csv` | `PREMIUMS_PAID`, `PU_PREMIUMS_PAID`, `SU_PREMIUMS_PAID`, `SL_PREMIUMS_PAID` |
| Converted history | `quikprmh.csv` (from PACTG) | Sum `PREMIUM` per `MPOLICY` |
| Target | `quikprmh` | Insert one adjustment row (`DATEPAID=2017-12-31`) |
| Reports | `QLA_Migration/Reports/` | Validation + negative exceptions |
| Out of scope (phase 1) | ISWL / PPBEN FV deposits | Separate analysis |

**Domain:** Premium history reconciliation — related to but distinct from **21G** (tax basis / QLAdmin total-premium screen field).

---

## 3. In scope / out of scope

### In scope (phase 1)

- Non-ISWL policies where LifePRO four-component total > current `quikprmh` sum
- Single positive conversion adjustment row
- Conversion Adjustment classification
- Validation report + negative-exception report
- Preserve all existing `quikprmh` payment rows

### Out of scope (phase 1)

- ISWL / UL deposit-basis reconciliation
- Full PACTG re-extract to issue date
- Negative adjustment loads
- Changing 21G tax-basis staging or inventing a new QLAdmin master field for totals

---

## 4. Related issues

| Issue | Relationship |
|---|---|
| **21G** | Shares LifePRO premium-paid source; 21G remains informational/staging until target field named |
| **21E** | UL/ISWL fund values — separate; ISWL excluded from 21F phase 1 |
| Prior 21F (v57.63) | “Accept floor” superseded by adjustment approach for totals reconciliation |

---

## 5. Next stage

1. Risk Review (blast radius on `quikprmh`, dual-write root/`QLA_Migration` app, report placement)  
2. Development Authorization  
3. Surgical implementation + issue validator  

**Canonical decisions:** `Issue_21F_Business_Decisions.md`  
**Planning detail:** `Issue_21F_Planning_Report.md`
