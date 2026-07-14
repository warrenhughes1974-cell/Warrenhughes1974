# Issue #54 — Planning Addendum (QuikBenh target locked)

**Date:** 2026-07-11  
**Supersedes:** Planning Report §3 target gap / Dependency Gate B1  
**Status:** Target confirmed — ready for Risk (G3)

---

## Corrected target architecture

| QLAdmin UI | Table | Grain |
|------------|-------|-------|
| Loan History **transaction grid** | **`quikbenh`** | Multi-row per `MPOLICY` (`MBENTYP`+`MDATE`+`MBEN`) |
| Loan History **footer** + Coverage loan summary | **`quikloan`** | One row per `MPOLICY` (#32/#44) |

Help: §5.1.2.7 Loan History · §7.47 QuikBenh · §6.5 Benefit Type Codes · §7.150 QuikLoan

---

## Proposed LifePRO → QuikBenh mapping (Development blueprint)

| LifePRO | → QuikBenh | Notes |
|---------|------------|-------|
| `POLICY_NUMBER` | `MPOLICY` | Crosswalk + #25 pad |
| PACTG `0411` | `MBENTYP=10` | Policy loans granted |
| PACTG `0412` | `MBENTYP=11` | Interest on policy loans |
| PACTG `0413` | `MBENTYP=12` | Payments on policy loans |
| PACTG (div loan pay — TBD) | `MBENTYP=20` | Seen on 14560K; confirm source |
| `EFFECTIVE_DATE` | `MDATE` | YYYYMMDD |
| `TRANS_AMOUNT` | `MBEN` | N(10.2); sign rules TBD |
| — | Balance | **Do not emit** — UI calculates |

**Out of Benh loan emit:** PACTG `0451` (offset), reversals (default), non-04xx.

**QuikLoan:** unchanged latest PLOAN snapshot for footer.

---

## Development outline (do not implement until G3 + approval)

1. New converter path: LifePRO PACTG 04xx → `quikbenh` loan-type rows (isolated module).  
2. Merge/append with any existing `quikbenh.csv` (dividends / #34 type 8) — **never replace whole file blindly**.  
3. Preserve #32/#44 QuikLoan.  
4. Keep 04xx out of QUIKCLMS.  
5. Validator: 14560K-style type map; sample LifePRO policies; no #25/#26 regression.  
6. Version bump both `app.py` copies when wired.

---

## Open questions for Risk / SME

1. PACTG-only vs also synthesize from PLOAN deltas?  
2. MBENTYP **20** source?  
3. APL (“Loans Granted” monthly) — PACTG 0411 or premium/APL path?  
4. Fleet overlap: policies with Benh dividends already vs new loan rows.
