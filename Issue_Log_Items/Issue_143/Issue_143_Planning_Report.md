# Issue #143 — Planning Report

**Issue:** #143 — Units Incorrect (RPU)  
**Framework stage:** Planning Agent  
**Status:** Planning complete — proceed to Dependency Gate  
**Generated:** 2026-08-18  
**Agent:** Cursor Grok 4.5  
**Code:** None  

---

## 1. Executive Finding

LifePRO RPU does not always reduce `NUMBER_OF_UNITS`. On **23** BF RPU policies, units remain the original issue quantity while Column DD (`BF_CURRENT_DB`) holds the paid-up death benefit. Current Output copies those units, so Amount Ins is the original face.

SME locked 2026-08-18: `MUNIT = BF_CURRENT_DB / VALUE_PER_UNIT` on that set only. Example `9010757606C`: 25.00000 → **19.10196**.

**82** BF RPU rows already match DD; **199** BA RPU rows have DD = 0 and must be left alone. Direction: surgical post-map remap of phase-1 `MUNIT` for the 23, then existing #55 decimal emit.

---

## 2. Confirmed LifePRO Source Table/File(s)

| Source table | File | In Source/? | Rows used |
|---|---|---|---:|
| Policy Master | `PPOLC_PolicyMaster_Extract_20260630.csv` | Yes | 304 `PAID_UP_TYPE=RU` |
| Policy Benefit | `PPBEN_PolicyBenefit_Extract_20260630.csv` | Yes | seq-1 units / VPU |
| Benefit Type | `PPBENTYP_BenefitType_Extract_20260630.csv` | Yes | `TYPE_CODE`, `BF_CURRENT_DB` (Col DD) |

Research cut is **20260630** (same files as Output under test). Development must re-count if the next batch uses `20260731`.

### Available source fields

| Field | Column / source | Notes |
|---|---|---|
| `POLICY_NUMBER` | PPOLC / PPBEN / PPBENTYP B | Join key → `MPOLICY` + `C` (#2) |
| `PAID_UP_TYPE` | PPOLC | `RU` = RPU |
| `BENEFIT_SEQ` | PPBEN / PPBENTYP C | Phase 1 = 1 |
| `NUMBER_OF_UNITS` | PPBEN AC | Current mapping to `MUNIT` |
| `VALUE_PER_UNIT` | PPBEN AB | $1,000 on all RPU rows measured |
| `TYPE_CODE` | PPBENTYP D | BF vs BA switch |
| `BF_CURRENT_DB` | PPBENTYP **DD** | Authority for BF death benefit |
| `BF_SPECIFIED_AMT` | PPBENTYP DC | Equals DD on this RPU BF cut |

`ORIGINAL_UNITS` / `ETI_RPU_*` are unused — do not use them.

---

## 3. Confirmed QLAdmin Target Structure

| Table | Field | Role | Help / schema |
|---|---|---|---|
| `quikridr` | `MUNIT` | Number of units of coverage | QLAdmin Help QuikRidr; Amount Ins = `MUNIT × MVPU` |
| `quikridr` | `MVPU` | Value per unit | Keep `VALUE_PER_UNIT` |
| `quikridr` | `MSAVEUNIT` | Pre-NFO units | **#108A: blank on ETI/RPU phase 1** |
| `quikmstr` | `MSTATUS` | 45 = RPU in force | Context only |

**Repo population paths**

| Location | Role |
|---|---|
| `Sync_Rulebook_quikridr.csv` | `NUMBER_OF_UNITS → MUNIT` (keep as default) |
| `qla_core/quikridr_decimal_emit.py` | #55 floor + leading-zero format |
| `app.py` `_apply_quikridr_v5796_defaults` | #108A blanks `MSAVE*` on NFO phase 1 |

---

## 4. Required Source-to-Target Field Mapping

| LifePRO source | Field | QLAdmin target | Transformation | Change? |
|---|---|---|---|---|
| PPBEN | `NUMBER_OF_UNITS` | `MUNIT` | Direct, then **#143 remap** if BF RPU mismatch | **Yes** (23 rows) |
| PPBENTYP | `BF_CURRENT_DB` | (input only) | `expected = DD / VPU` | New read |
| PPBEN | `VALUE_PER_UNIT` | `MVPU` | Direct | **No** |
| PPBEN | `ANN_PREM_PER_UNIT` | `MPREM` | #26 / #88 / #137 | **No** |

### Fields that must remain unchanged

| Target | Current source | Touch? |
|---|---|---|
| `quikridr.MPREM` | ANN + modalized fallback | **No** |
| `quikmstr.MMODEPREM` | PPOLC `MODE_PREMIUM` | **No** |
| `quikridr.MVPU` | `VALUE_PER_UNIT` | **No** |
| `MPOLICY` | source + `C`, width 11 (#2) | **No** |
| `MSAVEUNIT` on 44/45 | blank (#108A) | **No** — do not store original 25 |
| #55 floor | `0 < MUNIT < 0.001 → 0` | **No** change to threshold |
| BA RPU `MUNIT` | `NUMBER_OF_UNITS` | **No** |
| Aligned BF `MUNIT` | `NUMBER_OF_UNITS` | **No** |

---

## 5. Open Client Questions

None blocking. Documented residuals (not required to code):

1. Why LifePRO used two BF processors (23 vs 82) — does not change the locked rule.
2. PUA fold-in on already-RPU BF units — stays with #108.
3. Confirm 7/31 extract still has the same 23 (re-count at Development).

Recommended default: remap **all 23** (13 status 45 + 7 status 53 + 3 status 55). Same units-vs-DD defect.

---

## 6. Recommended Formatting Rules

| Rule | Recommendation |
|---|---|
| Policy key | Issue #2: source + `C`, width 11 (`9010757606C`) |
| Units | Five decimals after #55 emit (`19.10196`) |
| Face | `MUNIT × MVPU` must equal `BF_CURRENT_DB` |
| Blanks / zeros | Do not coerce; #55 floor only below 0.001 |
| Tolerance | Remap when `|units − DD/VPU| > 0.01` |

---

## 7. Memo / Text / Special Handling

N/A.

---

## 8. Policy Number Key Handling

1. LifePRO `POLICY_NUMBER` (e.g. `9010757606`)  
2. Emitted `MPOLICY` = source + `C` (`9010757606C`) per Issue #2  
3. PPBENTYP cache must key off source `POLICY_NUMBER`, not retired crosswalk `010757606C`

---

## 9. Estimated Record Counts

| Metric | Count | Basis |
|---|---:|---|
| RPU policies (`PUT=RU`) | 304 | PPOLC 20260630 |
| BA / no DD (do not remap) | 199 | seq-1 |
| BF aligned (do not remap) | 82 | units ≈ DD/VPU |
| **BF unaligned (remap)** | **23** | SME set |
| Of those, in-force MSTATUS 45 | 13 | Output join |
| Output already matching source units on the 23 | 23 | current `quikridr.csv` |

---

## 10. Sample Trace

| Policy (QLA) | Class | Output MUNIT now | Proposed MUNIT | Amount Ins after | Status |
|---|---|---:|---:|---:|---|
| `9010757606C` | BF unaligned | 25.00000 | **19.10196** | $19,101.96 | 45 |
| `9010766847C` | BF unaligned | 25.00000 | **5.16341** | $5,163.41 | 45 |
| `9010826422C` | BF unaligned | 50.00000 | **9.65590** | $9,655.90 | 45 |
| `9010732975C` | BF aligned | 14.08377 | 14.08377 | $14,083.77 | 45 |
| `9010165095C` | BA control | (source 1.69072) | unchanged | units × $1,000 | RU |

---

## 11. Risks and Unknowns

| Risk | Severity | Mitigation |
|---|---|---|
| Blanket RPU unit rewrite | High | Gate on BF + DD>0 + mismatch only |
| #108 `MSAVEUNIT` filled with 25 | High | Do not write save fields |
| #55 floor applied to remapped units | Low | All proposed values ≫ 0.001 |
| Names annual `MPREM × MUNIT` drops | Medium | Leave `MPREM`; UAT note |
| QuikIswl `MDB` follows new `MUNIT` | Medium | Consistent with #124; not an override |
| 7/31 population drift | Low | Re-count before coding |

---

## 12. Dependency Gate Preview

| Check | Met? |
|---|---|
| Source file present | **Yes** |
| Field definitions confirmed | **Yes** (DD = `BF_CURRENT_DB`) |
| Client scope clear | **Yes** — SME 2026-08-18 |
| Example policies available | **Yes** |

---

## 13. Recommended Risk Agent Prompt

```
Risk Agent — Issue #143 Units Incorrect (RPU).
Read Issue_143_Planning_Report.md and evidence/issue143_risk_impact_summary.json.
Quantify 23-row blast radius vs 82+199 untouched. Do not code.
Preserve #55, #108A MSAVE blank, #26 MPREM, #2 MPOLICY.
```

---

## 14. Recommended Development Task (Do Not Implement)

1. After `NUMBER_OF_UNITS → MUNIT` map and **before** #55 emit: if source policy is `PAID_UP_TYPE=RU`, PPBENTYP seq-1 `TYPE_CODE=BF`, `BF_CURRENT_DB > 0`, and `|MUNIT − DD/VPU| > 0.01`, set `MUNIT = DD / VPU`.
2. Do **not** change the rulebook default map. Do **not** write `MSAVEUNIT`.
3. Cache `BF_CURRENT_DB` by source `POLICY_NUMBER` + seq (same key pattern as #21A / #108F).
4. Version bump `APP_VERSION` in root `app.py` **and** `QLA_Migration/app.py`.
5. Validator: 23 remapped; 82 BF aligned unchanged; BA RPU unchanged; #55 traces unchanged.

---

## Appendix

- Research: `Issue_143_Research_Report.md`
- Risk sim: `Issue_143/_risk_sim_issue143.py`
- Related: #55, #108, #21A, #124, #2, #26
