# R4 — QLAdmin V5 Rate Loader Architecture

**Scope:** architecture + planning only. No production DBFs, no final loaders, no overflow handling invented.
**Inputs validated in R1–R3** (crosswalk PLAN resolution, TYPE_CODE routing, SEX/BAND/UWCLASS crosswalks, DURATION→CNTL paging). **R4 confirms field capacity and overflow profile.**

---

## 0. Confirmed facts this architecture builds on

| Fact | Status | Evidence |
|---|---|---|
| Factor columns `xx0..xx9` are `Character(7)`, decimals=0 | CONFIRMED | DBF field descriptors, all 6 tables |
| Implied format is fixed 2-decimal text `"9999.99"` | CONFIRMED | 100% of ~7.3M populated cells use 2 dp; max 4 integer digits |
| Positive capacity ≤ 9999.99 ; negative magnitude ≤ 999.99 | CONFIRMED | sign consumes one of the 7 chars; negatives only in `QuikTvs` |
| Factor row key = PLAN+AGE+CNTL+GENDER+UWCLASS+BAND+ISSCNTRY+ISSUEST+EFFDATE | CONFIRMED (R2) | factor + key DBF layouts |
| `CNTL` = duration decade page; column = duration mod 10 | CONFIRMED (R2/R3) | self-check vs populated `QuikTvs` |
| `NP` reserve assumptions share the `QuikPlTv` key | CONFIRMED (business) | per business decision |
| Overflow isolated to 2 plans / 2 families | CONFIRMED (R4) | `2665ST` DB (1,333), `A96DAR` CV (300); all other families 0 |

---

## 1. Pipeline overview

```
LifePRO extracts ──► [1 STAGE] ──► [2 TRANSFORM] ──► [3 VALIDATE] ──► [4 EMIT (R5)]
 Rate_Table_Extract      normalize       crosswalks +        capacity +        rollback-safe
 PAAGERAT (attained)     + classify      duration paging     key + dup         DBF writer
 Policy Form Crosswalk                   + pivot to grid     + segmentation
```

Each stage is isolated, idempotent, and read-only with respect to its inputs. Outputs land in a phase-scoped staging directory, never over existing production data.

## 2. Staging process (`rate_factor_loader.py` — stage step)
- Read `Rate_Table_Extract_*.csv` (long format: COVERAGE_ID, TYPE_CODE, AGE, SEX, BAND, UWCLASS, DURATION, VALUE) and the attained-age `PAAGERAT_*` extract separately (different shape).
- Classify each row:
  - **in-scope** TYPE_CODE ∈ {PR, CV, DB, NP, DV, RV} → routed to its family.
  - **excluded** TYPE_CODE ∈ {NN, PN, TP, TX, UF, NF, SL} → inventoried, never converted.
- Persist a normalized staging table (one physical row per source factor) with provenance columns (source file, line number) for auditability/rollback.

## 3. Transformation process
- **PLAN**: `COVERAGE_ID → PLAN` via `Policy Form Crosswalk 5.22.26.xlsx` (col A → col C). Reject unresolved / spaced / synthetic plans (governance).
- **SEX**: F→F, M→M, J→J. **BAND**: 1→01, 2→02, 3→03 (zero-pad 2). **UWCLASS**: 0→00, N→NS, S→SM, P→PR, B→ST.
- **DURATION**: `QL_DURATION = SOURCE_DURATION − 1`; `CNTL = QL_DURATION // 10` (2-char), `column = QL_DURATION % 10`.
- **Pivot**: collapse long rows into the wide `xx0..xx9` grid keyed by (PLAN, AGE, CNTL, segmentation, EFFDATE). One emitted factor row carries up to 10 duration cells.
- **Segmentation defaults**: ISSCNTRY/ISSUEST/EFFDATE not present in source → require a business-supplied default (see open items) before emit; current placeholder `0000 / 00 / EFFDATE`.

## 4. Validation process (`rate_validation.py` + `rate_capacity_validator.py`)
- Driven by `rate_emit_validation_matrix.csv` (this phase). Every check is a hard gate before emit.
- **Capacity gate** (`rate_capacity_validator.py`): for every factor, `len(f"{value:.2f}") <= 7` (and negatives within −999.99). Any failure blocks the affected plan/family and is reported in `overflow_detail_report.csv`. **No silent truncation, no invented rescaling.**
- Duplicate-key detection, missing-factor detection, EFFDATE/AGE/CNTL validity, segmentation completeness.

## 5. Emit process (deferred to R5)
- Rollback-safe DBF writer: write to a staging path, validate, then atomic publish; never mutate existing DBFs in place.
- Emit factor tables (`Quikxxs`) and their rate-key tables (`QuikPlxx`) as a matched set (see `rate_key_generation_strategy.md`).
- Preserve exact field order/type/length and the confirmed 7-char 2-decimal factor format.

## 6. Recommended modules
| Module | Responsibility |
|---|---|
| `qla_core/rate_dbf_schema.py` | Canonical field order/type/length/format per table; single source of truth for the 7-char factor format and key layouts |
| `qla_core/rate_factor_loader.py` | Stage + transform + pivot LifePRO extracts into the QLAdmin grid |
| `qla_core/rate_key_setup.py` | Generate `QuikPlxx` rate-key rows + assumption fields (TV/CV) |
| `qla_core/rate_validation.py` | Run the validation matrix; produce pass/fail + exception reports |
| `qla_core/rate_capacity_validator.py` | Dedicated 7-char capacity / overflow gate |

These are **recommendations** for R5; no modules are created in R4.
