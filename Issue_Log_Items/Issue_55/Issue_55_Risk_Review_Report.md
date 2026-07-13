# Issue #55 — Risk Review Report

**Issue:** #55 — Unit Issues (tiny-unit floor → zero)  
**Framework stage:** Risk Agent  
**Status:** **Conditional Go**  
**Generated:** 2026-07-13  
**Agent/script:** Risk Agent (Cursor Grok 4.5) + fleet scan of `Output/quikridr.csv`  
**Business rule (user 2026-07-13):** If `MUNIT` **&lt; 0.001** (and &gt; 0), set `MUNIT` to **0** automatically.

**Status note:** Risk analysis only — no production code changes in this stage.

---

## Go / No-Go Recommendation

**CONDITIONAL GO** — Surgical post-map floor on `quikridr.MUNIT` is low blast-radius and matches the stated business rule; **does not** fix Phase 2 false Units `3000` (QLAdmin NFO×VPU / plan INITVAL behavior). Approve Development only for the tiny-unit floor.

---

## 1. Current vs Proposed Mapping

| Field | Current | Proposed | Change? |
|-------|---------|----------|---------|
| `quikridr.MUNIT` | Direct `PPBEN.NUMBER_OF_UNITS` | After map: if `0 < MUNIT < 0.001` → `0` | **Yes** |
| `quikridr.MVPU` | Direct `VALUE_PER_UNIT` | Unchanged | **No** |
| Phase 2 SU units (e.g. 0.53) | As source | Unchanged (≥ 0.001) | **No** |

**Supersedes earlier ticket text** that Phase 1 should remain `0.00001` — user rule now zeros those.

**Threshold:** strict **less than** `0.001` (so `0.001` itself stays).

---

## 2. Premium / Related Fields Untouched

| Target | Source | Touched? |
|--------|--------|----------|
| `quikridr.MPREM` | `ANN_PREM_PER_UNIT` + #26 fallback | **No** |
| MPOLICY padding | `format_qladmin_mpolicy` (#25) | **No** |
| `MVPU` / fees / status | Existing | **No** |
| `quikmstr.MNFOPT` | Existing | **No** |

---

## 3. Repo References

| Location | Role |
|----------|------|
| `Configs/Sync_Rulebook_quikridr.csv` | `NUMBER_OF_UNITS → MUNIT` |
| Engine quikridr emit path (`app.py` / rulebook apply) | Apply floor after numeric coerce |
| `qladmin_core` / #21K | Preserve 5-dp storage; zero is valid |

Preferred implementation: **one surgical post-process** when writing/normalizing `MUNIT` (not a rulebook rewrite).

---

## 4. Population Analysis

| Metric | Count |
|--------|------:|
| Total `quikridr` rows | 6,934 |
| Rows with `0 < MUNIT < 0.001` | **148** |
| Rows unchanged by rule | 6,786 |

### Breakdown

| Dimension | rows | would_change |
|-----------|-----:|-------------:|
| Phase 1 + plan `1SALML` + `MUNIT=.00001` | 147 | 147 → `0` |
| Phase 2 + plan `1708PA` + `MUNIT=.00009` | 1 | 1 → `0` (`010434419C`) |
| Issue samples Phase 2 (0.53 / 1.05 / 0.647) | 3 | **0** |

---

## 5. Fallback Recommendation

| Option | Rows changed | Assessment |
|--------|-------------:|------------|
| A. Fleet: `MUNIT < 0.001` → `0` | 148 | **Recommended** — matches user rule |
| B. Limit to plan `1SALML` only | 147 | Reject unless user narrows scope (leaves PUA `.00009`) |
| C. No converter change (QLAdmin-only) | 0 | Reject for this rule — user asked conversion auto-set |

**Recommended:** Option A.

---

## 6. Trace Policies

| Policy | Phase | Before `MUNIT` | Proposed | Pass? |
|--------|------:|---------------:|---------:|:-----:|
| `018495BC` | 1 | 0.00001 | **0** | Y (per new rule) |
| `018495BC` | 2 | 0.53 | 0.53 | Y |
| `018499CC` | 1 | 0.00001 | **0** | Y |
| `018499CC` | 2 | 1.05 | 1.05 | Y |
| `018510C` | 1 | 0.00001 | **0** | Y |
| `018510C` | 2 | 0.647 | 0.647 | Y |
| `010434419C` | 2 | 0.00009 | **0** | Y (rule); confirm PUA OK |

**Out of scope for this change:** Edit Phase showing Units `3000` / `1.00000` while DBF `MUNIT` is correct — separate QLAdmin/product path (`MNFOPT×MVPU` / `INITVAL`).

---

## 7. Largest Changes (by |Δ|)

All 147 `1SALML` rows: **0.00001 → 0** (Δ = 0.00001, face Δ = **$0.01**).  
One PUA: **0.00009 → 0** (face Δ = **$0.09**).

---

## 8. Regression Surfaces

| Guard | Expectation |
|-------|-------------|
| #25 MPOLICY | Unchanged |
| #26 MPREM | Unchanged |
| #21K five-decimal `MUNIT` | Still emit 5 dp; zeros as `0` / `.00000` per existing formatter |
| Non-candidate rows `MUNIT ≥ 0.001` | Byte-identical |
| Phase 2 SU faces $530 / $647 / $1050 | Unchanged |

---

## 9. Validation Plan (post-Dev)

1. `0 < float(MUNIT) < 0.001` count = **0** in new `quikridr.csv`  
2. Trace three Issue #55 policies: Phase 1 = 0; Phase 2 unchanged  
3. Spot-check `010434419C` PUA → 0  
4. Diff: only `MUNIT` on the 148 keys; row counts unchanged  
5. Publish touched `quikridr` to `Output/Test_Validation/` on PASS  

---

## 10. Recommended Development Task (Composer 2.5)

```
Issue #55 approved for Development (Conditional Go — tiny-unit floor only).

Switch to Composer 2.5. Read AI_Agents/Development_Agent.md.
Surgical only: after NUMBER_OF_UNITS→MUNIT mapping, if 0 < MUNIT < 0.001 set MUNIT to 0.
Bump APP_VERSION in root app.py and QLA_Migration/app.py.
Do not change MVPU/MPREM/#25/#26. Do not attempt QLAdmin 3000 display fix.
Add QLA_Migration/_validate_issue55_munit_floor.py.
```

---

## Conditions

1. User confirms threshold is **strict `< 0.001`** (not `≤`).  
2. User accepts **fleet** apply including PUA `010434419C` `.00009 → 0`.  
3. Phase 2 **3000** UI issue tracked as **out of scope** for this Dev slice (or separate follow-up).
