# Shared Rate Candidate Implementation Report

## Scope Implemented

- Added a manifest-gated shared/inherited rate loader for confirmed QLAdmin destinations only.
- Runtime manifest: `Issue_Log_Items/Issue_Rates_Inheritance_Validation/master_rate_completeness/approved_shared_rate_candidates.csv`.
- Candidate evidence output remains separate: `inherited_shared_rate_candidates.csv`.
- CV remains handled by the existing Issue #40 CV inheritance loader.
- NN/PN remain excluded because no confirmed QLAdmin destination is being loaded.

## Pipeline Results

- Shared manifest entries: 43
- Shared in-scope rows emitted: 137,641
- Shared non-emitted rows requiring mapping/source review: 3,872
- Output key collisions: 0
- Pipeline blockers after shared-rate load: 1

## Manifest Entries By Source/Type

- PAAGERAT NF: 8 entries
- PAAGERAT PR: 14 entries
- Rate_Table DB: 1 entries
- Rate_Table DV: 3 entries
- Rate_Table NF: 10 entries
- Rate_Table NP: 3 entries
- Rate_Table PR: 1 entries
- Rate_Table RV: 3 entries

## Emitted Rows By Plan/Type/Table

- 1658C1 NF -> QuikNff (SHARED_PAAGERAT): 172 rows
- 1658C1 PR -> QuikGps (SHARED_PAAGERAT): 246 rows
- 1658CS PR -> QuikGps (SHARED_PAAGERAT): 246 rows
- 1659C2 PR -> QuikGps (SHARED_PAAGERAT): 246 rows
- 1659CR NF -> QuikNff (SHARED_PAAGERAT): 172 rows
- 1659CR PR -> QuikGps (SHARED_PAAGERAT): 246 rows
- 1659CS NF -> QuikNff (SHARED_PAAGERAT): 172 rows
- 1659CS PR -> QuikGps (SHARED_PAAGERAT): 246 rows
- 1659SR NF -> QuikNff (SHARED_PAAGERAT): 172 rows
- 1659SR PR -> QuikGps (SHARED_PAAGERAT): 246 rows
- 1668SP NF -> QuikNff (SHARED_PAAGERAT): 172 rows
- 1669SR NF -> QuikNff (SHARED_PAAGERAT): 172 rows
- 1669SR PR -> QuikGps (SHARED_PAAGERAT): 246 rows
- 1679CS PR -> QuikGps (SHARED_PAAGERAT): 82 rows
- 1L1095 PR -> QuikGps (SHARED_PAAGERAT): 1,164 rows
- 1L10OD PR -> QuikGps (SHARED_PAAGERAT): 1,164 rows
- 1L10SR PR -> QuikGps (SHARED_PAAGERAT): 1,164 rows
- 1SALMI NF -> QuikNff (SHARED_PAAGERAT): 76 rows
- 1SALML NF -> QuikNff (SHARED_PAAGERAT): 76 rows
- 1SALML PR -> QuikGps (SHARED_PAAGERAT): 135 rows
- 719CTR PR -> QuikGps (SHARED_PAAGERAT): 23 rows
- 960ADB PR -> QuikGps (SHARED_PAAGERAT): 52 rows
- 1658C1 NF -> QuikNff (SHARED_RATE_TABLE): 2,870 rows
- 1659C2 NF -> QuikNff (SHARED_RATE_TABLE): 2,870 rows
- 1659CR NF -> QuikNff (SHARED_RATE_TABLE): 2,870 rows
- 1659CS NF -> QuikNff (SHARED_RATE_TABLE): 2,870 rows
- 1659SR NF -> QuikNff (SHARED_RATE_TABLE): 2,870 rows
- 1669SR NF -> QuikNff (SHARED_RATE_TABLE): 2,870 rows
- 170588 NF -> QuikNff (SHARED_RATE_TABLE): 7,171 rows
- 17085M NF -> QuikNff (SHARED_RATE_TABLE): 7,171 rows
- 1L10SO NF -> QuikNff (SHARED_RATE_TABLE): 27,216 rows
- 1L10SR NF -> QuikNff (SHARED_RATE_TABLE): 27,216 rows
- 261PUA DV -> QuikDvs (SHARED_RATE_TABLE): 3,144 rows
- 261PUA NP -> QuikNps (SHARED_RATE_TABLE): 4,200 rows
- 261PUA RV -> QuikTvs (SHARED_RATE_TABLE): 4,200 rows
- 265PUA DB -> QuikDbs (SHARED_RATE_TABLE): 5,100 rows
- 265PUA DV -> QuikDvs (SHARED_RATE_TABLE): 1,800 rows
- 265PUA NP -> QuikNps (SHARED_RATE_TABLE): 7,140 rows
- 265PUA PR -> QuikGps (SHARED_RATE_TABLE): 117 rows
- 265PUA RV -> QuikTvs (SHARED_RATE_TABLE): 7,140 rows
- 280PUA DV -> QuikDvs (SHARED_RATE_TABLE): 3,716 rows
- 280PUA NP -> QuikNps (SHARED_RATE_TABLE): 4,200 rows
- 280PUA RV -> QuikTvs (SHARED_RATE_TABLE): 4,200 rows

## Non-Emitted Rows

Rows listed in `shared_rate_candidate_non_emitted_rows.csv` were not loaded because they do not fit the currently confirmed QLAdmin segmentation. The main known item is gross premium source band `4`, which maps to `BAND=04`; current validation only permits `00` through `03`.
