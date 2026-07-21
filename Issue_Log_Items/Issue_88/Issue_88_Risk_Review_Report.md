# Issue #88 — Risk Review Report

**Issue:** #88 — ISWL QuikIssc / QuikUint empty in batch CSV package (D1 + D2)  
**Framework stage:** Risk Agent (G3)  
**Status:** **GO → Ready for Development** (pending explicit user approval)  
**Generated:** 2026-07-21  
**Model:** Cursor Grok 4.5 (locked)  
**Status note:** Risk analysis only — no production code changes.  
**Depends on:** Dependency Gate **PASS** (`Issue_88_Dependency_Gate.md`)  
**Scope locked:** `Issue_88_Scope_Decisions.md`  
**Parent:** `Issue_ISWL` defects D1 / D2 (Sujitha 2026-07-20)

---

## Go / No-Go Recommendation

**GO** — Confirmed packaging/config defects with known healthy loaders and a proven correct emit pattern already in the R5 CLI. Fix restores intended Phase5/Phase6 outputs (QuikIssc **8** rows; QuikUint **32** rows) without changing rate math, allowlists, or policy conversion. Blast radius is confined to `qla_core/rate_emit.py` CSV branch + three config paths. Residual risk (partial-emit still allowing empty tables if paths break again) is mitigated by Validation gates; optional hardening listed below is **recommended but not required** for GO.

| Factor | Assessment |
|--------|------------|
| Symptom | QuikIssc + QuikUint header-only in batch CSV package |
| Root cause | D1 missing CSV writes; D2 stale 20260629 PDINT/PSEGT paths |
| Dependency Gate | PASS |
| Policy conversion rows impacted | **0** |
| Rate factor/key/member tables | **Untouched** (emit order unchanged; only add Issc/Uint CSV) |
| Loader / schedule / allowlist | **Untouched** |
| Primary risk | Shipping wrong QuikUint if wrong PDINT file chosen |
| Mitigation | Use present 20260630 files; validate against Phase5 baseline (32 rows / 8 MPLANs) |
| Client answers required | **None** for this issue |

Development may proceed after user says **Approved for Development** and switches to **Composer 2.5**.

---

## 1. Current vs Proposed Mapping

This issue does **not** change LifePRO→QLAdmin field mappings. It restores missing file writes and corrects extract paths.

| Surface | Current | Proposed | Change? |
|---------|---------|----------|---------|
| QuikIssc loader | Builds 8 rows | Unchanged | **No** |
| QuikUint loader | Builds 0 (missing PDINTTBL path) | Builds 32 with 20260630 paths | **Config only** |
| `rate_emit.py` CSV branch | Omits Issc/Uint writes | Write CSV when rows present | **Yes** (surgical) |
| `rate_emit.py` DBF branch | Already writes Issc/Uint | Unchanged | **No** |
| `rate_loader_config.json` | `*_20260629` PDINT/PSEGT | `*_20260630` | **Yes** |
| Factor tables (Coi/Cvs/Gps/…) | Emit as today | Unchanged | **No** |
| Policy tables / Sync_Rulebooks | — | Unchanged | **No** |
| `APP_VERSION` | Current | **No bump** unless Dev also edits `app.py` | Prefer **No** |

---

## 2. Premium / Related Fields Untouched

| Target | Touched? |
|--------|----------|
| quikmstr / quikridr / quikplan policy fields | **No** |
| QuikGps / QuikCoi / QuikGcoi values | **No** |
| QuikIssc SCHG schedule values | **No** (emit only) |
| QuikUint tier rates / merge rules | **No** (config path only) |
| Issue #25 / #26 | **No** |
| Sync_Rulebook_*.csv | **No** |

---

## 3. Repo References (touch points for Dev)

| Location | Role | Risk |
|----------|------|------|
| `qla_core/rate_emit.py` ~208–228 | **Add** QuikUint + QuikIssc CSV writes before manifest | Low — copy DBF/CLI pattern |
| `qla_core/rate_dbf_writer.py` | Existing `write_quik*_csv` | Read-only reuse |
| `plan_analysis/.../rate_loader_config.json` | Repoint 3 paths | Low — files verified present |
| `rate_loader_config.example.json` | Align example paths if stale | Docs/config only |
| `tools/validators/iswl_quikissc_reconcile.py` | Validation gate | No code change required |
| `tools/validators/iswl_quikuint_reconcile.py` | Validation gate | No code change required |
| `app.py` / `QLA_Migration/app.py` | Prefer **untouched** | Avoid version churn |

---

## 4. Population Analysis (package impact)

| Metric | Before (7/19 package) | After (expected) |
|--------|----------------------:|-----------------:|
| QuikIssc data rows | **0** | **8** |
| QuikUint data rows | **0** | **32** (4 tiers × 8 MPLANs) |
| QuikIssc plans with SCHG | 0 | 8 incl. 1659CR / 1659SR / 1669SR |
| Policy conversion rows changed | 0 | **0** |
| Factor table row deltas (Coi/Cvs/Gps/…) | — | **0 expected** |

### QuikUint expected tiers (Phase5 baseline)

| MEFFDATE | MCURRATE / MGTDRATE |
|----------|---------------------|
| 19800101 | 11.0000 |
| 19890101 | 9.0000 |
| 19990101 | 5.0000 |
| 20020101 | 4.5000 |

Source: `Issue_Log_Items/Issue_32/output/baselines/iswl_quikuint_regression_baseline.json` (`quikuint_rows: 32`).

### QuikIssc expected schedule (Phase6)

Hub `659 CEN II` SL durations 1–14: 100,100,70,60,50,40,30,20,15,10,8,6,4,2 (%). One row per MPLAN; AGE=0; GENDER=M.

---

## 5. Fallback Recommendation

| Option | Assessment |
|--------|------------|
| A. Fix D1 + D2 together (Planning plan) | **Recommended — GO** |
| B. Fix D1 only (Issc); leave Uint empty | Reject — Sujitha also needs interest; same emit path |
| C. Manual copy of Phase6 CSV into Output | Reject as permanent fix — will regress on next batch |
| D. Invent QuikIssc rows without loader | **Reject** |
| E. Change PARTIAL_EMIT_BLOCKERS this issue | **Optional follow-on** — do not block GO |

**Recommended fallback if Validation fails after Dev:** revert `rate_emit.py` + config path edits; leave prior empty CSVs; do not ship partial Issc without Uint when phase5 enabled.

---

## 6. Trace Plans (rate package)

| Plan | QuikIssc before | QuikIssc after | QuikUint before | QuikUint after |
|------|----------------:|---------------:|----------------:|---------------:|
| 1658CS | 0 | 1 | 0 | 4 |
| 1659CR | 0 | 1 | 0 | 4 |
| 1659SR | 0 | 1 | 0 | 4 |
| 1669SR | 0 | 1 | 0 | 4 |
| 1679CS | 0 | 1 | 0 | 4 |
| (all 8) | 0 | 8 | 0 | 32 |

No policy-level MPOLICY traces — rate tables only.

---

## 7. Material Calculation Impact

| Area | Impact |
|------|--------|
| Surrender charge math | None — restores approved schedule to package |
| Credited interest math | None — restores Phase5 tiers to package |
| COI / GPS / CV | None |
| Guideline premium / quikspec | None (out of scope) |
| ISWL account values in QLAdmin UAT | **Positive** — Sujitha can load non-empty Issc/Uint |

---

## 8. Prior Fix Preservation

| Check | Result |
|-------|--------|
| Issue #25 MPOLICY padding | **Preserved** (untouched) |
| Issue #26 MPREM / MMODPREM | **Preserved** |
| Issue #31 COI/GCOI | **Preserved** |
| Issue #32 QuikUint design | **Preserved** — re-enable via correct paths |
| Issue #33 QuikIssc design | **Preserved** — re-enable via CSV write |
| Issue #40 CV inheritance | **Preserved** |
| Issue #51 QuikAint stubs | **Preserved** (existing CSV write stays) |
| Issue A A10 QuikUwpo | **Preserved** |

---

## 9. Conditional soft recommendation (non-blocking)

**Partial-emit silence:** `PARTIAL_EMIT_BLOCKERS` includes `V-UINT-PDINT`, `V-ISSC-RATE`, `V-ISSC-SL`, which allowed the 7/19 batch to succeed with empty Issc/Uint CSVs.

| Recommendation | In #88 Dev? |
|----------------|-------------|
| After Fix A/B, Validation must assert non-empty Issc/Uint when phases enabled | **Yes — required** |
| Log explicit `RATE_LOG` lines with Issc/Uint row counts on emit | **Yes — recommended** (low risk) |
| Remove UINT/ISSC from `PARTIAL_EMIT_BLOCKERS` | **No for #88** — defer; could block CV package on transient path errors |

---

## 10. Regression Testing Checklist (for Validation Agent)

- [ ] QuikIssc.csv: **8** data rows; plans = full ISWL allowlist including 1659CR/1659SR/1669SR  
- [ ] QuikIssc: AGE=0; SCHG01–14 match hub schedule; SCHG15–20 blank  
- [ ] `iswl_quikissc_reconcile.py` PASS  
- [ ] QuikUint.csv: **32** data rows; 4 tiers × 8 MPLANs; rates match Phase5 baseline  
- [ ] `iswl_quikuint_reconcile.py` PASS; no `V-UINT-PDINT`  
- [ ] `rate_csv_manifest.csv` counts match files  
- [ ] QuikCoi / QuikGcoi / QuikGps / QuikCvs row counts unchanged vs pre-fix snapshot  
- [ ] Publish modified rate CSVs only to `Output/Test_Validation/rates/` on PASS  

---

## 11. Recommended Development Agent Task

1. In `qla_core/rate_emit.py` CSV branch (after QuikUwpo/QuikAint, before `_write_csv_manifest`): write QuikUint.csv and QuikIssc.csv when `res.quikuint_rows` / `res.quikissc_rows` are non-empty; append manifest entries; add RATE_LOG messages with row counts.  
2. In `rate_loader_config.json` (and example if needed): repoint `psegt_csv`, `pdint_extract`, `pdinttbl_extract` to `*_20260630.csv`.  
3. Do **NOT** change loaders, allowlists, SL schedule, COI/GCOI, Sync_Rulebooks, or policy converters.  
4. Prefer **no** `app.py` / `APP_VERSION` bump.  
5. Re-run rate emit; run Issc + Uint reconcile validators; snapshot factor-table row counts for regression.  
6. On PASS: copy `QuikIssc.csv` + `QuikUint.csv` (+ manifest if useful) to `QLA_Migration/Output/Test_Validation/rates/`.  
7. Write `Issue_88_Implementation_Notes.md`.  

**Model for Development:** **Composer 2.5** (locked).

---

## Gate decision

| Gate | Result |
|------|--------|
| G0 Intake | PASS |
| G1 Planning | PASS |
| G2 Dependency | PASS |
| **G3 Risk** | **GO** |
| Development | Awaiting user: **Approved for Development on Issue 88** (+ Composer 2.5) |

**Recommended tracking status:** **Ready for Development**
