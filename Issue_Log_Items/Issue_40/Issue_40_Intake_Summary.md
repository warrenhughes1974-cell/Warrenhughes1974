# Issue #40 — Intake Summary (Exhaustive)

**Issue:** #40 — Inherited Cash Value Rate Load (GL85 anchor + fleet)  
**Date:** 2026-07-06  
**Framework stage:** Intake complete (G0) — **revised for exhaustive validation scope**  
**Status:** Approved → Planning (Development **No-Go** until G2 + G3)  
**Owner:** Conversion (Warren) · **Assigned:** Warren · **Business status:** No-Go (awaiting actuarial + validation design sign-off)

---

## 1. Client / business symptom (verbatim + normalized)

**Client report (normalized from issue log):**

Plan **`17085M`** (LifePRO coverage **`670 GL85-M`**, male pay-at-age **85**) has **no QuikCvs cash value rates loaded** in QLAdmin (~**212** issued policies). LifePRO stores the CV factors under sister coverage **`670 GL85-8`** (QLAdmin plan **`170858`**; **9,121** source CV rows). Product setup shows **`670 GL85-M` inherits those rates through **8 active PCOVRSGT segment slots**. QLA today maps `Rate_Table.COVERAGE_ID` directly to plan code and **does not walk inheritance**, so **`17085M` is absent** from the emitted rate package.

**What the client sees:**

- Policies on plan **`17085M`** cannot calculate or display cash values in QLAdmin.
- Sister plan **`170858`** (`670 GL85-8`, pay-at **88**) **does** have CV rates loaded.
- This is not a single-plan typo — fleet scan found **10 issued plans** with the same missing inherited-CV pattern.

**What this is NOT:**

- **Issue #21E** — stored policy fund balances on screen (load vs calculate decision is separate).
- **Issue #41** — duration/index placement for CV rows that **already exist** (recently fixed for direct-loaded plans).
- **Issue #37** — LifePRO-style CV grid builder (still required **after** inherited rows are emitted).

---

## 2. Why this issue is hard (and why prior CV work missed it)

We have corrected cash value **placement** twice (Issues **#37** and **#41**) on plans where CV rows were already emitted. Issue **#40** is a different failure mode: **the rows never load at all** because LifePRO and QLAdmin do not share a single obvious “plan = rate table” key.

| Layer | LifePRO | QLAdmin | Gap |
|-------|---------|---------|-----|
| Product identity | `PCOVR.COVERAGE_ID` e.g. `670 GL85-M` | `quikplan.PLAN` e.g. `17085M` | Crosswalk exists and is stable (#28) |
| Rate storage | `Rate_Table` keyed by **rate-owner** coverage e.g. `670 GL85-8` | `QuikCvs.PLAN` = **issuing** plan | Loader uses direct `COVERAGE_ID → PLAN` only |
| Inheritance | `PCOVRSGT` segment slots point issuing coverage → rate-owner segment | No equivalent table | `SegmentResolver` exists but is **not wired** into Rate_Table CV emit |
| Duration grid | Issue age × policy duration in extract | `CNTL` pages + `CV0–CV9` columns | Issue #37/#41 rules apply **after** rows exist |

**Data dictionary gap:** There is no complete, authoritative dictionary that states, for every CV-capable product:

1. Which coverage owns the `Rate_Table` rows.
2. Which PCOVRSGT slots inherit those rows for the issued coverage.
3. How LifePRO duration maps to QLAdmin `CNTL*10 + column`.
4. Whether pay-age differences (85 vs 88 on GL85) change the **rate table** or only **cease-age calculation**.

Because of that, every CV fix must be **proven empirically** — source extract → generated `QuikCvs.csv` → QLAdmin screen — not assumed from field names alone. That is why Issue #40 intake explicitly requires **100% source-to-QLA validation** for every plan touched, not spot checks only.

---

## 3. Normalized finding — GL85 anchor (`17085M`)

Measured at intake (**2026-07-06**):

| Check | `17085M` (`670 GL85-M`) | `170858` (`670 GL85-8`) | `170588` (`670 GL8588`) |
|-------|-------------------------|-------------------------|-------------------------|
| `Rate_Table` TYPE `CV` rows | **0** | **9,121** | **7,346** |
| Current `QuikCvs.csv` rows | **0** | **1,002** | **835** |
| `quikplan` catalog row | Yes | Yes | Yes |
| CSO / CV assumptions (`INTMETHCV`, etc.) | Yes | Yes | Yes |
| Issued policies (`quikridr`) | **212** | ~294 | — |
| PCOVRSGT inherit slots → `670 GL85-8` | **8** (slots 2, 3, 12, 13, 22, 29, 32, 33) | N/A (rate owner) | — |

**Interpretation:** The CV **values exist in source** under `670 GL85-8` and are **already converted correctly for plan `170858`**. They are **not emitted under the issuing plan `17085M`**, which is what QLAdmin needs for policies on that plan.

---

## 4. Fleet scope — all plans with the same failure mode

Full audit: `Issue_40_Fleet_CV_Inheritance_Audit.csv`  
Intake evidence counts: `Issue_40_Intake_Source_Gap_Evidence.csv`

| Priority | QLA plan | LifePRO coverage | Issued policies | Rate owner | Owner source CV rows | Issuing plan QuikCvs rows today |
|----------|----------|------------------|------------------:|------------|---------------------:|----------------------------------:|
| High | `1L10SO` | `L10 SR OLD` | 449 | `L10 PRE97` + `L10 LP95` | 58,862 combined | **0** |
| High | **`17085M`** | **`670 GL85-M`** | **212** | **`670 GL85-8`** | **9,121** | **0** |
| High | `1668SP` | `668 SPWL` | 160 | `659 CEN II` | 9,678 | **0** |
| High | `1L10SR` | `L10 LP95SR` | 159 | `L10 LP95` + `L10 PRE97` | 58,862 combined | **0** |
| High | `1SALMI` | `SAL MULTPL` | 153 | `SAL OL` | 4,750 | **0** |
| High | `1SALML` | `SAL ML` | 152 | `SAL OL` | 4,750 | **0** |
| Medium | `1666AI` | `897 666` | 8 | `666 WL` | 4,895 | **0** |
| Medium | `280PUA` | `980 PUA` | 3 | `980 END65` | 4,143 | **0** |
| Medium | `265PUA` | `665 PUA` | 1 | `665 STME95` | 3,479 | **0** |
| Low | `261PUA` | `961 PUA` | 0 | `961 ME65` | 4,069 | **0** |

**Total issued policies affected (High + Medium):** **1,145** (excluding zero-issued `261PUA`).

Issue #40 intake scope: **fix the loader pattern for all approved inherited-CV candidates**, not only GL85 — but **GL85 remains the anchor proof case** because it is the client-visible example and has a single clear rate owner.

---

## 5. Root cause (confirmed at intake)

**Category:** Loader architecture gap + product hierarchy not modeled in Rate_Table emit

1. LifePRO stores CV factors under **rate-owner** coverage IDs (e.g. `670 GL85-8`), not under every **issued** coverage (`670 GL85-M`).
2. `qla_core/rate_factor_loader.transform_source()` assigns plan via `cov2plan.get(COVERAGE_ID)` only — **no PCOVRSGT inheritance walk** for Rate_Table CV rows.
3. `SegmentResolver` in `qla_core/rate_segment_resolution.py` supports segment chains for PAAGERAT but is **not invoked** when emitting QuikCvs from Rate_Table.
4. Plans like **`17085M`** were never added to QuikCvs regression baselines because no rows were emitted.

Relevant loader behavior today:

```172:176:qla_core/rate_factor_loader.py
            plan = cov2plan.get(cov)
            if not plan:
                yield {"status": "PLAN_UNRESOLVED", "type_code": typ, "coverage_id": cov,
                       "lineno": lineno}
                continue
```

---

## 6. Required fix direction (intake — not implemented)

After actuarial sign-off:

1. **PCOVRSGT-aware CV inheritance emit** — for each issuing coverage/plan with zero direct CV rows, walk active PCOVRSGT slots to rate-owner coverages that have Rate_Table CV rows.
2. Emit inherited rows under the **issuing plan code** (e.g. `17085M`), not the rate-owner plan (`170858`).
3. Apply existing Issue **#37 / #41** CV grid rules to inherited rows unchanged.
4. Validate **100%** of emitted cells against source for every approved plan (see `Issue_40_Intake_Validation_Matrix.md`).

**Rejected at intake:**

- Pointing `670 GL85-M` policies at plan `170858` in crosswalk (breaks plan identity, modal factors #21J).
- Blind copy of `170858` QuikCvs grid to `17085M` without PCOVRSGT provenance and actuarial approval.
- Fixing only GL85 while leaving the other 9 fleet candidates unfixed.

---

## 7. Example trace policies (UAT anchors)

| QLAdmin policy | LifePRO | Plan | Role |
|----------------|---------|------|------|
| `010367438C` | `9010367438` | `17085M` | MPREM / loan trace |
| `010615191C` | `9010615191` | `17085M` | MUNIT precision trace |
| `010464869C` | `9010464869` | `17085M` | Issue #21D population |

Full fleet population: `Issue_40_Population.csv` (**212** policies on `17085M`).

Post-fix UAT minimum: **3 policies** from population + **source-vs-QLA grid proof** on `17085M` vs `170858` (must show identical CV values at same duration index, different `PLAN` code).

---

## 8. Artifact inventory

| Artifact | Status | Path |
|----------|--------|------|
| Client symptom / issue log row | **Provided** | Master tracking + user intake paste |
| Rate_Table extract | **Met** | `plan_analysis/source_data/rates/Rate_Table_Extract_20260427.csv` |
| PCOVRSGT segment linkage | **Met** | `plan_analysis/source_data/coverage/PCOVRSGT.csv` |
| PCOVR product metadata | **Met** | `plan_analysis/source_data/coverage/PCOVR.csv` |
| Policy Form Crosswalk | **Met** | `plan_analysis/source_data/crosswalk/Policy Form Crosswalk 5.22.26.xlsx` |
| CSO mortality / CV assumptions | **Met** | `plan_analysis/source_data/rates/CSO_Mortiality_Crosswalk.csv` |
| Fleet inherited-CV audit | **Met** | `Issue_40_Fleet_CV_Inheritance_Audit.csv` |
| Intake source gap evidence | **Met** | `Issue_40_Intake_Source_Gap_Evidence.csv` |
| Issued population (`17085M`) | **Met** | `Issue_40_Population.csv` |
| Planning report | **Met** | `Issue_40_Planning_Report.md` |
| Dependency gate | **Met** | `Issue_40_Dependency_Gate.md` |
| QLAdmin data dictionary for CV inheritance | **Missing** | Must be inferred from Product Book + empirical proof |
| Actuarial approval — GL85 85 vs 88 table equivalence | **Missing** | **Blocks development** |
| Actuarial approval — fleet inherited-CV scope | **Missing** | **Blocks fleet-wide emit** |
| Client UAT screenshots (LifePRO CV screen for `670 GL85-M`) | **Not provided at intake** | Recommended before closure |

---

## 9. Related issues (must not regress)

| Issue | Relationship |
|-------|--------------|
| **#41** | CV duration endpoint — **must remain PASS** on direct-loaded plans after inherited emit |
| **#37** | CV grid builder — inherited rows must use same transform |
| **#31** | QuikCvs baseline — rebaseline after inherited keys added |
| **#28** | Plan crosswalk authority — `670 GL85-M` → `17085M` unchanged |
| **#21J** | PAC GL85 modal overrides on `170858` / `17085M` — preserve |
| **#21E** | Policy fund values — separate client decision |
| **#25 / #26** | MPOLICY padding / MPREM — must not regress |

---

## 10. Blockers visible at intake

| Blocker | Owner | Blocks |
|---------|-------|--------|
| May `17085M` use `670 GL85-8` CV table? (pay age 85 vs 88) | Client / Actuarial | Development on GL85 anchor |
| Confirm LifePRO runtime uses inherited rates for `670 GL85-M` | Conversion + SME | G2 sign-off |
| Approve fleet inherited-CV candidates (10 plans) or narrow scope | Client / Actuarial | Fleet loader scope |
| RV/NP/DV inherit same way as CV? | Client / Actuarial | Scope beyond CV |
| Issue #21E load-vs-calculate | Client | UAT criteria overlap |
| **100% source-to-QLA validation plan accepted** | Conversion + Client | G5 acceptance — see validation matrix |

---

## 11. G0 gate — intake complete

- [x] Issue folder and artifact set present
- [x] Client symptom documented (GL85 anchor + fleet)
- [x] Root cause confirmed with source counts and loader trace
- [x] Fleet population and source gap evidence quantified
- [x] Exhaustive validation acceptance criteria documented
- [x] Owner assigned (Warren)
- [x] No code or rulebook changes at intake

**Next stage:** Planning (complete) → Dependency Gate (awaiting actuarial) → Risk Agent → Development → **G5 validation with 100% source-to-QLA proof per approved plan**
