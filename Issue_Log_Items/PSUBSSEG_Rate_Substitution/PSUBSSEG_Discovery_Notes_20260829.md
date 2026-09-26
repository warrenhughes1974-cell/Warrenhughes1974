# PSUBSSEG Coverage Substitution — Discovery Notes (Stage 0)

**Date:** 2026-08-29
**Source package:** `docs/New_Segments/` (New Era extracts dated 2026-08-21, provided via CSO)
**Status:** Discovery complete. No production code changed. Development requires Intake → Risk chain and explicit approval.

## What the data is

LifePRO's Issue Date Substitution feature (PSUBS + PSUBSSEG, defaults in PCONT):
for policies **issued on or after** the date on a substitution record, LifePRO replaces
the coverage's **segment list** used for rate lookups (PR premium, CV cash value,
RV terminal reserve, NP net premium, TX/TP tax). Policies issued before the substitution
date keep the original segment list. All 3,048 PSUBS records are segment-list
substitutions (SUB_COVERAGE_ID blank, CONTINUATION_FLAG=Y); none replace whole coverages.

Readme also confirms: paid-up statuses (PU/ET/RP) value reserves from the CV
attained-age rates (PAAGE), paid-up rate fixed at 1000.

## Measured impact (evidence in `evidence/`)

From `_reconcile_psubsseg_vs_output.py` (read-only; PSUBSSEG + PCOVRSGT defaults
+ PPBEN 20260630 + crosswalk + current `Output/rates/`):

- 533 coverage IDs in PSUBS; **57 intersect our converted PCOVR universe**.
- 213 (coverage, rate-type, expected-segment) reconciliation rows:
  - 138 `SINGLE_SEGMENT_PRESENT` — single expected segment, source rates held, plan emits rows.
  - 27 `EMIT_MISSING` — source rates exist but the plan emits **nothing** for that table.
  - 25 `SOURCE_MISSING` — expected segment absent from every rate extract we hold.
  - 23 `MULTI_ERA_REVIEW` — in-force spans eras with different expected segments.
- **13 substituted segment IDs have no rates in any extract** (Rate_Table, PAAGE,
  PAAGERAT, PDAGE): `L01 10Y 95`, `L05 10Y 95`, `L07 5Y 95`, `L10 CDT 95`,
  `619 DT 95`, `619DTCH95`, `619DTSP95`, `619CHPU95`, `619SPPU95`, `670 GL858`,
  `670GL858NL`, `991 PWL73`, plus `667 ART 95` (RV present in PDAGE, NP missing).
  755 policy/rate-type slots (363 active) depend on them → data request drafted
  (`Email_Eric_PSUBSSEG_Missing_Rate_Segments_20260829.md`).
- **11 multi-era coverages** (in-force spans different RV/NP segments):
  619 DT, 619 DT SP, 667 ART, 670 GL85-8, 670 GL85-M, 991 PWL, L01 10Y LT,
  L05 10Y LT, L10 CDT, L10 PRE97, L10 SR OLD.

### Value spot-check highlights (emitted vs expected segment values)

| Plan | Finding |
|---|---|
| `5L0110` (L01 10Y LT) | Emitted NP matches pre-95 `L01 10Y` exactly (overlap 1.0); 131 of 220 policies (79 active) need missing `L01 10Y 95`. Same pattern: `5L0510`, `170858`, `17085M`, `5CDT10`, `7619DT`, `719SDT`. |
| `1L10OD` (L10 PRE97) | Emitted matches `L10 LP95` (1.0), but 128 of 143 policies (92 active) are 1995+ issues that PSUBSSEG maps to `L10 LP9595` (overlap only ~0.22–0.27). **Both segments are in PDAGE — fixable with data on hand.** Direct bearing on held Issue #107. |
| `1L10SO` (L10 SR OLD) | Emitted overlaps only 0.37 with `L10 LP95SR` and 0.08–0.12 with `L10SR 95`; 420 policies map to `L10SR 95`. Both segments in extracts — fixable with data on hand. |
| `5667AT` (667 ART) | RV/NP source rates exist (PAAGE/PDAGE) but plan emits **no** QuikTvs/QuikNps rows — 195 policies (95 active). Matches the held "zero RV" L-series/ART track; reserves are not zero, they were never emitted. |
| L17 children (`10L171`, `117JPO`, `10L172`, `17MJPO`) | RV inheritance was shipped, but PSUBSSEG maps **CV and NP** to segment `L17` too, and those tables are `EMIT_MISSING` for the children. |

## QLAdmin EFFDATE semantics (evidence/qladmin_help_effdate_pages.txt)

- Rate File Option keys are `Plan + Gender + UWClass + Band + IssCntry + IssueSt + EffDate`
  (QuikPlTv index, Help 7.183; QuikTvs rows carry `EFFDATE` "effective date of the rate file", 7.217).
- Multiple effective-dated keys per plan are a designed feature (Rate File Options,
  Help pp. 535–543); `01/01/1900` is the default single-set date — matching our current emit.
- The Help states the ≥-selection rule explicitly only for commission rates
  ("[issue date] must be equal to or greater than the Effective Date", p. 581).
- **Confirmed by Warren 2026-08-31:** QLAdmin selects plan-value rate bands the same
  way — latest EFFDATE on or before the policy issue date. Era-banded emit is the
  approved representation; no plan splits needed and no Eric confirmation required.

## Relationship to existing issues

- **Issue #107 (held NO-GO)** — PSUBSSEG answers the LP95 vs LP9595 question:
  `L10 LP95` issued ≥1994 takes RV/NP from `L10 LP9595`. Supports un-holding after Eric confirms.
- **Held L01/L05/L07/667 ART RV** — "zero RV in LifePRO" is explained: post-95
  reserves live on segment IDs missing from our extracts (extract gap, not zero reserves).
- **L17 RV inheritance (shipped)** — independently confirmed by PSUBSSEG; extend to CV/NP.
- **Closed rows #40/#42/#106** — no conflict found, but any implementation touching
  their tables goes through the standard conflict check (Framework rule 13).

## Next steps (pending approvals)

1. Send data request to Eric/New Era (draft in this folder) — 13 missing segment IDs.
   (EFFDATE selection rule no longer needs confirmation — see above.)
2. On approval: Intake → Planning → Dependency Gate → Risk for a substitution-aware
   resolution layer in `qla_core` (PSUBSSEG-driven segment→plan attribution for
   PR/CV/RV/NP; era-banded EFFDATE emit where in-force spans eras).
3. Immediately actionable once approved (no new data needed): `1L10OD` era banding
   (~12,384 added QuikTvs/QuikNps rows), `1L10SO` re-source + era banding (~8,256 rows),
   L17 children CV/NP emit (~3,936 rows), `5667AT` NP emit, QuikGps premium fills
   (~2,850 PAAGERAT source rows). `5667AT` RV: the 95-era segment is genuinely all
   zeros in PDAGE (plausible for ART) — decide emit-as-.00 vs leave absent at Planning.

## Update 2026-09-01 — New Era response received

New Era found rates for **all 13 missing segment IDs** (extract queries were
PPBEN-plan-filtered; substitution segments invisible). Refreshed
PDAGE/PAAGE/PAAGERAT extracts generated night of 2026-08-31 will contain them.
New Era also independently endorsed the EFFDATE dual-band approach and supplied
the PSEGT rate-type parse (byte 20 of SEGT_DATA: I/A→PAAGE, O/D→PDAGE), which we
verified against all tranche-1 segments. See
`New_Era_Email_Response_20260831.md`. Tranche 2 unblocks on receipt of the files.

## Folder inventory

- `PSUBSSEG_Discovery_Notes_20260829.md` — this document
- `Email_Eric_PSUBSSEG_Missing_Rate_Segments_20260829.md` — data request draft
- `_reconcile_psubsseg_vs_output.py` — read-only reconciliation script
- `evidence/psubsseg_reconciliation.csv` — 213 reconciliation rows
- `evidence/psubsseg_reconciliation_summary.json` — run summary
- `evidence/qladmin_help_effdate_pages.txt` — QLAdmin Help EFFDATE excerpts
