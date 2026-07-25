# Issue #108 — Planning Report

**Issue:** #108 — Statuses and NFO (ETI/RPU) conversion conformance
**Framework stage:** Planning Agent (G1)
**Status:** Planning complete — 108F blocked pending key-convention resolution
**Generated:** 2026-07-25
**Baseline:** `QLA_Migration/Output/` (`quikmstr.csv` 2026-07-23, `quikridr.csv` 2026-07-24), app `v58.31`
**Analysis:** read-only queries against Output + `QLA_Migration/Source/`; no scripts committed, no code changed

---

## 1. Executive Finding

Robert's specification and our conversion agree on the **status codes** (44/45 are crosswalked correctly from `PAID_UP_TYPE`/`CONTRACT_REASON` via `Master_Value_Translation.csv`) and on three field behaviours (`MPAYUP` = paid-to, RPU expiry unchanged, dividend accumulations extinguished). They disagree on almost everything else in the NFO field set.

The material problem is **not** the statuses — it is that the phase-1 driver fields QLAdmin uses to rebuild ETI/RPU cash values are wrong on all 400 NFO policies. `MAGE` is the issue age rather than the attained age at the nonforfeiture date (median error 24.5 years, max 55), `MLASTANN` is one year high on 167 policies, and `MCV1`/`MCV2` are blank on all 400 — so QLAdmin **will** rebuild, using `q(x+t)` at an age understated by roughly 25 years. Cash values and reserves on the whole NFO book are unreliable until 108B lands.

Separately, the `MSAVE*` fields are populated with post-NFO values, which would make a future reinstatement restore the policy to its ETI/RPU state.

Two findings changed shape under investigation and are **not** what they first appeared:

- The 82 "riders still in force on NFO policies" are really **77 `1SALMI` rows that carry the entire face amount** (their `1SALML` phase-1 base has zero units) plus **5 genuine leftovers on 4 policies**. Applying Robert's rule mechanically would zero out 77 RPU policies.
- `MNFOPT` is not merely mis-derived; the PPBENTYP election enrichment is **completely inert**, and so is the `MDIVOPT` enrichment that shares its code path. Root cause is a one-character policy-key mismatch.

**Direction:** proceed with 108A–108D and 108G; hold 108E for SME confirmation; hold 108F for the key-convention decision.

---

## 2. Confirmed LifePRO Source Table(s)

| Source table | File | In `Source/`? | Rows |
|---|---|---|---:|
| PPOLC Policy Master | `PPOLC_PolicyMaster_Extract_20260630.csv` | Yes | ~5.1k |
| PPBEN Policy Benefit | `PPBEN_PolicyBenefit_Extract_20260630.csv` | Yes | ~7k |
| PPBENTYP Benefit Type | `PPBENTYP_BenefitType_Extract_20260630.csv` | Yes | 7,003 |

> `PPOLC_PolicyMaster_Extract_20260630.csv` is not UTF-8 decodable (byte `0xFF` at offset 740). Read with `encoding='latin-1'` or `errors='replace'`. Not a blocker; noted so Development does not trip on it.

### Source fields relevant to this issue

| Field | Source | Populated | Notes |
|---|---|---|---|
| `CONTRACT_CODE`, `CONTRACT_REASON`, `PAID_UP_TYPE` | PPOLC | Yes | Feed the `MSTATUS` composite key |
| `PAID_TO_DATE` → `MPAIDTO` | PPOLC | 400 of 400 on NFO policies | **Date of nonforfeiture** — the anchor for 108B |
| `NON_FORFEITURE` | PPBENTYP | 2,583 non-blank | `4`=ETI (1,383), `3`=APL (106), `5`=RPU (61) |
| `BF_NON_FORFEITURE` | PPBENTYP | 2,348 non-blank | ISWL/BF rows (Issue #21A) |
| `STATUS_CODE` | PPBEN | Yes | Feeds `MPHSTAT` |
| `ISSUE_AGE` → `MAGE` | PPBEN | Yes | Current source of the 108B defect |
| `MATURE_EXPIRE_DATE` → `MEXPRY` | PPBEN | Yes | Passthrough; 108E question |

**Distinct policies with an NFO election in PPBENTYP: 4,346.**

### Derivability of `MAGE` (the 108B enabler)

Both inputs are complete on the affected population — no source gap:

| Input | Coverage on 400 NFO policies |
|---|---|
| `quikmstr.MPAIDTO` (date of nonforfeiture) | 400 of 400 populated |
| `quikridr.MPHDOB` (phase-1 date of birth) | 400 of 400 populated |

Attained age is therefore fully computable in-converter.

---

## 3. Confirmed QLAdmin Target Structure

Per `QLAdmin_ETI_RPU.docx` and the two worked examples. Field names below are as they appear in `quikridr.csv`; note the document writes `MCVO` where the schema field is **`MCV0`**.

| Table | Field | Spec behaviour at ETI (44) | Spec behaviour at RPU (45) |
|---|---|---|---|
| quikmstr | `MSTATUS` | 44 | 45 |
| quikmstr | `MSTATDATE` | status change date | status change date |
| quikridr ph1 | `MPHSTAT` | 44 | 45 |
| quikridr ph1 | `MLASTANN` | 0 at event; increments each NFO anniversary | same |
| quikridr ph1 | `MEXPRY` | **recalculated ETI expiry** | **unchanged** |
| quikridr ph1 | `MPAYUP` | paid-to date | paid-to date |
| quikridr ph1 | `MAGE` | attained age at paid-to | attained age at paid-to |
| quikridr ph1 | `MUNIT` | base + PUA units (additive) | calculated reduced amount from (base + PUA) |
| quikridr ph1 | `MPREM` | **0.00** | **unchanged** (see Q4) |
| quikridr ph1 | `MCV0/1/2` | recalculated | recalculated |
| quikridr ph1 | `MSAVEAGE/UNIT/VPU/PREM/STAT` | **pre-NFO values** | **pre-NFO values** |
| quikridr ph2+ | `MPHSTAT` | 54 | 54 |
| quikloan | — | balance extinguished into NFO calc | same |
| quikdvdp / quikdvpr | — | accumulations extinguished | same |

### Worked example arithmetic (policy `010367133C`, from client workbooks)

| Field | Active | ETI | RPU |
|---|---|---|---|
| ph1 `MPHSTAT` | 22 | 44 | 45 |
| ph1 `MLASTANN` | 55 | 0 | 0 |
| ph1 `MEXPRY` | 2063-08-01 | **2047-07-28** | 2063-08-01 |
| ph1 `MPAYUP` | 2048-08-01 | 2026-02-01 | 2026-02-01 |
| ph1 `MAGE` | 7 | **62** | **62** |
| ph1 `MUNIT` | 4.976 | **9.22949** (= 4.976 + 4.25349) | **8.668** (calculated) |
| ph1 `MPREM` | 9.96 | **0** | 9.96 |
| ph1 `MSAVESTAT` | blank | **22** | **22** |
| ph1 `MSAVEUNIT` | blank | **4.976** | **4.976** |
| ph2 `1708PA` `MPHSTAT` | 41 | **54** | **54** |

The ETI unit fold is confirmed additive: 4.976 + 4.25349 = 9.22949 exactly.

**Note for the client reply:** in the RPU workbook Robert leaves `MNFOPT` = 2 (ETI) alongside `MSTATUS` = 45. That is the exact combination Issue #72 currently overwrites, and it supports treating the match as a warning rather than a force.

### Repo references (population paths)

| Location | Role |
|---|---|
| `app.py:7624–7654` | `MSTATUS` composite key interceptor (#13), incl. hardcoded 7-policy allowlist (#59) |
| `app.py:7851–7854` | `ST_`/`NF_` prefixed translation lookup |
| `app.py:7688–7705` | PPBENTYP `MNFOPT`/`MDIVOPT` enrich-on-zero — **inert, see §5** |
| `app.py:7856–7884` | Issue #49 `MSTATUS` override from first active later phase |
| `app.py:8121–8176` | Phase-1 `MPHSTAT` forced to inherit `MSTATUS` |
| `app.py:3080–3107` | Issue #60 PUA `MPHSTAT` → 41 when base < 50 |
| `app.py:5503–5519` | Issue #72 `MNFOPT` forced from `MSTATUS` |
| `app.py:5536–5547` | v57.96 `MSAVE*` mirror of live fields |
| `app.py:5551–5564` | Issue #76 phase-1 `MPAYUP`/`MLASTANN` on 44/45 |
| `app.py:5251–5267` | `_compute_quikridr_mlastann` — calendar-year duration |
| `Master_Value_Translation.csv` | `ST_PUT_ET`→44, `ST_PUT_RU`→45, `NF_4`→2, `NF_5`→3 |

---

## 4. Required Source-to-Target Mapping (proposed)

| Track | Target | Current | Proposed | Change? |
|---|---|---|---|---|
| 108A | ph1 `MSAVE*` on 44/45 | mirror of live (post-NFO) values | **blank** | Yes |
| 108B | ph1 `MAGE` on 44/45 | `PPBEN.ISSUE_AGE` | attained age at `MPAIDTO` from `MPHDOB` | Yes |
| 108B | ph1 `MLASTANN` on 44/45 | `now().year − payup_year` | anniversary-accurate NFO duration vs **valuation date** | Yes |
| 108C | ph1 `MPREM` on 44 only | `ANN_PREM_PER_UNIT` | `0.00` | Yes |
| 108D | PUA `MPHSTAT` when base is 44/45 | `41` (#60) | `54` | Yes |
| 108F | `MNFOPT` | inert enrichment + #72 force | fix key join; downgrade #72 to warning | Yes |
| 108G | governance | none | new cross-table DG item | Yes (new) |

### Fields that must remain unchanged

| Target | Current source | Touch this issue? |
|---|---|---|
| `quikmstr.MSTATUS` | `ST_*` crosswalk | **No** — codes are correct |
| `quikmstr.MMODPREM` | `PPOLC.MODE_PREMIUM` | **No** |
| `quikridr.MPREM` on RPU and on all non-NFO | `ANN_PREM_PER_UNIT` (#26) | **No** |
| `quikridr.MAGE` on all non-NFO phases | `ISSUE_AGE` | **No** |
| `quikridr.MEXPRY` | `MATURE_EXPIRE_DATE` | **No** — 108E is a source question, not a code change |
| `quikridr.MUNIT` | `NUMBER_OF_UNITS` (#55 floor) | **No** — pending Q1 |
| `MPOLICY` padding | `format_qladmin_mpolicy()` (#25) | **No** |
| PUA `MPHSTAT` = 41 when base < 44 | Issue #60 | **No** — only the 44/45 window changes |
| Phase 2+ `MPHSTAT` generally | `PPBEN.STATUS_CODE` | **No** — no cascade |

---

## 5. Track 108F — why `MNFOPT` is empty

`app.py:7688–7705` enriches `MNFOPT`/`MDIVOPT` from the PPBENTYP cache when the mapped value is `0`:

```
pol_id     = normalize(row_data['MPOLICY'])          # '9010143726C'
legacy_id  = reverse_cw_map.get(pol_id, pol_id)      # miss -> '9010143726C'
pulled_val = lifepro_extra['NON_FORFEITURE'].get(legacy_id)   # cache keyed '9010143726'
```

Key shapes in the batch under test:

| Key | Example | Length |
|---|---|---|
| `quikmstr.MPOLICY` | `9010143726C` | 11 (4,954 of 5,083) |
| `Master_Crosswalk.csv` `Old_Value` | `9010143726` | 10 |
| `Master_Crosswalk.csv` `New_Value` | `010143726C` | 10 |
| `PPBENTYP.POLICY_NUMBER` | `9010143726` | 10 |

Set overlap of `MPOLICY` against crosswalk `New_Value`: **0**. Against `Old_Value`: **0**. Against `Old_Value + "C"`: **5,083 of 5,083**.

So `reverse_cw_map` misses, `legacy_id` falls back to the suffixed key, and both cache lookups fail. Confirmed by outcome: **`MDIVOPT` = 0 on all 5,083 policies** and every non-zero `MNFOPT` in the Output is exactly attributable to the Issue #72 force (206 twos = 206 ETI policies; 194 threes = 194 RPU policies).

### Root cause — confirmed (revised 2026-07-25)

> An earlier draft of this section treated the key convention as unresolved and blocked 108F pending a re-batch. It was settled by inspection instead. **Correction:** the 11-character keys do **not** violate Issue #25. Issue #25 is formally superseded.

Issue **#2** ("11 Character Policy Number", closed 2026-07-23 at **v58.29**) deliberately replaced the strip-9 crosswalk with source + trailing `C` at width 11:

```
qla_core/normalize_utils.py:23–46
"Issue #2: keep source policy number, append C, right-justify to 11 characters.
 Supersedes Issue #25 (10-char pad after strip-9 crosswalk)."
```

The Output under test is therefore a valid v58.29+ batch, and `Master_Crosswalk.csv` `New_Value` is the retired convention. Issue #2 realigned the identity paths it knew about but missed two that still resolve through the retired columns:

| Path | Location | Live keys resolved |
|---|---|---:|
| `reverse_cw_map` → PPBENTYP `MNFOPT`/`MDIVOPT` enrichment | built `app.py:6118`, consumed `app.py:7695` | **0 of 5,083** |
| `cw_map` → Issue #71 phase-1 provisional status cache | `app.py:7867` | **0 of 5,194** |

The second double-appends the suffix (`9010143726` → `010143726C` → `010143726CC`), producing a key that exists nowhere in the Output. **Consequence: Issue #71's fix is inert and phase-1 `MPHSTAT` inherits the post-#49 status — raise separately, not part of #108.**

**108F is a confirmed code defect and a bounded regression from Issue #2 v58.29.** `reverse_cw_map` has exactly one consumer, so the blast radius is three fields.

### Exact sizing (exact-key join, `MPOLICY` minus trailing `C`)

Election vs emitted value across the 4,346 matched policies:

| Source election | Emitted 0 | Emitted 2 | Emitted 3 |
|---|---:|---:|---:|
| APL (1) | 1,878 | 12 | 55 |
| ETI (2) | 2,184 | 108 | 44 |
| RPU (3) | 50 | 0 | 15 |

- **4,112 `MNFOPT` values** would be populated by the fix.
- **1,933 of 1,933 in-force policies** (`MSTATUS` < 44) hold a source election and emit `MNFOPT` = 0.
- **111 of 234 NFO policies** have an election that disagrees with the #72-forced value. These are precisely the population Robert asks us to flag and confirm against the source; today they are overwritten silently, and his proposed check returns 0 by construction.

**Fix direction:** key the PPBENTYP cache off `src_row['POLICY_NUMBER']` directly rather than through `reverse_cw_map`. Retiring or regenerating `Master_Crosswalk.csv` `New_Value` is separate cleanup.

---

## 6. Formatting / fallback rules

| Rule | Recommendation |
|---|---|
| Attained age | `MPAIDTO` year − `MPHDOB` year, less 1 if (month, day) not yet reached. Emit zero-padded to current `MAGE` width |
| NFO duration | Same anniversary convention against the **batch valuation date**, never `datetime.now()` |
| `MSAVE*` on 44/45 | Blank. Do **not** zero-fill — the RPU workbook shows `0` on the terminated PUA row and blank on the ETI one; blank is the safer conversion default per Robert |
| `MPREM` zero | Emit using the existing `quikridr` decimal emit path so formatting matches neighbouring rows |
| Missing `MPHDOB` or `MPAIDTO` | Leave `MAGE` at current value and raise a governance finding. Zero occurrences today |

---

## 7. Special handling

`MLASTANN` deserves an explicit note because it reads as a discrepancy and is not one. Robert's spec sets it to **0** at the instant the ETI/RPU transaction is processed. Our policies converted **already on NFO**, sometimes for decades, and QLAdmin increments the counter each NFO anniversary. Issue #76's "duration since nonforfeiture" is therefore the correct conversion concept. Only the arithmetic is wrong (calendar-year subtraction, and `now()` instead of the valuation date). Do not "fix" this to 0.

---

## 8. Policy key handling

Current identity per Issue **#2** (v58.29): normalize source `POLICY_NUMBER`, append `C`, right-justify to 11 via `format_qladmin_mpolicy()`. The policy crosswalk is **bypassed** for `MPOLICY`. Issue #25's width-10 strip-9 contract is superseded.

108A–108D operate entirely within a single `quikridr` row plus the `quikmstr` status/paid-to cache, both keyed on the emitted `MPOLICY`, so they are unaffected. 108F must use `src_row['POLICY_NUMBER']` as the PPBENTYP cache key and must **not** reintroduce `reverse_cw_map`.

---

## 9. Estimated record counts

| Track | Rows changed | Policies |
|---|---:|---:|
| 108A `MSAVE*` blanked | 400 | 400 |
| 108B `MAGE` corrected | 400 | 400 |
| 108B `MLASTANN` corrected | 167 | 167 |
| 108C ETI `MPREM` → 0 | 204 | 204 |
| 108D PUA 41 → 54 | 27 | 27 |
| 108E rider terminations | 5 (pending SME) | 4 |
| 108F `MNFOPT` populated | up to 1,933 | up to 1,933 |
| **Total `quikridr` rows touched (A–D)** | **≤ 427 of 6,934 (6.2%)** | |

---

## 10. Sample Trace (5 policies)

**`9010391355C`** — ETI, `MPAIDTO` 2009-12-01, base `17085M` + PUA `1708PA`

| Field | Before | Proposed |
|---|---|---|
| ph1 `MAGE` | `13` | `51` |
| ph1 `MLASTANN` | `17` | `16` |
| ph1 `MPREM` | `11.64000` | `0` |
| ph1 `MSAVESTAT` / `MSAVEUNIT` / `MSAVEPREM` | `44` / `13.71152` / `11.64000` | blank / blank / blank |
| ph2 `1708PA` `MPHSTAT` | `41` | `54` |
| ph1 `MUNIT` | `13.71152` | unchanged pending **Q1** (spec fold would give 18.01104) |

**`9010407670C`** — RPU, `MPAIDTO` 2012-10-01, base `170858` + PUA `1708PA`. Robert's own #72 sample.

| Field | Before | Proposed |
|---|---|---|
| ph1 `MAGE` | `33` | `73` |
| ph1 `MLASTANN` | `14` | `13` |
| ph1 `MSAVESTAT` | `45` | blank |
| ph2 `1708PA` `MPHSTAT` | `41` | `54` |
| `MNFOPT` | `3` (forced) | source election = ETI → **governance warning**, not overwrite |

**`9010149295C`** — ETI, `MPAIDTO` 1992-12-01, single phase `221END`

| Field | Before | Proposed |
|---|---|---|
| ph1 `MAGE` | `20` | `51` |
| ph1 `MLASTANN` | `34` | `33` (NFO anniversary falls in December; not yet reached) |
| ph1 `MSAVESTAT` | `44` | blank |

**`9018313AC`** — RPU, worst `MAGE` gap in the book

| Field | Before | Proposed |
|---|---|---|
| ph1 `MAGE` | `10` | `65` (gap of 55 years) |
| ph1 `MLASTANN` | `19` | `19` (unchanged — anniversary already passed) |
| ph2 `1SALMI` `MPHSTAT` | `22` | **unchanged** — see 108E |

**`9010820645C`** — ETI, base `5667AT`, genuine rider leftover

| Field | Before | Proposed |
|---|---|---|
| ph1 `MAGE` | `19` | attained at `MPAIDTO` |
| ph2 `9595WP` `MPHSTAT` | `22` | `54` **pending SME confirmation** |

---

## 11. Risks and Unknowns

| Risk | Severity | Mitigation |
|---|---|---|
| Mechanically applying "terminate all phases 2+" would zero the face on 77 RPU policies where `1SALMI` carries the insurance | **Critical** | Exclude `1SALML`/`1SALMI` from any termination rule; 108E is SME-gated, never automatic |
| Correcting `MAGE` changes QLAdmin's CV rebuild on 400 policies — reserves will move | High | Intended correction, not drift. Quantify with Robert before UAT reload; Validation must compare rebuilt CVs |
| `MAGE` is also consumed by `_derive_mphdob_from_issue_age` (`app.py:5325`) | High | Scope the change to phase-1 rows on 44/45 **after** `MPHDOB` derivation, or `MPHDOB` will be corrupted |
| Issue #60 validator baselines phase-1 against v57.85 and predates #76 | Medium | 108D requires amending `validate_issue60_pua_phase.py`, not just re-running it |
| Issue #72 validator asserts the force that 108F removes | Medium | `validate_issue72_mnfopt_status.py` must be rewritten as a warning check; #72 is still "Ready for Validation" so no closed gate is broken |
| `MSAVE*` blanking could trip a DBF not-null expectation | Medium | Verify against `quikridr` schema before emit; blank is already the rulebook default |
| 108F depends on an unresolved key convention | High | Gated at Dependency Gate; do not implement on the current Output |
| ETI `MUNIT` fold may double-count if LifePRO already folded PUA into the base | High | **Q1** — do not implement the fold until answered |

---

## 12. Dependency Gate Preview

| Check | Met? |
|---|---|
| Source files present | Yes |
| Target field semantics confirmed | Yes — client docx + two worked examples |
| Example policies available | Yes — client sample plus 5 traces above |
| Before-state measurable | Yes — all tracks (108F sized exactly once the Issue #2 key rule was confirmed) |
| Client scope clear | **Partial** — 4 open questions |

---

## 13. Recommended Risk Agent Prompt

```
Risk Agent — Issue #108: Statuses and NFO (ETI/RPU) conversion conformance

Read AI_Agents/Risk_Agent.md, Templates/Risk_Report_Template.md, and
Issue_Log_Items/Issue_108/Issue_108_Planning_Report.md.

Read-only before/after simulation on QLA_Migration/Output/. Do NOT change
app.py, rulebooks, or Master_Value_Translation.csv.

Quantify per track (108A-108G): rows changed, rows unchanged, blast radius
outside the 400 NFO policies, and regression surface against #25, #26, #55,
#60, #72, #76.

Issue a per-track Go / Conditional Go / No-Go.
```

---

## 14. Recommended Development Task (do not implement)

Sequenced so each step is independently validatable and rollback-safe.

1. **108B first** — it is the prerequisite for any CV comparison. Add an NFO phase-1 hook that sets `MAGE` to the attained age at `MPAIDTO`, and correct `_apply_issue76_eti_rpu_phase1_payup_mlastann` to use an anniversary-accurate duration against the batch valuation date. Must run **after** `MPHDOB` derivation.
2. **108A** — in `_apply_quikridr_v5796_defaults`, skip the `MSAVE*` mirror when phase-1 policy status is 44/45; leave blank.
3. **108C** — zero `MPREM` on phase-1 rows where policy status is 44 only. Do not touch 45.
4. **108D** — in `_apply_pua_rider_inheritance`, carve 44/45 out of the `< 50` window and set `MPHSTAT` = 54. Do not attempt the units fold (gated on Q1).
5. **108F** — repoint the PPBENTYP `MNFOPT`/`MDIVOPT` enrichment at `app.py:7688–7705` to key off `src_row['POLICY_NUMBER']`; drop the `reverse_cw_map` hop. Then downgrade Issue #72 from a force to a governance warning so the 111 disagreements surface. Populates 4,112 `MNFOPT` values.
6. **108G** — new data governance item with Robert's four checks plus an NFO field-completeness check. `1SALML`/`1SALMI` excluded from the phase-2+ rule with a documented reason.
7. **108E** — no code until SME answers.

Do **not** change: `MSTATUS` derivation, the `ST_*` crosswalk, `MEXPRY`, `MUNIT`, RPU `MPREM`, non-NFO `MAGE`, `MPOLICY` padding, or phase-2+ `MPHSTAT` outside PUA.

Version bump: **v58.32** in **both** `app.py` and `QLA_Migration/app.py`.
Validator: `tools/validators/validate_issue108_nfo_conformance.py`.
Amend: `validate_issue60_pua_phase.py`, `validate_issue72_mnfopt_status.py`.

---

## 15. Open Client / SME Questions

1. **PUA units fold (Q1).** For a policy already on ETI/RPU in LifePRO, does `PPBEN.NUMBER_OF_UNITS` on the base phase already reflect the folded (ETI) or reduced (RPU) amount? Trace `9010391355C`: base `17085M` 13.71152 + PUA `1708PA` 4.29952. If LifePRO has already folded, we must **not** add again.
2. **`1SALML` / `1SALMI` structure.** 147 of 152 `1SALML` phase-1 rows carry **zero units**, with the face on phase-2 `1SALMI`; 77 of those policies are RPU. Is this the intended product shape, or is the phase structure itself wrong? This determines whether 77 policies are a false positive on Robert's check 2b or a separate structural defect.
3. **Genuine rider leftovers.** 4 ETI policies on base `5667AT` retain in-force `9595WP` (waiver) and `967ADB` (accidental death) riders: `9010779553C`, `9010820645C`, `9011001302C`, `9011136641C`. Note `9010779553C` has `9595WP` at 56 but `967ADB` at 22 — inconsistent within one policy. Confirm these should terminate at 54.
4. **ETI `MEXPRY`.** 92 of 206 ETI policies have an expiry at attained age ≥ 95, which looks like the original maturity rather than a calculated ETI expiry (the other 112 are below 90 and look correct). Source-data question — we pass `MATURE_EXPIRE_DATE` through untouched.
5. **RPU `MPREM`.** The specification updates `MPREM` to 0.00 for ETI but is silent for RPU, and the RPU workbook retains 9.96. Intentional? A fully paid-up policy retaining a premium per unit is counter-intuitive.
6. **Save fields.** Robert suggested asking Greg how conversion handled `MSAVE*`. Blank is our recommendation; confirm before Development.

---

## Appendix

- Client specification: `docs/research/Conversion - Statuses, NFO/QLAdmin_ETI_RPU.docx`
- Worked examples: `Example_ETI.xlsx`, `Example_RPU.xlsx` (same folder)
- Related: #13, #21A, #44, #49, #57, #59, #60, #72, #76
- Governance catalog: `data_governance/docs/RULE_CATALOG.md` — `DG-QUIKMSTR` items 001–026, no cross-table status rule, no QuikRidr item
