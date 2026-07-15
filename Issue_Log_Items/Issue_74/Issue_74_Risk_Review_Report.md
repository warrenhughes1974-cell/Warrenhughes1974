# Issue #74 — Risk Review Report

**Issue:** #74 — Var DB Code (`VARDB`) `4` → `0` only  
**Framework stage:** Risk Agent  
**Status:** **Go → Ready for Development** (pending explicit user approval)  
**Generated:** 2026-07-15  
**Model:** Cursor Grok 4.5 (locked)  
**Status note:** Risk analysis only — no production code changes.  
**Evidence:** `evidence/issue74_risk_impact_summary.csv` · `evidence/issue74_risk_vardb_simulation.csv` · `evidence/issue74_risk_structure_plans_unchanged.csv` · `scripts/risk_review_issue74_vardb.py`

---

## Go / No-Go Recommendation

**GO** — Single Sync Rulebook default change (`VARDB` `4` → `0`); Option B left on so structure plans stay `1`/`2`/`3`; impact fully quantified (121 change / 20 unchanged).

| Factor | Assessment |
|--------|------------|
| Scope | `quikplan.VARDB` only — plans currently at `4` |
| Impact | **121 / 141** rows `4` → `0` |
| Preserved | **20** plans at `1`/`2`/`3` unchanged (all have QuikPlDb keys) |
| Engine touch | **None required** if Option B stays enabled (default `AUTO_APPLY=false`; Option B still applies `1`/`2`/`3`) |
| #25 / #26 | Untouched |
| Governance | `Data_Goverence.txt` “VARDB ≠ 4 → QuikDbs/QuikPlDb” will apply to the 121 `0` plans; do **not** rebuild rates in this issue — advisory/audit only unless client expands |

Development may proceed after user says **Approved for Development** and switches to **Composer 2.5**.

---

## 1. Current vs Proposed Mapping

| Field | Current | Proposed | Change? |
|-------|---------|----------|---------|
| `quikplan.VARDB` (default plans) | Rulebook default `4` | Rulebook default **`0`** | **Yes** (121 rows) |
| `quikplan.VARDB` (structure plans) | Option B `1`/`2`/`3` | Unchanged | **No** (20 rows) |
| `quikplan.VARGP` | `4` fleet-wide | Unchanged | **No** |
| Option B `apply_vardb_structure_overrides*` | Active | **Keep active** | **No** |

---

## 2. Premium / Related Fields Untouched

| Target | Touched? |
|--------|----------|
| MPOLICY padding (#25) | **No** |
| quikridr.MPREM / MMODPREM (#26) | **No** |
| VARGP | **No** |
| LOANINTX (#70) | **No** |
| `*VARY*` / PLANVALOPT (R7B) | **No** |
| QuikDbs / QuikPlDb content | **No** |
| quikmstr / quikridr | **No** |
| Other Sync Rulebooks | **No** |

---

## 3. Repo References

| Location | Role |
|----------|------|
| `QLA_Migration/Configs/Sync_Rulebook_quikplan.csv` | `,VARDB,4,,,` — **only change site** |
| `qla_core/quikplan_converter.py` | Option B `apply_vardb_structure_overrides*` — **do not disable** |
| `QLA_Migration/Configs/variation_classification_config.example.json` | `AUTO_APPLY_VARIATION_CODES: false` (full auto-apply off) |
| `QLA_Migration/Data_Goverence.txt` | If VARDB ≠ 4, validate QuikDbs/QuikPlDb |
| `tools/validators/validate_issue72_mnfopt_status.py` | Life-with-CV alternate: QuikPlCv **or** VARDB≠0 |

**Grep confirmation:** No need to hardcode VARDB in `app.py`; blank-source default from rulebook + Option B post-process.

---

## 4. Population Analysis (simulated on current Output)

| Metric | Count |
|--------|------:|
| quikplan rows | 141 |
| VARDB = 4 (before) | 121 |
| VARDB ∈ {1,2,3} (before) | 20 |
| VARDB = 0 (before) | 0 |
| **Would change `4` → `0`** | **121** |
| **Unchanged (structure)** | **20** |
| Residual `VARDB=4` after (target) | **0** |
| After distribution | 0:121 · 1:3 · 2:7 · 3:10 |

### Breakdown

| Dimension | rows | would_change |
|-----------|-----:|-------------:|
| VARDB=4 (rulebook default) | 121 | 121 |
| VARDB=3 | 10 | 0 |
| VARDB=2 | 7 | 0 |
| VARDB=1 | 3 | 0 |

Structure keep-list (20): `130JEB`, `1659SR`, `17CSI3`, `17CSI5`, `17CSI7`, `1970JB`, `1CSIMN`, `1L16GD`, `2665ST`, `542STR`, `578STR`, `719CDT`, `7619DT`, `7619PU`, `7647FP`, `7647SP`, `7686S3`, `7690DT`, `9L16PF`, `A60MIR` — **20/20 have QuikPlDb**.

---

## 5. Fallback Recommendation

| Option | Rows changed | Assessment |
|--------|-------------:|------------|
| **A. Rulebook `4`→`0`, keep Option B (recommended)** | 121 | Matches client clarification |
| B. Rulebook + disable Option B (force all to 0) | 141 | **Reject** — violates revised scope |
| C. Post-map force only rows currently `4` in `app.py` | 121 | Reject — unnecessary if rulebook + Option B already yield this |
| D. Leave rulebook at `4` | 0 | Reject — fails client |

**Recommended:** Option A. No fallback needed.

---

## 6. Trace Plans

| PLAN | VARDB before | After | VARGP (must stay) | Pass? |
|------|--------------|-------|-------------------|-------|
| `920ADB` | 4 | **0** | 4 | Yes |
| `965ADB` | 4 | **0** | 4 | Yes |
| `960ADB` | 4 | **0** | 4 | Yes |
| `130JEB` | 3 | **3** | 4 | Yes (keep) |
| `17CSI3` | 2 | **2** | 4 | Yes (keep) |
| `1659SR` | 1 | **1** | 4 | Yes (keep) |
| `A60MIR` | 2 | **2** | 4 | Yes (keep) |

Full fleet simulation: `evidence/issue74_risk_vardb_simulation.csv`.

---

## 7. Top Changes

Not numeric magnitude. Uniform transition for in-scope rows: `4` → `0`. Largest “class” = all 121 default plans.

---

## 8. Material Calculation Impact

| Area | Impact |
|------|--------|
| Premium / MPREM | None |
| CV / QuikCvs lookup | Structure plans still VARDB≠0; default plans rely on QuikPlCv (unchanged emit) |
| Issue #72 NFO life-with-CV check | Still PASS expected — QuikPlCv primary; structure plans keep VARDB≠0 alternate |
| QuikDbs rebuild | **Not in scope** — advisory governance may flag VARDB=`0` without DB tables |

Intentional correction only; no accidental premium/CV math drift from this field alone.

---

## 9. Prior Fix Preservation

| Check | Result |
|-------|--------|
| Issue #25 MPOLICY padding | **Preserved** — not touched |
| Issue #26 MPREM / MMODPREM | **Preserved** — not touched |
| Issue #70 LOANINTX | **Preserved** |
| Issue #72 MNFOPT | **Preserved** — re-run validator after as guard |

---

## 10. Regression Testing Checklist (for Validation Agent)

- [ ] `count(VARDB=4) = 0` on Output `quikplan.csv`
- [ ] `count(VARDB=0) = 121` (or equal to pre-fix count of `4`)
- [ ] Structure plans unchanged: all 20 in `issue74_risk_structure_plans_unchanged.csv` still `1`/`2`/`3`
- [ ] Spot-check: `920ADB`→`0`; `130JEB`→`3`; `17CSI3`→`2`; `1659SR`→`1`
- [ ] `VARGP` still all `4` (no drift)
- [ ] Row count `quikplan` still 141
- [ ] #25 / #26 untouched (no quikmstr/quikridr publish required)
- [ ] Re-run `tools/validators/validate_issue72_mnfopt_status.py` — expect PASS
- [ ] On PASS: publish **only** `quikplan.csv` to `Output/Test_Validation/`

---

## 11. Recommended Development Agent Task

1. Edit `QLA_Migration/Configs/Sync_Rulebook_quikplan.csv`: change `VARDB` Default_Value from `4` to `0`.
2. **Do NOT** disable or alter `apply_vardb_structure_overrides*` / Option B.
3. **Do NOT** change `VARGP`, other rulebooks, `app.py` (unless a version bump is somehow required — prefer rulebook-only; **no APP_VERSION bump** if only rulebook changes).
4. Re-emit / batch so `Output/quikplan.csv` refreshes (or surgically regenerate quikplan if that is the standard path).
5. Add `Issue_Log_Items/Issue_74/scripts/validate_issue74_vardb.py` — FAIL if any `VARDB=4`; FAIL if any of the 20 structure plans drifted from baseline `1`/`2`/`3`; assert sample traces.
6. On validator PASS: copy modified `quikplan.csv` to `Output/Test_Validation/`.
7. Switch model: **Composer 2.5** for Development after **Approved for Development**.

---

## Gate Criteria (G3)

- [x] Risk report published with Go/No-Go
- [x] Impact quantified (121 / 20)
- [x] Unrelated fields marked untouched
- [x] #25 / #26 preservation confirmed
- [ ] User acknowledgment — await **Approved for Development**

---

## Appendix

- Impact summary: `Issue_Log_Items/Issue_74/evidence/issue74_risk_impact_summary.csv`
- Full simulation: `Issue_Log_Items/Issue_74/evidence/issue74_risk_vardb_simulation.csv`
- Structure keep list: `Issue_Log_Items/Issue_74/evidence/issue74_risk_structure_plans_unchanged.csv`
- Script: `Issue_Log_Items/Issue_74/scripts/risk_review_issue74_vardb.py`
