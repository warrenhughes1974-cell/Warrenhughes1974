# 145B UAT files

| Path | What |
|---|---|
| `CONTROL/QuikIsrr.csv` | Current Output QuikIsrr (3,657 rows). SHA matches `QLA_Migration/Output/QuikIsrr.csv`. |
| `TEST/QuikIsrr.csv` | Same file minus 10 gold 0561 rows (3,647). |
| `comparison/issue145b_removed_quikisrr_rows.csv` | The 10 removed rows. |
| `comparison/issue145b_control_vs_test.json` | Hashes, counts, gold sums. |

Load Control from current Output. For Test, swap **only** QuikIsrr. Do not overwrite Output with TEST.
