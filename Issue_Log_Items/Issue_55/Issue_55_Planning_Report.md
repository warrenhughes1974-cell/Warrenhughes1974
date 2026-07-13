# Issue #55 — Planning Report

**Issue:** #55 — Unit Issues (RPU / reduced base units)  
**Framework stage:** Planning Agent  
**Status:** **Blocked — Awaiting Client Clarification** (CSV already matches client targets)  
**Generated:** 2026-07-13  
**Agent/script:** Planning Agent + `Issue_55/scripts/research_issue55_units_trace.py`  

---

## 1. Executive Finding

For all three cited policies, current conversion output **`quikridr.MUNIT` already equals** LifePRO **`PPBEN.NUMBER_OF_UNITS` (Column AC)** and the client’s stated expected units. Phase-2 faces compute as **$530** (`0.53 × 1000`) and **$647** (`0.647 × 1000`) as requested.

**Hypothesis:** Defect is **not** in the PPBEN→`MUNIT` mapping in the current batch CSV. More likely: **stale QLAdmin/DBF load**, **Coverage display rounding** (see #21K), or client looking at a different field/phase than stored `MUNIT`.

**Direction:** Do **not** change converter/`NUMBER_OF_UNITS→MUNIT` rulebook until client confirms stored QLAdmin values vs CSV. Tracking **No-Go** (Eric) is consistent with this finding. Development task below is **contingent** only if UAT proves CSV≠DBF or a different target field is wrong.

---

## 2. Confirmed LifePRO Source Table/File(s)

| Source table | File pattern | In Source/ package? | Notes |
|--------------|--------------|---------------------|-------|
| Policy Benefit | `PPBEN_PolicyBenefit_Extract_20260630.csv` | Yes | Client label “PPEN” = **PPBEN** |
| Policy Master | `PPOLC_PolicyMaster_Extract_20260630.csv` | Yes | Context only |
| Crosswalk | `Mapping/Master_Crosswalk.csv` | Yes | Old→New |

### Available source fields (units path)

| Field | Column / source | Notes |
|-------|-----------------|-------|
| Policy number | B `POLICY_NUMBER` | LP key |
| Benefit seq | C `BENEFIT_SEQ` | → `MPHASE` |
| Benefit type | D `BENEFIT_TYPE` | BA / SU on samples |
| Status reason | G `STATUS_REASON` | `CR` on RPU samples |
| Plan code | I `PLAN_CODE` | **blank** on all three samples |
| Value per unit | AB `VALUE_PER_UNIT` | `1000.00` |
| **Number of units** | **AC `NUMBER_OF_UNITS`** | Client Column AC |
| Ann prem / unit | AD `ANN_PREM_PER_UNIT` | #26 path — do not touch |

---

## 3. Confirmed QLAdmin Target Structure

| Table | Field | Role |
|-------|-------|------|
| `quikridr` | `MUNIT` | Coverage units |
| `quikridr` | `MVPU` | Value per unit |
| `quikridr` | `MPHASE` | Phase (1=base, 2=SU on samples) |
| `quikridr` | `MPHSTAT` | Phase status |
| `quikmstr` | `MSTATUS` | Policy status (45=RPU) |

Face / PU DB (no separate face field on rider): **`MUNIT × MVPU`**.

**Repo mapping:** `QLA_Migration/Configs/Sync_Rulebook_quikridr.csv` line: `NUMBER_OF_UNITS,MUNIT,,`

---

## 4. Required Source-to-Target Field Mapping

| LifePRO source | LifePRO field | QLAdmin target | Transformation | Change? |
|----------------|---------------|----------------|----------------|---------|
| PPBEN | `NUMBER_OF_UNITS` | `quikridr.MUNIT` | Direct (preserve decimals) | **No** — already correct in CSV |
| PPBEN | `VALUE_PER_UNIT` | `quikridr.MVPU` | Direct | **No** |
| PPBEN | `BENEFIT_SEQ` | `quikridr.MPHASE` | Direct | **No** |

### Fields that must remain unchanged

| Target | Current source | Touch this issue? |
|--------|----------------|-------------------|
| `quikridr.MPREM` | `ANN_PREM_PER_UNIT` + fallback (#26) | **No** |
| MPOLICY padding | `format_qladmin_mpolicy` (#25) | **No** |
| RPU `MSTATUS`/`MPHSTAT` 45 | Status mapping (#49 pattern) | **No** unless client opens status defect |

---

## 5. Open Client Questions

1. **What exact Units / Amount Ins does QLAdmin show today** for `018495BC` Phases 1–2, `018499CC` Phase 1, and `018510C` Phases 1–2? (Screenshot or Coverage grid export preferred.)  
2. **Which `quikridr` / QUIKRIDR.DBF load** is under review — latest `Output/quikridr.csv` from current engine, or an older UAT package?  
3. For `018499CC`, Phase 2 is already correct per client — confirm Phase 1 still wrong **in the same DBF** that has Phase 2 = 1.05 (rules out partial reload).  
4. Is the complaint about **stored `MUNIT`**, or **displayed Amount Ins / PU DB** only? (#21K: display can round while stored units drive benefit.)  
5. Confirm acceptance: Phase 1 face = `$0.01` (`0.00001 × 1000`) is intentional “near-zero” base coverage on RPU/reduced-base patterns.

---

## 6. Recommended Formatting Rules

| Rule | Recommendation |
|------|----------------|
| Policy key | Crosswalk + 10-char MPOLICY padding (#25) |
| Units | Preserve PPBEN precision (five decimals where present); do **not** zero `.00001` |
| Money / face | `MUNIT × MVPU`; do not invent a separate face map for this issue |
| Blanks / zeros | Do not coerce tiny units to `0` |

---

## 7. Memo / Text / Special Handling

N/A.

---

## 8. Policy Number Key Handling

1. LifePRO `POLICY_NUMBER` → `Master_Crosswalk.csv` → QLA  
2. `format_qladmin_mpolicy()` for CHARACTER(10)  
3. Samples: `9018495B`→`018495BC`, `9018499C`→`018499CC`, `9018510`→`018510C`

---

## 9. Estimated Record Counts

| Metric | Count | Basis |
|--------|------:|-------|
| Client sample phases | 6 | 3 policies × 2 phases |
| CSV vs client expected mismatches | **0** | Evidence CSV |
| CSV vs PPBEN mismatches (tiny seq1 fleet) | **0** | Research scan |
| RPU masters with Phase1 `MUNIT=.00001` | **77** | Current `quikmstr`/`quikridr` |
| PPBEN seq1 `NUMBER_OF_UNITS=.00001` | **147** | Source extract |

---

## 10. Sample Trace (3 policies)

| Policy (QLA) | Phase | PPBEN AC units | `quikridr.MUNIT` | Client expected | Match | Notes |
|--------------|------:|---------------:|-----------------:|----------------:|:-----:|-------|
| `018495BC` | 1 | .00001 | .00001 | 0.00001 | **Y** | Master/phase1 `45` RPU; MPLAN `1SALML` |
| `018495BC` | 2 | .53000 | .53000 | 0.53 | **Y** | Face **$530**; MPHSTAT `22` |
| `018499CC` | 1 | .00001 | .00001 | 0.00001 | **Y** | Master `22`; MPHSTAT `54` |
| `018499CC` | 2 | 1.05000 | 1.05000 | 1.05 | **Y** | Client says QLA Phase 2 OK |
| `018510C` | 1 | .00001 | .00001 | 0.00001 | **Y** | RPU `45` |
| `018510C` | 2 | .64700 | .64700 | 0.647 | **Y** | Face **$647**; MPHSTAT `22` |

Evidence: `Issue_Log_Items/Issue_55/evidence/issue55_trace_three_policies.csv`

**Status note:** Blank PPBEN `PLAN_CODE` on samples; engine assigns `1SALML` / `1SALMI`. Phase 2 often `MPHSTAT=22` while master RPU=`45` — consistent with #49 preservation pattern; not a units mapping failure.

---

## 11. Risks and Unknowns

| Risk | Severity | Mitigation |
|------|----------|------------|
| Client UAT DBF out of date vs CSV | High (explains report) | Ask reload from current `quikridr.csv`; compare stored MUNIT |
| Display-only rounding of `.00001` → `0` | Medium | Confirm stored field; cite #21K |
| Wrong screen field mistaken for units | Medium | Screenshot + field name |
| Unnecessary converter “fix” zeros tiny units | High | **Do not code** without DBF mismatch proof |
| Touching #26/#25 | High | Explicit no-touch list |

---

## 12. Dependency Gate Preview

| Check | Met? |
|-------|------|
| Source file present | **Yes** |
| Field definitions confirmed | **Yes** (AC = NUMBER_OF_UNITS → MUNIT) |
| Client scope clear (expected values) | **Yes** |
| Example policies available | **Yes** |
| Proof QLAdmin stored value ≠ CSV | **No** — blocker |
| Screenshots | **No** — blocker |

---

## 13. Recommended Risk Agent Prompt

```
Proceed to Risk Agent for Issue #55 ONLY after client answers OBQ-1..3
(or confirms CSV/DBF mismatch).

Read AI_Agents/Risk_Agent.md and Templates/Risk_Report_Template.md.
Model: Cursor Grok 4.5. Do not code.

Context: Planning found quikridr.MUNIT already matches PPBEN Column AC and
client expected units for 018495BC, 018499CC, 018510C. Quantify go/no-go:
default recommendation is No-Go for Development (converter) unless new
evidence shows DBF/load defect requiring a non-converter fix path.
Preserve #25 MPOLICY and #26 MPREM.
```

---

## 14. Recommended Development Task (Do Not Implement)

**Default: no Development.** Contingent only if client proves stored QUIKRIDR.MUNIT ≠ CSV:

1. Diagnose DBF writer / load path for five-decimal `MUNIT` (reuse #21K tooling).  
2. **Do not** alter Sync_Rulebook `NUMBER_OF_UNITS→MUNIT` if CSV already correct.  
3. Version bump only if engine/DBF path changes.  
4. Validation: extend trace script to assert three policies + fleet tiny-unit equality PPBEN↔CSV.

If client confirms CSV correct after reload → **Closure as converter N/A / UAT reload** without code.

---

## Appendix

- Diagnostic script: `Issue_Log_Items/Issue_55/scripts/research_issue55_units_trace.py`  
- Evidence: `Issue_Log_Items/Issue_55/evidence/issue55_trace_three_policies.csv`  
- Related: #21K, #25, #26, #49  
- Rulebook: `QLA_Migration/Configs/Sync_Rulebook_quikridr.csv`
