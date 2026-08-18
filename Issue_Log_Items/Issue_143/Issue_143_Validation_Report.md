# Issue #143 — Validation Report

**Issue:** #143 — Units Incorrect (RPU)  
**Framework stage:** Validation Agent  
**Engine version:** v58.96  
**Output directory:** `QLA_Migration/Output/`  
**Before snapshot:** `Issue_Log_Items/Issue_143/evidence/quikridr_pre_issue143_20260818T130527Z.csv`  
**Source cut:** LifePRO extracts `20260630`  
**Generated:** 2026-08-18  
**Verdict:** **PASS**

---

## 1. Validation verdict

**PASS.** Independent source derivation found exactly **23** BF RPU mismatches. All 23 Output rows have `MUNIT = BF_CURRENT_DB / VALUE_PER_UNIT`. Amount Ins reconciles to Column DD. Controls, field-level diff, #55, and #108A hold. Issue #124 was not modified.

**Recommendation:** **READY FOR REGRESSION** — do not start Regression in this session.

---

## Commands run

```text
python Issue_Log_Items/Issue_143/_validate_issue143_independent.py
python Issue_Log_Items/Issue_143/_probe_ba_absent.py
python Issue_Log_Items/Issue_143/_probe_ba_join.py
python tools/validators/validate_issue143_rpu_munit.py
python tools/validators/validate_issue55_munit_floor.py
```

Independent classification did **not** import Development’s candidate helper. It reread PPOLC / PPBEN / PPBENTYP and applied the locked conditions itself.

---

## 2. Independent candidate derivation

| Source | Field used |
|--------|------------|
| `PPOLC_PolicyMaster_Extract_20260630.csv` | `PAID_UP_TYPE = RU` (304 policies) |
| `PPBEN_PolicyBenefit_Extract_20260630.csv` | seq-1 `NUMBER_OF_UNITS`, `VALUE_PER_UNIT` |
| `PPBENTYP_BenefitType_Extract_20260630.csv` | seq-1 `TYPE_CODE`, `BF_CURRENT_DB` (Column DD) |

Locked rule applied independently:

```text
RU AND TYPE_CODE=BF AND BF_CURRENT_DB>0
AND abs(NUMBER_OF_UNITS - BF_CURRENT_DB/VALUE_PER_UNIT) > 0.01
THEN expected MUNIT = BF_CURRENT_DB / VALUE_PER_UNIT
```

| Independent cohort | Count | Locked expectation |
|--------------------|------:|--------------------|
| BF RPU mismatch (candidates) | **23** | 23 |
| BF RPU already aligned | **82** | 82 |
| Traditional BA RPU | **199** | 199 |

Full candidate worksheet: `evidence/issue143_independent_candidates.csv`.

---

## 3. 23-row reconciliation

| Metric | Result |
|--------|--------|
| Expected candidates | 23 |
| Output rows corrected | **23** |
| Missing expected corrections | **0** |
| Unauthorized corrections | **0** |
| Death-benefit fails (`MUNIT×MVPU` vs DD) | **0** |

Every candidate: `Actual MUNIT == BF_CURRENT_DB / VALUE_PER_UNIT` within 0.01 (largest residual is floating-point ~1e-15). Every candidate: `MUNIT × MVPU` equals `BF_CURRENT_DB` within $0.02.

| Policy | PLAN | TYPE | PUT | Units | BF_CURRENT_DB | VPU | Expected MUNIT | Actual MUNIT | Diff | Amt Ins | Result |
|--------|------|------|-----|------:|--------------:|----:|---------------:|-------------:|-----:|--------:|--------|
| 9010757606C | 1659C2 | BF | RU | 25 | 19101.96 | 1000 | 19.10196 | 19.10196 | 0 | 19101.96 | PASS |
| 9010760069C | 1659C2 | BF | RU | 25 | 20367.07 | 1000 | 20.36707 | 20.36707 | 0 | 20367.07 | PASS |
| 9010766847C | 1659C2 | BF | RU | 25 | 5163.41 | 1000 | 5.16341 | 5.16341 | 0 | 5163.41 | PASS |
| 9010774868C | 1659C2 | BF | RU | 25 | 22995.64 | 1000 | 22.99564 | 22.99564 | 0 | 22995.64 | PASS |
| 9010780870C | 1659C2 | BF | RU | 25 | 21457.07 | 1000 | 21.45707 | 21.45707 | 0 | 21457.07 | PASS |
| 9010786243C | 1659C2 | BF | RU | 25 | 21899.80 | 1000 | 21.89980 | 21.89980 | 0 | 21899.80 | PASS |
| 9010796917C | 1659C2 | BF | RU | 25 | 20860.18 | 1000 | 20.86018 | 20.86018 | 0 | 20860.18 | PASS |
| 9010805394C | 1659C2 | BF | RU | 25 | 18394.00 | 1000 | 18.39400 | 18.39400 | 0 | 18394.00 | PASS |
| 9010812930C | 1659C2 | BF | RU | 30 | 12506.02 | 1000 | 12.50602 | 12.50602 | 0 | 12506.02 | PASS |
| 9010823867C | 1658C1 | BF | RU | 25 | 4572.08 | 1000 | 4.57208 | 4.57208 | 0 | 4572.08 | PASS |
| 9010823868C | 1658C1 | BF | RU | 25 | 6384.28 | 1000 | 6.38428 | 6.38428 | 0 | 6384.28 | PASS |
| 9010823869C | 1658C1 | BF | RU | 25 | 9320.78 | 1000 | 9.32078 | 9.32078 | 0 | 9320.78 | PASS |
| 9010823870C | 1658C1 | BF | RU | 25 | 6869.97 | 1000 | 6.86997 | 6.86997 | 0 | 6869.97 | PASS |
| 9010826422C | 1658C1 | BF | RU | 50 | 9655.90 | 1000 | 9.65590 | 9.65590 | 0 | 9655.90 | PASS |
| 9010835334C | 1659CR | BF | RU | 10 | 4509.17 | 1000 | 4.50917 | 4.50917 | 0 | 4509.17 | PASS |
| 9010847463C | 1659C2 | BF | RU | 25 | 20295.98 | 1000 | 20.29598 | 20.29598 | 0 | 20295.98 | PASS |
| 9010885442C | 1659C2 | BF | RU | 25 | 20961.55 | 1000 | 20.96155 | 20.96155 | 0 | 20961.55 | PASS |
| 9010933370C | 1659C2 | BF | RU | 25 | 19216.77 | 1000 | 19.21677 | 19.21677 | 0 | 19216.77 | PASS |
| 9011001627C | 1659C2 | BF | RU | 30 | 3044.64 | 1000 | 3.04464 | 3.04464 | 0 | 3044.64 | PASS |
| 9011025612C | 1659CR | BF | RU | 5 | 2742.60 | 1000 | 2.74260 | 2.74260 | 0 | 2742.60 | PASS |
| 9011044907C | 1659C2 | BF | RU | 35 | 21084.59 | 1000 | 21.08459 | 21.08459 | 0 | 21084.59 | PASS |
| 9011069977C | 1659C2 | BF | RU | 25 | 12625.25 | 1000 | 12.62525 | 12.62525 | 0 | 12625.25 | PASS |
| 9011154856C | 1659C2 | BF | RU | 25 | 6104.75 | 1000 | 6.10475 | 6.10475 | 0 | 6104.75 | PASS |

Risk extra traces: `9010766847C` 5.16341 PASS; `9010826422C` 9.65590 PASS.

---

## 4. Gold-policy trace — `9010757606C`

| Step | Source / field | Value |
|------|----------------|-------|
| LifePRO units | PPBEN `NUMBER_OF_UNITS` | **25** |
| LifePRO VPU | PPBEN `VALUE_PER_UNIT` | **1000** |
| Enrichment | PPBENTYP `TYPE_CODE` | **BF** |
| Enrichment | PPOLC `PAID_UP_TYPE` | **RU** |
| Column DD | PPBENTYP `BF_CURRENT_DB` | **19101.96** |
| Expected MUNIT | 19101.96 / 1000 | **19.10196** |
| Pre-fix Output | baseline `MUNIT` | **25.00000** |
| Post-fix Output | current `MUNIT` | **19.10196** |
| Amount Ins | `MUNIT × MVPU` | **19101.96** |

Protected on gold (baseline vs current):

| Field | Before | After | Result |
|-------|--------|-------|--------|
| `MPREM` | 9.77037 | 9.77037 | Unchanged |
| `MVPU` | 1000.00 | 1000.00 | Unchanged |
| `MSAVEUNIT` | blank | blank | Unchanged (#108A) |
| `MPOLICY` | 9010757606C | 9010757606C | Unchanged |
| `MPLAN` | 1659C2 | 1659C2 | Unchanged |

---

## 5. Aligned BF control (82)

Independently identified **82** BF RPU rows where `abs(NUMBER_OF_UNITS − DD/VPU) ≤ 0.01`.

| Check | Result |
|-------|--------|
| Expected aligned BF | 82 |
| Still on original LifePRO units | **82** |
| Changed by Issue #143 | **0** |
| Risk control `9010732975C` | 14.08377 unchanged PASS |

---

## 6. BA control (199) and the “15 absent” rows

| Check | Result |
|-------|--------|
| BA / no-DD source population | **199** |
| Present in Output and still on source units | **184** |
| Constructed key not found under naive `source+C` join | **15** |
| BA rows that received an #143 `MUNIT` override | **0** |
| Risk BA control `9010165095C` | 1.69072 unchanged PASS |

### The 15 rows — pre-existing join artifact, not an Output hole

Development reported 184 present / 15 absent. Validation looked only far enough to classify that report.

Those 15 PPOLC `POLICY_NUMBER` values **already end in `C`** (or are short C-suffixed stems). Issue #2 emits `source + C`, so Output MPOLICY is the extra-C form (`9018166C` → `9018166CC`). A naive join looking for the source string therefore misses the converted row.

| Constructed lookup (not in Output) | Actual Issue #2 MPOLICY | In pre-#143 baseline | In current Output | `MUNIT` vs baseline |
|------------------------------------|-------------------------|----------------------|-------------------|---------------------|
| 901222DC | 901222DCC | Yes | Yes | Unchanged |
| 9014100C | 9014100CC | Yes | Yes | Unchanged |
| 9018166C | 9018166CC | Yes | Yes | Unchanged |
| 9018167C | 9018167CC | Yes | Yes | Unchanged |
| 9018236C | 9018236CC | Yes | Yes | Unchanged |
| 9018237C | 9018237CC | Yes | Yes | Unchanged |
| 9018258C | 9018258CC | Yes | Yes | Unchanged |
| 9018284C | 9018284CC | Yes | Yes | Unchanged |
| 9018330C | 9018330CC | Yes | Yes | Unchanged |
| 9018465C | 9018465CC | Yes | Yes | Unchanged |
| 9018495C | 9018495CC | Yes | Yes | Unchanged |
| 9018645C | 9018645CC | Yes | Yes | Unchanged |
| 9018845C | 9018845CC | Yes | Yes | Unchanged |
| 901ML4140C | 901ML4140CC | Yes | Yes | Unchanged |
| 901ML8378C | 901ML8378CC | Yes | Yes | Unchanged |

**Conclusion:** the 15-row “absence” pre-existed Issue #143. It is a lookup-key mismatch against Issue #2 MPOLICY, not a conversion drop and not an #143 change. Out of scope to fix.

Evidence: `evidence/issue143_ba_absent_join.json`.

---

## 7. Field-level before/after diff

Compared `quikridr_pre_issue143_20260818T130527Z.csv` to current `QLA_Migration/Output/quikridr.csv`.

| Check | Result |
|-------|--------|
| Pre rows | 6,934 |
| Post rows | 6,934 |
| Rows that differ | **23** |
| Fields that differ | **`MUNIT` only** (23 hits) |
| `MPREM` / `MVPU` / `MSAVEUNIT` / other QuikRidr fields / `MPOLICY` | **0** #143-induced diffs |

The 23 differing MPOLICY keys are exactly the independent candidate set.

---

## 8. Issue #55 / #108A protection

### Issue #55

`python tools/validators/validate_issue55_munit_floor.py` → **PASS**.

| Trace | Phase | Expected | Actual |
|-------|------:|---------:|--------|
| 9018495BC | 1 | 0.0 | 0.00000 PASS |
| 9018495BC | 2 | 0.53 | 0.53000 PASS |
| 9018499CC | 1 | 0.0 | 0.00000 PASS |
| 9018499CC | 2 | 1.05 | 1.05000 PASS |
| 9018510C | 1 | 0.0 | 0.00000 PASS |
| 9018510C | 2 | 0.647 | 0.64700 PASS |
| 9010434419C PUA | 2 | floored 0 | 0.00000 PASS |

Rows with `0 < MUNIT < 0.001`: **0**. Leading-dot decimals: **0**. Floor logic was not edited.

### Issue #108A

All **13** status-45 candidates still have blank `MSAVEUNIT` (including gold). No #143 write of original units into save fields.

---

## 9. Issue #124 expected downstream impact

`QuikIswl.csv` was **not** rewritten. All 23 candidates are ISWL (`1658C1` / `1659C2` / `1659CR`).

Locked #124 formula remains `MDB = MUNIT × 1000`. After the next authorized seed, stored MDB will follow the corrected units. That is **not** a regression.

| Policy | Current stored QuikIswl MDB | Expected MDB after next #124 seed |
|--------|----------------------------:|----------------------------------:|
| 9010757606C | 25000.00 | **19101.96** |
| 9010760069C | 25000.00 | 20367.07 |
| 9010766847C | 25000.00 | 5163.41 |
| 9010774868C | 25000.00 | 22995.64 |
| 9010780870C | 25000.00 | 21457.07 |
| 9010786243C | 25000.00 | 21899.80 |
| 9010796917C | 25000.00 | 20860.18 |
| 9010805394C | 25000.00 | 18394.00 |
| 9010812930C | 30000.00 | 12506.02 |
| 9010823867C | 25000.00 | 4572.08 |
| 9010823868C | 25000.00 | 6384.28 |
| 9010823869C | 25000.00 | 9320.78 |
| 9010823870C | 25000.00 | 6869.97 |
| 9010826422C | 50000.00 | 9655.90 |
| 9010835334C | 10000.00 | 4509.17 |
| 9010847463C | 25000.00 | 20295.98 |
| 9010885442C | 25000.00 | 20961.55 |
| 9010933370C | 25000.00 | 19216.77 |
| 9011001627C | 30000.00 | 3044.64 |
| 9011025612C | 5000.00 | 2742.60 |
| 9011044907C | 35000.00 | 21084.59 |
| 9011069977C | 25000.00 | 12625.25 |
| 9011154856C | 25000.00 | 6104.75 |

Gold: current stored MDB **25000.00**; expected next seed **19101.96**. Acceptable at this Validation stage.

---

## 10. Version / implementation isolation

| Check | Result |
|-------|--------|
| `app.py` `APP_VERSION` | **v58.96** |
| `QLA_Migration/app.py` `APP_VERSION` | **v58.96** |
| Issue #143 hook | Isolated post-map override before #55 emit |
| `Sync_Rulebook_quikridr.csv` `NUMBER_OF_UNITS,MUNIT` | Unchanged |

Working-tree note (not an #143 defect): `Sync_Rulebook_quikridr.csv` has an unrelated comment-only #137 MPREM note. Default units mapping was not rewritten.

#143 production files: `qla_core/issue143_rpu_munit.py`, `app.py`, `QLA_Migration/app.py`. #55 emit and #124 loader were not modified.

---

## 11. Exceptions or observations

1. **15 BA “absent” keys** — lookup artifact vs Issue #2 extra-C MPOLICY. Pre-existing. Converted rows exist in baseline and Output and were not remapped. Do not expand #143.
2. **QuikIswl MDB still at original face** — expected until the next #124 seed. Not a Validation fail.
3. **Unrelated rulebook comment** (#137 MPREM) present in the working tree. Out of #143 scope.

No failures. No return to Development.

---

## 12. Final recommendation

- [x] **READY FOR REGRESSION**
- [ ] Return to Development

Formal Regression was **not** started.

### Evidence

| Artifact | Path |
|----------|------|
| Independent summary | `evidence/issue143_independent_validation.json` |
| Candidate CSV | `evidence/issue143_independent_candidates.csv` |
| BA join probe | `evidence/issue143_ba_absent_join.json` |
| Development validator | `evidence/issue143_validation_summary.json` |
| Pre-fix backup | `evidence/quikridr_pre_issue143_20260818T130527Z.csv` |
