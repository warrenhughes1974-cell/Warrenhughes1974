# New Era response — missing substituted rate segments (documented 2026-09-01)

**Source:** `docs/New_Segments/New_Email.docx` (Eric Scow fwd, 2026-09-01)
**From:** Geoffrey Williams (New Era) → Eric Scow (CSO), 2026-08-31 4:08 PM
**Re:** Our 2026-08-29 data request (13 substituted segment IDs + EFFDATE approach)

## What New Era said

1. **Rates found for ALL 13 requested coverage IDs.** They were missing because
   the original PDAGE/PAAGE/PAAGERAT extract queries selected only coverage IDs
   matching `PPBEN.PLAN_CODE` for company 03 — substitution-table segment IDs
   were invisible to that filter. Queries are updated and verified; the rows
   "will be on the extracts generated tonight" (night of 2026-08-31).
2. **Proactive follow-up:** Geoffrey is scanning the substitution tables for any
   *other* coverage IDs that should be included and will report back.
3. **EFFDATE approach endorsed:** "QLAdmin's decision to load both rate sets
   (keying by effective date) should be fine" per his reading of LifePRO code.
4. **PAAGE vs PDAGE selection mechanism:** LifePRO parses `PSEGT.SEGT_DATA`
   (hex) for a rate-type character — `I` (Issue) / `A` (Attained) → PAAGE;
   `O` (Duration) / `D` (Age/Duration) → PDAGE. His SQL:
   `select substring(convert(varchar(256), SEGT_DATA), 20, 1) as RateType from PSEGT where SEGMENT_ID = '...'`.
   He notes 28 different code paths check this and copybook positions are
   inconsistent, but byte 20 worked for his `L01 10Y LT` example (→ `A`, PAAGE).

## Our verification (2026-09-01, read-only)

Applied the byte-20 parse to our `PSEGT_Segment_Extract_20260630.csv`:

- **100% consistent with observed rate placement for tranche-1 segments:**
  `L10 LP9595` RV/NP → `D` (PDAGE) ✓; `L10SR 95` RV/NP → `D` ✓; `L10 LP95SR`
  RV/NP → `D`, PR → `I` (PAAGE) ✓; `L17` CV/NP/RV → `D`, PR → `I` ✓;
  `667 ART` PR/NP/RV → `A` (PAAGE) ✓ — matching where each segment's rates
  actually live in our extracts.
- The rule holds for rate-bearing SEGT_TYPEs (PR/CV/RV/NP/NN/PN/RD); non-rate
  slots (LN, NB) show other characters, as Geoffrey cautioned.
- **All 13 tranche-2 segment IDs are also absent from our PSEGT extract** —
  same PPBEN-filtered root cause. Geoffrey listed PDAGE/PAAGE/PAAGERAT as the
  updated queries but did **not** mention PSEGT.

## Conclusions

1. **Tranche 2 unblocks imminently.** Watch for new dated extracts
   (`PDAGE/PAAGE/PAAGERAT_*_2026090x.csv`). Once dropped into
   `QLA_Migration/Source/`, the dated-merge infrastructure picks them up
   automatically (newest filename wins). First action on receipt: rerun
   `_reconcile_psubsseg_vs_output.py` — `source_missing_segments` should go to
   zero (or shrink to a named residue).
2. **Root cause generalizes.** Any extract filtered on PPBEN plan codes has the
   substitution blind spot. Ask Eric/Geoffrey to include the substitution
   segment IDs in the **PSEGT** extract too (needed for PAAGE-vs-PDAGE
   classification and duration semantics of the new segments). Low priority:
   PCOVRSGT (keyed by coverage; likely unaffected).
3. **EFFDATE risk retired.** Three independent confirmations now: Warren
   (2026-08-31), QLAdmin Help key structure, and New Era's code reading.
   Risk R1 in the Risk Review drops from High/Low to Low/Low.
4. **New deterministic tool for the loader:** the PSEGT rate-type byte gives
   tranche 2 a data-driven way to select the source family per segment instead
   of assuming PDAGE — verified against every tranche-1 segment. Design note
   added for Development.
5. **Sequencing decision for Warren:** tranche-1 Development approval is still
   pending. With tranche-2 data arriving ~today, one combined Development +
   Validation + single batch covering both tranches is now feasible and saves a
   full validation/regression cycle. Alternative: proceed tranche 1 now,
   tranche 2 as follow-on. Either is safe; combined is less total work if the
   extracts land clean.

## Follow-ups

- [ ] Receive tonight's extracts; stage dated files into `QLA_Migration/Source/`
- [ ] Rerun reconciliation; confirm the 13 segments now have rates (and check
      `667 ART 95` NP specifically)
- [ ] Reply to Eric: request PSEGT rows for the substitution segment IDs
- [ ] Await Geoffrey's scan for additional affected coverage IDs
- [ ] Warren: choose combined vs tranche-1-first Development
