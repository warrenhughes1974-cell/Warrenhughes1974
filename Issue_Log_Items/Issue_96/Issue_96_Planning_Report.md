# Issue #96 — Planning Report

**Issue:** #96 — CSO valuation cannot use SAL MULTPL / L17 RV rates (PVO + QuikPl* wiring)  
**Framework stage:** Planning Agent  
**Status:** Planning → Dependency Gate  
**Generated:** 2026-07-22  
**Agent:** Planning Agent (Cursor Grok 4.5)  
**Code changes:** None (Planning)

---

## 1. Executive Finding

**RV factor grids are already in Output.** Eric’s LifePRO pointing is implemented for Track 1 QuikTvs:

| Plan | QuikTvs | Grid source |
|------|--------:|-------------|
| `1SALOL` / `1SALMI` / `1SALML` | 508 each | SAL OL (MI/ML inherited) |
| `1L17SP` + four L17 children | 38 each | L17 parent; children match `1L17SP` |

The valuation needle did not move because QLAdmin **plan valuation options and assumption keys** blocked use of those tables:

| Defect | Plans | Effect |
|--------|-------|--------|
| `PLANVALOPT=N` / blank TV vary flags | `10L171`, `10L172`, `117JPO` | TV tables ignored |
| `GDVARYTV/CV=N` | `1SALMI` | Rates present but not selected |
| Blank / incomplete QuikPlTv + QuikPlCv | `1SALMI` | No usable CSO assumption codes |

**Recommended Development direction (surgical):**

1. After non-CV inheritance + CSO key emit, **re-derive / force** quikplan PVO so any plan with emitted QuikTvs (or QuikPlTv) has `PLANVALOPT=Y` and TV family vary flags consistent with #77 + presence of TV rates (`GDVARYTV=Y` when TV factors exist — not only when gender count > 1).
2. When inheriting RV (and for SAL, CV) onto `1SALMI` from `1SALOL`, **also inherit QuikPlTv / QuikPlCv assumption codes** (MORT/RSVINT/… and MORT/ETIMORT/NFOINT/…) from the source plan — do not leave blank stubs.
3. Ensure full-batch emit order: inherit factors → emit Pl* keys → **then** R7B PVO apply (so flags see final rates).
4. Keep Track 2 holds (L01/L05/L07/667 ART) out of scope.

A 2026-07-22 Output/load-package patch already mirrors the desired end state for UAT. Development must make the converter produce that state so the next full batch does not regress.

---

## 2. Confirmed LifePRO Source(s)

| Source | Role | Evidence |
|--------|------|----------|
| PCOVRSGT / segment refs | SAL MULTPL RV → SAL OL; L17* RV → L17 | Issue #42 segment evidence; Eric 7/22 note |
| Rate_Table / PDAGE (RV) | Factor grids for SAL OL and L17 | PDAGE extract; `1L17SP` / `1SALOL` QuikTvs |
| `approved_first_pass_scope.csv` | Manifest Yes rows for `1SALMI`/`1SALML`←`1SALOL` RV; L17 children←`1L17SP` RV | Rates Inheritance folder |

No new LifePRO extract is required for Track 1.

---

## 3. Confirmed QLAdmin Target Structure

| Table | Fields | Role |
|-------|--------|------|
| **QuikTvs** | PLAN, AGE, CNTL, TVn, GENDER, UWCLASS, BAND, … | RV factors (already correct) |
| **QuikPlTv** | PLAN, GENDER, …, MORT, RSVINT, RSVMETH, INTMETHTV, STOREMEANS, CALCMIDS | Reserve key / assumptions |
| **QuikPlCv** | PLAN, GENDER, …, MORT, ETIMORT, NFOINT, INTMETHCV | CV key / assumptions (SAL) |
| **quikplan** | PLANVALOPT, GDVARYTV, GDVARYCV, GDVARYGP, GDVARYDB, BDVARY*, UW*, ST* | Enables valuation options |
| Member tables | QuikPlGd / Uw / Bd / St / Nb | Key dimensions |

Help / prior issues: #77 (PVO), #80 (CSO coded assumptions), #42 (L17 parent load).

---

## 4. Proposed Source-to-Target Mapping / Engine Changes

| # | Change | Location (likely) | Notes |
|---|--------|-------------------|-------|
| 1 | Re-run or extend PVO derivation **after** inherited QuikTvs/PlTv/PlCv exist | `qla_core/quikplan_rate_variation_flags.py` + `rate_pipeline.py` / quikplan post-process | Today `GDVARYTV` sets Y mainly when `len(genders)>1`; TV-only single-gender plans can still need PLANVALOPT=Y via BDVARYTV — verify emit order first |
| 2 | For plans with QuikTvs rows > 0: ensure `PLANVALOPT=Y` and `GDVARYTV=Y` (and BDVARYTV as #77) | Same | Matches UAT patch / load package |
| 3 | `1SALMI` QuikPlTv + QuikPlCv copy assumption codes from `1SALOL` when inheriting | `cso_valuation_setup.py` and/or non_cv inheritance / rate_key_setup | Blank stub is the CV/TV setup gap |
| 4 | L17 children already have PlTv/PlCv A1/A codes from #80 — keep; only fix PVO if batch regresses | — | Do not invent NP for L17 children (Track 1 was RV only) |
| 5 | Validator | Extend or keep `validate_l17_rv_inheritance_v5825.py` + add PVO/PlCv checks | Gate Val+Reg |

### Fields that must remain unchanged

| Target | Why |
|--------|-----|
| Issue #25 MPOLICY | Plan-level rates only |
| Issue #26 / #88 MPREM | Out of touch set |
| QuikTvs factor values for SAL OL / L17 parent | Already correct; inheritance grid equality |
| Annuity A* PVO rules (Issue A A8e) | Do not force PLANVALOPT=Y on annuities |
| Track 2 zero-RV plans | Explicit hold |

---

## 5. Open Client Questions

| # | Question | Blocking? |
|---|----------|:---------:|
| Q1 | Confirm UAT pass = ValxLife/QLR reserve **non-zero** (or closer) on SAL MULTPL + L17 sample policies after reload | No for Dev design; Yes for Closure |
| Q2 | Track 2 (L01/L05/L07/667 ART) remains held until actuarial? | No — already agreed Eric |

No new Eric scope questions for Track 1 — pointing already approved.

---

## 6. Formatting / Fallback Rules

| Rule | Value |
|------|-------|
| Inherit PlTv codes for `1SALMI` | From `1SALOL`: MORT=`O1`, RSVINT=`4`, RSVMETH=`1`, INTMETHTV=`0`, STOREMEANS=`N`, CALCMIDS=`N`; both M/F |
| Inherit PlCv codes for `1SALMI` | From `1SALOL`: MORT=`O1`, ETIMORT=`Q1`, NFOINT=`4`, INTMETHCV=`0`; both M/F |
| L17 PlTv/PlCv | Keep #80 codes (A1 / A / C1) on parent + children |
| PVO when QuikTvs present | `PLANVALOPT=Y`, `GDVARYTV=Y` (and CV vary Y when QuikCvs present for SAL) |
| Do not invent factors | Values=N companions only if #83 rules already apply |

---

## 7. Policy Key Handling

Plan-level only. No MPOLICY / crosswalk change. Preserve #25 padding on any future policy traces.

---

## 8. Estimated Record Counts

| Artifact | Count |
|----------|------:|
| QuikTvs SAL family | 508 × 3 |
| QuikTvs L17 family | 38 × 5 |
| QuikPlTv focus plans | 2 × 8 |
| QuikPlCv focus plans | 2 × 8 (after `1SALMI` fix) |
| quikplan rows touched | 4–8 plans (PVO flags) |
| Reserve-gap SAL/L17 QLA_ZERO (pre-fix) | ~111 rows in analysis CSV |

---

## 9. Sample Trace (≥3)

| Policy (Valx/LP) | Plan | Before (pre-patch batch) | Desired after durable emit |
|------------------|------|--------------------------|----------------------------|
| `901ML8307` | `1SALMI` | QuikTvs present; PlCv blank; GDVARYTV=N; QLA reserve 0 | PlCv/Tv = SAL OL codes; GDVARYTV=Y; valuation can compute reserve |
| `9011258158` | `10L171` | QuikTvs=38; PLANVALOPT=N | PLANVALOPT=Y, GDVARYTV=Y; reserve path open |
| `9011227611` | `117JPO` | QuikTvs=38; PLANVALOPT=N | same |

---

## 10. Risks and Unknowns

| Risk | Mitigation |
|------|------------|
| Full batch overwrites UAT Output patch | Dev must fix emit; Val against full Output |
| #77 gender rule alone insufficient for GDVARYTV | Explicit “TV factors present ⇒ GDVARYTV=Y” or ensure BDVARYTV drives PLANVALOPT and QLAdmin still uses TV |
| Forcing GDVARYTV=Y on single-gender plans | Confirm QLAdmin accepts (matches load package UAT intent) |
| Issue A annuity PVO | Scope guard: only life SAL/L17 (+ plans with QuikTvs from this track) |
| Ordering bugs | Document pipeline step order in Dev notes |

---

## 11. Recommended Risk Agent Prompt

```
Proceed to Risk Agent for Issue #96.

Scope: Durable conversion emit so SAL MULTPL (1SALMI) and L17 children
(10L171/10L172/117JPO/17MJPO) can use already-inherited QuikTvs in CSO valuation:
fix quikplan PLANVALOPT/GDVARYTV (and SAL CV vary), inherit 1SALMI QuikPlTv/QuikPlCv
from 1SALOL, preserve L17 Pl* codes, preserve Track 2 hold.

Quantify: plans touched, reserve-gap population (~111 SAL/L17 QLA_ZERO),
regression surface (#77/#80/Issue A annuity PVO), Go/No-Go for Development on Composer 2.5.
```

---

## 12. Recommended Development Outline (for Risk)

1. Reproduce before-state from unpatched emit path (or document patch as temporary).
2. Surgical pipeline/PVO/`1SALMI` Pl* inheritance fix + APP_VERSION bump both `app.py` copies.
3. Validator: QuikTvs inheritance + PVO flags + PlTv/PlCv codes for eight plans.
4. Full or rates+quikplan rebatch; publish Test_Validation; user reloads QLAdmin + re-runs Life valuation QLRs.
