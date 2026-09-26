# PSUBSSEG Rate Substitution — Intake Summary

**Issue:** PSUBSSEG — LifePRO issue-date coverage substitution vs QLAdmin rate load
**Date:** 2026-08-31
**Framework stage:** Intake complete (G0/G1); Discovery completed 2026-08-29
**Status recommendation:** Ready for Planning → Dependency Gate → Risk (Pre-Dev chain)
**Owner:** Conversion (Warren)
**Raised by:** CSO (via New Era substitution extracts, `docs/New_Segments/` 2026-08-21)
**Priority:** Internal / High (reserve correctness for ~1,025 active benefit rows)
**Related:** #107 (LP95/LP9595, held), L01/L05/L07/667 ART RV hold (Eric 2026-07-22), #40 (CV inheritance), #96/#106 (QuikTvs), #42 (PDAGE miss-fill)

---

## Business symptom

New Era's substitution tables (PSUBS/PSUBSSEG/PCONT) show LifePRO replaces a
coverage's rate segment list for policies issued on/after dated substitution
records. Our rate load resolves segments with no date awareness, so plans whose
in-force spans substitution dates are valued off the wrong (or no) rate segment
in QLAdmin.

## Normalized finding (from Discovery, evidence in `evidence/`)

- 57 of 141 converted coverages have substitution records; 213 reconciliation slots:
  138 already correct, 27 emit-missing, 25 source-missing, 23 multi-era.
- EFFDATE semantics confirmed by Warren 2026-08-31: QLAdmin selects the rate band
  with the latest EFFDATE on or before the policy issue date. Era-banded emit is
  the approved representation.

## Scope — two tranches

### Tranche 1 (this issue, data on hand — Development scope)

| Fix | Plans | Tables | Rows in |
|---|---|---|---|
| Era-band RV/NP (add 19950101 band from `L10 LP9595`) | `1L10OD` | QuikTvs, QuikNps + key rows | ~12,384 |
| Re-source + era-band RV/NP (`L10 LP95SR` / `L10SR 95`) | `1L10SO` | QuikTvs, QuikNps + key rows | ~8,256 (replaces 6,198) |
| CV/NP inheritance from segment `L17` | `10L171`, `10L172`, `117JPO`, `17MJPO` | QuikCvs, QuikNps + key rows | ~3,936 |
| NP emit from PAAGERAT `667 ART` | `5667AT` | QuikNps | ~288 source rows |
| Premium fills from PAAGERAT (PSUBSSEG-confirmed owners) | `17CSI5`, `719SDT`, `221END`, `1666WL`, `170858`, `170588`, `7686S3`, `2961ME`, `280END`, `1L15GD`, `5646AT`, `57ATCR` | QuikGps (+QuikNps where NP) | ~2,850 source rows |

### Tranche 2 (blocked — awaiting New Era data)

13 substituted segment IDs missing from all extracts (`L01 10Y 95`, `L05 10Y 95`,
`L07 5Y 95`, `L10 CDT 95`, 619 family ×5, `670 GL858`, `670GL858NL`, `991 PWL73`,
`667 ART 95` NP). ~360 active policies. Data request drafted
(`Email_Eric_PSUBSSEG_Missing_Rate_Segments_20260829.md`). Not part of this
Development scope; reopens as follow-on when data arrives.

## Out of scope / preserve

- TX/TP (tax) segment substitution — no QLAdmin tax rate tables in our load.
- L17 RV (shipped, #96/#106 — PSUBSSEG confirms; do not touch).
- Whole-coverage substitution (none exist in the data).
- Policy tables (`quikmstr` etc.) — no plan splits needed given EFFDATE confirmation.
- `5667AT` RV: LifePRO's 95-era segment is genuinely all zeros (plausible for ART).
  Default: leave absent (QLAdmin treats missing as zero). Decision logged for Dev approval.

## Example policies (active, from PPBEN 20260630)

| Plan | Pre-95 band | Post-95 band |
|---|---|---|
| `1L10OD` (L10 PRE97) | 9011088338 (1994-05-01), 9011088512, 9011090113 | 9011103507 (1995-01-12), 9011103641, 9011103642 |
| `1L10SO` (L10 SR OLD) | 9011093379 (1994-07-21), 9011098597, 9011100080 | 9011106176 (1995-02-25), 9011106727, 9011111218 |
| `5667AT` (667 ART) | 9010764158 (1985-09-09), 9010764248 | 9011121183 (1995-10-25), 9011136641 |
| L17 children | 9011217014 (`10L171`), 9011227611 (`117JPO`), 9011266391 (`10L172`), 9011227606 (`17MJPO`) | (single era) |

## Artifact inventory

| Artifact | Status |
|---|---|
| PSUBS/PSUBSSEG/PCONT extracts + readme + SQL | In `docs/New_Segments/` |
| Reconciliation script + 213-row evidence CSV/JSON | In this folder |
| QLAdmin Help EFFDATE excerpts | `evidence/qladmin_help_effdate_pages.txt` |
| EFFDATE selection rule | Confirmed by Warren 2026-08-31 (no client dependency) |
| Missing-segment data request | Drafted, awaiting send/response (Tranche 2 only) |

## Gate G0/G1

- [x] Issue folder created (2026-08-29)
- [x] Intake summary written
- [x] Example policies listed per band
- [x] Owner and priority assigned
- [x] No code or rulebook changes made
