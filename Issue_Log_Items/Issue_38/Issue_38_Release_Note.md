# Issue #38 — Release Note (v57.44)

**Version:** v57.44  
**Release date:** 2026-07-04  
**Prior version:** v57.43  
**Primary issue:** **#38 — Dividend Accumulations (`quikdvdp.MDEPOSIT`)**  
**Engine:** `app.py` / `QLA_Migration/app.py`

---

## Summary

Release **v57.44** restores QLAdmin dividend accumulation balances by preserving rulebook-mapped **`PPBENTYP.ACCUM_DIVIDENDS` → `quikdvdp.MDEPOSIT`**. Post-emit enrichment no longer zeroes deposits when the PACTG cache misses. PACTG path resolves dynamically; **MINTYTD** / **MINTDATE** enrich from account **641** only.

---

## Issue #38 — Primary change

| Metric | Value |
|--------|------:|
| quikdvdp rows | 5,083 |
| Policies with MDEPOSIT corrected | **59** |
| PACTG 641 cache policies (MINTDATE) | 63 |
| Policies with 2026 MINTYTD > 0 | 18 |

### Mapping authority

| Field | Rule |
|-------|------|
| MDEPOSIT | `PPBENTYP.ACCUM_DIVIDENDS` (rulebook; preserved on emit) |
| MINTYTD | PACTG account **641** credits in current calendar year |
| MINTDATE | Latest PACTG **641** transaction date |
| MDEPINT | Unchanged (Issue #21D ISWL allowlist preserved) |

### Trace policies validated

| Policy | MDEPOSIT |
|--------|--------:|
| 010378830C | 9,888.08 |
| 010380808C | 9,220.33 |
| 010713704C | 0.00 (ISWL control) |

---

## Engine and core files

| File | Change |
|------|--------|
| `app.py` | v57.44; quikdvdp enrichment + PACTG 641 cache |
| `QLA_Migration/app.py` | Mirror |
| `tools/validators/validate_issue38_mdeposit.py` | New validator |
| `QLA_Migration/_research_issue38_quikdvdp.py` | Read-only research |
| `QLA_Migration/_risk_review_issue38_quikdvdp.py` | Risk simulation |

**Rulebook:** `Sync_Rulebook_quikdvdp.csv` — **unchanged**

---

## Preserved issues

| ID | Status |
|----|--------|
| #25 MPOLICY padding | Preserved |
| #26 MPREM | Preserved |
| #21D ISWL MDEPINT 4.50 | Preserved |
| #37 QuikCvs duration grid | Preserved |
| quikdvdp row count | Unchanged (5,083) |

---

## Validation

```powershell
python tools/validators/validate_issue38_mdeposit.py
python tools/validators/validate_issue21d_mdepint.py
python tools/validators/validate_mpolicy_width.py
python tools/validators/validate_issue26_mprem.py
```

All **PASS** after full batch at v57.44.

**Client UAT pending:** QLAdmin dividend accumulation display for **010378830C** and **010380808C**.

---

## Network batch

Pull latest branch, confirm **v57.44** in `app.py`, run full batch (`Output/` is gitignored — regenerate `quikdvdp.csv` locally).

---

## Documentation

| File | Purpose |
|------|---------|
| `Issue_Log_Items/Issue_38/Issue_38_Resolution_Summary.md` | Closure summary |
| `Issue_Log_Items/Issue_38/Issue_38_Validation_Report.md` | G5 validation |
| `Issue_Log_Items/Issue_38/Issue_38_Regression_Report.md` | G6 regression |
