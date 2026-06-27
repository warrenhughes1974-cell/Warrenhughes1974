# Issue 21K — PUA Amount Precision — Risk Review Report

**Issue:** 21K — PUA Amount Precision  
**Framework stage:** Risk Agent (Stage 4)  
**Dependency Gate:** **GO** (2026-06-24) — `MUNIT`/units confirmed **`N(10,3)`** today; updating to **`N(10,5)`**  
**Status:** **CONDITIONAL GO** — proceed with **QLAdmin schema migration + reload**; **no converter Development** unless post-UAT display gap remains  
**Generated:** 2026-06-24  
**Agent/script:** `_risk_review_issue21k_munit.py` v1.0  
**Code changes:** None (Risk stage)

---

## Go / No-Go Recommendation

**CONDITIONAL GO** for remediation via **QLAdmin units-field precision expansion (`N(10,3)` → `N(10,5)`)** across the six named tables, followed by **reload/reindex and client UAT**.

**No converter Development is required** — simulation shows **0 of 7,002** `quikridr` rows would change under current mapping. Conversion CSV already emits correct five-decimal `MUNIT` values (e.g. `5.75296` for policy **010448806C**).

**Conditions before Closure:**

1. All six tables updated consistently: **QUIKPOLX**, **QUIKRIDR**, **QUIKRVAL**, **QUIKVALF**, **QUIKVERR**, **QUIKTVAL**.
2. Post-schema **full reload** of conversion CSV into QUIKRIDR (truncated in-memory values are not self-healing).
3. **UAT on policy 010448806C** — PUA face **$5,752.96** in QLAdmin after reload.
4. Confirm **display/report formatters** do not re-truncate to 3 dp after storage supports 5 dp.
5. Client validates **valuation/error/temp-valuation** tables (conversion does not populate these — separate QLAdmin regression surface).

---

## 1. Root Cause — Confirmed

| Layer | `MUNIT` / units | Face (`× MVPU 1000`) | Verdict |
|-------|-----------------|----------------------|---------|
| LifePRO | 5.75296 | $5,752.96 | Source correct |
| `quikridr.csv` | **5.75296** | **$5,752.96** | **Conversion correct** |
| QLAdmin **`N(10,3)`** | 5.752 (truncate) | **$5,752.00** | **Root cause** |
| QLAdmin **`N(10,5)`** (proposed) | 5.75296 | **$5,752.96** | **Expected fix** |

Dependency Gate finding aligns with Planning hypothesis. Issue is **downstream schema**, not LifePRO extract or converter mapping.

---

## 2. Proposed Remediation vs Converter Scope

| Component | Current | Proposed | Converter change? |
|-----------|---------|----------|:-----------------:|
| QLAdmin units field (6 tables) | `N(10,3)` | **`N(10,5)`** | **No** — client/QLAdmin |
| `quikridr.MUNIT` mapping | `NUMBER_OF_UNITS` → `MUNIT` | Unchanged | **No** |
| `quikridr.csv` emission | Up to 5 dp (`5.75296`) | Unchanged | **No** |
| Rulebook | Direct map, line 14 | Unchanged | **No** |
| `app.py` | Generic rulebook loop | Unchanged | **No** |

---

## 3. Repo References — Conversion Touchpoints

| Location | Role | Truncates `MUNIT`? |
|----------|------|:------------------:|
| `QLA_Migration/Configs/Sync_Rulebook_quikridr.csv` | `NUMBER_OF_UNITS → MUNIT` | **No** |
| `app.py` / `QLA_Migration/app.py` | Rulebook-driven emit; no `MUNIT`-specific transform | **No** |
| `validation_config/schema_manifest.json` | Column list only (no `N(?,?)`) | N/A |
| `QLA_Migration/RUN_GUIDE.md` | Emits **CSV only** for business tables | N/A |
| `qla_core/quikmemo_dbf_generator.py` | DBF for memos only | N/A |
| `claims_analysis/.../uat_emitted_csv_dbf_generator.py` | Claims DBF; `truncate_char` on **claims** fields | **No** (not quikridr) |
| `QLA_Migration/QLAdmin_Converted_Tables.txt` | `quikpolx` listed; **not converted**; no quikrval/quikvalf/quikverr/quiktval | N/A |

**Conclusion:** No in-repo import/load path truncates `quikridr.MUNIT` before storage. Truncation occurs in **QLAdmin `N(10,3)`** at load/store time.

---

## 4. Population Analysis (Read-Only Simulation)

Source: `QLA_Migration/Output/quikridr.csv` (7,002 rows)  
Script: `QLA_Migration/_risk_review_issue21k_munit.py`

| Metric | Count | Interpretation |
|--------|------:|----------------|
| Total `quikridr` rows | **7,002** | Full batch |
| **Converter rows that would change** | **0** | No Development needed in mapping layer |
| Rows with sub-mill `MUNIT` (meaningful 4th–5th dp) | **1,068** | Precision at risk under `N(10,3)` |
| Rows with fractional-cent face | **1,070** | User-visible cent accuracy |
| Rows **recovered** by `N(10,5)` vs `N(10,3)` (face Δ ≥ $0.01) | **1,067** | Benefit of schema fix |
| PUA-style (`MPLAN` ends `PA`) rows recovered | **488** | Includes `1708PA` cohort |
| Unique policies benefiting | **949** | Fleet-wide, not PUA-only |
| Maximum face recovery (single row) | **$5.02** | `010510671C` ph1 (`MVPU = 5234`) |

### Top plans by recovery row count

| MPLAN | Rows recovered |
|-------|---------------:|
| 1708PA | 409 |
| 1SALML | 147 |
| 170858 | 105 |
| 1960PA | 71 |
| 1668SP | 66 |

---

## 5. Risk Analysis — `N(10,3)` → `N(10,5)` Across Six Tables

### 5.1 DBF / table schema compatibility

| Risk | Severity | Assessment |
|------|----------|------------|
| Field width insufficient | **Low** | `N(10,5)` max magnitude **99999.99999** — exceeds fleet `MUNIT` range (sample max ~15 units) |
| Table structure change | **Medium** | FoxPro/QLAdmin requires **table rebuild or vendor migration** — not an in-place silent widen in all environments |
| Index corruption | **Low–Medium** | Numeric width change typically requires **reindex** on affected tables; index *keys* (e.g. `MPOLICY`) unchanged |
| Six-table inconsistency | **High** if partial | **All six tables must move together** — mixed precision could cause cross-table unit mismatch in valuation workflows |

**Mitigation:** Apply schema change as a **single coordinated release** across QUIKPOLX, QUIKRIDR, QUIKRVAL, QUIKVALF, QUIKVERR, QUIKTVAL.

### 5.2 Existing QLAdmin calculations

| Risk | Severity | Assessment |
|------|----------|------------|
| `MUNIT × MVPU` face calculation | **Positive** | More precise inputs → **correct** fractional face (intended fix) |
| Premium calculations using units | **Low** | Widen-only change; values that fit in 3 dp are **unchanged numerically** |
| Valuation engine using units from QUIKRVAL/QUIKTVAL | **Medium** | **Beneficial** if those tables also widen; **verify** no hard-coded 3 dp intermediate math in QLAdmin routines |

**Mitigation:** Run valuation smoke tests on policies with sub-mill units after reload.

### 5.3 Screens / reports expecting 3 decimals

| Risk | Severity | Assessment |
|------|----------|------------|
| UI format masks (`999.999`) | **Medium** | Storage may hold 5 dp while screen still shows 3 — **UAT required** |
| Crystal/custom reports | **Medium** | Report templates may format units to 3 dp — cosmetic unless export used for reconciliation |
| Exported files | **Low–Medium** | Exports may show full precision after fix — generally desirable |

**Mitigation:** Explicit UAT on **Coverage tab PUA face** and any unit columns on valuation screens. If display still shows `$5,752.00` with stored `5.75296`, escalate **display formatter** to New Era (separate from schema).

### 5.4 Reindex / load behavior

| Risk | Severity | Assessment |
|------|----------|------------|
| CSV reload after schema change | **Medium** | **Required** — existing rows retain truncated values until reloaded |
| Partial reload | **High** | Policies not reloaded keep wrong units — use **full quikridr reload** or targeted rebuild for UAT cohort |
| Conversion re-run | **Low** | Re-running batch produces **identical** `MUNIT` CSV (0 row delta) — safe |

**Mitigation:** Full batch reload checklist; validate **010448806C** first in UAT environment.

### 5.5 Backward compatibility with existing data

| Scenario | Behavior |
|----------|----------|
| Values already fitting 3 dp (e.g. `5.778`) | **Unchanged** — `5.77800` equivalent |
| Values truncated to 3 dp in DBF (e.g. `5.752`) | **Remain wrong until reload** from CSV |
| Mixed old/new environments | **Risk** — do not load 5 dp CSV into old `N(10,3)` schema |

**Mitigation:** Schema migration **before** reload; no parallel old-schema loads.

### 5.6 Regression across policy, rider, valuation, error, and temp-valuation tables

| Table | Conversion populates? | Risk focus |
|-------|:---------------------:|------------|
| **QUIKRIDR** | **Yes** (`quikridr.csv`) | **Primary** — 7,002 rows; PUA example |
| **QUIKPOLX** | **No** (not in conversion scope) | Client/QLAdmin native — verify extension records |
| **QUIKRVAL** | **No** | Valuation routines — unit precision in reserve/CV paths |
| **QUIKVALF** | **No** | Valuation file — confirm no 3 dp assumptions |
| **QUIKVERR** | **No** | Error/work table — low business visibility |
| **QUIKTVAL** | **No** | Temporary valuation — session/scratch precision |

**Conversion regression surface:** **QUIKRIDR only** (zero CSV delta expected).  
**Client regression surface:** **all six tables** plus valuation batch jobs.

### 5.7 Import / load code truncating before storage

| Path | Truncates? |
|------|:----------:|
| Conversion `app.py` → `quikridr.csv` | **No** |
| In-repo claims DBF generator | **No** (wrong table) |
| Client QLAdmin CSV import | **Was yes** (implicit via `N(10,3)`) → **fixed by schema** |
| Custom client ETL (if any) | **Unknown** — client must confirm ETL uses 5 dp after schema change |

### 5.8 Display logic after storage supports 5 decimals

| Risk | Severity | Assessment |
|------|----------|------------|
| Storage fixed, display still 3 dp | **Medium** | Possible if UI rounds/truncates for display only |
| PUA accumulated face derived field | **Medium** | May compute from stored units — should improve if storage fixed |

**Mitigation:** Post-reload DBF read of **010448806C** MPHASE 2 — confirm stored `5.75296` **and** UI shows **$5,752.96**.

---

## 6. Fields That Must Remain Unchanged (Conversion)

| Target | Source / behavior | Touched by 21K? |
|--------|-------------------|:---------------:|
| `quikridr.MUNIT` mapping | `NUMBER_OF_UNITS` direct | **No change** |
| `quikridr.MVPU` | `VALUE_PER_UNIT` | **No** |
| `quikridr.MPREM` | `ANN_PREM_PER_UNIT` + fallback (#26) | **No** |
| `quikmstr.MMODPREM` | PPOLC `MODE_PREMIUM` | **No** |
| `MPOLICY` padding | `format_qladmin_mpolicy()` (#25) | **No** |
| Row counts / phase structure | PUA inheritance logic | **No** |

---

## 7. Trace Policies — Before / After Simulation

| Policy | Phase | Plan | CSV `MUNIT` | Face @ `N(10,3)` | Face @ `N(10,5)` | Recovery |
|--------|------:|------|------------:|-----------------:|-----------------:|---------:|
| **010448806C** | 2 | 1708PA | 5.75296 | $5,752.00 | **$5,752.96** | **$0.96** |
| 010615191C | 2 | 1708PA | 3.74599 | $3,745.00 | $3,745.99 | $0.99 |
| 010510671C | 1 | 2665ST | 1.15296 | $6,029.57 | $6,034.59 | $5.02 |

Full simulation: `Issue_Log_Items/Issue_21/Issue_21K_Risk_Simulation.csv`

---

## 8. Fallback Options

| Option | Assessment | Recommendation |
|--------|--------------|----------------|
| **A — QLAdmin `N(10,5)` schema + reload** | Correct structural fix; 1,067 rows recover ≥ $0.01 face | **Recommended** |
| **B — Converter truncate to 3 dp** | 0 converter delta today; would **destroy** correct CSV | **Reject** |
| **C — PUA-only formatting hack** | Misses 581 non-PA policies | **Reject** |
| **D — Alternate face field** | No approved field; unnecessary if schema widens | **Reject** |

**Recommended path:** Option A only (client/QLAdmin). **No converter fallback.**

---

## 9. Prior Fix Preservation

| Check | Result |
|-------|--------|
| Issue #25 MPOLICY padding | **Unaffected** — no `MPOLICY` logic in 21K remediation |
| Issue #26 MPREM / MMODPREM | **Unaffected** — separate fields |
| Issue #21B Bill Day | **Unaffected** |
| Issue #21C Policy fees | **Unaffected** |
| Issue #21M QUIKMEMO | **Unaffected** |

---

## 10. Regression Testing Checklist (Validation Agent)

### Client / QLAdmin (primary)

- [ ] All six tables show units field **`N(10,5)`** after migration
- [ ] Reindex completed on affected tables
- [ ] Full `quikridr` reload from conversion CSV
- [ ] **010448806C** — stored `MUNIT = 5.75296`, PUA face **$5,752.96** on screen
- [ ] Sample from **Issue_21K_MUNIT_Precision_Trace.csv** (4 policies) — face matches LifePRO
- [ ] Valuation job smoke test on policy with sub-mill units (e.g. `010510671C`)
- [ ] Confirm no mixed `N(10,3)` tables remain in valuation chain

### Conversion (secondary — expect zero delta)

- [ ] Full batch re-run — **7,002** `quikridr` rows (count stable)
- [ ] **`MUNIT` byte-identical** to pre-fix batch (0 row change)
- [ ] `MVPU`, `MPREM`, `MMODEPREM` unchanged (#26)
- [ ] `MPOLICY` padding unchanged (#25)
- [ ] `_validate_issue21k_munit.py` — sub-mill precision preserved in CSV

---

## 11. Recommended Development Agent Task

**Default: no `app.py` Development.**

Remediation is **client-side QLAdmin schema migration + reload**. Development Agent should **not** begin unless post-UAT evidence shows a remaining conversion or display gap.

If Validation Agent is engaged:

1. Add **`QLA_Migration/_validate_issue21k_munit.py`** (read-only CSV precision checks; optional DBF compare when client supplies post-load sample).
2. **Do not** change `Sync_Rulebook_quikridr.csv`, `app.py`, or `MUNIT` formatting.
3. **Do not** bump engine version for schema-only client fix.
4. Update **`Issue_21_Tracking_Sheet.md`** row 21K status after UAT pass.

**If UAT fails after schema + reload:**

| Failure mode | Next owner |
|--------------|------------|
| DBF stores `5.752` still | Client load / ETL truncation |
| DBF stores `5.75296`, UI shows `$5,752.00` | QLAdmin display formatter — New Era ticket |
| CSV wrong (unlikely) | Re-open Planning — converter regression |

---

## 12. Risk Summary Matrix

| Risk area | Level | Blocks Go? |
|-----------|-------|:----------:|
| Schema widen `N(10,3)` → `N(10,5)` | Low–Medium | No |
| Six-table coordinated migration | Medium | No (with condition) |
| Full reload required | Medium | No |
| Display layer 3 dp format | Medium | Conditional UAT |
| Converter change regression | **None** | No |
| Valuation table regression (non-conversion) | Medium | Client test |
| Partial migration / mixed precision | **High** | Yes — must complete all 6 tables |

---

## Appendix

| Artifact | Path |
|----------|------|
| Planning report | `Issue_Log_Items/Issue_21/Issue_21K_Planning_Report.md` |
| Intake report | `Issue_Log_Items/Issue_21/Issue_21K_Intake_Report.md` |
| Population script | `QLA_Migration/_research_issue21k_munit.py` |
| Risk simulation | `QLA_Migration/_risk_review_issue21k_munit.py` |
| Trace CSV | `Issue_Log_Items/Issue_21/Issue_21K_MUNIT_Precision_Trace.csv` |
| Risk simulation CSV | `Issue_Log_Items/Issue_21/Issue_21K_Risk_Simulation.csv` |

---

**Stop point:** Risk Agent complete. **Do not begin Development** until project lead accepts **CONDITIONAL GO** and client completes schema migration + reload UAT on **010448806C**.
