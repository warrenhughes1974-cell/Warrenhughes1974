# Issue #59 — Regression Report

**Issue:** #59 — Incorrect QL Status (`quikmstr.MSTATUS`)  
**Framework stage:** Regression Agent  
**Engine version:** **v57.84**  
**Baseline:** `Issue_Log_Items/Issue_59/evidence/quikmstr_pre_v5784_baseline.csv` (MSTATUS) + Validation G5 evidence  
**Output directory:** `QLA_Migration/Output/`  
**Generated:** 2026-07-14  
**Model:** Cursor Grok 4.5 (locked Regression)  
**Verdict:** **PASS**

---

## 1. Scope of Change (expected)

| Component | Expected impact |
|-----------|-----------------|
| `quikmstr.MSTATUS` | **Exactly 7** client-scoped policies |
| `quikridr.MPHSTAT` (phase 1 only) | Same 7 (display align) |
| All other tables / fields | No intentional change |
| Full fleet rebatch | Not required — surgical Output patch + scoped interceptor |

---

## 2. Row Count Comparison

| Table | After | Notes | OK? |
|-------|------:|-------|-----|
| quikmstr | 5,083 | Matches #59 / #49 baselines | **Yes** |
| quikridr | 6,934 | Matches #49 baseline | **Yes** |
| quikprmh | 209,470 | Unchanged by this issue | **Yes** |
| quikplan | 141 | Unchanged | **Yes** |
| quikclid | 34,449 | Unchanged | **Yes** |
| quikclnt | 13,597 | Unchanged | **Yes** |
| quikmemo | 5,083 | Unchanged | **Yes** |
| quikdvdp | 5,083 | Unchanged | **Yes** |

No table gained/lost rows for Issue #59.

---

## 3. Non-Target Field Diff (affected tables)

| Check | Result | OK? |
|-------|--------|-----|
| `MSTATUS` deltas vs pre-v57.84 | **Exactly 7**; all in scoped set | **Yes** |
| Non-scoped `MSTATUS` (random 30 + full baseline scan) | **0** mismatches | **Yes** |
| Blank `MSTATUS` | **0** / 5,083 | **Yes** |
| Blank `MRIDRID` | **0** / 6,934 | **Yes** |
| `quikmstr` column count | 45 (schema stable) | **Yes** |
| `quikridr` column count | 40 (schema stable) | **Yes** |

Intentional transitions only:

| Before → After | Count |
|----------------|------:|
| 54 → 22 | 6 |
| 41 → 50 | 1 |

---

## 4. Prior Issue Fix Regression

### Issue #25 — MPOLICY padding

| Check | Result |
|-------|--------|
| `validate_mpolicy_width.py` | **PASS** (exit 0) |
| All `quikmstr` MPOLICY width = 10 | **PASS** (0 violations) |
| Scoped short keys still padded (` 01ML8171C`, etc.) | **PASS** |

### Issue #26 — MPREM mapping

| Check | Result |
|-------|--------|
| `validate_issue26_mprem.py` | Blocked — missing `*_20260530` extracts (environmental) |
| Spot-check phase-1 `MPREM` on 7 scoped policies | Populated / stable values present (e.g. 26.04000, 7.24638, 10.58000) — **PASS** |
| MMODPREM on sample `01122D991C` | Still 26.04 (Validation) — **PASS** |

### Issue #13 — Termination precedence

| Policy | Expected | Actual | OK? |
|--------|----------|--------|-----|
| 010516211C | 54 | 54 | **Yes** |
| 011101663C | 56 | 56 | **Yes** |

### Issue #49 — Active later phase

| Check | Result |
|-------|--------|
| Override samples 018252C / 018253C = 22 | **PASS** |
| Preserve 018187C=45, 010380550C=41 | **PASS** |
| 01ML8007C shape MSTATUS=22, Ph1=54, Ph2=22 | **PASS** |
| 35 override candidates still MSTATUS=22; Ph1=54 | **PASS** (Validation) |
| Overlap with #59 scoped set | **None** |

### Issue #59 primary

| Check | Result |
|-------|--------|
| `validate_issue59_mstatus.py` | **PASS** (exit 0) |

---

## 5. Schema Integrity (AGENTS.md)

| Check | Result |
|-------|--------|
| Field order preserved | **PASS** — no schema edit |
| Field types/lengths preserved | **PASS** |
| No new blank MRIDRID | **PASS** |
| QLA formatting / MPOLICY pad | **PASS** (#25) |
| Rulebooks / translation CSV | Untouched |

---

## 6. Batch / Fleet Checks

| Check | Result |
|-------|--------|
| Full batch re-run post-fix | **No** — surgical scoped patch (by design) |
| Interceptor scoped to 7 keys in v57.84 | **Yes** — future batches will not expand blast radius |
| `Output/Test_Validation/` | `quikmstr.csv` + `quikridr.csv` present for partial UAT reload |
| Audit anomalies | None observed |

---

## 7. Failures (if any)

None blocking.

| Item | Severity | Disposition |
|------|----------|-------------|
| `validate_issue26_mprem.py` missing 20260530 extracts | Environmental | Waived; MPREM spot-check PASS |
| `validate_issue49_mstatus.py` non-candidate list of 7 | Informational | Expected #59 deltas (documented in Validation) |

---

## 8. Recommendation

- [x] Advance to **Closure Agent** / **Ready for Client UAT**
- [ ] Return to **Development Agent**

**Status:** **Ready for Client UAT** (Closure next on Composer 2.5)

### Client UAT reload

1. Load `Output/Test_Validation/quikmstr.csv` and `quikridr.csv` (or full Output equivalents)  
2. Verify only:

| Policy | Expected QL status |
|--------|-------------------|
| 01122D991C, 014FG8217C, 016FG8217C, 01ML8171C, 01ML8250C, 01ML8522C | Active (**22**) |
| 010521213C | Death Claim Pending (**50**) |

---

## Appendix

- Validation: `Issue_59_Validation_Report.md` (G5 PASS)  
- Baseline: `evidence/quikmstr_pre_v5784_baseline.csv`  
- Implementation: `Issue_59_Implementation_Notes.md` (v57.84)
