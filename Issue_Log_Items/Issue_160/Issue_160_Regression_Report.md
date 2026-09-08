# Issue #160 — Regression Report

**Issue:** #160 — PUA phase stays Expired (56) instead of following base terminal status
**Framework stage:** Regression Agent
**Engine version:** v59.09
**Baseline:** `QLA_Migration/Archive/issue160_pre_remap/quikridr_pre_issue160.csv`
**Output directory:** `QLA_Migration/Output/`
**Generated:** 2026-09-08
**Verdict:** **PASS**

---

## 1. Scope of Change (expected)

| Component | Expected impact |
|---|---|
| Target table/field | `quikridr.MPHSTAT` on PUA rows only — 239 rows |
| Other tables | No row count change |
| Other fields | No change |

---

## 2. Row Count Comparison

| Table | Before | After | Delta | OK? |
|---|---:|---:|---:|-----|
| quikmstr | 5,083 | 5,083 | 0 | Yes |
| quikridr | 6,956 | 6,956 | 0 | Yes |
| quikprmh | 211,709 | 211,709 | 0 | Yes |
| quikplan | 142 | 142 | 0 | Yes |
| quikclid | 32,285 | 32,285 | 0 | Yes |
| quikclnt | 13,598 | 13,598 | 0 | Yes |
| quikbenf | 5,916 | 5,916 | 0 | Yes |
| quikdvdp | 5,083 | 5,083 | 0 | Yes |

Counts match the #159 Regression Report baseline (2026-09-02) exactly for every table other than `quikridr`'s intentional target — confirming no drift since the last Closed issue's regression pass.

---

## 3. Non-Target Field Diff (quikridr)

| Check | Result |
|---|---|
| Columns other than MPHSTAT | 0 rows changed (independently confirmed in Validation §4/§5) |
| MPOLICY / MPAR / MPLAN / MEFFDATE / MAGE / MPAYUP | 0 of 6,956 changed |
| Row count | 6,956 / 6,956 unchanged |

---

## 4. Prior Issue Fix Regression

Catalog: `Issue_Log_Items/Completed_Issues_Release_Validation_Guide.md`

### Issue #2 / #25 — Policy key width

| Check | Result |
|---|---|
| `#2 MPOLICY width-11` (release smoke) | **PASS** |

### Issue #60 — PUA phase rules (direct overlap — this is the function #160 modified)

| Check | Result |
|---|---|
| `tools/validators/validate_issue60_pua_phase.py` | **PASS** — "Issue #60 Track A PUA phase rules; NFO PUA terminated per #108D". Cross-release CLASS_A_WARN (informational midyear v57.85 baseline drift, not same-cut) — pre-existing, not a #160 regression. |

### Issue #105 / #119 — PUA MPAR=0

| Check | Result |
|---|---|
| `tools/validators/validate_issue105_mpar.py` | **PASS** — 494 PUA rows, all non-PUA plan-PAR logic intact |
| `tools/validators/validate_issue119_pua_mpar.py` | **PASS** — 494/494 PUA rows still MPAR=0 |

### Issue #55 — MUNIT floor / decimal formatting

| Check | Result |
|---|---|
| `tools/validators/validate_issue55_munit_floor.py` | **PASS** — 0 sub-floor MUNIT, 0 leading-dot fields, trace policies pass |

### Issue #159 — plan-aware MUWCLASS (same table, different column)

| Check | Result |
|---|---|
| `tools/validators/validate_issue159_muwclass_plan_aware.py` (release smoke) | **PASS** |

### Other Closed rows overlapping `quikridr` (release smoke suite)

| Issue | Smoke | Result |
|---|---|---|
| #71 BAND=00 | `#71 BAND=00` | PASS — 12,418 band cells all 00 |
| #98 QuikCvs endpoint | `#98 QuikCvs endpoint` | PASS |
| #138 rate/age alignment | `#138 QuikGps age vs LifePRO premium` | PASS |
| #140 attained-age axis | `#140 attained-age storage axis` | PASS |
| #143 BF RPU MUNIT | `#143 BF RPU MUNIT` | PASS |
| #158 PR segment ownership | `#158 PR segment SEQ 1 ownership` | PASS |
| #142 SL rider 9SUBLF | `#142 SL rider 9SUBLF` | PASS |

### Pre-existing, unrelated FAIL (not a #160 regression)

| Check | Result |
|---|---|
| `tools/validators/validate_issue59_mstatus.py` (release smoke) | **FAIL** — Death-claim expectation: `9010521213C` and `901ML8250C` expected `MSTATUS=53` per the current 8/31 active source (`CONTRACT=T/DC` → `ST_T_DC=53`), but Output's base phase/policy status has not been refreshed to that value. **Identical to the FAIL already documented in `Issue_Log_Items/Issue_159/Issue_159_Regression_Report.md` (2026-09-02)** — same two named policies, same expected value, pre-dates #160 by six days. Not caused by, or worsened by, this fix. |

**Note on `9010521213C`:** this policy is also one of #160's own trace/example policies (base phase MPHSTAT=50, PUA phase corrected 22→50). The #59 gap means the base phase itself is stale (source now implies 53, Output still shows 50) — a pre-existing data-refresh issue, not a #160 defect. #160's fix is base-status-agnostic: whatever base phase 1 shows in Output is what the PUA phase now follows, so once #59 is remediated and base phase 1 is refreshed to 53, the PUA phase will automatically follow to 53 on the next remap/batch — no #160 code change will be needed.

---

## 5. Schema Integrity (AGENTS.md)

| Check | Result |
|---|---|
| Field order preserved | PASS — quikridr header identical to archive |
| Field types/lengths preserved | PASS |
| No new blank MRIDRID | N/A — field not touched |
| QLA formatting rules preserved | PASS — CRLF line endings confirmed restored (see Validation Report §9) |

---

## 6. Batch / Fleet Checks

| Check | Result |
|---|---|
| Full policy batch | No — scoped `MPHSTAT`-only remap of `quikridr`; `app.py` wired for next full batch |
| `validate_release_closed_issues.py --smoke-only` | **RELEASE_BLOCKED** — solely on pre-existing #59 FAIL (above); every other high-risk smoke (23 jobs) **PASS**, including #159 and every quikridr-adjacent Closed issue |
| Audit log anomalies | None |

---

## 7. Failures

None attributable to #160. The single release-gate FAIL (#59 MSTATUS allowlist) is a pre-existing, previously-documented gap (first recorded in #159's Regression Report, 2026-09-02) unrelated to this fix's scope (`quikridr.MPHSTAT` on PUA rows only).

---

## 8. Recommendation

- [x] Advance to **Closure Agent**
- [ ] Return to **Development Agent**

---

## Appendix

- Before snapshot: `QLA_Migration/Archive/issue160_pre_remap/quikridr_pre_issue160.csv`
- Independent Validation: `Issue_Log_Items/Issue_160/Issue_160_Validation_Report.md`
- Release gate report: `QLA_Migration/Reports/release_closed_issues_gate_latest.md`
