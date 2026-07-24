# Issue #106 — Validation Report

**Issue:** #106 — RV Rates Off by One Duration (QuikTvs) — Defect #1  
**Framework stage:** Validation (G5)  
**Date:** 2026-07-24  
**Version:** v58.31  
**Result:** **PASS**

---

## Validator

```text
python Issue_Log_Items/Issue_106/validate_issue106_quiktvs_duration.py
→ OVERALL PASS
```

Against full `QLA_Migration/Output/rates/QuikTvs.csv`.

| Plan | Slice | Checks |
|------|-------|--------|
| 170858 | M/17 | Dur1=0, Dur2=8.76, Dur83=1000 |
| 17085M | M/17 | same (inherited) |
| 170588 | M/17 | same (inherited) |
| 1659C2 | M/17 SM | Dur1=1, Dur83=978 |
| 221END | M/17 | Dur1=0 |
| 1960OL | M/17 | Dur1=4 |

Dur0 no longer holds the former Dur1 factors for these proofs.

---

## UAT publish

`Output/Test_Validation/rates/QuikTvs.csv` published via:

```text
python tools/publish_test_validation.py --issue Issue_106 --rates QuikTvs
```

---

## Defect #2 (not validated here)

`1L1095` / L10 LP9595 source mismatch — **out of scope** for this Validation. Still pulls L10 LP95.
