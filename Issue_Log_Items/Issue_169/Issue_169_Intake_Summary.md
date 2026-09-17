# Issue #169 — Intake Summary (v2)

**Issue:** #169 — Missing Reserves (960 LP85-M, SAL ADB, 619 SPS PU, 1595/667 ART, 1596 L01)
**Framework stage:** Intake
**Date:** 2026-09-15 (v2 same day)
**Track:** Client-facing (Jill Burns / CSO), Go-No-Go priority (valuation)
**Supersedes:** v1 Intake. The three-bucket model in v1 was built from the terminal-reserve grid alone and misclassified five of the eight plans — see `Issue_169_Independent_Review_20260915.md`.

---

## Problem statement

Jill's five form numbers resolve to **8 QLAdmin plan codes**. The reserve on these plans is driven by the **net valuation premium** (`QuikNps` → `MTABNET`), not by the terminal-reserve grid, which is why a `QuikTvs`-only reading of the evidence produced the wrong answer first time round.

Measured against LifePRO's own valuation output (`docs/Valuation/QuikValf.dbf` 9/2 run vs `VALXLIFE.TXT`, 6/30/2026):

| Cause | Plans | Rows | QLAdmin | LifePRO | Nature |
|---|---|---:|---:|---:|---|
| **RC-1** No `QuikNps` rows emitted — net premiums exist only in the attained-age PAAGERAT extract, which nothing loads for `TYPE_CODE='NP'`. PSUBSSEG emit entry **E4** was scoped for this and dropped from the delivered manifest | `5667AT` (667 ART) | 96 | **$0.00** | **$132,229.48** | **Our defect. Data already in the 8/31 package** |
| **RC-2** `QuikPlTv` `MORT`/`RSVINT`/`RSVMETH` blank — plan absent from `CSO_Valuation_Setup.csv` (PSUBSSEG open item **OI-1**, unresolved) | `7619PU`; also the magnitude driver for `901ADB`, `996ADB` | 6 | $123.00 | $405.92 | **Client input required. Must not be invented (#80)** |
| **RC-3** Source tabular durations stop at 12; policy is at duration 57; formula plan (`RSVMETH=3`) | `196085` (960 LP85-M) | 1 | $0.00 | $1,858.42 | QLAdmin/actuarial question |
| **RC-4** **No defect** — LifePRO holds a $0 reserve | `9595WP`, `967ADB`, `9SLADB` | 10 | $101.85 | **$0.00** | Opposite direction; confirm expectation with Jill |

## In scope for Development

**RC-1 only** — emit `5667AT`'s net-premium grid from the PAAGERAT attained-age extract by adding a `TYPE_CODE='NP'` wrapper to the existing parameterised PAAGERAT loader, allowlisted to `5667AT`. 98.6% of the issue's dollars, data already present, additive to a plan that emits nothing into `QuikNps` today.

**Gated on:** Warren clearing Dependency Gate **D-1** — the change touches the scope manifest of Closed row **PSUB**, which requires a written OK under Framework rule 13.

## Out of scope

- **RC-2** — `7619PU`, `901ADB`, `996ADB` need `QuikPlTv` assumption codes from the CSO Valuation_Setup workbook. Closed issue #80's rule is "blank cells stay blank"; inventing a mortality table or reserve method would contravene it. Narrow client ask instead.
- **RC-3** — `196085`, 1 policy / $1,858.42. Log and defer.
- **RC-4** — `9595WP`, `967ADB`, `9SLADB`. No change; confirm with Jill whether a reserve is expected at all.
- **`967ADB` crosswalk governance** — `CROSSWALK_DIVERGENT` / `FORM_CONFLICT_REVIEW` on LifePRO coverage `1596 667` is real and separately tracked, but it is not a reserve defect and not a blocker.
- Any change to `map_uwclass` / `map_rider_uwclass` (#159), `*VARY*` flag derivation (#136), `QuikGps` / `QuikNff` (#158/#157), or `5667AT`'s all-zero `QuikTvs` grid (PSUBSSEG OI-2).
- Any plan or form Jill did not name.

## Impacted tables (RC-1 only)

| Table | Change |
|---|---|
| `rates/QuikNps` | Add `5667AT` rows from PAAGERAT `TYPE_CODE='NP'`. No existing row modified |
| `rates/QuikPlTv` | Add `5667AT` key rows if the existing `19950101` generation does not cover the NP grid (D-7) |
| everything else | No change — byte-identical before/after is a hard regression gate |

## Client commitments

1. **Narrow data ask to CSO** (replaces the v1 reserve-factor request, which must not be sent): supply `QuikPlTv_MORT`, `QuikPlTv_RSVINT`, `QuikPlTv_RSVMETH` for `7619PU`, `901ADB`, `996ADB`.
2. **Question to Jill:** LifePRO's own ValX reports $0 reserve on 1595 WP, SAL ADB and 1596-667 ADB — confirm whether a reserve is expected on those three before either side spends more time on them.
3. **No claim** about 667 ART dollar amounts until a fresh `QuikValf` is run against the current package (the 9/2 run predates the 9/13–9/14 rate regeneration).

## Stakeholders

- Issue owner: Warren
- Client contact: Jill Burns (CSO)
- Prior related work: **PSUB** / PSUBSSEG substitution (Closed — owns `5667AT` generations; E4 dropped, OI-1 unresolved), **#80** (CSO Valuation Setup — owns the blank assumptions), **#158/#157** (share `paagerat_pr_loader.py`), **CEN NP** (`QuikNps` level flatten — `1668SP` excluded), **#42** (PDAGE miss-fill — shares `QuikNps`), **#168** (L14 — the review that established the net-premium mechanism), **#77** (key-row completeness).
