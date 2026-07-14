# Issue #57 — Validation Report

**Issue:** #57 — NFO Option incorrect  
**Framework stage:** Validation Agent (G5)  
**Engine version:** v57.78 (no engine change — rulebook + translation only)  
**Validation script:** `tools/validators/validate_issue57_mnfopt.py` v1.0  
**Output directory:** `QLA_Migration/Output/`  
**Before snapshot:** `Issue_Log_Items/Issue_57/evidence/issue57_risk_simulation.csv` (pre-fix `MNFOPT`)  
**Generated:** 2026-07-13  
**Verdict:** **PASS**

---

## Commands Run

```bash
python Issue_Log_Items/Issue_57/scripts/rebatch_quikmstr.py
python tools/validators/validate_issue57_mnfopt.py
```

Validator stdout: `Issue_Log_Items/Issue_57/evidence/issue57_validation_stdout.txt`

---

## 1. Trace Policy Results

| Policy | LP code | Field | Expected | Actual | Result |
|--------|:---:|-------|----------|--------|--------|
| 010367131C | 4 ETI | MNFOPT | 2 | **2** | **PASS** |
| 010148272C | 4 ETI | MNFOPT | 2 | **2** | **PASS** |
| 010143726C | 4 ETI | MNFOPT | 2 | **2** | **PASS** |
| 010392763C | 5 RPU | MNFOPT | 3 | **3** | **PASS** |
| 011221309C | 3 APL | MNFOPT | 1 | **1** | **PASS** |
| 010391876C | 4 ETI | MNFOPT | 2 (guard) | **2** | **PASS** (#21A regression) |

---

## 2. Acceptance Criteria (from Risk checklist §10)

| # | Criterion | Result |
|---|-----------|--------|
| 1 | Eric ETI policies → `MNFOPT=2` | **PASS** |
| 2 | Eric RPU `010392763C` → `MNFOPT=3` (PUT=PU no longer blocks) | **PASS** |
| 3 | Eric APL `011221309C` → `MNFOPT=1` (not 3) | **PASS** |
| 4 | Sample #21A code-1 BF still APL where applicable | **PASS** (010391876C unchanged at 2) |
| 5 | `MDIVOPT`, `MSTATUS`, `MMODPREM` unchanged on Eric set | **PASS** |
| 6 | `quikmstr` row count = 5,083 | **PASS** |
| 7 | MPOLICY width on trace set | **PASS** (10-char keys on Eric policies) |
| 8 | `quikridr.MPREM` unchanged on trace phase-1 rows | **PASS** |
| 9 | `PAID_UP_TYPE→MNFOPT` removed from rulebook | **PASS** |
| 10 | Translation keys NF_3/4/5 correct | **PASS** |

---

## 3. Source Alignment

| Check | Result |
|-------|--------|
| PPBENTYP `NON_FORFEITURE` / `BF_NON_FORFEITURE` → translated `MNFOPT` | **PASS** — enrich-on-zero + NF_ prefix |
| LifePRO code 3 → QLA 1 (APL) | **PASS** — `011221309C` |
| LifePRO code 4 → QLA 2 (ETI) | **PASS** — 2,336 fleet policies at 2 |
| LifePRO code 5 → QLA 3 (RPU) | **PASS** — incl. `010392763C` with PUT=PU |
| Codes 1/2 → APL (1) preserved | **PASS** — #21A entries intact |
| Code 9 → 0 safety | **PASS** — `NF_9→0` unchanged |

---

## 4. Untouched Fields Confirmed

| Field / table | Check | Result |
|---------------|-------|--------|
| `quikmstr.MMODPREM` | Eric trace policies | **Unchanged** (e.g. 010367131C=31.20) |
| `quikmstr.MSTATUS` | Eric trace policies | **Unchanged** (22/53/44 as before) |
| `quikmstr.MDIVOPT` | Eric trace policies | **Unchanged** |
| `quikridr.MPREM` phase 1 | Eric trace (9.12 / 51.48 / etc.) | **Unchanged** |
| MPOLICY padding (#25) | Eric policies 10-char | **PASS** |
| MPREM (#26) | No rulebook/engine change | **N/A — untouched** |

---

## 5. Row Counts

| Table | Count | Before (issue scope) | Match? |
|-------|------:|---------------------|--------|
| quikmstr | **5,083** | 5,083 | **Yes** |
| quikridr | (not rebatched) | — | N/A — out of scope |

**Note:** Validation used targeted **quikmstr-only** rebatch. Full fleet batch not re-run in this session; Regression Agent should confirm non-candidate tables unchanged.

---

## 6. Impact Summary

| Metric | Value |
|--------|------:|
| `MNFOPT` policies changed vs pre-fix snapshot | **2,721** |
| Primary fixes | 0→2 (ETI): 2,014; 3→1 (APL): 192; 0→3 (RPU): 41 |
| Collateral (Option B — drop PUT→MNFOPT) | 2→0: 175; 3→0: 99; 3→2: 93; etc. |
| Post-fix `MNFOPT` distribution | 0:737 · 1:1,945 · 2:2,336 · 3:65 |

---

## 7. Failures

None.

---

## 8. Recommendation

- [x] Advance to **Regression Agent**
- [ ] Return to Development — not required

**Partial UAT:** `QLA_Migration/Output/Test_Validation/quikmstr.csv` published.

---

## Appendix

### Validator stdout (summary)

```
TRACE ERIC 010367131C: MNFOPT=2 expected=2
TRACE ERIC 010148272C: MNFOPT=2 expected=2
TRACE ERIC 010143726C: MNFOPT=2 expected=2
TRACE ERIC 010392763C: MNFOPT=3 expected=3
TRACE ERIC 011221309C: MNFOPT=1 expected=1
TRACE 21A 010391876C: MNFOPT=2 expected=2
Errors: 0
PASS
```

### Evidence files

- `evidence/issue57_risk_simulation.csv` — pre-fix baseline
- `evidence/issue57_validation_stdout.txt`
- `evidence/issue57_risk_options.csv` — Option B simulation
