# Issue 172 — Validation Report

**Issue:** 172 — Fleet-wide shared underwriting-class rate key completion  
**Framework stage:** Validation Agent (Stage 6 / G5)  
**Engine version:** v59.20 (both `app.py` and `QLA_Migration/app.py`)  
**Validation script:** `tools/validators/validate_issue172_shared_uw_keys.py`  
**Output directory:** `QLA_Migration/Output/` (quikplan/quikridr anchors); rates proof under issue-local staging  
**Before snapshot:** N/A (OFF staging = copy of current Output/rates)  
**Generated:** 2026-09-22  
**Verdict:** **PASS** (durable full staged emit and isolated package delta proven)

---

## Commands Run

```text
python -m unittest qla_core.tests.test_issue172_shared_uw_keys -v
→ 8/8 OK

python -m py_compile qla_core/issue172_shared_uw_keys.py qla_core/rate_emit.py tools/validators/validate_issue172_shared_uw_keys.py
→ OK

# Initial issue-local runner attempt (superseded harness/path failure)
python Issue_Log_Items/Issue_172/evidence/validation/logs/_emit_runner.py off
→ FAILED RC=1: missing QLA_Migration/Source/Rate_Table_Extract_Txt.txt

# Successful root-context durable emit
qla_core.rate_emit.run_rate_emit(
  config=plan_analysis/phase_r5_rate_loader/rate_loader_config.json,
  csv_dir=Issue_Log_Items/Issue_172/evidence/validation/full_on_rates
)
→ SUCCESS RC=0; blockers=0; 23 tables; 274,030 CSV rows
→ resolver fallback: plan_analysis/source_data/rates/Rate_Table_Extract_20260427.csv
→ Issue #172 hook: inserted=5,056; identical_noop=0

python tools/validators/validate_issue172_shared_uw_keys.py --rates-dir .../full_on_rates
→ PASS

# Isolated integration proof (same replication as rate_emit hook)
robocopy QLA_Migration/Output/rates → evidence/validation/off_rates and on_rates
apply_to_rates_directory(off, env QLA_ISSUE172_SHARED_UW_KEYS=0)
apply_to_rates_directory(on,  env QLA_ISSUE172_SHARED_UW_KEYS=1)

python tools/validators/validate_issue172_shared_uw_keys.py --rates-dir .../off_rates  → FAIL (expected)
python tools/validators/validate_issue172_shared_uw_keys.py --rates-dir .../on_rates   → PASS
python tools/validators/validate_issue172_shared_uw_keys.py                            → FAIL (full Output stale)

python tools/validators/validate_issue136_pvo_flags.py                                 → PASS (current Output)
python tools/validators/validate_issue159_muwclass_plan_aware.py                       → PASS (current Output quikridr)
python tools/validators/validate_issue168_l14_reserve_class_replication.py             → PASS (current Output)
python tools/validators/validate_issue168_l14_reserve_class_replication.py --output-dir .../wrap_on_output  → PASS
python tools/validators/validate_issue168_l14_reserve_class_replication.py --output-dir .../wrap_off_output → PASS
```

---

## 1. Trace Policy Results

| Policy | Plan | Field | Expected | Actual | Result |
|--------|------|-------|----------|--------|--------|
| 9011006697C | 1659C2 | MUWCLASS (phase 1) | PR | PR | PASS |
| 9010713704C | 1659C2 | MUWCLASS (phase 1) | PR | PR | PASS |
| 9010718276C | 1659C2 | MUWCLASS (phase 1) | ST | ST | PASS |
| 9011006697C / 9010713704C | 1659C2 | QuikCvs/QuikPlCv PR (ON) | Present; == ST except UWCLASS | PR=1082 / PlCv PR=2; payloads match | PASS |
| 9010718276C | 1659C2 | QuikCvs ST | Unchanged | ST=1082 OFF/ON | PASS |
| — | 1659C2 | UWVARYCV | N | N | PASS |
| — | 1658C1 | CV PR vs ST | Distinct (Category C) | 738/1032 keys differ | PASS |
| — | 1659C2 | QuikCvs NT/PQ | Absent | None | PASS |

---

## 2. Acceptance Criteria

| # | Criterion | Result |
|---|-----------|--------|
| 1 | Feature OFF: no primary PR; validator FAIL | PASS |
| 2 | Feature ON: QuikCvs +1082 PR, QuikPlCv +2 PR | PASS |
| 3 | Headers/schema field order unchanged | PASS |
| 4 | No Category C collapse (1658C1) | PASS |
| 5 | No GP / MUWCLASS / UWVARY* changes | PASS |
| 6 | No unauthorized 1659C2 NT/PQ CV | PASS |
| 7 | L14 absorb idempotent | PASS (noop 3972; 0 inserts) |
| 8 | Closed #136 / #159 / #168 | PASS |
| 9 | APP_VERSION v59.20 both apps | PASS |
| 10 | Full Output/rates has 1659C2 PR | Pending release emit — expected G7 hold, not a G5 failure |

---

## 3. Source Alignment

| Check | Result |
|-------|--------|
| ST→PR identical except UWCLASS | PASS (1082/1082) |
| L14 already equal → noop | PASS |
| Conflict fail-closed | Unit tests 8/8 |
| Hook after `_finalize_equal_cv_tv_keys` | PASS (source order) |

---

## 4. Untouched Fields Confirmed

| Field / table | Check | Result |
|---------------|-------|--------|
| UWVARYCV 1659C2 | Remains N | PASS |
| quikridr MUWCLASS | Anchors + #159 PASS | PASS |
| QuikGps/Tvs/Nps/Nff/Dbs/Dvs | OFF vs ON hash SAME | PASS |
| QuikPlGp/Tv/Db/Dv/Uw/Uwpo | OFF vs ON hash SAME | PASS |
| 1658C1 QuikCvs | Distinct PR/ST | PASS |
| QuikCvs/QuikPlCv headers | Identical OFF vs ON | PASS |

---

## 5. Row Counts (OFF → ON)

| Table | Plan / class | OFF | ON | Delta |
|-------|--------------|----:|---:|------:|
| QuikCvs | 1659C2 ST | 1082 | 1082 | 0 |
| QuikCvs | 1659C2 PR | 0 | 1082 | **+1082** |
| QuikPlCv | 1659C2 ST | 2 | 2 | 0 |
| QuikPlCv | 1659C2 PR | 0 | 2 | **+2** |
| QuikCvs.csv file | all | 40950 | 42032 | +1082 |
| QuikPlCv.csv file | all | 260 | 262 | +2 |
| 1L14SC eight tables | four-class | equal | equal | 0 inserts |

ON summary: `inserted=1084 identical_noop=3972`. Changed file SHAs: QuikCvs.csv, QuikPlCv.csv only (22 other rate CSVs unchanged).

### Fresh full staged emit

| Table | Plan / class | Delta |
|-------|--------------|------:|
| QuikCvs | 1659C2 PR | **+1,082** |
| QuikPlCv | 1659C2 PR | **+2** |
| QuikTvs | 1L14SC PQ/PR/ST | **+996** |
| QuikNps | 1L14SC PQ/PR/ST | **+984** |
| QuikCvs | 1L14SC PQ/PR/ST | **+996** |
| QuikNff | 1L14SC PQ/PR/ST | **+972** |
| QuikPlTv / Cv / Db / Dv | 1L14SC PQ/PR/ST | **+6 each** |

Full staged summary: `inserted=5056 identical_noop=0`; inherited-rate verification PASS. The Issue #172 validator PASSed against this freshly generated package.

---

## 6. Impact Summary

| Metric | Value |
|--------|------:|
| Isolated current-package primary inserts | 1084 |
| Isolated current-package L14 identical no-ops | 3972 |
| Isolated current-package files changed | 2 |
| Fresh full-emitter inserts | 5056 |
| Fresh full-emitter blockers | 0 |
| Full Output/rates 1659C2 PR | still 0 |

---

## 7. Existing Closed-Issue Validators

| Issue | Target | Result | Notes |
|-------|--------|--------|-------|
| #136 | current Output | PASS | Output PVO proof — not staged-rates claim |
| #159 | current Output quikridr | PASS | Output MUWCLASS proof |
| #168 | current Output | PASS | L14 already four-class |
| #168 | staged ON wrap | PASS | After ON apply |
| #168 | staged OFF wrap | PASS | Pre-existing L14 |

---

## 8. Limitations

1. The initial issue-local runner failed before using the source resolver; that harness/path setup result is superseded by the successful root-context full staged emit and is not a production blocker.
2. `full_on_rates/` proves the durable fresh emit, including all L14 inserts. The isolated ON package proves the narrower delta against the current package.
3. **Full `Output/rates` remains intentionally stale** for 1659C2 PR until the release rate emit.
4. **G7 Closure is not available** — full-Output validator still fails; no SMOKE_JOBS registration yet; Validation stops here.

---

## 9. Test_Validation Publish

| Published path | Source |
|----------------|--------|
| `QLA_Migration/Output/Test_Validation/rates/QuikCvs.csv` | Isolated ON (current package + Issue #172 only) |
| `QLA_Migration/Output/Test_Validation/rates/QuikPlCv.csv` | Isolated ON (current package + Issue #172 only) |

The full staged emit is validation evidence only; it was not published to Test_Validation. Full `Output/rates` was not modified.

---

## 10. Failures

None for Option K scope.

---

## 11. Recommendation

- [x] Advance to **Regression Agent**
- [ ] Return to **Development Agent**

**Status:** Ready for Regression  
**Date Resolved:** blank (Closure only)  
**G7:** Do not Close until full Output/rates re-emit includes 1659C2 PR.

---

## Appendix — Evidence Paths

| Artifact | Path |
|----------|------|
| OFF rates | `Issue_Log_Items/Issue_172/evidence/validation/off_rates/` |
| ON rates | `Issue_Log_Items/Issue_172/evidence/validation/on_rates/` |
| Full durable ON emit | `Issue_Log_Items/Issue_172/evidence/validation/full_on_rates/` |
| Full durable emit result | `Issue_Log_Items/Issue_172/evidence/validation/logs/full_on_emit.json` |
| OFF/ON proof JSON | `Issue_Log_Items/Issue_172/evidence/validation/logs/off_on_isolated_proof.json` |
| Superseded harness failure | `Issue_Log_Items/Issue_172/evidence/validation/logs/off_emit.json` |
| Validator transcript | `Issue_Log_Items/Issue_172/evidence/validation/logs/validators.txt` |
| Anchors/controls | `Issue_Log_Items/Issue_172/evidence/validation/logs/anchors_controls.txt` |
| #168 ON wrap | `Issue_Log_Items/Issue_172/evidence/validation/wrap_on_output/` |
| Manifest | `Issue_Log_Items/Issue_172/business_inputs/issue172_shared_uw_keys_manifest.csv` |
