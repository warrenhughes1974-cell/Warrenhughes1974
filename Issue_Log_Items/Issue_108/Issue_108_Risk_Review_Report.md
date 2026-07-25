# Issue #108 — Risk Review Report

**Issue:** #108 — Statuses and NFO (ETI/RPU) conversion conformance
**Framework stage:** Risk Agent (G3)
**Status:** Conditional Go (108A–108D, 108G) / Conditional Go, separate release (108F) / No-Go (108E)
**Generated:** 2026-07-25 — **108F section revised same day after the key convention was resolved**
**Baseline:** `QLA_Migration/Output/` at app `v58.31`
**Method:** read-only before/after simulation against emitted Output; no production logic changed

---

## Go / No-Go Recommendation

**CONDITIONAL GO** for tracks **108A, 108B, 108C, 108D (status only), 108G** — 427 of 6,934 `quikridr` rows (6.16%), zero `quikmstr` rows, and zero rows outside the 400 NFO policies. The conditions are the sequencing constraint in §8 and the validator amendments in §9.

**CONDITIONAL GO, SEPARATE RELEASE** for **108F** — now unblocked (see §7A), but it populates **4,112 `MNFOPT` values** across the fleet versus 427 NFO-scoped rows for A–D. Shipping both in one version makes regression attribution unnecessarily hard. Recommend A–D + G as **v58.32**, then 108F as **v58.33**.

**NO-GO** for **108E** (SME-gated).

The single most important point for the approval decision: **108B is the reason to do this work now.** The other tracks are correctness hygiene. 108B is what makes QLAdmin's cash-value rebuild defensible on 400 policies, and it must land before anyone compares reserves.

---

## 1. Current vs Proposed Mapping

| Track | Field | Current | Proposed | Change? |
|---|---|---|---|---|
| 108A | ph1 `MSAVEAGE/UNIT/VPU/PREM/STAT` on 44/45 | mirror of live post-NFO values | blank | Yes |
| 108B | ph1 `MAGE` on 44/45 | `PPBEN.ISSUE_AGE` | attained age at `MPAIDTO` | Yes |
| 108B | ph1 `MLASTANN` on 44/45 | `now().year − payup_year` | anniversary-accurate duration vs valuation date | Yes |
| 108C | ph1 `MPREM` on 44 | `ANN_PREM_PER_UNIT` | `0.00` | Yes |
| 108D | PUA `MPHSTAT` where base is 44/45 | `41` | `54` | Yes |
| 108G | governance | no cross-table rule | new DG item | New artifact only |

---

## 2. Fields Explicitly Untouched

| Target | Source | Touched? |
|---|---|---|
| `quikmstr.MSTATUS` | `ST_*` crosswalk | **No** — codes verified correct against spec |
| `quikmstr.MNFOPT` | #72 force | **No** in the v58.32 release — 108F ships separately as v58.33 |
| `quikmstr.MMODPREM` | `PPOLC.MODE_PREMIUM` | **No** |
| `quikmstr.MPAIDTO` | PPOLC | **No** — read-only anchor |
| `quikridr.MPREM` on RPU (194 rows) and all non-NFO | `ANN_PREM_PER_UNIT` (#26) | **No** |
| `quikridr.MAGE` on all non-NFO and all phase 2+ | `ISSUE_AGE` | **No** |
| `quikridr.MEXPRY` | `MATURE_EXPIRE_DATE` | **No** |
| `quikridr.MUNIT` | `NUMBER_OF_UNITS` (#55 floor) | **No** — fold gated on Q1 |
| `quikridr.MPAYUP` | #76 | **No** — already correct, 400/400 |
| `quikridr.MPHSTAT` phase 2+ non-PUA | `PPBEN.STATUS_CODE` | **No** |
| PUA `MPHSTAT` where base < 44 (467 rows) | #60 | **No** |
| `MPOLICY` padding | `format_qladmin_mpolicy()` (#25) | **No** |
| `quikloan`, `quikdvdp`, `quikdvpr` | — | **No** |

**Verified:** every proposed edit is filtered on policy status 44/45. Simulated rows changing outside the NFO population: **0**.

---

## 3. Population Analysis

| Metric | Count |
|---|---:|
| `quikridr` rows total | 6,934 |
| NFO phase-1 rows | 400 |
| **Distinct rows touched** | **427 (6.16%)** |
| Field-level edits | 1,198 |
| `quikmstr` rows touched | **0** |
| Rows touched outside NFO policies | **0** |

### By track

| Track | Rows changing | Rows in scope left unchanged |
|---|---:|---|
| 108A `MSAVE*` → blank | 400 | 0 (all 400 currently populated) |
| 108B `MAGE` | 400 of 400 | 0 — not one row is currently correct |
| 108B `MLASTANN` | 167 of 400 | 233 already correct |
| 108C ETI `MPREM` → 0 | 204 of 206 | 2 already zero; 194 RPU untouched |
| 108D PUA 41 → 54 | 27 of 27 | 467 PUA rows fleet-wide untouched |

---

## 4. Material Calculation Impact

This is the section that matters for UAT sign-off.

`MCV1` and `MCV2` are blank on **all 400** NFO phase-1 rows and `MCV0` is blank on **348**, so QLAdmin will rebuild these cash values from plan NFO mortality and interest (`QuikPlcv`). Robert's formula is:

```
tCV = [ (t-1)CV × (1 + i) − VPU × q(x+t) ] / ( 1 − q(x+t) )
```

where **x is the age at nonforfeiture** and **t is the NFO duration**. Today we supply `x` = issue age and, on 167 policies, a `t` that is one year high.

`MAGE` is wrong on **400 of 400** rows. Delta distribution: minimum 3 years, median 24.5, maximum 55.

| Policy | `MAGE` before | Attained at paid-to | Delta |
|---|---:|---:|---:|
| `9018313AC` | 10 | 65 | +55 |
| `901ML8314BC` | 3 | 55 | +52 |
| `9014075AC` | 1 | 52 | +51 |
| `9014075BC` | 0 | 50 | +50 |
| `9010448375C` | 34 | 83 | +49 |

Understating the mortality age by a median of 24.5 years understates `q(x+t)`, which overstates the ETI/RPU cash value and, for ETI, pushes the calculated expiry out. **These are intentional corrections, not drift** — but reserves on the NFO book will move, and the direction is downward on cash value for most policies.

**Recommendation:** treat the post-fix CV/reserve movement as a deliverable in its own right. Validation should capture rebuilt `MCV0/1/2` before and after and hand Robert the comparison before any UAT reload. There is currently no agreed tolerance (Dependency Gate, UAT criteria = Missing).

`MLASTANN` also feeds CV interpolation directly, since `MCV0` is the value at the last anniversary and `MCV1` at the next. The current computation uses `datetime.now()`, so the value **changes between reruns of the same batch** — a reproducibility defect independent of the off-by-one.

---

## 5. Trace Policies

| Policy | Field | Before | Proposed | Pass? |
|---|---|---|---|---|
| `9010391355C` (ETI) | ph1 `MAGE` | `13` | `51` | Yes |
| | ph1 `MLASTANN` | `17` | `16` | Yes |
| | ph1 `MPREM` | `11.64000` | `0` | Yes |
| | ph1 `MSAVESTAT` | `44` | blank | Yes |
| | ph2 `1708PA` `MPHSTAT` | `41` | `54` | Yes |
| `9010407670C` (RPU) | ph1 `MAGE` | `33` | `73` | Yes |
| | ph1 `MLASTANN` | `14` | `13` | Yes |
| | ph1 `MPREM` | `0` | `0` (RPU untouched) | Yes |
| `9010149295C` (ETI) | ph1 `MAGE` | `20` | `51` | Yes |
| | ph1 `MLASTANN` | `34` | `33` | Yes |
| `9018313AC` (RPU) | ph1 `MAGE` | `10` | `65` | Yes |
| | ph2 `1SALMI` `MPHSTAT` | `22` | **unchanged** | Yes — 108E excluded |
| `9010820645C` (ETI) | ph2 `9595WP` `MPHSTAT` | `22` | **unchanged** | Yes — 108E excluded |

---

## 6. Regression Surfaces

| Surface | Severity | Assessment |
|---|---|---|
| **`MPHDOB` derivation ordering** | **Critical** | `_derive_mphdob_from_issue_age(MEFFDATE, MAGE)` at `app.py:5325–5328` reads `row_data['MAGE']`. If 108B writes attained age before this runs, `MPHDOB` is recomputed as issue-date minus attained-age and is corrupted on 400 rows — and `MPHDOB` is the input 108B itself depends on. **The `MAGE` hook must run after `MPHDOB` resolution.** Validation must assert `MPHDOB` is byte-identical before and after |
| **Issue #60 validator** | High | `validate_issue60_pua_phase.py` asserts PUA alignment against a v57.85 phase-1 baseline and predates #76. 108D changes 27 PUA rows and 108A–108C change phase 1. Validator must be amended, not merely re-run |
| **Issue #76 behaviour** | Medium | 108B modifies `_apply_issue76_eti_rpu_phase1_payup_mlastann`. `MPAYUP` must stay at 400/400 = `MPAIDTO`; only the duration arithmetic changes. `validate_issue76_eti_rpu_payup.py` should still pass on the `MPAYUP` half |
| **Issue #26 `MPREM`** | Medium | 108C narrows to ETI phase-1. RPU (194) and all non-NFO rows must be unchanged — assert explicitly |
| **`MSAVE*` consumers** | Low | No reader found in `qla_core/` or the converter; `_apply_quikridr_v5796_defaults` is the only writer. The consumer is QLAdmin at reinstatement. Confirm the `quikridr` DBF schema tolerates blank before emit |
| **v57.96 default** | Low | 108A adds a status condition to an existing default; non-NFO rows keep the mirror |
| **Issue #2 / #55** | None | No key or units change in scope |

---

## 7A. Track 108F — Unblocked (revised)

The Dependency Gate originally blocked 108F pending a canonical re-batch. The question was settled **by inspection instead**, so no batch was run and the Output baseline for A–D is intact.

**Root cause:** Issue **#2** (closed 2026-07-23, v58.29) replaced the strip-9 crosswalk with source + `C` at width 11 and formally superseded Issue #25's width-10 contract. It realigned the identity paths it knew about but missed two that still resolve through the retired crosswalk columns.

| Path | Live keys resolved | Effect |
|---|---:|---|
| `reverse_cw_map` → PPBENTYP enrichment (`app.py:7695`) | **0 of 5,083** | `MNFOPT` and `MDIVOPT` dead fleet-wide |
| `cw_map` → Issue #71 provisional cache (`app.py:7867`) | **0 of 5,194** | Issue #71 inert; phase-1 inherits post-#49 status |

**Correction to the earlier gate:** the 11-character keys are correct and current. They do not violate Issue #25, which is superseded. The Output under test is a valid v58.29+ batch.

### Sizing and risk

| Metric | Count |
|---|---:|
| `MNFOPT` values populated by the fix | **4,112** |
| In-force policies currently losing their election | 1,933 of 1,933 |
| NFO policies where election disagrees with the #72 force | 111 of 234 |
| `MDIVOPT` also restored by the same repoint | up to 5,083 |

| Risk | Severity | Assessment |
|---|---|---|
| Blast radius is fleet-wide, not NFO-scoped | High | Ship separately from A–D so regression is attributable |
| `MDIVOPT` moves on the same code path | High | `MDIVOPT` is out of #108 scope but **will** change when the key is repointed. Either scope it in deliberately or gate the repoint to `MNFOPT` only |
| Removing the #72 force changes 111 policies from forced to source-derived | Medium | Intended per Robert's email; surfaces as governance warnings |
| `validate_issue72_mnfopt_status.py` asserts the force being removed | Medium | Must be rewritten as a warning check before this ships |
| Reintroducing `reverse_cw_map` in the fix | High | **Do not.** Key off `src_row['POLICY_NUMBER']` directly |

### Spun out — do not fold into #108

The Issue #71 provisional-cache failure is a separate closed-issue regression with its own population and validator. It should be raised as its own issue rather than absorbed here.

---

## 7. Why 108E Is a No-Go, Not a Deferral

Robert's check 2b ("phases 2+ in force on an NFO policy") returns **109 rows on 108 policies** in current Output. Decomposed:

| Population | Rows | Disposition |
|---|---:|---|
| `1708PA` / `1705PA` PUA at status 41 | 27 | **108D** — real defect, cleared |
| `1SALMI` at status 22 | 77 | **False positive** — see below |
| `9595WP` (waiver) / `967ADB` (accidental death) at status 22 | 5 | **108E** — genuine, 4 policies, SME-gated |

The `1SALMI` rows are not riders that failed to terminate. Across the `1SALML` fleet, **147 of 152 phase-1 base rows carry zero units** and the face amount sits on the phase-2 `1SALMI` row; 77 of those policies are RPU. Mechanically applying "terminate all phases 2+" would **zero the entire in-force amount on 77 RPU policies**.

This is exactly the trap Robert anticipated when he wrote that phases 2+ "could be wrong... this should be validated with the source system to see if it is legit or not." It is also the strongest single argument for his architectural position: a forcing rule in the converter would have destroyed 77 policies silently, whereas a governance check surfaces them for review.

The 5 genuine rows sit on 4 ETI policies, all base plan `5667AT`. Note `9010779553C` carries `9595WP` at 56 but `967ADB` at 22 within the same policy — an internal inconsistency that suggests source error rather than intent.

---

## 8. Sequencing Constraint (condition of the Go)

1. `MPHDOB` resolution — **unchanged, runs first**
2. 108B `MAGE` → attained age at `MPAIDTO` (phase 1, status 44/45 only)
3. 108B `MLASTANN` → anniversary-accurate duration vs valuation date
4. 108C `MPREM` → 0.00 (phase 1, status **44 only**)
5. 108D PUA `MPHSTAT` → 54 where base is 44/45
6. 108A `MSAVE*` → blank on 44/45 — **must run last**, after every other phase-1 write, so nothing re-mirrors

Step 6 last is not cosmetic: `_apply_quikridr_v5796_defaults` currently runs after `_apply_issue76_*`, so if the ordering is disturbed the mirror will re-populate `MSAVE*` from the newly corrected fields and re-create the defect in a subtler form.

---

## 9. Prior Fix Preservation

| Check | Result |
|---|---|
| Issue #2 `MPOLICY` identity (source + `C`, width 11) | **Preserved** — no key change. Issue #25 width-10 is superseded by #2 |
| Issue #26 `MPREM` / `MMODPREM` | **Preserved** — 108C scoped to ETI phase-1; RPU and non-NFO untouched |
| Issue #55 `MUNIT` floor | **Preserved** — no units change |
| Issue #60 PUA inheritance | **Modified by design** — 44/45 carved out; validator amendment required |
| Issue #72 `MNFOPT` force | **Untouched this release** — deferred to 108F |
| Issue #76 `MPAYUP` | **Preserved** — 400/400 unchanged; only duration arithmetic changes |
| Issue #13 / #49 `MSTATUS` | **Untouched** |

---

## 10. Regression Testing Checklist (for Validation Agent)

- [ ] Trace policies: `9010391355C`, `9010407670C`, `9010149295C`, `9018313AC`, `9010820645C`
- [ ] `MPHDOB` byte-identical before and after on all 6,934 `quikridr` rows — **hard gate**
- [ ] `MAGE` unchanged on all non-NFO rows and all phase 2+ rows
- [ ] `MPREM` unchanged on 194 RPU phase-1 rows and all non-NFO rows
- [ ] `MPAYUP` still equals `MPAIDTO` on 400 of 400
- [ ] PUA `MPHSTAT` unchanged on 467 fleet-wide rows; changed on exactly 27
- [ ] `MSAVE*` blank on exactly 400 rows; mirror intact elsewhere
- [ ] `quikmstr` byte-identical (0 rows expected to change)
- [ ] Row counts stable: `quikridr` 6,934; `quikmstr` 5,083
- [ ] `1SALMI` (77) and `9595WP`/`967ADB` (5) rows unchanged — 108E not in this release
- [ ] Robert's four checks re-run; document that 2a and 4 remain neutered by forcing until 108G/108F
- [ ] Rebuilt `MCV0/1/2` before/after comparison captured for Robert
- [ ] Publish modified tables to `Output/Test_Validation/` on PASS

---

## 11. Recommended Development Agent Task

1. Implement 108B, 108C, 108D, 108A in the order given in §8, all gated on phase 1 and policy status 44/45 (108C on 44 only).
2. Do **not** implement: the PUA units fold (Q1), any `MEXPRY` change, any phase-2+ termination beyond PUA, any `MNFOPT` change, any `MSTATUS` change.
3. Do **not** remove the Issue #59 allowlist or the phase-1 inherit in this release — those belong with 108G once the governance checks exist to replace them.
4. Amend `validate_issue60_pua_phase.py` and add `tools/validators/validate_issue108_nfo_conformance.py`.
5. Version bump **v58.32** in **both** `app.py` and `QLA_Migration/app.py`.

---

## Appendix

- Planning report: `Issue_Log_Items/Issue_108/Issue_108_Planning_Report.md`
- Dependency gate: `Issue_Log_Items/Issue_108/Issue_108_Dependency_Gate.md`
- Client specification: `docs/research/Conversion - Statuses, NFO/QLAdmin_ETI_RPU.docx`
- Simulation was read-only against emitted Output; no script committed, no production logic touched
