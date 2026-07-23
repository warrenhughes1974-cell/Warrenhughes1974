# Issue #96 — Validation Report

**Issue:** CSO valuation cannot use SAL MULTPL / L17 RV rates (PVO + QuikPl* wiring)  
**Stage:** Validation (G5)  
**Date:** 2026-07-22  
**App version:** v58.26  
**Result:** **PASS**

---

## Checks run

| Check | Result |
|-------|--------|
| `validate_issue96_cso_pvo.py` on full `QLA_Migration/Output/` | **PASS** |
| `validate_l17_rv_inheritance_v5825.py` (QuikTvs Track 1) | **PASS** |
| Annuity A* `PLANVALOPT=N` (Issue A A8e after post-rate R7B) | **PASS** (`A60MIR`, `A96DAR`) |

## Focus plans (Output)

| Plan | PLANVALOPT | GDVARYTV | QuikTvs | QuikPlTv | QuikPlCv |
|------|:----------:|:--------:|--------:|---------:|---------:|
| 1SALOL / 1SALMI / 1SALML | Y | Y | 508 | 2 | 2 |
| 1L17SP + 10L171 / 10L172 / 117JPO / 17MJPO | Y | Y | 38 | 2 | 2 |

`1SALMI` PlTv/PlCv codes match `1SALOL`.

## Test_Validation publish

```text
python tools/publish_test_validation.py quikplan --issue Issue_96 --rates QuikTvs QuikPlTv QuikPlCv
```

## Framework stop

Per locked auto-chain: **stop after Validation**. Next: Regression → Closure (G6/G7) when advanced.
