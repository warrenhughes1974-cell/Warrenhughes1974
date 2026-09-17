# Issue #169 — Planning Report (v2, net-premium path)

**Framework stage:** Planning
**Date:** 2026-09-15
**Supersedes:** the v1 Planning Report of the same date (class-replication approach), retracted after independent review — see `Issue_169_Independent_Review_20260915.md`.

> **Why v1 was retracted.** v1 reasoned entirely from the terminal-reserve grid (`QuikTvs`) and proposed replicating `901ADB`/`996ADB`'s `UWCLASS=00` rows onto `PR`/`ST`. QLAdmin never reads that grid for these plans — their reserve is `MTABNET / 2`, driven by `QuikNps`, whose rows are *already* keyed `PR`/`ST`. The v1 fix was a no-op, and its proposed CSO/New Era reserve-data request covered three plans for which LifePRO itself holds a $0 reserve.

---

## 1. Confirmed root causes

| # | Cause | Plans | Exposure (6/30/2026, 9/2 run) |
|---|---|---|---|
| **RC-1** | `QuikNps` emits **zero rows** — net premiums exist only in the attained-age `PAAGERAT` extract and nothing loads `TYPE_CODE='NP'` from it. PSUBSSEG emit entry **E4** was scoped for exactly this and dropped from the delivered manifest. | `5667AT` (667 ART) | **96 rows / $132,229.48** vs QLAdmin $0.00 |
| **RC-2** | `QuikPlTv` valuation assumptions (`MORT`/`RSVINT`/`RSVMETH`) blank — plan absent from `CSO_Valuation_Setup.csv`. PSUBSSEG open item **OI-1** anticipated this; its "copy the existing band" fallback cannot fire for a plan with no row to copy. | `7619PU` (619 SPS PU); also drives the `901ADB`/`996ADB` magnitude gap | `7619PU` $0 vs $90.47; `901ADB` $98 vs $261.45; `996ADB` $25 vs $54.00 |
| **RC-3** | Tabular durations exhausted — `PDAGE` carries the whole `960` family at durations 1–12; the policy is at duration 57. `RSVMETH=3` (formula) plan. | `196085` (960 LP85-M) | 1 row / $1,858.42 |
| **RC-4** | **No defect.** LifePRO holds a $0 reserve; QLAdmin emits a small positive. | `9595WP` ($55.25), `967ADB` ($43.00), `9SLADB` ($3.60) | LifePRO $0.00 on every row |

Evidence for all four: `Issue_169_Independent_Review_20260915.md` Parts 1 and 4, reproducible via `tools/verify_issue169_reserve_mechanism.py`, `tools/scope_paagerat_np_gap.py`, `tools/diagnose_mtabnet_zero.py`.

## 2. In scope for Development — RC-1 only

`5667AT` net-premium emit. It is the only item in this issue that is (a) a defect on our side, (b) fully supported by data already in the 8/31 package, and (c) worth 98.6% of the issue's dollars.

### 2.1 What exists to build on

`qla_core/paagerat_pr_loader.py` already streams PAAGERAT rows for **one parameterised `TYPE_CODE`**, segment-resolved to `PLAN`:

```
stream_paagerat_rows(..., type_code: str, target_table=None)
    table = target_table or S.TYPE_TO_TABLE.get(type_code)
```

Two thin wrappers exist today — `type_code="PR"` (→ `QuikGps`) and `type_code="NF"` (→ `QuikNff"`). `rate_dbf_schema.TYPE_TO_TABLE` already maps `"NP": "QuikNps"` and `KEY_TABLE` already maps `QuikNps → QuikPlTv`, so the target table and key table resolve with no schema change.

The pipeline also already has the gating pattern: `paagerat_bp_*`, `paagerat_coi_*`, `paagerat_db_*`, `paagerat_pua_cv_*` each carry an `_enabled` flag and an `_mplan_allowlist` in `rate_pipeline.py`.

### 2.2 Proposed change

1. Add a third wrapper alongside the `PR`/`NF` pair for `type_code="NP"` → `QuikNps`. No new module, no new framework — reuse `stream_paagerat_rows` exactly as `NF` does.
2. Gate it with a `paagerat_np` config block (`enabled` + `mplan_allowlist`), mirroring `paagerat_bp` / `paagerat_coi`.
3. **Allowlist `5667AT` only** for this issue.
4. Emit companion `QuikPlTv` key rows via the existing `rate_key_setup.build_key_rows()` path (Issue #77 invariant: every emitted grid has a key row).
5. Preserve first-writer-wins: skip any `(plan, table, key)` already emitted, per the PSUBSSEG loader's established collision rule.
6. Bump `APP_VERSION` in **both** `app.py` and `QLA_Migration/app.py` (`AGENTS.md`).

### 2.3 Why the allowlist must not be opened wider

Six coverages have attained-age `NP` data and no `QuikNps` rows today; two have attained-age `NP` data and **already** carry `QuikNps` rows from PDAGE:

| Coverage | PAAGERAT NP rows | PDAGE NP rows | Plan | `QuikNps` today | In scope? |
|---|---:|---:|---|---:|---|
| `667 ART` | 288 | 0 | `5667AT` | 0 | **yes** |
| `667 ART 95` | 304 | 0 | `5667AT` (95-era segment) | 0 | **yes — confirm at Dev** |
| `667 ART CR` | 384 | 0 | unresolved (`CROSSWALK_DIVERGENT` → proposed `57ATCR`) | 0 | no — governance |
| `646 ART` | 82 | 0 | unresolved passthrough | 0 | no |
| `L03 ART` | 53 | 0 | unmapped | 0 | no |
| `SAL OL` | 76 | 0 | `1SALOL` | 0 | no — not in this issue |
| `668 SPWL` | 117 | 0 | `1668SP` | **2,128** | **no — collision + level-NP risk** |
| `896 DAR` | 3 | **12** | `A96DAR` | 8 | **no — NP in both extracts** |

`1668SP` is on the `QUIKNPS_LEVEL_NP_MPLANS` allowlist in `qla_core/quiknps_level_np.py` (the CEN/ISWL level-NP flatten). Adding attained-age rows there could interact with that flatten and with the Closed **CEN NP** guide row. `896 DAR` is the only coverage carrying `NP` in *both* extracts. Both stay out.

`667 ART 95` resolving to `5667AT` is evidenced by the existing `QuikTvs` emit — `5667AT`'s 2,020 rows came from `667 ART 95` PDAGE `RV` via PSUBSSEG. Development must confirm whether the 95-era NP belongs on the `19950101` generation and the base `667 ART` NP on `19000101`, matching the PSUBSSEG era pattern, before emitting both.

### 2.4 Files expected to change

| File | Change |
|---|---|
| `qla_core/paagerat_pr_loader.py` | Add `stream_paagerat_np_rows()` wrapper (`type_code="NP"`), mirroring the existing `NF` wrapper |
| `qla_core/rate_pipeline.py` | Wire `paagerat_np` gate + `mplan_allowlist`, mirroring `paagerat_bp` / `paagerat_coi`; status counters |
| `plan_analysis/phase_r5_rate_loader/rate_loader_config.json` | New `paagerat_np` block, `mplan_allowlist: ["5667AT"]` |
| `QLA_Migration/Output/rates/QuikNps.csv` | `+5667AT` rows (net new plan; no existing row modified) |
| `QLA_Migration/Output/rates/QuikPlTv.csv` | `+5667AT` `QuikNps` key rows if the existing RV keys do not already cover the generation |
| `app.py` + `QLA_Migration/app.py` | `APP_VERSION` bump |
| `tools/validators/validate_issue169_667art_np_emit.py` (new) | Fail-closed: `5667AT` `QuikNps` row count > 0, values cell-identical to PAAGERAT source, key rows present. Exit 1 if absent |

### 2.5 Explicitly not invented

- No reserve **values** are authored. Every emitted cell must be value-identical to a PAAGERAT source cell — same standard as the PSUB and PUA-CV Closed rows.
- No `MORT` / `RSVINT` / `RSVMETH` invented for any plan (see §3).
- No change to `QuikTvs` for `5667AT` — its all-zero RV grid is correct and PSUBSSEG **OI-2** already accepted it.
- No change to `map_uwclass` / `map_rider_uwclass` (#159) or any `*VARY*` flag (#136).

## 3. Out of scope — RC-2, a precise client ask (not code)

`7619PU`, `901ADB`, `996ADB`, `967ADB`, `9595WP`, `9SLADB` have **no row** in `CSO_Valuation_Setup.csv`, so their `QuikPlTv` assumptions ship blank. We must not invent a mortality table, reserve interest basis, or reserve method — that is an actuarial determination and `CSO_Valuation_Setup.csv` is the client-authoritative source under Closed issue **#80** ("blank cells stay blank").

The correct ask to CSO is narrow and answerable: *supply `QuikPlTv_MORT`, `QuikPlTv_RSVINT`, `QuikPlTv_RSVMETH` for these plan codes.* Recommend limiting the ask to `7619PU`, `901ADB`, `996ADB` — the three with a real LifePRO reserve. This **replaces** the v1 reserve-factor request, which should not be sent.

## 4. Out of scope — RC-3 and RC-4

- **RC-3 `196085`** — 1 policy / $1,858.42. The source genuinely stops at duration 12 and the plan is formula-based (`RSVMETH=3`). Determining how QLAdmin should produce a formula reserve past the tabular range is a QLAdmin/actuarial question, not a conversion emit. Log and defer.
- **RC-4 `9595WP`, `967ADB`, `9SLADB`** — LifePRO holds $0. No change. Confirm with Jill whether she expects any reserve on these three before either side spends more time; if she does not, they should come off the issue. Note QLAdmin currently emits a small positive against LifePRO's zero, which is a separate (small, opposite-direction) discrepancy.
- **`967ADB` crosswalk governance** — the `CROSSWALK_DIVERGENT` / `FORM_CONFLICT_REVIEW` state for LifePRO coverage `1596 667` is real and worth resolving on its own merits, but it is not a reserve defect and not a blocker here.

## 5. Population affected by the proposed fix

| Plan | `quikridr` policies | Valued rows (9/2) | LifePRO reserve at stake |
|---|---:|---:|---:|
| `5667AT` | 195 (95 active per PSUBSSEG Discovery) | 96 | **$132,229.48** |

No other plan's rows are touched. Every other plan in `QuikNps` must be byte-identical before/after.

## 6. Acceptance criteria

1. `5667AT` has `QuikNps` rows, and every emitted cell is value-identical to its PAAGERAT source cell.
2. Every emitted `5667AT` grid has a matching `QuikPlTv` key row (#77 invariant).
3. `QuikNps` rows for **every other plan** — byte-identical to the pre-change emit (hard regression gate).
4. `5667AT` `QuikTvs` — unchanged, still the all-zero RV grid (PSUBSSEG OI-2 preserved).
5. `1668SP` `QuikNps` (2,128 rows) and `A96DAR` (8 rows) — unchanged; CEN NP level-flatten unaffected.
6. `validate_psubsseg_substitution.py` — still PASS.
7. `validate_issue136_pvo_flags.py`, `validate_issue158_pr_segment_ownership.py`, `validate_issue168_l14_reserve_class_replication.py` — still PASS.
8. `validate_release_closed_issues.py --smoke-only` — PASS.
9. New `validate_issue169_667art_np_emit.py` — PASS, and fails closed when the rows are absent.
10. Reserve proof: after a fresh valuation, `5667AT` `MTABNET` resolves and `MRESERVE` reconciles to LifePRO's `RV_MEAN_RV` on the anchor policies (`9010764158C`, `9010764248C`, `9010768802C`).
