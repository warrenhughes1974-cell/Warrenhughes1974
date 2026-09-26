# Issue #158 — Discovery Notes

**Issue:** #158 — PR rates attributed to the wrong QLAdmin plan (segment→plan resolution ignores PCOVRSGT SEQ)
**Framework stage:** Discovery (Stage 0)
**Generated:** 2026-08-29
**Origin:** PR-segment rate validation against 12 LifePRO screenshots in `docs/Rate_Validation/`

---

## How this was found

Warren supplied 12 LifePRO Attained Age premium-rate screenshots and asked whether the
converted rates are correct today, and whether the pending PSUBSSEG source file would make
them correct. Analysis scripts: `docs/Rate_Validation/_compare_pr_screenshots.py` and
`_pr_owner_and_emit_check.py`.

## What Discovery established

1. **The source data is right.** All 12 screenshots reproduce `PAAGERAT_AttainedAge_Rates_Extract_20260731.csv`
   cell-for-cell at the Issue #138 offset (`SEQ = attained age + 1`). No extract defect.

2. **The rates are landing on the wrong QLAdmin plans.** Not one of the 12 segments emits to the
   plan its own coverage crosswalks to. Examples: `961 ME65` rates appear on `261PUA` instead of
   `2961ME`; `L15` rates appear on `1L16GD` instead of `1L15GD`; `686S 30MRG` rates appear on
   `7687J3` instead of `7686S3`.

3. **PSUBSSEG does not fix it.** PSUBSSEG substitutes *which segment* a coverage reads by issue
   date. It does not change segment→plan attribution, so it cannot correct this class of defect.
   Different root cause from the PSUBSSEG missing-segment work.

4. **Root cause is in `SegmentResolver`.** It accepts any `PCOVRSGT` row with `SEGT_FLAG=Y`,
   ignores `SEQ`, and keeps a single parent per segment (last row wins). `SEQ` is the rate-type
   slot, so a rider or PUA coverage that references a segment at SEQ 7/10/26 can capture that
   segment's premium grid away from the coverage that owns it at SEQ 1.

## Corrections to earlier readings in this thread

| Earlier claim | Correct position |
|---|---|
| Band values collapsing to `00` is a defect | Intentional — Issue #71 fleet standard; `band_collapse_priority` is wired and band 1 wins |
| `686S 30MRG` rates "land nowhere" | They land on `7687J3` and are then overwritten by `687J 30MRG` |
| 78/78 screenshot cells matched source | Inflated — zero-value gold cells were counted against absent source rows |

## Open question taken into Intake

Is `PCOVRSGT.SEQ` 1/2/12/13 authoritative for PR/CV/RV/NP segment ownership? Supporting
evidence at Discovery: New Era's `PSSUBSSEG_SegtFlag_Query.sql` uses that mapping, and the
PSUBSSEG reconciliation script already encodes it.

## Related

- `Issue_Log_Items/PSUBSSEG_Rate_Substitution/` — separate issue, missing 1995-basis RV/NP segments
- Issue #138 (PR SEQ offset), #140 (attained-age slot axis), #107 (held — L10 family)
