# Rate Loader Implementation Plan (V5) — Future Architecture

**This is a plan for a LATER phase. Nothing here is built in R2.** It is intentionally lightweight, isolated from
the stable claims/plan conversion, and grounded in the **confirmed physical DBF structures** in
`docs/plan_conversion_reference/`. **V5 only** — no V4 sharing logic.

---

## 1. Principles

- **Isolation:** a self-contained `rate_conversion/` tree + `qla_core` rate modules. **Zero edits** to the stable
  `app.py` claims/plan/product paths to load rates.
- **Keys before factors:** never emit a `QuikxxS` factor whose `(PLAN+segmentation+EFFDATE)` lacks a `QuikPlxx`
  key. (Orphan factors were observed even in QLAdmin's own data — do not reproduce them.)
- **Authoritative PLAN only:** every PLAN validated against the governed product catalog / P3C/P3E authority.
  Reject blank, spaced, synthetic, or non-authoritative plans at ingestion.
- **Config-driven**, mirroring the existing `Sync_Rulebook_*` rulebook pattern. No hardcoded factor logic.
- **Deterministic, replay-safe, rollback-safe**, matching platform norms.

---

## 2. Recommended modules

| Module | Responsibility |
|---|---|
| `qla_core/rate_dbf_schema.py` | Single source of truth for the **confirmed** physical layouts: field order, type, length, decimals for `QuikGps/Cvs/Dbs/Dvs/Nps` (19-field grid), `QuikPlGp/Db/Dv` (7-field key), `QuikPlCv` (11), `QuikPlTv` (13), `QuikPlGd` (3), `QuikPlNb` (5). Includes the `xxN`-duration mapping and C7 text-factor format. |
| `qla_core/rate_key_setup.py` | Build `QuikPlxx` key rows from authoritative PLAN + PVO members + VARY matrix; build/validate `QuikPlGd` gender members; attach CV/TV assumptions to `QuikPlCv`/`QuikPlTv`. |
| `qla_core/rate_factor_loader.py` | Normalize actuarial source → `QuikxxS` factor grids; page durations into `CNTL`/`xx0..xx9`; format factors to C7 text; one adapter per family. |
| `qla_core/rate_validation.py` | Referential, uniqueness, overflow, segmentation, and authoritative-PLAN validation (see §5). |
| `qla_core/rate_dbf_writer.py` | (later) deterministic DBF emitter honoring exact field order/type/length; isolated output tree; no production authorization in early phases. |

> Naming follows the user's suggested modules (`rate_dbf_schema`, `rate_key_setup`, `rate_factor_loader`,
> `rate_validation`) plus a dedicated writer kept separate so emission can be gated independently.

---

## 3. Folder / staging layout (isolated)

```
rate_conversion/
  config/
    rate_families.json            # GP/CV/DB/DV/NP/TV registry: prefix, target table, par-gated?, assumption sidecar
    Sync_Rulebook_quikgps.csv     # source->target field maps, mirroring existing rulebook style
    Sync_Rulebook_quikcvs.csv
    ... (one per family)
    rate_segmentation_rules.json  # gender/UW/band/state member mapping + VARY-driven default collapsing
    reserve_assumption_map.json   # source -> MORT/RSVINT/RSVMETH/INTMETHTV/STOREMEANS/CALCMIDS
    cashval_assumption_map.json   # source -> MORT/ETIMORT/NFOINT/INTMETHCV
    mortality_code_map.json       # LifePRO basis -> QLAdmin mortality code (appendix 6.9)
  staging/
    keys/        # QuikPlxx staging CSV (human-reviewable, target-schema only)
    factors/     # QuikxxS staging CSV
  output/        # isolated final outputs (NOT production-authorized DBFs in early phases)
  reports/       # validation + reconciliation reports
```

Two staged artifacts per family: a **keys** CSV (→ `QuikPlxx`) and a **factors** CSV (→ `QuikxxS`), both
target-schema-only and reviewable before any DBF write.

---

## 3b. Source extracts → target mapping (CONFIRMED inputs)

Two LifePRO source extracts are now available in `docs/plan_conversion_reference/`:

| Source | Shape | Rows | Columns | Feeds |
|---|---|---|---|---|
| `Rate_Table_Extract_20260427.csv` | issue-age × duration (long/normalized) | ~1.13M | `COVERAGE_ID, TYPE_CODE, AGE, SEX, BAND, UNDERWRITING_CLASS, DURATION, VALUE` | GP/CV/DB/DV/NP/TV grids (`AGE`-keyed) |
| `PAAGERAT_AttainedAge_Rates_Extract_20260428.csv` | attained-age | ~24k | `COVERAGE_ID, TYPE_CODE, SEX, BAND, UWCLS, RECORD_SEQ, SEQ, VALUE_INFO, VALUE_FLOAT, AAGE_KEY0` | attained-age grids (Var-code 3) |

**Loader transform pipeline (long → QLAdmin grid):**
```
1. drop the dashed separator row (row 2) and trim fixed-width padding from every field
2. COVERAGE_ID            → authoritative PLAN        (governed crosswalk; reject blank/space/synthetic)
3. TYPE_CODE              → rate family (GP/CV/DB/DV/NP/TV)  (governed crosswalk; drop out-of-scope types)
4. SEX/BAND/UWCLASS       → QLAdmin GENDER/BAND/UWCLASS codes (member-table-validated)
5. DURATION (1-based)     → QLAdmin duration (0-based): dur0 = DURATION-1 → CNTL = dur0//10, col = dur0%10
6. VALUE (high precision) → CHAR(7) 2dp text; check overflow (<= 9999.99); preserve sign (TV can be negative)
7. pivot to one row per (PLAN, AGE, segment, EFFDATE, CNTL) with columns xx0..xx9
```

**Confirmed source vocabulary:** `TYPE_CODE ∈ {CV,DB,NP,DV,RV,NN,PN,TP,TX,UF,PR,NF,SL}` (13 — richer than the 6
QLAdmin families; needs a governed map + out-of-scope list); `SEX ∈ {F,M,J}`; `BAND ∈ {1,2,3}`;
`UWCLASS ∈ {0,B,N,P,S}`; `AGE 0–99`; `DURATION 1–117`. **Confirmed format quirks:** values use leading-dot
notation (`.00`) and **terminal reserves can be negative** (`-2.19`).

## 4. Duration paging (CONFIRMED contract for the loader)

```
For a factor schedule of values v[0..D] over durations 0..D for a (PLAN, AGE, segment, EFFDATE):
    page p = duration // 10        -> CNTL = zero-padded 2-char str(p)   ("00","01",...)
    col  c = duration %  10        -> column xx{c}
    cell  = format_c7(v[duration]) -> e.g. "1000.00" (CHAR(7), 2 decimals)
Emit one row per (PLAN, AGE, segment, EFFDATE, CNTL) page that has any non-empty cell.
```

- `xxN` columns are **CHAR(7)** → enforce `value <= 9999.99` (see overflow check §5).
- `AGE` = issue age, or `00` when the grid is duration-only (per the plan's Var code).

---

## 5. Validation strategy (the core deliverable of any loader)

| Check | Rule | Severity | Basis |
|---|---|---|---|
| **Authoritative PLAN** | every PLAN exists in governed catalog; no blank/space/synthetic | BLOCK | business rule + blank-PLAN row seen in template |
| **Key→factor referential** | every factor `(PLAN+seg+EFFDATE)` has a `QuikPlxx` key | BLOCK | 4 orphan factors found in QLAdmin sample |
| **Empty-key report** | keys with no factors are listed | WARN | 4 empty keys found in sample |
| **Uniqueness** | no duplicate `PLAN+AGE+CNTL+seg+EFFDATE` (factors) / `PLAN+seg+EFFDATE` (keys) | BLOCK | confirmed key columns |
| **Factor overflow** | every `xxN` text fits CHAR(7) (`<= 9999.99`) | BLOCK | confirmed C7 width |
| **Segmentation legality** | segment values exist as PVO members (gender via QuikPlGd; band/state/UW via member tables) | BLOCK | confirmed member tables |
| **VARY consistency** | non-default segment values appear only where the plan's VARY flag = Y | WARN | confirmed VARY mechanism |
| **Assumption completeness (TV/CV)** | reserve/CV keys have MORT + method + interest populated | BLOCK (reserve) | confirmed assumption columns |
| **Mortality resolvability** | every MORT/ETIMORT code exists in QuikQxs / appendix | BLOCK | confirmed code reference |
| **Duration monotonicity (advisory)** | flag suspicious gaps/reversals in factor schedules | INFO | actuarial sanity |
| **Gold standard** | QLAdmin statutory valuation runs with empty Error Valuation report | ACCEPT | manual (R1) |

---

## 6. DBF writer strategy (later phase)

- Honor the **exact confirmed layout** from `rate_dbf_schema.py` (field order, type, length, decimals). Factor
  cells are **CHAR text**, not numeric fields.
- **Deterministic ordering** (sort by full key) for replay-stable output and diff-ability.
- **Never overwrite production DBFs**; emit to the isolated `output/` tree; production authorization is a separate,
  explicit, gated step.

---

## 7. Effective-date / generations

- Treat `EFFDATE` as part of the key in both staging and emit; support **multiple coexisting generations** per
  plan; never overwrite an older generation when loading a newer one.
- Carry `QuikPlNb` availability windows (`EFFDATE`/`TERMDATE`) as the source of plan-by-state availability.
- (Sample data uses a single `19000101` default generation; multi-generation must be designed in, not retrofitted.)

---

## 8. Duplicate detection & missing-factor handling

- **Duplicate detection:** hash the full uniqueness tuple; reject exact dup keys/factors; report near-dups
  (same key, different factor) for actuarial review.
- **Missing factor:** for every active policy's resolved `(PLAN+seg+EFFDATE+AGE+duration)`, assert a populated
  cell exists; produce a **pre-valuation missing-factor report** (mirrors QLAdmin's Error Valuation, caught before
  load rather than after).

---

## 9. Recommended phasing

| Phase | Goal | Output |
|---|---|---|
| **R2 (this)** | Physical structure confirmed | the six analysis outputs in this folder |
| **R3** | `rate_dbf_schema.py` + key-setup prototype | build `QuikPlGp` keys for one authoritative pilot plan; reconcile vs factors |
| **R4** | Single-family factor prototype | load **Gross Premiums (GP)** for the pilot plan end-to-end into staging; full validation |
| **R5** | Reserve workstream | `QuikTvs` layout + `QuikQxs` mortality now CONFIRMED; needs populated TV+NP factor data; load TV+NP+assumptions+mortality together |
| **R6** | Generalize + enterprise | CV/DB/DV families; all authoritative plans; versioning, rollback, audit |

**Recommended next implementation phase = R3** (schema module + key-setup prototype on one authoritative plan).
The reserve workstream is now *structurally* unblocked (`QuikTvs` layout + `QuikQxs` mortality confirmed); it still
needs **populated TV/NP factor data** and the **band/UW member tables** before it can run end-to-end.

> **Mortality note:** `QuikQxs` is a **shared global library keyed by `MORT`** (no PLAN), with **NUMERIC** qx
> (`Q000..Q121`). Build a dedicated `rate_mortality_setup` path that loads it **once globally**, distinct from the
> per-plan CHAR factor loaders.
