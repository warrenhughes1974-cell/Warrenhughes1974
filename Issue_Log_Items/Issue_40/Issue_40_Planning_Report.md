# Issue #40 — Planning Report

**Issue:** #40 — GL85 Cash Value Rate Load (`17085M`)  
**Framework stage:** Planning Agent (G1)  
**Status:** Planning complete — proceed to Dependency Gate  
**Generated:** 2026-07-06  
**Agent:** Planning Agent (read-only research)

---

## 1. Executive finding

**Confirmed defect:** Plan **`17085M`** has **zero** cash value rate rows in `Rate_Table_Extract` and **zero** QuikCvs keys in the emitted rate package, while **~212 issued policies** reference that plan in `quikridr.csv`. Sister plan **`170858`** (`670 GL85-8`) has **9,121** source CV rows and **986** QuikCvs keys.

**Fleet-wide finding:** `17085M` is not isolated. Applying the same PCOVRSGT inheritance test across mapped products found **10 missing inherited-CV candidates** where the issuing plan has no direct QuikCvs keys but active LifePRO segments point to CV-bearing rate-owner coverages. The highest issued populations are **`1L10SO` (449)**, **`17085M` (212)**, **`1668SP` (160)**, **`1L10SR` (159)**, **`1SALMI` (153)**, and **`1SALML` (152)**. Detail is in `Issue_Log_Items/Issue_40/Issue_40_Fleet_CV_Inheritance_Audit.csv`.

**Confirmed LifePRO design:** Coverage **`670 GL85-M`** inherits actuarial rate segments from **`670 GL85-8`** through **8 PCOVRSGT slots** (2, 3, 12, 13, 22, 29, 32, 33). Slot **31** (`LIFEWCV`) is a whole-life-with-CV **semantic flag**, not the rate table key. The actual CV factors live under **`Rate_Table.COVERAGE_ID = 670 GL85-8`**.

**Recommended direction (Planning):** Implement **PCOVRSGT-aware CV rate inheritance** as a generic loader rule, not a GL85-only patch. The rule should emit inherited CV rows under the issuing plan when the issuing coverage has no direct CV table and one or more active PCOVRSGT segments point to CV-bearing rate-owner coverages. Do **not** blindly copy rates where multiple source segments or pay-age differences exist — those require actuarial sign-off.

**Go/no-go for Development:** **No-Go until G2 + G3** — actuarial decision on inherited-rate equivalence required, especially for `17085M`, L10 Senior Life variants, SAL Modified Life variants, and PUA rider behavior.

---

## 2. LifePRO product hierarchy (inheritance trace)

### 2.1 Product identity (PCOVR)

| LifePRO coverage | QLA plan | Form | Type | Premium cease age |
|------------------|----------|------|------|------------------:|
| `670 GL85-M` | `17085M` | 960 | WHO | **85** |
| `670 GL85-8` | `170858` | 960 | WHO | **88** |
| `670 GL8588` | `170588` | 960 | WHO | **88** |

Source: `plan_analysis/source_data/coverage/PCOVR.csv`

### 2.2 PCOVRSGT — what `670 GL85-M` inherits

Active slots on **`670 GL85-M`** (16 total):

| Slot | Segment ID | Relationship |
|-----:|------------|--------------|
| 1 | `GL LP85` | Product-family segment → parent `670 GL85-M` |
| **2, 3, 12, 13, 22, 29, 32, 33** | **`670 GL85-8`** | **Inherited rate owner** |
| 6 | `5 ADV` | Shared SAL OL family |
| 10 | `ENDOW100` | Shared SAL OL family |
| **18** | **`AGE 85`** | Pay-age segment (male variant) |
| 19 | `DA3` | Dividend segment → parent `670 GL85-M` |
| **31** | **`LIFEWCV`** | WL+CV flag (parent `SAL OL` — not rate table) |
| 37, 38 | `LIFE` | Shared SAL OL family |

Source: `plan_analysis/source_data/coverage/PCOVRSGT.csv`

**Key difference vs `670 GL85-8`:** slot **18** is **`AGE 85`** (not **`AGE 88`**). All other inherited slots match the `-8` variant pattern.

### 2.3 Rate_Table — where CV rows actually live

| `Rate_Table.COVERAGE_ID` | QLA plan (direct crosswalk) | CV rows | Other rate families |
|--------------------------|----------------------------|--------:|---------------------|
| `670 GL85-8` | `170858` | **9,121** | RV 9,230 · NP 6,988 · DV 7,126 · NF/NN/PN |
| `670 GL8588` | `170588` | **7,346** | CV only in extract |
| `670 GL85-M` | `17085M` | **0** | — |

Source: `plan_analysis/source_data/rates/Rate_Table_Extract_20260427.csv`  
Analysis: `plan_analysis/phase_r4_loader_architecture/rate_factor_capacity_analysis.csv`

### 2.4 Inheritance flow (LifePRO → QLA today)

```text
670 GL85-M (issued coverage, plan 17085M)
    │
    ├── PCOVRSGT slots 2,3,12,13,22,29,32,33 ──► segment "670 GL85-8"
    │         │
    │         └── Rate_Table[670 GL85-8, TYPE=CV]  (9,121 rows)
    │                   │
    │                   ├── LifePRO: used for CV calc on 670 GL85-M policies
    │                   └── QLA loader today: emitted ONLY as plan 170858
    │
    └── Rate_Table[670 GL85-M]  →  EMPTY  →  plan 17085M gets NO QuikCvs
```

---

## 3. Confirmed QLAdmin target

| Target | Role | Current state for `17085M` |
|--------|------|----------------------------|
| **`QuikCvs.csv`** / **`QuikPlCv`** | CV factor grid (issue age × duration × sex × UW × band) | **Missing** |
| **`quikplan`** | Plan assumptions (`INTMETHCV`, `MORT`, `NFOINT`, variation flags) | Row exists; CSO crosswalk populated |
| Policy CV display | Calculated from rates + assumptions | **Blocked** without QuikCvs |

Issue #37 fixed **duration placement** for CV rows that exist. Issue #40 adds the **missing plan universe** for `17085M`.

QuikCvs baseline reference: `Issue_Log_Items/Issue_31/output/baselines/iswl_quikcvs_regression_baseline.json` — lists `170858` and `170588`, **not** `17085M`.

---

## 4. Root cause in conversion code

| Component | Current behavior | Gap |
|-----------|------------------|-----|
| `qla_core/rate_factor_loader.transform_source()` | `plan = cov2plan.get(cov)` on Rate_Table row | No inheritance walk |
| `qla_core/rate_segment_resolution.SegmentResolver` | Can resolve segment → parent → plan | **Not called** from rate loader |
| R4 assumption template | `170858` / `170588` listed for CASH_VALUE | **`17085M` absent** |
| Rate variation flags | `170858` has CV vary flags | **`17085M` blank** |

Relevant code:

```172:176:qla_core/rate_factor_loader.py
            plan = cov2plan.get(cov)
            if not plan:
                yield {"status": "PLAN_UNRESOLVED", "type_code": typ, "coverage_id": cov,
                       "lineno": lineno}
                continue
```

---

## 5. Resolution options

| Option | Description | Pros | Cons | Planning recommendation |
|--------|-------------|------|------|-------------------------|
| **A — PCOVRSGT inheritance emit** | For each issued plan, walk PCOVRSGT inherited segment IDs; load Rate_Table rows from rate-owner coverage; emit under **issuing** plan code | Matches LifePRO segment design; reusable for all missing inherited-CV products | Requires inheritance map + validation; actuarial sign-off still needed | **Preferred** |
| **B — Static alias table** | Config: `17085M` inherits CV from `670 GL85-8` / copy `170858` grid to `17085M` | Fast to implement | Brittle; doesn't generalize; misses other plans found in fleet scan | Acceptable **interim** only if GL85 must be isolated |
| **C — Request LifePRO re-extract** | Ask client for `Rate_Table` rows keyed `670 GL85-M` | Clean direct mapping | **Unlikely** — LifePRO product uses inheritance by design | **Not recommended** as primary path |
| **D — Point policies at `170858`** | Change crosswalk so `670 GL85-M` → `170858` | None — wrong plan identity | Breaks plan catalog, modal factors (#21J), premium cease age on plan row | **Rejected** |

---

## 5A. Fleet-wide missing inherited-CV candidates

The following plans have **no direct CV rows and no current QuikCvs keys**, but their PCOVRSGT active segments point to one or more CV-bearing rate-owner coverages. These are the plans the Issue #40 loader rule should evaluate before development sign-off.

| Priority | QLA plan | LifePRO coverage | Issued rows | Rate owner(s) | Notes |
|----------|----------|------------------|------------:|---------------|-------|
| High | `1L10SO` | `L10 SR OLD` | 449 | `L10 PRE97`, `L10 LP95` | Multiple rate-owner segments; actuarial selection rule required. |
| High | `17085M` | `670 GL85-M` | 212 | `670 GL85-8` | Original GL85-M case; pay age 85 vs 88 must be approved. |
| High | `1668SP` | `668 SPWL` | 160 | `659 CEN II` | Single Premium Whole Life inherits ISWL-like CV-bearing segment. |
| High | `1L10SR` | `L10 LP95SR` | 159 | `L10 LP95`, `L10 PRE97` | Multiple rate-owner segments; actuarial selection rule required. |
| High | `1SALMI` | `SAL MULTPL` | 153 | `SAL OL` | Modified Life inherits SAL OL CV table. |
| High | `1SALML` | `SAL ML` | 152 | `SAL OL` | Modified Life inherits SAL OL CV table. |
| Medium | `1666AI` | `897 666` | 8 | `666 WL` | Additional insured whole-life coverage; confirm target behavior. |
| Medium | `280PUA` | `980 PUA` | 3 | `980 END65` | PUA rider; confirm whether QuikCvs is needed at rider plan. |
| Medium | `265PUA` | `665 PUA` | 1 | `665 STME95` | PUA rider; confirm whether QuikCvs is needed at rider plan. |
| Low | `261PUA` | `961 PUA` | 0 | `961 ME65` | No current issued dependency count; include for completeness. |

One additional research item, **`196085` / `960 LP85-M`**, has `LIFEWCV` semantics and issued rows but no direct or inherited CV-bearing segment in this scan. It should not be auto-fixed by the inherited-CV rule until the source path is traced.

Full audit: `Issue_Log_Items/Issue_40/Issue_40_Fleet_CV_Inheritance_Audit.csv`.

## 6. Recommended implementation plan (Development stage)

**Prerequisite:** Client/actuarial confirms Option A for the affected product families, or approves a narrower interim scope.

### Phase 1 — Inheritance map (read-only + config)

1. Build GL85 inheritance manifest from PCOVRSGT:
   - Parent coverage → inherited segment ID → rate-owner coverage → rate families present in Rate_Table
2. Document for `670 GL85-M`:
   - CV (and optionally RV/NP/DV) inherited from `670 GL85-8`
   - Pay-age segment `AGE 85` has **no** Rate_Table rows (cease-age logic only)

### Phase 2 — Rate loader change (surgical)

1. Extend rate pipeline to support **plan-targeted inheritance**:
   - Input: issuing coverage `670 GL85-M` → plan `17085M`
   - Rate source: `670 GL85-8` rows where PCOVRSGT slot points to that segment
   - Output: QuikCvs keys tagged **`PLAN=17085M`** (not `170858`)
2. Apply existing Issue #37 CV grid transform to inherited rows unchanged.
3. Add `17085M` to:
   - `plan_rate_key_assumption_mapping_template.csv` (CASH_VALUE row)
   - QuikCvs regression baseline
4. Bump `app.py` version if batch rate path touched.

**Suggested touch points (minimal blast radius):**

| File | Change |
|------|--------|
| `qla_core/rate_factor_loader.py` or `qla_core/rate_pipeline.py` | Inheritance-aware plan assignment for configured coverage pairs |
| `plan_governance/config/` or phase_r4 business inputs | GL85 inheritance manifest (coverage → rate owner → plans) |
| `qla_core/quikplan_rate_variation_flags.py` | Align CV vary flags for `17085M` with inherited segmentation |
| `QLA_Migration/_validate_issue40_gl85_cv_inheritance.py` | New validator |
| `Issue_Log_Items/Issue_31/output/baselines/iswl_quikcvs_regression_baseline.json` | Add `17085M` key count after emit |

### Phase 3 — Validation (G5)

| Test | Expected |
|------|----------|
| `17085M` QuikCvs key count | Matches inherited grid from `670 GL85-8` (post-#37 placement) |
| `170858` row count | **Unchanged** (no regression) |
| Sample policies on `17085M` | QLAdmin CV calc proceeds (client UAT) |
| Issue #37 proof ages | Placement still PASS on inherited rows |

### Phase 4 — Regression (G6)

| Guard | Must hold |
|-------|-----------|
| Issue #25 MPOLICY padding | PASS |
| Issue #26 MPREM | PASS |
| Issue #37 CV placement | PASS on all plans including new `17085M` |
| ISWL QuikCvs plans (8 ISWL MPLANs) | Row counts unchanged |
| `quikplan` row for `17085M` | PLAN code unchanged |

---

## 7. Open client / actuarial questions

| # | Question | Blocks |
|---|----------|--------|
| 1 | May plan **`17085M`** use the **`670 GL85-8`** CV rate table (same factors as **`170858`**)? | Development |
| 2 | Does pay-age difference (**85** vs **88**) require **different CV factors**, or only different **cease-age calculation** on the same table? | Option A vs B |
| 3 | Should RV/NP/DV inherit the same way as CV for `17085M`? | Scope |
| 4 | Relationship to **Issue #21E**: load stored fund values **and** rates, or rates only? | UAT criteria |

---

## 8. Fleet impact (estimated)

| Metric | Value |
|--------|------:|
| Policies on plan `17085M` | ~212 |
| New QuikCvs keys (if mirroring `170858`) | ~986 (estimate — verify post-emit) |
| Source CV rows inherited | 9,121 |
| Plans affected in rate package | +1 (`17085M`) |
| Policy table row count delta | 0 |

---

## 9. Explicitly not changed (regression guards)

- `quikplan.PLAN` for `670 GL85-M` remains **`17085M`**
- Issue #21J PAC GL85 modal overrides (`170858` / `17085M`)
- Issue #37 CV duration grid logic (apply to new rows, do not rewrite)
- Sister plan **`170858`** / **`170588`** existing QuikCvs emits

---

## 10. Artifact index

| Artifact | Path |
|----------|------|
| Intake summary | `Issue_Log_Items/Issue_40/Issue_40_Intake_Summary.md` |
| Dependency gate | `Issue_Log_Items/Issue_40/Issue_40_Dependency_Gate.md` |
| Population | `Issue_Log_Items/Issue_40/Issue_40_Population.csv` |
| PCOVRSGT source | `plan_analysis/source_data/coverage/PCOVRSGT.csv` |
| Rate_Table source | `plan_analysis/source_data/rates/Rate_Table_Extract_20260427.csv` |
| Rate capacity analysis | `plan_analysis/phase_r4_loader_architecture/rate_factor_capacity_analysis.csv` |
| Segment resolver | `qla_core/rate_segment_resolution.py` |
| Rate loader | `qla_core/rate_factor_loader.py` |
| CSO assumptions | `plan_analysis/source_data/rates/CSO_Mortiality_Crosswalk.csv` (row `670 GL85-M`) |

---

## 11. Next framework stage

**Dependency Gate (G2)** — confirm actuarial answer on inherited-rate equivalence, then **Risk Agent (G3)** for blast-radius review before any loader change.

**Do not code until G1 + G2 + G3 satisfied** (per `AI_Agents/Framework.md`).
