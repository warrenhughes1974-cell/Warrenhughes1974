# Reinsurance Phase 1 — MSTATUS / MUWCLASS Code Verification

**Date:** 2026-07-19  
**Trigger:** Comparison vs sample QLAdmin DBFs in `docs/` showed our `quikrmst` emit contains `MSTATUS` values `50`/`57` and `MUWCLASS` values `T`/`R` that never appear in the 16,618-row client sample `QUIKRMST.DBF`.  
**Verification source:** `docs/QLAdmin_Help.pdf`

---

## MSTATUS 50 and 57 — VERIFIED VALID, no action

QLAdmin Help §6.6 "Life Policy Status Codes" (PDF page 652) lists both:

| Code | Meaning | Category |
|------|---------|----------|
| 50 | Pending Death | Inactive (>= 50) |
| 57 | Matured | Inactive (>= 50) |

Full emit domain check — every `MSTATUS` we emit (22, 44, 45, 50, 53, 55, 57) is on the official list (22 Premium Paying, 44 Extended Term, 45 Reduced Paid Up, 50 Pending Death, 53 Deceased, 55 Surrender, 57 Matured). The values were absent from the sample DBF only because that block (company G) had no policies in those statuses.

**Disposition:** No crosswalk change needed. `MSTATUS` is sourced from converted `QUIKRIDR.MPHSTAT`, which already follows QLAdmin status codes.

## MUWCLASS T and R — LifePRO pass-throughs, existing Issue #59 decision applies

- `quikrmst.MUWCLASS` inherits from converted `quikridr.MUWCLASS` (`qla_core/reinsurance_lookups.py`), falling back to `PREIN.UNDERWRITING_CLASS`.
- Per the Issue #59 business decision recorded in `qla_core/rate_dbf_schema.py` (`RIDER_UWCLASS_MAP`), LifePRO UW letters map `0→00, N→NS, S→SM, P→PR, B→ST, Q→NS`; **unknown codes (explicitly including `R` and `T`) pass through unchanged for business review**. Bare Master_Value_Translation rows (`N→T`, `T→56`, etc.) must NOT be applied.
- Affected reinsurance rows: `T` = 21 rows, `R` = 39 rows (of 733).

**Disposition:** No crosswalk entry added — adding one would override the standing Issue #59 pass-through decision without business confirmation. Client must confirm the QLAdmin risk-class codes for LifePRO classes `T` and `R`; once confirmed, the mapping belongs in `RIDER_UWCLASS_MAP` (a Development-stage change) and the reinsurance emit will inherit it automatically via quikridr.

## Related schema note (help vs client sample drift)

QLAdmin Help §7.205 (QuikRmst, PDF page 905) documents `MTREATY` as C(10) and `MUWCLASS` as C(3), while the client sample `QUIKRMST.DBF` uses `MTREATY` C(20) and `MUWCLASS` C(2). Our emit truncates to C(20)/C(2) (matches the client sample; longest live treaty code is 8 chars, so no truncation occurs either way). See Phase 2 scope notes for the same drift in `QUIKRBLL`.
