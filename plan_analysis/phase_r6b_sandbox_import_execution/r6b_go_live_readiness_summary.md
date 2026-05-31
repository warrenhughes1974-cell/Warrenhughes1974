# R6B — QLAdmin Sandbox Import Go-Live Readiness Summary

Practical sandbox execution package for QLAdmin functional validation of the R5-generated
rate library. **Not a production cutover.** Conversion logic unchanged; no DBFs modified.

## Overall status: **READY FOR SANDBOX EXECUTION**

| Gate | Status |
|---|---|
| Conversion blockers | 0 |
| Member table validation (R6A) | PASS |
| Import package complete (R6B) | YES |
| Production deployment | **NOT AUTHORIZED** |

---

## What is complete

### Product & governance foundation
- P3 Product Authority — COMPLETE
- P3E MPLAN Alignment — COMPLETE
- P3G Product Catalog Governance — COMPLETE

### Rate conversion pipeline
- R4 Rate Capacity Analysis — COMPLETE
- R5 Rate Loader Framework — COMPLETE
- R5 Rate DBF Generation — COMPLETE (16 tables, 85,556 rows)
- R6 Import Validation Package — COMPLETE
- R6A Member Table Validation — COMPLETE (structural + referential PASS)
- **R6B Sandbox Import Execution Package — COMPLETE**

### Generated rate library (emitted DBFs)

**Member tables (384 rows)**

| Table | Rows |
|---|---:|
| QuikPlGd | 110 |
| QuikPlUw | 80 |
| QuikPlBd | 66 |
| QuikPlSt | 64 |
| QuikPlNb | 64 |

**Rate key tables (227 rows)**

| Table | Rows |
|---|---:|
| QuikPlGp | 13 |
| QuikPlDv | 20 |
| QuikPlDb | 12 |
| QuikPlCv | 70 |
| QuikPlTv | 112 |

**Factor tables (84,945 rows)**

| Table | Rows |
|---|---:|
| QuikGps | 1,123 |
| QuikDvs | 3,978 |
| QuikDbs | 1,380 |
| QuikCvs | 25,717 |
| QuikTvs | 26,097 |
| QuikNps | 26,650 |

**Keys + factors subtotal:** 85,172 rows (matches R5 baseline)  
**Full library including members:** 85,556 rows

### Business rules enforced
- `EFFDATE = 19000101` on all EFFDATE-bearing tables — verified
- AGE > 99 capped to 99 with collision-safe logic — implemented and audited
- Excluded TYPE_CODEs not loaded: NN, PN, TP, TX, UF, NF, SL

---

## What was tested (automated pre-sandbox)

| Validation | Result |
|---|---|
| DBF readability | PASS (16/16) |
| Row count integrity | PASS |
| PLAN population | PASS (0 blank PLAN) |
| Duplicate key detection | PASS |
| Member ↔ rate-key referential alignment | PASS (64/64 plans) |
| EFFDATE standardization | PASS |
| Placeholder governance documented | PASS |

**Not yet tested (requires QLAdmin sandbox — R6B execution):**

- Live DBF import into QLAdmin
- Plan maintenance screen member display
- Runtime factor lookup / premium / CV / DB / reserve retrieval
- QLAdmin read-back of large factors (`2665ST`, `A96DAR`)
- Valuation behavior with deferred actuarial assumptions

---

## R6B deliverables

| File | Purpose |
|---|---|
| `qla_sandbox_import_execution_guide.md` | Step-by-step sandbox import procedure |
| `qla_functional_test_script.md` | Tester-friendly functional test script (60 tests) |
| `rate_import_validation_matrix.csv` | Test matrix with EXPECTED_RESULT pre-populated |
| `sandbox_import_manifest.csv` | 16-table inventory with load sequence |
| `qladmin_lookup_trace_template.csv` | 17 factor lookup traces for QLAdmin read-back |
| `_build_r6b_package.py` | Regenerate CSV artifacts (read-only) |
| `r6b_go_live_readiness_summary.md` | This document |

---

## Recommended import order

1. QuikPlan *(prerequisite — already exists)*
2. QuikPlGd → QuikPlUw → QuikPlBd → QuikPlSt → QuikPlNb
3. QuikPlGp → QuikPlDv → QuikPlDb → QuikPlCv → QuikPlTv
4. QuikGps → QuikDvs → QuikDbs → QuikCvs → QuikTvs → QuikNps

---

## Key functional tests (sandbox)

1. **Member display** — gender (M/F/J), UW (00/NS/SM/PR/ST), band (01/02/03), state (`0000/00`)
2. **Plan lookup** — `130JEB`, `2665ST`, `A96DAR`, `1L10OD`
3. **Factor retrieval** — all six families (GP, DV, DB, CV, TV, NP)
4. **AGE 99 scenario** — `1L10OD` CV = 1000.00 at AGE 99
5. **Large factors** — `2665ST` DB = 28134.0; `A96DAR` CV = 12164.9

---

## What still requires business review

| Item | Owner | Notes |
|---|---|---|
| Sandbox UAT execution | QLAdmin admin + business tester | Complete validation matrix + lookup trace |
| `BDLOWVAL` band breakpoints | Actuarial / business | Currently 0 placeholder (66 rows) |
| `MLOANINT` loan interest | Business | Currently blank (64 rows) |
| `TERMDATE` plan availability | Business | Currently open (64 rows) |
| ISSCNTRY/ISSUEST variation | Business | Currently default `0000/00` only |
| Large factor runtime parsing | QLAdmin tester | Confirm >9999.99 text factors display correctly |

---

## Actuarial assumptions deferred (not sandbox blockers)

These remain blank placeholders in rate-key tables. **Do not block R6B testing** because of them.
Reserve/NP/CV *calculation completeness* may be partial until supplied:

- MORT, ETIMORT
- RSVINT, RSVMETH
- INTMETHCV, INTMETHTV
- NFOINT, STOREMEANS, CALCMIDS

---

## What must occur before production usage

1. **R6B sandbox UAT complete** — all 60 validation tests executed; failures resolved or accepted with business sign-off.
2. **Actuarial assumptions populated** — re-emit rate keys; re-validate CV/TV/NP behavior.
3. **Member business values supplied** — `BDLOWVAL`, `MLOANINT`, `TERMDATE` where production depends on them.
4. **Production import runbook approved** — separate from R6B; includes production backup, change control, and rollback.
5. **Business sign-off** — product, actuarial, and operations stakeholders.

---

## Open risks

| Risk | Severity | Mitigation |
|---|---|---|
| Deferred actuarial assumptions | Medium | Expected; document partial reserve/CV calc behavior in UAT |
| Large text factors at runtime | Low–Medium | Explicit UAT on `2665ST` / `A96DAR` |
| Default state/country only | Low | Confirm no plan requires state-specific segmentation |
| Band breakpoint placeholders | Medium | Supply `BDLOWVAL` before band-dependent production behavior |
| No ground-truth QLAdmin population (R3) | Info | Value validation occurs in sandbox, not against reference DBFs |

---

## Rollback safety

- R6B is documentation + read-only artifacts only — **zero conversion risk**
- Sandbox import reversible via pre-import backup
- Production environments **untouched**
- Emitted DBFs are not modified during R6B

---

## Commands to regenerate artifacts

```bash
# R6B package (manifest + validation matrix + lookup trace)
python plan_analysis/phase_r6b_sandbox_import_execution/_build_r6b_package.py

# Related packages (if DBFs re-emitted)
python plan_analysis/phase_r5_rate_loader/rate_loader_emit.py
python plan_analysis/phase_r5_rate_loader/effdate_verification.py
python plan_analysis/phase_r6_qla_rate_import_validation/_build_r6_package.py
python plan_analysis/phase_r6a_member_table_validation/_build_r6a_package.py
```

---

## Code changes (R6B)

**None** to `app.py`, `qla_core`, emitted DBFs, product governance, or claims logic.
New read-only artifacts under `plan_analysis/phase_r6b_sandbox_import_execution/` only.
