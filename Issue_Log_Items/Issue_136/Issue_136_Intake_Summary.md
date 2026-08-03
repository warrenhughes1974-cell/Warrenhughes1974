# Issue #136 — Intake Summary

**Issue ID:** #136 (correction sub-package of Internal Issue A / A11)  
**Title:** PVO / category variance flags must reflect real rate variation only  
**Framework stage:** Intake  
**Opened:** 2026-08-02  
**Reporter:** Warren (UAT review after A11 Q deploy) / Robert original PVO theme  
**Owner:** Conversion  
**Track:** **Internal only**  
**Priority:** High — QLAdmin Plan Values Options misrepresents plan setup  
**Independent review:** Luna concurs with locked rule (2026-08-02)

---

## Client / operator symptom

On plan **1658C1** after A11 DBF deploy to `Q:\CSO\CSO_Test_6_30_2026`:

- Band shows `00` / NOT APPLICABLE but GP/DB/CV/TV/DV Band checkboxes are all selected
- No dividends loaded, yet DV checkboxes are selected (Gender / UW / Band)
- No individual states, yet Country/State ALL (OTHER) has GP/DB selected
- Gross Prems browse shows 6 Sex×UW keys with Band `00` / Cntry `0000` / State `00` — defaults presented as if they justify full variation

Warren: *We should only be creating variances if there is actually a variance. If we have a default rate loaded then there is nothing for that plan to have a variance on. This needs to apply to all plans.*

---

## Normalized symptom

Conversion still turns on QuikPlan category / `*VARY*` flags from **structural / default key presence** (and legacy Issue #77 “any real row ⇒ Band / STVARYGP”) instead of from **actual multi-value differentiation in loaded factor rates**. Result: UAT shows variance where none exists (Band, State, DV especially).

---

## Evidence (read-only, 2026-08-02)

### Test_Validation / deployed package — `1658C1`

| Field / table | Observed | Expected under locked #136 |
|---------------|----------|----------------------------|
| `PLANVALOPT` | Y | Y only if legitimate Gender/UW (etc.) remain after cleanup |
| `PAR` | 0 | 0 (correct — no DV factors) |
| `DEFICIENCY` | N | N (unchanged) |
| `BDVARYGP/DB/CV/TV/DV` | all Y | all **N** (only Band `00`) |
| `STVARYGP` | Y | **N** (only `0000`/`00`) |
| `GDVARYDV`, `BDVARYDV` | Y | **N** (`QuikDvs` rows = 0) |
| `GDVARYDB`, `BDVARYDB` | Y | **N** unless real DB factors exist (`QuikDbs` rows = 0 today) |
| `QuikGps` | 246 rows; Band `00` only; State `00`/`0000`; UW NS/PR/SM; Sex F/M | Gender/UW GP may stay Y if factors differ |
| `QuikCvs` / `QuikTvs` | real F/M × UW; Band/State defaults only | Gender/UW may stay Y; Band/State N |
| `QuikDvs` | **0** rows | No DV flags |
| `QuikDbs` | **0** rows | No DB flags |
| `QuikPlBd` | 1 structural row | Must not enable Band checkboxes |
| `QuikPlSt` | 1 row State `00` / Cntry `0000` | Must not enable State checkboxes |

### Code root cause (intake — not a fix)

| Location | Behavior conflicting with #136 |
|----------|--------------------------------|
| `qla_core/quikplan_rate_variation_flags.py` → `derive_plan_flags()` | Sets `BDVARY*=Y` for any real family row (incl. Band `00` only); sets `STVARYGP=Y` for any real GP presence |
| Same file → `apply_factor_table_pvo_enablement()` (Issue #96) | Forces `PLANVALOPT` + `GDVARYCV/TV` + `BDVARYCV/TV` from mere QuikCvs/QuikTvs row presence |
| Issue #77 historical lock | Explicitly allowed Band-on-presence and STVARYGP-on-GP-presence — **superseded** by #136 for Band/State |

Default stubs alone are already excluded via `real_row_count == 0`, but **real factor rows that only use default Band/State** still light Band/State flags.

---

## Suspected domain

**Primary:** QuikPlan PVO / variation flag enrichment (`quikplan_rate_variation_flags.py`)  
**Secondary:** Issue #96 factor-table enablement path; checklist A6 (category settings match keys)  
**Not primary:** Rate key emit structure (default keys may remain); claims; policy tables

---

## In scope

1. Lock and implement real-rate-only variance for Gender / UW / Band / State / DV per family
2. Fleet-wide correction for all plans in `quikplan.csv`
3. Supersede Issue #77 Band/STVARYGP presence rules
4. Align Issue #96 enablement so it does not force Band (or Gender) without real differentiation
5. Validation + UAT gold: **1658C1** Band/DV/State off; no invented DB/DV without factors
6. Preserve prior A11: default keys for structure; independent CV/TV UW collapse; PAR from real DV; DEFICIENCY=N; LOANINTX

## Out of scope

- Claims (`quikclms` / `quikclmp`)
- Redesign of rate factor generation / GP key matrix itself
- A7 `VARGP=4` structure codes (separate OPEN item)
- A5 blank BASIS / Valuation_Setup
- Removing TESTRD-style default keys from plans that need them

---

## Acceptance criteria

See `Issue_#136_Locked_Acceptance_Criteria.md` (Warren + Luna locked).

---

## Dependencies / unknowns for Planning

- Confirm Gender/UW for 1658C1 GP/CV/TV against factor **value** equality (keys alone insufficient — Luna)
- Confirm whether any plans have genuine multi-band or multi-state rates in extracts (expected rare)
- Confirm Issue #96 QLAdmin requirement: can CV/TV factor tables be used with `PLANVALOPT=Y` driven only by legitimate Gender/UW without forcing Band?
- Whether DB flags for 1658C1 come from PAAGERAT / key stubs vs a separate enrichment path

---

## Handoff to Planning

Plan a surgical change to `derive_plan_flags` (+ Issue #96 path) so Band/State require multi-value real differentiation; DV/DB require real family factors; preserve Gender/UW multi-value; fleet validate with 1658C1 as primary gold.