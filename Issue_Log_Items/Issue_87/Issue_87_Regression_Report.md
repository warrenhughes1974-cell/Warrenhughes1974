# Issue #87 — Regression Report

**Issue:** #87 — QuikForge Balancing feature — source-to-QLAdmin reconciliation report  
**Framework stage:** Regression Agent (G6)  
**Engine version:** **v58.14**  
**Baseline:** Risk evidence row counts + Output on disk pre/post v58.14 (2026-07-19; no batch re-run)  
**Output directory:** `QLA_Migration/Output/`  
**Generated:** 2026-07-19  
**Verdict:** **PASS**

---

## 1. Scope of Change (expected)

| Component | Expected impact |
|-----------|-----------------|
| `qla_core/balancing.py` | **New** read-only report module |
| `QLA_Migration/Balancing/` | **New** report artifacts |
| QuikForge UI | **+ Balancing** button (thread runner) |
| `APP_VERSION` | v58.13 → v58.14 |
| quik* conversion output | **No change** |
| Sync_Rulebook_*.csv | **No change** (Issue #87 scope) |
| MPREM / MPOLICY emit logic | **No change** |

---

## 2. Row Count Comparison

| Table | Before (Risk baseline) | After (current Output) | Delta | OK? |
|-------|----------------------:|-------------------------:|------:|:---:|
| quikmstr | 5,084 | 5,084 | 0 | **Yes** |
| quikridr | 6,936 | 6,936 | 0 | **Yes** |
| quikclnt | 13,532 | 13,532 | 0 | **Yes** |
| quikclid | 32,176 | 32,176 | 0 | **Yes** |
| quikbenf | 5,852 | 5,852 | 0 | **Yes** |
| quikprmh | 201,572 | 201,572 | 0 | **Yes** |
| quikloan | 365 | 365 | 0 | **Yes** |
| quikdvdp | 5,084 | 5,084 | 0 | **Yes** |
| quikdvpr | 28 | 28 | 0 | **Yes** |
| quikplan | — | 141 | — | N/A |

**Fleet impact:** **Zero** unintended row-count drift on balancing-scoped tables.

---

## 3. Non-Target Field Diff (affected tables)

Issue #87 does not modify conversion emit. No quik* cell diffs expected or observed.

| Table | Column | Rows changed | OK? |
|-------|--------|-------------:|:---:|
| All quik* tables | All columns | **0** (no re-batch) | **Yes** |

Balancing runs write **only** to `QLA_Migration/Balancing/` — verified no `Balancing_*` files under `Output/`.

---

## 4. Prior Issue Fix Regression

### Issue #25 — MPOLICY padding

| Check | Result |
|-------|--------|
| `tools/validators/validate_mpolicy_width.py` | **PASS** — all MPOLICY fields exactly 10 characters (5,084 rows) |

### Issue #26 — MPREM mapping

| Check | Result |
|-------|--------|
| `tools/validators/validate_issue26_mprem.py` | **N/A** — expects 20260530 extracts (not in Source/) |
| Output spot-check (MPREM / MMODEPREM on sample policies) | **PASS** — values present; no Issue #87 engine change |

---

## 5. Schema Integrity (AGENTS.md)

| Check | Result |
|-------|--------|
| Field order preserved | **PASS** — no schema emit changes |
| Field types/lengths preserved | **PASS** |
| No new blank MRIDRID | **PASS** — read-only issue |
| QLA formatting rules preserved | **PASS** |
| Output folder policy (CSV load package only) | **PASS** — reports in `Balancing/` |

---

## 6. Batch / Fleet Checks

| Check | Result |
|-------|--------|
| Full batch re-run for v58.14 | **Not required** — additive read-only feature |
| Issue #87 validator | **PASS** (exit 0) |
| Governance Audit UI path | **Unchanged** — separate button |
| Claims / rates converters | **Unchanged** |

---

## 7. Failures (if any)

None.

---

## 8. Recommendation

- [x] Advance to **Closure Agent** / **Ready for Client UAT**
- [ ] Return to Development Agent

**Client UAT suggestion:** Click **Balancing** in QuikForge after a Full Batch; confirm report opens and `Balancing_Methodology.md` is readable alongside the CSV.

---

## Appendix

- Validation report: `Issue_Log_Items/Issue_87/Issue_87_Validation_Report.md`
- Latest balancing report: `QLA_Migration/Balancing/Balancing_Report_20260719_195536.csv`
- Issue #87 changed files (dev scope): `qla_core/balancing.py`, both `app.py`, `Balancing/`, `balancing_exclusions.csv`
