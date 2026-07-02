# ISWL QUIKCVS PDAGE Parity Report

**Script:** v1.1  
**V-CVS-05 verdict:** **PARTIAL / NEEDS REVIEW**  
**SME match threshold:** 99.5% on shared keys

## Sources

- Rate_Table: `C:\Users\warren\Documents\GitHub\Warrenhughes1974\plan_analysis\source_data\rates\Rate_Table_Extract_20260427.csv` (column `VALUE`, `UNDERWRITING_CLASS`)
- PDAGE: `C:\Users\warren\Documents\GitHub\Warrenhughes1974\QLA_Migration\Source\PDAGE_AgeDuration_Rates_Extract_20260530.csv` (column `VALUE1`, `UWCLS`)

## Global summary

| Metric | Count |
|--------|------:|
| ISWL keys in Rate_Table CV | 72,271 |
| ISWL keys in PDAGE CV | 12,084 |
| Keys in both | 12,084 |
| Keys only Rate_Table | 60,187 |
| Keys only PDAGE | 0 |
| Matched values (shared keys) | 1,262 |
| Mismatched values (shared keys) | 10,822 |
| Match rate (shared keys) | 10.44% |
| Max delta (mismatches) | 968.0000 |
| ISWL MPLANs with PDAGE rows | 8/8 |

## Per-MPLAN / coverage

| MPLAN | Coverage | RT keys | PDAGE keys | Shared | Match % | Only RT |
|-------|----------|--------:|-----------:|-------:|--------:|--------:|
| 1658C1 | 658 CEN I | 18,124 | 2,112 | 2,112 | 14.39 | 16,012 |
| 1658CS | 658 CEN SD | 9,113 | 1,824 | 1,824 | 8.33 | 7,289 |
| 1659C2 | 659 CEN II | 9,678 | 1,104 | 1,104 | 15.58 | 8,574 |
| 1659CR | 659 CEN SR | 9,678 | 2,064 | 2,064 | 8.33 | 7,614 |
| 1659CS | 659 CEN SD | 9,288 | 1,824 | 1,824 | 8.33 | 7,464 |
| 1659SR | 659 SR GD | 9,700 | 1,500 | 1,500 | 11.47 | 8,200 |
| 1669SR | 669 SR GD | 2,340 | 864 | 864 | 8.33 | 1,476 |
| 1679CS | 679 CEN SD | 4,350 | 792 | 792 | 8.33 | 3,558 |

## Conclusions

- PDAGE ISWL CV is a **strict subset** of Rate_Table keys (12,084 ⊆ 72,271; 0 PDAGE-only keys).
- Shared-key match rate **below SME threshold** — **Rate_Table remains authoritative** for Phase 1 emit.
- **No loader change required** — existing R5 Rate_Table path is validated; PDAGE is not a drop-in scalar substitute on shared keys.
- PDAGE row layout uses `VALUE1` per `(AGE, DURATION)`; systematic value divergence suggests different grid semantics or extract vintage — **SME review required** before any source switch.

Detail CSV: `C:\Users\warren\Documents\GitHub\Warrenhughes1974\Issue_Log_Items\Issue_31\Phase1_QUIKCVS\iswl_quikcvs_parity_by_coverage.csv`
