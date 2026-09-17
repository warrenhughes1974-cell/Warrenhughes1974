# Issue #169 — Discovery Notes

**Issue:** #169 — Missing Reserves: 960 LP85-M, SAL ADB, 619 SPS PU, 1595 (667 ART), 1596 LO1
**Framework stage:** Discovery
**Date:** 2026-09-15
**Raised by:** Jill Burns (CSO), 9/3/2026 ValX reserve comparison email

> **⚠ Classification superseded 2026-09-15.** The raw counts and table-presence facts below reproduce, and the form-number → plan-code map in §2 is correct. The **three-bucket classification is retracted**: it was derived from the terminal-reserve grid (`QuikTvs`) alone, and QLAdmin does not read that grid for these plans — the reserve is driven by the net valuation premium (`QuikNps` → `MTABNET`). Five of the eight plans are misclassified as a result, including all three "no source data / needs a CSO data request" calls. Read `Issue_169_Independent_Review_20260915.md` and `Issue_169_Intake_Summary.md` (v2) for the current position. Kept unedited as history.

---

## 1. Client-reported symptom

> "QL is not calculating reserves for the following form numbers: 960 LP85-M, SAL ADB, 619 SPS PU, 1595 (667 ART), 1596 LO1."

## 2. Form number → QLAdmin plan code map (confirmed via `plan_governance/product_catalog_crosswalk.csv` and `Master_Crosswalk.csv`)

| Jill's item | LifePRO plan label | QL plan code | Role |
|---|---|---|---|
| 960 LP85-M | `960` | `196085` | Base plan (Life Paid Up Age 85-88) |
| SAL ADB | `SAL ADB` | `9SLADB` | ADB rider on SAL ML |
| 619 SPS PU | `619` | `7619PU` | Base plan (Decreasing Term Paid Up for Spouse) |
| 1595 (667 ART) | `1595` (WP rider) + `667` (base) | `9595WP` + `5667AT` | WP rider + its base plan |
| 1596 LO1 | `1596 L01` (+ siblings `1596`, `1596 667`) | `901ADB` (+`996ADB`, `967ADB`) | ADB rider family under 1596/L01/667 |

"1596 LO1" is almost certainly "1596 L01" (L-zero-one), a typo/OCR mix-up of L01. `901ADB`'s own crosswalk description literally reads "Accidental DB Rider - L01 10Y LT."

## 3. Evidence pulled (all read-only, all against the **current** batch)

- Rate table output: `QLA_Migration/Output/rates/QuikTvs.csv` (reserve grid, 9/14/2026), `QuikPlTv.csv` (key/method layer, 9/14/2026)
- Policy population: `QLA_Migration/Output/quikridr.csv` (9/13/2026)
- Authoritative reserve-method assignment: `plan_analysis/source_data/rates/CSO_Valuation_Setup.csv` (Issue #80) and its full "coded expected" universe `Issue_Log_Items/Issue_80/evidence/cso_valuation_setup_coded_expected.csv`
- Newest LifePRO rate source extracts: `QLA_Migration/Source/PDAGE_AgeDuration_Rates_Extract_20260831.csv`, `PAAGE_...`, `PAAGERAT_...` (8/31/2026 pull — newer than the 4/27 extract #168 originally used)
- LifePRO's own actual reserve output vs QLAdmin's, 6/30/2026 valuation (the freshest ValX/QuikValf comparison in the repo, generated 9/2/2026 — one day before Jill's email, so this **is** the data behind her report): `docs/Valuation/analysis/reserve_gap_population.csv`, `Valx_QuikValf_Comparison_20260630.md`
- Scan tooling written for this issue: `Issue_Log_Items/Issue_169/tools/scan_source_issue169_v2.py`, `agg_june_reserve_gap_by_plan.py`
- Full findings table: `Issue_Log_Items/Issue_169/evidence/issue169_current_output_findings.csv`

## 4. Findings — three distinct root causes, not one

### Class A — No reserve data exists anywhere upstream (same class as #168's L05; not fixable in our code)

**`5667AT` (667 ART base plan) — 195 policies loaded today, $132,229 confirmed missing per the June ValX comparison (96 rows in that snapshot alone).**
`QuikTvs` has 2,020 rows with the *correct* key shape (UWCLASS 00/PR/ST matching every loaded policy's class) — but **every single value is 0.00**. That's not a lookup/key bug; it's a faithful copy of the source: the newest 8/31 LifePRO extract carries 3,728 `TYPE_CODE=RV` rows for the "667 ART 95"/"667 ART CR" coverage IDs and **all ten VALUE columns are zero on every one of them.** LifePRO's own extract never publishes a nonzero reserve factor for this plan. LifePRO's *actual* valuation output (ValX) nonetheless shows a real $132K reserve for these policies — meaning LifePRO computes 667 ART's reserve internally via formula (CSO mortality + net premium), not from the static table it exports to us. We cannot replicate a number LifePRO never hands us in the extract.

**`9595WP` (1595, Waiver of Premium rider on 667 ART) — 38 policies loaded.**
Zero rows in `QuikTvs`. Source extract has only `TYPE_CODE=PR` (premium) rows for coverage "1595" (84 rows, all nonzero) — never a single `RV` row. No reserve data exists to load.

**`9SLADB` (SAL ADB rider) — 6 policies loaded.**
Zero rows in `QuikTvs`. Source extract has only `PR` rows for "SAL ADB" (234 rows) — no `RV` rows anywhere.

All three of these match #168's L05 finding exactly: *"zero RV rows anywhere in the extract for this coverage... still requires a real source pull from CSO/New Era."* This is not code-fixable without new data from the client.

### Class B — Key mismatch: real data exists, but only under a class no policy carries (same class as #168's L14 — likely fixable)

**`901ADB` (1596 L01 ADB rider, 11 policies: 8 PR + 3 ST) and `996ADB` (bare 1596 ADB rider, 2 policies: 1 PR + 1 ST).**
`QuikTvs` has 192 rows each for these two plans, half of them nonzero — but **only under `UWCLASS='00'`.** Every currently loaded policy under either plan carries class `PR` or `ST`, never `00`. Every real policy therefore misses the lookup and reserves at $0 — the identical mechanism #168 diagnosed for L14.

New wrinkle not present in #168: `901ADB`'s and `996ADB`'s `UWCLASS=00` values are **byte-for-byte identical** to each other (all 192 keyed rows match exactly). Tracing into the source extract shows why — LifePRO doesn't carry plan-specific RV data for the 1596 family at all (no "1596"-prefixed coverage_id ever appears with `TYPE_CODE=RV`); instead there is a **generic, company-wide ADB rider factor table** in the source (coverage IDs `ADB 25 5`, `ADB 25 65`, `ADB 25 66`, `ADB 25 68`, `ADB 25 69`, `ADB 30 65` — a standard accidental-death-benefit grid indexed by cents-per-unit and expiry age, independent of base plan). Our pipeline evidently already borrows from that generic grid for `901ADB`/`996ADB`, but only ever stores it under class `00`.

If ADB reserves are genuinely class-invariant in LifePRO (highly plausible — accidental death mortality doesn't depend on the life underwriting class), then the #168 playbook applies directly: replicate the existing real `00` grid onto the `PR`/`ST` keys these policies actually carry. This needs the same source confirmation step #168 did for L14 before Development (Planning stage).

**`967ADB` (1596 667 ADB rider, 8 policies: 6 PR + 2 ST) — inconsistent sibling.**
Zero rows in `QuikTvs` at all — not even the generic `00` grid that `901ADB`/`996ADB` got. Same rider family (`1596`), same generic ADB source available, but this specific plan code got nothing. This looks like a gap in whatever rule assigns the generic ADB table to plan codes — three siblings, two got the (wrong-keyed) table, one got none.

### Class C — Looks structurally correct today; needs reconciliation against Jill's dated evidence, not a code fix

**`196085` (960 LP85-M) — 4 policies loaded, ages 17/19/24/35, all `UWCLASS=00`.**
`QuikTvs` has dense, plausible, nonzero reserve values at exactly those ages/gender/class. `QuikPlTv` carries a real reserve method (`MORT=O1, RSVINT=2, RSVMETH=3`) from `CSO_Valuation_Setup.csv` (Issue #80, `IN_SCOPE`). Source extract has real nonzero `RV` rows for "960 LP85-8" (the 11-char-truncated form of "960 LP85-88"). On paper this plan is fully wired. The June ValX comparison flagged exactly **one** row missing $1,858.42 for this plan — a single small-dollar exception, not a structural gap. Given the setup looks complete, this may already be resolved by the 8/31 rate refresh / CSO Valuation Setup work that landed after the June comparison was taken, or it may be a narrow duration-boundary case on that one policy. Needs a direct re-check against a fresh ValX pull before concluding anything is still broken here.

**`7619PU` (619 SPS PU) — 2 policies loaded, ages 34/59, both `UWCLASS=00`.**
`QuikTvs` has a full, believable term-reserve curve (rises then falls with duration) at both ages, all nonzero. Source extract confirms real nonzero `RV` data for "619 SPS PU" (570 rows, 412 nonzero). The one thing that stands out: `7619PU` is **not** listed in `CSO_Valuation_Setup.csv` at all, so its `QuikPlTv` `MORT`/`RSVINT`/`RSVMETH`/`INTMETHTV` fields are blank. Its sibling `619 DT` (`7619DT`) **is** in that setup file with a real method. Whether a blank `RSVMETH` actually blocks QLAdmin's engine from using an otherwise-complete `QuikTvs` table is unconfirmed from our side — table-lookup plans elsewhere in the system look no different in shape. Flagging this as an open question for Planning rather than a confirmed defect, given the June exception here was a single $90.47 row.

## 5. Prior-issue conflict check (per `.cursor/rules/completed-issues-release-guide.mdc`)

- **#168** (L14, in progress) established the exact playbook Class B needs here (replicate a class-invariant real grid onto the classes policies actually carry). No conflict — this issue would extend, not contradict, that approach, pending its own source confirmation for the ADB family.
- **#136** (`*VARY*` flags must reflect real rate differentiation only) — not yet touched by this Discovery; would need the same real-variation confirmation step before any Class B fix, exactly as #168 did.
- **#80** (CSO Valuation Setup authoritative list) — this Discovery did **not** change that file; it only reads it. Class A/B plans below are simply absent from its scope. Any fix that adds entries for `7619PU`, `9595WP`, `901ADB`, `967ADB`, `996ADB`, `9SLADB` would be **extending** #80's coverage, not overriding a Closed decision — but this should be called out explicitly at Planning since #80 deliberately scoped riders out originally (its "coded expected" universe never lists an ADB/WP rider, only base plans).

## 6. Scope split for the eventual Intake/Planning

| Bucket | Plans | Path |
|---|---|---|
| **Blocked — no source data** | `5667AT` (667 ART base), `9595WP` (1595 WP), `9SLADB` (SAL ADB), `967ADB` (1596 667 ADB) | New data ask to CSO/New Era, same as the standing L05 ask |
| **Likely fixable — key mismatch, real generic data exists** | `901ADB` (1596 L01 ADB), `996ADB` (bare 1596 ADB) | Confirm ADB reserve is class-invariant in source, then replicate `00` grid onto `PR`/`ST`, mirroring #168's L14 fix |
| **Needs reconciliation, not a code change (yet)** | `196085` (960 LP85-M), `7619PU` (619 SPS PU) | Re-run against a fresh ValX pull; if still $0, chase the blank `RSVMETH` question for `7619PU` and the single-row duration gap for `196085` |

Do not conflate these three buckets. Jill's five-item list actually spans all three.
