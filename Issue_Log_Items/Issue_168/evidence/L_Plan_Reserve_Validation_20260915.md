# L-plan reserve validation — 6/30 test region

**Region:** `Q:\CSO\CSO_Test_6_30_2026`  
**QuikValf:** 2026-09-15 10:04 (today’s anniversary / valuation run)  
**Rates on region:** QuikTvs / QuikNps 2026-09-15 07:23 (this morning’s 8/31 Append, including #168 L14 copies)  
**LifePRO compare:** `docs/Valuation/VALXLIFE.TXT` (6/30)  
**Script:** `Issue_Log_Items/Issue_168/tools/validate_l_plans_q_region.py`

## L14 (#168) — PASS

| Class | Rows | Match ≤ $1 | QLA reserve | LifePRO reserve |
|---|---:|---:|---:|---:|
| NT | 37 | 36 | 244,196.70 | 243,784.05 |
| PQ | 65 | 65 | 894,649.90 | 894,645.40 |
| PR | 5 | 5 | 42,789.70 | 42,789.44 |
| ST | 1 | 1 | 3,121.45 | 3,121.45 |

Named traces: `9011227604C` PQ = 9,895.80; `9011258186C` PQ = 9,543.45; `9011226092C` NT = 9,895.80. All exact.

The one NT miss is `9011269177C` (age 1, duration 84, prefix C1A1): QLA 807.90 vs LifePRO 396.31. That is not a missing class key.

## Rate tables present on the region

Every in-force L **base** plan has QuikTvs and/or QuikNps rows matching its policy classes, except:

- `9L05WP` (1 rider) and `9L16PF` (2 riders) — no TV/NP rows at all
- Term family (`5L0110`, `5L0510`, `5L075Y`) — TV grids are all zero **by design**; reserve rides on QuikNps (present)

`1L14SC` now has NT/PQ/PR/ST on both QuikTvs and QuikNps (332 / 328 each).

## Remaining L-book zeros (QLA $0, LifePRO > 0)

131 rows / $196,609 — **none are L14**:

| Plan | Class | Rows | LifePRO $ |
|---|---|---:|---:|
| 5L0110 (L01) | PR/ST | 124 | 169,718 |
| 5L0510 (L05) | PR/ST | 5 | 20,836 |
| 5L01MA | ST | 1 | 1,354 |
| 1L10SR | BL | 1 | 4,700 |

## Other known (not missing rates)

- **1L1095** valued on every row but ~$131k / 6% low vs LifePRO (rate/factor, previously logged)
- **1L17SP** QLA has $47,825; LifePRO VALX `RV_MEAN_RV` is 0 on those 20 rows
- **5L075Y** matches LifePRO to the dollar
- **10L171 / 10L172** match
