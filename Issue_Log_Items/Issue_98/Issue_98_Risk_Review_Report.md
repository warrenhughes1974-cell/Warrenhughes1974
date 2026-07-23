# Issue #98 — Risk Review Report

**Issue:** #98 — CV Endpoint Off By One  
**Framework stage:** Risk Agent (G3)  
**Status:** Conditional Go — awaiting Development approval  
**Generated:** 2026-07-22  
**Agent:** Risk Agent (Cursor Grok 4.5, read-only)

**Status note:** Risk analysis only — no production code changes.

---

## Go / No-Go Recommendation

**CONDITIONAL GO** — Real conversion defect confirmed in current Output (not stale UAT). Safe to develop a surgical QuikCvs remap fix **only if** #37/#41 validators remain PASS and inheritance parity `#40` (`17085M` vs `170858`) is rechecked after re-emit.

---

## 1. Is this actually an issue?

**Yes.**

| Question | Answer |
|----------|--------|
| Was #41 “done”? | Partially — `1960PO` M/26 endpoint proof still holds |
| Does Eric’s new case match Output? | **No** — 5/5 proof points FAIL |
| Is Output missing `17085M` CV? | **No** — 1,002 keys present (#40 held) |
| Root cause | `#37` `cv_lifepro_first_duration` over-shift for this age → +1 late vs LifePRO + truncates terminal `1000` |

Prior decisions that still stand:

1. **#37:** Build LifePRO-style CV grid with FNZ + first-duration offset; maturity `100 - age`.  
2. **#41:** Keep age-100 endpoint (`return lp_d`, not `lp_d - 1`).  
3. **#40:** `17085M` may inherit `670 GL85-8` CV factors.

What did **not** get closed: the 960-PO-derived first-duration matrix does not match LifePRO display years on GL85 (and many other ages truncate source `1000`).

---

## 2. Current vs proposed mapping

| Field / rule | Current | Proposed | Change? |
|--------------|---------|----------|---------|
| `cv_remap_ql_duration` formula shape | `source + first - fnz` | Keep shape **or** endpoint-anchor equivalent | Maybe |
| `cv_lifepro_first_duration(M,14)` | `4` | Effective offset **+1** (e.g. first=`3`) | **Yes** |
| Age-100 last duration | `100 - age` | Unchanged | No |
| CV values | From Rate_Table | Unchanged | No |
| Non-CV tables | — | Unchanged | No |

Eric-aligned targets for `17085M` M/14:

| Duration | Value |
|---------:|------:|
| 3 | 0.06 |
| 54 | 674.69 |
| 55 | 688.11 |
| 85 | 975.61 |
| 86 | 1000.00 |

---

## 3. Before / after impact (measured)

### Client proof (before)

Evidence: `evidence/issue98_010398471C_cv_trace.csv` — **5 / 5 FAIL**.

### Fleet signal (before, GL85 owner only)

On `670 GL85-8` CV slices, current first-duration rule **truncates** source terminal `1000` for **89** sex/age slices (kept for **53**). `17085M` Output today: **85** slices end at `975.61`, **53** end at `1000`, **4** other.

A correct remap should move terminal `1000` onto duration `100 - age` wherever source provides it — large intentional QuikCvs churn on inherited + direct CV plans.

### Untouched surfaces

| Target | Touched? |
|--------|----------|
| `quikplan` / `quikmstr` / `quikridr` | **No** |
| `QuikNps` / `QuikGps` / other non-CV | **No** |
| `#40` owner selection | **No** |
| `#25` / `#26` | **No** |

---

## 4. Regression surfaces

| Surface | Risk | Mitigation |
|---------|------|------------|
| Issue #41 `1960PO` M/26 (`784.65` @ 57; 1000 @ 74) | High if offset logic rewritten carelessly | Must PASS `_validate_issue41_quikcvs_endpoint.py` |
| Issue #37 G5 placement matrix | High | Must PASS `_validate_issue37_quikcvs_placement.py` / `_validate_issue37_g5_matrix.py` |
| Issue #40 `17085M` vs `170858` parity | Medium | Same remap on owner + child → values equal at same index |
| Other products’ leading zeros | Medium | Spot-check first nonzero vs LifePRO for 2–3 non-960 plans |
| Full guarded rate emit / QuikUint | Pre-existing | QuikCvs-only re-emit acceptable (same as #41) if Uint still blocked |

---

## 5. Fallback options

| Option | When | Impact |
|--------|------|--------|
| **Primary — remap fix + QuikCvs re-emit** | Default | Fleet CV placement correction |
| **Narrow — GL85 / young-age first-duration only** | If endpoint-anchor regresses 960 PO | Fixes Eric; leaves other truncated ages |
| **No code — client reload only** | **Rejected** | Output already wrong for Eric’s anchors |

---

## 6. Recommended Development task (surgical)

1. In `qla_core/rate_factor_loader.py`, correct CV duration offset so that for proof `17085M`/`670 GL85-8` M/14:
   - `.06` → QL duration **3**
   - `1000` → QL duration **86** (not truncated)
2. Prefer a rule that also clears truncated-`1000` slices generally **without** moving `1960PO` M/26 off its #41 anchors.
3. Bump `APP_VERSION` in root `app.py` and `QLA_Migration/app.py` if engine path changes.
4. Add `QLA_Migration/_validate_issue98_quikcvs_endpoint.py` (or extend #41 validator) with Eric’s five anchors.
5. Re-emit `QLA_Migration/Output/rates/QuikCvs.csv`; publish to `Output/Test_Validation/rates/` on PASS.
6. Re-run #37 + #41 validators.

**Do not** change inheritance manifests, non-CV loaders, or policy tables.

---

## 7. Validation checklist (for Validation Agent)

- [ ] V98-01…07 from Planning Report  
- [ ] Issue #41 endpoint 5/5 PASS  
- [ ] Issue #37 placement PASS  
- [ ] `17085M` == `170858` at matched QL durations  
- [ ] Accountability / Output gate when closing (G7)

---

## 8. Decision gates

| Gate | Result |
|------|--------|
| G0 Intake | **PASS** |
| G1 Planning | **PASS** |
| G2 Dependency | **PASS (Conditional — screenshots optional)** |
| G3 Risk | **CONDITIONAL GO** |

**Stop:** Awaiting explicit **Approved for Development** before any code change.
