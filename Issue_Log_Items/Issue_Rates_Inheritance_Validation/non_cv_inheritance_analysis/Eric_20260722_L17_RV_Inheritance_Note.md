# Eric 2026-07-22 — L17 / SAL RV inheritance (Track 1)

**Engine:** v58.25  
**Scope implemented:** L17 child plans → QuikTvs from LifePRO segment `L17`  
**Held (Track 2):** L01 10Y, L05, L07, 667 ART — Eric confirmed LifePRO shows zero RV; awaiting actuarial

## Client statement

- SAL MULTPL points at SAL OL RVs; factors exist in LifePRO  
- L17 items point at L17 RVs; factors exist in LifePRO  
- L01 10Y / L05 / L07 / 667 ART show zero RV in LifePRO (actuarial discussion)

## Before / after (QuikTvs) — verified after v58.25 emit

| PLAN | Before | After | Notes |
|------|-------:|------:|-------|
| `1SALOL` | 508 | 508 | Direct |
| `1SALMI` | 508 | 508 | Already inherited (no change) |
| `1SALML` | 508 | 508 | Already inherited (no change) |
| `1L17SP` | 38 | 38 | PDAGE miss-fill parent |
| `10L171` | 0 | **38** | Grid match `1L17SP` |
| `10L172` | 0 | **38** | Grid match `1L17SP` |
| `117JPO` | 0 | **38** | Grid match `1L17SP` |
| `17MJPO` | 0 | **38** | Grid match `1L17SP` |
| `5L0110` / `5L0510` / `5L075Y` | 424 / 424 / 318 | same | Track 2 hold |
| `5667AT` | 0 | 0 | Track 2 hold (actuarial) |

**Validator:** `validate_l17_rv_inheritance_v5825.py` → PASS  
**UAT reload:** `QLA_Migration/Output/rates/QuikTvs.csv` (+ `Test_Validation/rates/QuikTvs.csv`)

## Change

Manifest only (`approved_first_pass_scope.csv`): four Yes rows for `10L171`, `10L172`, `117JPO`, `17MJPO` with `Source Segment=L17`, source plan `1L17SP`, type RV → QuikTvs.

No loader code change. No L01/L05/L07/667 ART manifest rows added.
