# Issue #38 — Validation Report (G5)

**Issue:** Dividend Accumulations  
**Date:** 2026-07-04  
**Engine:** v57.44  
**Status:** **PASS**

---

## Validators run

| Validator | Result | Notes |
|-----------|--------|-------|
| `validate_issue38_mdeposit.py` | **PASS** | 59 policies MDEPOSIT > 0; trace policies match PPBENTYP |
| `validate_issue21d_mdepint.py` | **PASS** | ISWL 4.50; non-ISWL 4.00 unchanged |

---

## Trace confirmation

| Policy | MDEPOSIT | MINTYTD | MINTDATE | MDEPINT |
|--------|----------|---------|----------|---------|
| 010378830C | 9,888.08 | 0.00 | 20251231 | 4.00 |
| 010380808C | 9,220.33 | 0.00 | 20251231 | 4.00 |
| 010435671C | 17,237.02 | 0.00 | 20251231 | 4.00 |
| 010713704C | 0.00 | 0.00 | 20260619 | 4.50 |

---

## Row counts

| Table | Rows |
|-------|-----:|
| quikdvdp | 5,083 |
| MDEPOSIT > 0 | 59 |

**Batch log:** `QLA_Migration/Output/_full_batch_test_log.txt` — PACTG 641 cache (63 policies) loaded from `PACTG_Accounting_Extract20260530.csv`.

---

## G5 gate: **PASS**
