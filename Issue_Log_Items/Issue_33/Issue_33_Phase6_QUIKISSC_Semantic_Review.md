# Issue #33 — Phase 6 QUIKISSC Semantic Review

**Issue:** #33 — ISWL Phase 6 QUIKISSC (Surrender Charges)  
**PR:** PR-6  
**Review date:** 2026-07-01  
**Mode:** Review only — no code changes  
**Verdict:** **APPROVED**

---

## Review scope

Confirm that the 8 emitted `QuikIssc.csv` rows correctly match the LifePRO hub `659 CEN II` Rate_Table SL interpretation, including intentional schedule replication to all 8 target MPLANs.

**Artifacts reviewed:**

| Artifact | Path |
|----------|------|
| Emitted output | `QLA_Migration/Output/rates/QuikIssc.csv` |
| Reconcile summary | `Issue_Log_Items/Issue_33/output/Phase6_QUIKISSC/iswl_quikissc_reconcile_summary.json` |
| Row detail export | `Issue_Log_Items/Issue_33/output/Phase6_QUIKISSC/iswl_quikissc_keys_by_mplan.csv` |
| LifePRO source | `plan_analysis/source_data/rates/Rate_Table_Extract_20260427.csv` |
| SME authority | `Issue_Log_Items/Issue_33/Issue_33_QUIKISSC_SME_Answers.md` |

---

## 1. MPLAN coverage (8/8)

**Expected MPLAN targets (ISWL fleet):**

`1658C1`, `1658CS`, `1659C2`, `1659CR`, `1659CS`, `1659SR`, `1669SR`, `1679CS`

**Emitted `PLAN` values in QuikIssc.csv:**

| PLAN | Present | Row count |
|------|:-------:|:---------:|
| 1658C1 | Yes | 1 |
| 1658CS | Yes | 1 |
| 1659C2 | Yes | 1 |
| 1659CR | Yes | 1 |
| 1659CS | Yes | 1 |
| 1659SR | Yes | 1 |
| 1669SR | Yes | 1 |
| 1679CS | Yes | 1 |

**Result:** 8 rows, 8 distinct MPLANs, exact match to expected fleet. No missing MPLANs. No extra MPLANs. No duplicates.

---

## 2. Source interpretation — hub 659 CEN II Rate_Table SL

**Approved runtime path:**

```text
PCOVRSGT → PSEGT(SEGT_TYPE=SL) → OSLNS00XT/SLD000 → Rate_Table TYPE_CODE=SL
```

**Authoritative source slice (LifePRO extract):**

| Field | Source value |
|-------|--------------|
| COVERAGE_ID | `659 CEN II` |
| TYPE_CODE | `SL` |
| AGE | `0` |
| SEX | `M` |
| BAND | `1` |
| UNDERWRITING_CLASS | `S` |
| DURATION | 1–14 |

**Source schedule (Rate_Table extract lines 283217–283230):**

| Duration | Source VALUE | QuikIssc field | Emitted value |
|----------|-------------|----------------|---------------|
| 1 | 100.0000000 | SCHG01 | 100.0000 |
| 2 | 100.0000000 | SCHG02 | 100.0000 |
| 3 | 70.0000000 | SCHG03 | 70.0000 |
| 4 | 60.0000000 | SCHG04 | 60.0000 |
| 5 | 50.0000000 | SCHG05 | 50.0000 |
| 6 | 40.0000000 | SCHG06 | 40.0000 |
| 7 | 30.0000000 | SCHG07 | 30.0000 |
| 8 | 20.0000000 | SCHG08 | 20.0000 |
| 9 | 15.0000000 | SCHG09 | 15.0000 |
| 10 | 10.0000000 | SCHG10 | 10.0000 |
| 11 | 8.0000000 | SCHG11 | 8.0000 |
| 12 | 6.0000000 | SCHG12 | 6.0000 |
| 13 | 4.0000000 | SCHG13 | 4.0000 |
| 14 | 2.0000000 | SCHG14 | 2.0000 |

**Cross-check:** Only two SL schedules exist in Rate_Table for `AGE=0 / M / Band 1 / UWCLASS S`: `659 CEN II` (14 durations, ISWL hub) and `668 SPWL` (10 durations, non-ISWL product). ISWL coverages resolve to hub `659 CEN II` via PCOVRSGT/PSEGT (8/8). PDAGE SL rejected (all zeros). Correct source selected.

**Result:** Source interpretation confirmed. All 14 populated SCHG values match hub Rate_Table SL on a duration-for-duration basis (4-decimal percent literal formatting).

---

## 3. Intentional hub replication to all 8 MPLANs

**SME decision (Gate B):** Replicate shared `659 CEN II` CEN II surrender schedule to all 8 ISWL MPLANs → exactly 8 QuikIssc rows.

| Coverage → MPLAN | SL via hub 659 CEN II |
|------------------|:---------------------:|
| 658 CEN I → 1658C1 | Yes |
| 658 CEN SD → 1658CS | Yes |
| 659 CEN II → 1659C2 | Yes |
| 659 CEN SR → 1659CR | Yes |
| 659 CEN SD → 1659CS | Yes |
| 659 SR GD → 1659SR | Yes |
| 669 SR GD → 1669SR | Yes |
| 679 CEN SD → 1679CS | Yes |

**Replication check:** All 8 emitted rows carry identical SCHG01–SCHG14 values (hub schedule). Each row differs only by `PLAN` (target MPLAN). This matches the approved replication design.

**Result:** Intentional replication confirmed. Not an error.

---

## 4. Dimensional and trailing-field mapping

| QuikIssc field | Expected (SME) | All 8 rows |
|----------------|----------------|:----------:|
| AGE | 0 | 0 |
| GENDER | M (source SEX) | M |
| UWCLASS | SM (source S → SM) | SM |
| BAND | 01 (source Band 1) | 01 |
| ISSCNTRY | 0000 | 0000 |
| ISSUEST | 00 | 00 |
| SCHG15–SCHG20 | blank | blank |

**Result:** All dimensional fields match approved SME mapping on every row.

---

## 5. Row-level mismatch scan

| Check | Finding |
|-------|---------|
| Missing MPLAN rows | None |
| Extra MPLAN rows | None |
| Duplicate index keys (PLAN+GENDER+UWCLASS+BAND+ISSCNTRY+ISSUEST) | None |
| Per-row SCHG deviation from hub schedule | None |
| Incorrect percent literal interpretation | None |
| Non-blank SCHG15–20 | None |

**Result:** No row-level mismatches identified.

---

## 6. Verdict

**APPROVED — FINAL AUTHORITY**

All 8 emitted QuikIssc rows semantically match the LifePRO hub `659 CEN II` Rate_Table SL interpretation. Schedule replication to all 8 target MPLANs is correct and intentional per SME Gate B. No missing, extra, or incorrectly mapped MPLAN rows.

`QLA_Migration/Output/rates/QuikIssc.csv` is the approved final authority for ISWL full surrender charge schedules.

---

## 7. Post-review status

| Item | Status |
|------|--------|
| PR-6 implementation | Complete |
| Reconcile (V-ISSC-01–12) | PASS |
| Phase 1–5 regression | PASS |
| Semantic review | **APPROVED** |
| Code changes required | None |

**Next gate (out of scope for this review):** Expense setup / QuikIsrr — not started.
