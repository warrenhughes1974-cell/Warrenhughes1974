# Issue Closure Summary — First-Pass Non-CV Inherited Rate Resolution

**Date:** 2026-07-07  
**Issue:** `Issue_Rates_Inheritance_Validation` — non-CV inherited/shared rate first pass  
**Status:** **CLOSED**

---

## What Problem Was Solved

Prior validation confirmed direct `Rate_Table` conversion and Issue #40 inherited cash value (`CV`) rates were correct, but **35 non-CV inherited/shared rate candidates** had source rows on PCOVRSGT owner segments and **zero issuing-plan output** in `QuikNps`, `QuikTvs`, `QuikDvs`, and `QuikDbs`.

This implementation resolved the **approved first-pass subset** of those gaps by adding a manifest-gated inherited rate loader that:

1. Reads `approved_first_pass_scope.csv`
2. Emits inherited `NP`, `RV`, `DV`, and `DB` rows from approved source segments under issuing plan codes
3. Runs in the rate pipeline after direct `Rate_Table` conversion and Issue #40 CV inheritance, before PAAGERAT processing

**Result:** **375,840** inherited non-CV `IN_SCOPE` cells emitted across **24** approved manifest entries, with **0** source-to-output mismatches and **0** inherited-plan grid collisions.

---

## What Was Intentionally Excluded

| Category | Items | Rationale |
|----------|-------|-----------|
| PUA non-CV | `261PUA`, `265PUA`, `280PUA` | PUA non-CV inheritance requires separate actuarial approval |
| `PR` / `QuikGps` | All gross-premium inherited candidates | Excluded to avoid premium source conflicts with existing PAAGERAT/direct paths |
| PAAGERAT precedence | 301 source/output conflicts | Separate workstream — output already exists; values disagree due to precedence rules, not missing inherited rows |
| Unlisted candidates | Any row not marked `Include In First Pass = Yes` | Manifest-gated scope only |

**Validation confirmed:** PUA non-CV rows were not emitted, inherited `PR` rows from this loader = 0, and PAAGERAT precedence logic was not changed.

---

## Business / Actuarial Items Still Pending

These items remain **outside** the closed first-pass scope:

1. **PUA non-CV inheritance** (`261PUA`, `265PUA`, `280PUA`) — NP/RV/DV/DB/PR gaps require actuarial sign-off before implementation.
2. **Inherited `PR` / `QuikGps`** — business rule needed on whether issuing plans should inherit gross premiums when direct and PAAGERAT paths already populate output.
3. **PAAGERAT precedence conflicts** (301 cases) — business rule needed on which source wins when PAAGERAT and `Rate_Table` values disagree for the same grid key. See `paagerat_precedence_questions.md`.
4. **Multi-segment merge precedence** — for plans like `1669SR` and `1679CS`, manifest segment order first-wins was used when owner segments overlap. Actuarial review may be needed if a different owner precedence is required.
5. **Unrelated pipeline blocker** — `V-UINT-PDINT` (`QuikUint` / missing `PDINTTBL`) predates this work and remains a separate remediation item.

---

## Evidence of Validation

### Commands Run (all PASS, exit code 0)

```powershell
python QLA_Migration/_validate_non_cv_inherited_rates.py
python QLA_Migration/_validate_issue40_inherited_cv_source_parity.py
python QLA_Migration/_validate_issue37_quikcvs_placement.py
python QLA_Migration/_validate_issue41_quikcvs_endpoint.py
```

### Key Metrics

| Metric | Result |
|--------|--------|
| Manifest entries confirmed | 24 / 24 |
| Inherited non-CV `IN_SCOPE` cells | 375,840 |
| Source-to-output mismatches | **0** |
| Inherited-plan grid collisions | **0** |
| Anchor checks | **72 / 72** PASS |
| Inherited `PR` rows from loader | **0** |
| PUA non-CV rows emitted | **0** |
| Direct `Rate_Table` transform count | 774,400 (still reconciles) |
| Issue #40 CV parity | 101,793 inherited CV rows, 0 mismatches |
| Issue #37 QuikCvs placement | PASS |
| Issue #41 QuikCvs endpoint | 5/5 PASS |

### Evidence Files

- `evidence/non_cv_inherited_rate_parity_summary.json`
- `evidence/non_cv_inherited_rate_plan_counts.csv`
- `evidence/non_cv_inherited_rate_anchor_points.csv`
- `non_cv_inheritance_implementation_report.md`
- `approved_first_pass_scope.csv`

---

## Approved Plans and Row Counts

| Issuing Plan | NP | RV | DV | DB |
|---|---:|---:|---:|---:|
| 1666AI | 9,890 | 9,890 | — | — |
| 1668SP | 19,780 | 19,780 | — | — |
| 1669SR | 22,666 | 22,654 | — | 100 |
| 1679CS | 22,666 | 22,654 | — | — |
| 170588 | 6,988 | 9,230 | 7,126 | — |
| 17085M | 6,988 | 9,230 | 7,126 | — |
| 1L10OD | 27,606 | 28,908 | — | — |
| 1L10PR | 27,606 | 28,908 | — | — |
| 1L10SO | 27,606 | 28,908 | — | — |
| 1SALMI | — | 4,750 | — | — |
| 1SALML | — | 4,750 | — | — |
| 7687J3 | — | — | — | 30 |

All plan/rate rows: **0 mismatches**.

---

## Pre-Existing Unrelated Blocker

Regression validators report **1 pipeline blocker** that is **not caused by this implementation**:

- **`V-UINT-PDINT`** — `QuikUint` / `PDINTTBL` extract missing or not configured

This blocker is documented in the prior rate inheritance validation report and does not affect non-CV inheritance parity. It should be tracked and resolved separately.

---

## Final Recommendation

**Close** the first-pass non-CV inherited rate resolution issue.

The approved manifest scope is fully implemented, validated, and regression-tested. No further code changes are required for this first pass.

**Follow-on work** (separate issues):

- PUA non-CV inheritance (actuarial approval required)
- Inherited `PR` / `QuikGps` (business rule required)
- PAAGERAT precedence conflicts (business rule required)
- `V-UINT-PDINT` / `QuikUint` blocker (infrastructure/data delivery)
