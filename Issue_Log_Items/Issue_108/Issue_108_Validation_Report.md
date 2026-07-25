# Issue #108 — Validation Report

**Date:** 2026-07-25
**Framework stage:** Validation (stage 6)
**Engine:** `v58.33`
**Batch:** full headless UAT batch, 28m 53s, exit code 0
**Source:** `PPOLC_PolicyMaster_Extract_20260630.csv`
**Result:** **PASS** for tracks 108A, 108B, 108C, 108D, 108F

Baseline for comparison: `QLA_Migration/Archive/pre_v5833_baseline_20260725/`
(the pre-change `Output/` tables, written 2026-07-24 06:57).

---

## 1. Structural integrity

| Check | Result |
|---|---|
| `quikmstr` rows | 5,083 → 5,083 (no change) |
| `quikridr` rows | 6,934 → 6,934 (no change) |
| `quikmstr` column list | identical |
| `quikridr` column list | identical |
| Field order / types / lengths | unchanged |

---

## 2. Track results

### 108A — save fields blanked on NFO phase 1

| Field | Non-blank on NFO phase 1 after | Target |
|---|---:|---:|
| `MSAVEAGE` | 0 | 0 |
| `MSAVEUNIT` | 0 | 0 |
| `MSAVEVPU` | 0 | 0 |
| `MSAVEPREM` | 0 | 0 |
| `MSAVESTAT` | 0 | 0 |

All 400 ETI/RPU phase-1 rows changed. **PASS.**

### 108B — attained age and duration

`MAGE` changed on 400 / 400 NFO phase-1 rows. `MLASTANN` changed on 312 / 400.

**Critical guard: `MPHDOB` changed on 0 of 400 rows.** This proves the sequencing constraint
held — the attained-age write lands after `_derive_mphdob_from_issue_age` has consumed the
issue age, so no date of birth was corrupted. This was the single highest-risk item in the
release.

Representative rows:

| Policy | Status | MAGE before → after | MLASTANN before → after |
|---|---|---|---|
| 9010149295C | 44 | 20 → 51 | 34 → 33 |
| 9010165095C | 45 | 21 → 47 | 38 → 37 |
| 9010374099C | 44 | 00 → 39 | 17 → 16 |
| 9010379477C | 45 | 02 → 31 | 26 → 25 |

`MPAYUP` changed on 0 rows, confirming Issue #76's pay-up assignment is untouched and only
the duration arithmetic moved. **PASS.**

### 108C — ETI premium

ETI (44) phase-1 rows with non-zero `MPREM` after: **0 of 206**.
RPU (45) phase-1 rows with `MPREM` changed: **0 of 194** — correctly excluded per spec.
**PASS.**

### 108D — PUA termination

| Population | MPHSTAT before | MPHSTAT after |
|---|---|---|
| PUA on ETI/RPU base (27 rows) | `41` | `54` |
| PUA on non-NFO base (467 rows) | 238×`56`, 228×`41`, 1×`22` | unchanged |

Issue #60's original population is intact. **PASS.**

### 108F — NFO election recovery

| `MNFOPT` | Before | After |
|---|---:|---:|
| `0` (dropped) | 4,683 | 737 |
| `1` (APL) | 0 | 1,945 |
| `2` (ETI) | 206 | 2,336 |
| `3` (RPU) | 194 | 65 |

**3,946 elections recovered.** The PPBENTYP cache logged 4,930 entries keyed on raw source
numbers (`9010143726`), confirming the repointed key matches the cache's own key format.

**Independent corroboration from Issue #57.** `validate_issue57_mnfopt.py` names six trace
policies with client-specified expected values. All six now carry exactly the expected
election:

| Policy | Expected | Emitted |
|---|---|---|
| 9010143726C | 2 | 2 |
| 9010392763C | 3 | 3 |
| 9011221309C | 1 | 1 |
| 9010391876C | 2 | 2 |
| 9010367131C | 2 | 2 |
| 9010148272C | 2 | 2 |

The validator still reports FAIL only because it looks the policies up under the
pre-Issue-#2 10-character key (`010143726C`), which no longer exists in the output. The data
is correct; the validator is stale. **PASS.**

---

## 3. Regression

### `quikmstr` — only the intended field moved

Comparing all 5,083 policies field by field, exactly one column changed: `MNFOPT`
(4,389 rows). Every other column — including `MPOLICY`, `MSTATUS`, `MPAIDTO`, `MDIVOPT`,
banking, and billing — is byte-identical. Issue #2's `MPOLICY` identity is intact.

### `quikridr` — non-NFO rows

Comparing all 6,361 non-NFO rows, the only column that moved is `MPAR` (466 rows).

**`MPAR` is not attributable to this release.** Three independent lines of evidence:

1. All 493 `MPAR` changes are `0 → 1` and every affected `MPLAN` ends in `PA` (PUA rider
   plans such as `1705PA`, `2665PA`).
2. `MPAR` is written at only two places, `app.py:7674` and `app.py:8048`. This release
   consists of 11 hunks, none of which covers either line.
3. The baseline was written **2026-07-24 06:57**; the Issue #105 `MPAR` code was committed
   **2026-07-24 11:56**, five hours later. The baseline simply predates the feature.

This is Issue #105 reaching `Output/` for the first time. It does raise a separate question
(tracked as **#111**): PUA plans are absent from `quikplan`, so `MPAR` is inherited from the
base plan before the PUA rename rather than resolved from the product table.

### NFO phase-2+ rows

Three columns moved on 27 rows: `MPHSTAT` (108D, intended), `MSAVESTAT` (follows `MPHSTAT`
through the unchanged v57.96 mirror, which correctly still applies to non-phase-1 rows), and
`MPAR` (as above).

---

## 4. Robert's four consistency checks against the new output

| Check | Before | After | Note |
|---|---:|---:|---|
| 1. Terminated policy with in-force coverage | 0 | **0** | clean |
| 2a. NFO policy, phase 1 status ≠ policy status | 0 | **0** | still masked by the phase-1 force; 108G removes it |
| 2b. NFO policy, phase 2+ in force | 109 | **82** | 27 PUA resolved by 108D |
| 3. Active policy with no in-force coverage | 0 | **0** | clean |
| 4. NFO status vs election | 0 (masked) | **277** | now real data, see below |

**Check 2b residual (82 rows, 81 policies)** splits exactly as predicted at Planning:

| MPLAN | Rows | Disposition |
|---|---:|---|
| `1SALMI` | 77 | zero-unit base structure — client question, 108E |
| `9595WP` | 3 | waiver of premium leftovers, 108E |
| `967ADB` | 2 | accidental death leftovers, 108E |

**Check 4 (277 policies)** could never fire before because Issue #72 forced the value it
tested. With the force downgraded to a report, the real picture is visible:

| NFO type | Emitted | Reason | Policies |
|---|---|---|---:|
| ETI | `0` | election missing in source | 86 |
| ETI | `1` | election disagrees (APL vs ETI) | 12 |
| RPU | `0` | election missing in source | 80 |
| RPU | `1` | election disagrees (APL vs RPU) | 55 |
| RPU | `2` | election disagrees (ETI vs RPU) | 44 |

166 have no election in PPBENTYP at all; 111 carry an election that genuinely contradicts
the policy status. All 277 are written to
`QLA_Migration/Reports/nfo_election_status_mismatch.csv`.

**Open decision for the client:** for the 166 policies with no source election, the output
now carries `MNFOPT = 0` where it previously carried a forced 2 or 3. That is what Robert
asked for architecturally, but it does mean an ETI policy can emit with no election. Robert
should confirm whether blank is acceptable or whether a status-derived default should be
restored for the missing-election subset only.

---

## 5. Validator status

| Validator | Result | Assessment |
|---|---|---|
| `validate_issue57_mnfopt` | FAIL | **Stale** — uses pre-Issue-#2 10-char keys. Data verified correct on all six traces. |
| `validate_issue60_pua_phase` | FAIL (81) | **Expected** — 27 NFO PUA rows × 3 assertions. Asserts PUA inherits base `MAGE`/`MLASTANN`/`MPHSTAT`, which 108B/108D deliberately break for NFO. Non-NFO PUA rows pass. |
| `validate_issue72_mnfopt_status` | FAIL (277) | **Expected by design** — asserts the force that Robert asked to remove. Count matches the exception report exactly. |
| `validate_issue76_eti_rpu_payup` | FAIL (312) | **Expected** — encodes the old calendar-year arithmetic. `payup_fail=0`, so only the corrected duration differs. |
| `validate_issue105_mpar` | FAIL (493) | **Pre-existing**, see #111. Not attributable to this release. |
| `validate_issue21a_mnfopt` | ERROR | **Environmental** — points at `_20260530` extracts; source is now `_20260630`. |
| `validate_issue26_mprem` | ERROR | **Environmental** — same missing `_20260530` extracts. |

Four validators encode behaviour this release intentionally supersedes. They must be
rewritten before Closure (G7), which requires validator PASS on full `Output/`.

**Issue #108 cannot be closed until those rewrites land.** Status stays *Validated —
pending validator rewrite*.

---

## 5A. Superseded by v58.34 (Issue #110)

After this report was written the user approved Issue #110 (`MDIVOPT`) for immediate release
as `v58.34`, and a second full batch was run. That release changed `MDIVOPT` on 811 policies
and nothing else:

- `MNFOPT` identical to v58.33 on all 5,083 policies — every 108F result above still holds
- `quikridr` **byte-identical** to v58.33 on every row and column — every 108A/B/C/D result
  above still holds unchanged

The findings in this report therefore stand as written against the final `v58.34` output.
Cumulatively, `quikmstr` differs from the pre-change baseline in exactly two columns:
`MNFOPT` (4,389 rows) and `MDIVOPT` (811 rows). See
`Issue_Log_Items/Issue_110/Issue_110_Implementation_Notes.md`.

---

## 6. Publication

`quikmstr.csv` and `quikridr.csv` copied to `QLA_Migration/Output/Test_Validation/` for
partial UAT reload.

`QLA_Migration/Output/` root confirmed to contain table CSVs only. Five batch artifacts were
relocated per the Output folder policy: `claims_cross_table_validation_report.csv` and
`claims_emit_enhancement_validation.csv` to `Validation/`; `claims_review_hold_manifest.csv`,
`cso_mortality_crosswalk_qa.csv`, and `variation_code_audit.csv` to `Reports/`.

---

## 7. Follow-on work

1. Rewrite `validate_issue72_mnfopt_status.py` to assert the exception report rather than the force
2. Amend `validate_issue60_pua_phase.py` to carve out NFO bases (expect `54`, no age inheritance)
3. Update `validate_issue76_eti_rpu_payup.py` to the anniversary-accurate duration
4. Repoint `validate_issue57_mnfopt.py` to Issue #2 keys
5. Open **#111** for the PUA `MPAR` / missing PUA plans question
6. Client answers on 108E, and the missing-election decision from section 4
7. 108G governance build — required before the phase-1 force can be retired
