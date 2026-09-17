# 667 ART — why the 6/30 test region still does not match

**Compared:** `docs/Valuation/VALXLIFE.TXT` (LifePRO 6/30, dated 9/2) vs `Q:\CSO\CSO_Test_6_30_2026\QuikValf.dbf` (valuation 9/15 10:04).

There is only one LifePRO VALX file in this repo. No second VALX extract was found.

## Why ART is still $0

The #169 net-premium grid is **in repo Output** (`QuikNps` 1,736 rows for `5667AT`) and **not on the test region**.

| Place | `5667AT` QuikNps | mtime |
|---|---|---|
| `QLA_Migration/Output/rates/QuikNps.csv` | 1,736 rows (PR 960 / ST 776) | after #169 |
| `Q:\CSO\CSO_Test_6_30_2026\QuikNps.dbf` | **0 rows** | 9/15 7:23 — L14 load |

That 7:23 file is the L14 ShareFile set (`CSO\L_Rate_Setup`). It did not include the later 667 ART net-premium rows. QuikTvs for `5667AT` is present and **all zeros** (LifePRO’s own RV extract is zero; the reserve rides on net premium). Every valued ART row has `MTABNET=0` and `MRESERVE=0`.

## 667 ART (`5667AT`) vs LifePRO

| | Count | QLAdmin | LifePRO |
|---|---:|---:|---:|
| Valued rows | 96 | $0.00 | $132,229.48 |
| QLAdmin $0 / LifePRO > 0 | 95 | | $132,229.48 |
| Match | 1 | zero-units / $0 both sides | |

Full list: `art_policy_listing_20260916_0806.csv`

## Other ART-family riders on this Valf (not the $132k hole)

| Plan | Rows | QLAdmin | LifePRO |
|---|---:|---:|---:|
| 9595WP | 3 | $55.25 | $0.00 |
| 967ADB | 2 | $43.00 | $0.00 |
| 9SLADB | 5 | $3.60 | $0.00 |

## Next

Load the #169 `QuikNps` (and matching `QuikPlTv` if not already current), reindex, run valuation again. Do not use the pre-#169 L14-only QuikNps.
