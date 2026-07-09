# Issue #44 — Risk Review Report

**Issue:** #44 — ETI/RPU QuikLoan Balance Clear  
**Framework stage:** Risk Agent (G3)  
**Status:** **GO** — Ready for Development (Phase A + Phase B approved)  
**Generated:** 2026-07-09  
**Agent:** Risk Agent — read-only review (no production code in this stage)

---

## Go / No-Go Recommendation

**GO** — Surgical QuikLoan-only change:

1. **Phase A:** Fix `LAST_CHG_TIME` sort so chronological clears win.  
2. **Phase B:** Hold QuikLoan emit when `quikmstr.MSTATUS` is ETI (44) or RPU (45).

Blast radius is confined to `qla_core/quikloan_converter.py` (+ derivation rules note + version bump). No status remapping, no product-setup, no unrelated tables.

---

## 1. Current vs proposed

| Area | Current | Proposed |
|------|---------|----------|
| Latest PLOAN row | Time mis-parsed → stale balance | Correct HHMMSS order |
| Zero latest balance | Held (no emit) | Unchanged behavior once latest is correct |
| ETI/RPU with open PLOAN | Still emits loan | **Hold** — no QuikLoan row |
| MSTATUS 44/45 | Correct | Unchanged |

---

## 2. Impact (simulated)

| Metric | Value |
|--------|------:|
| Phase A policies flipping to zero latest | ~30 |
| BA samples fixed by Phase A alone | 5 / 6 |
| BA samples needing Phase B | 1 (`011226579C`) |
| Current ETI QuikLoan rows | 6 |
| Expected ETI QuikLoan rows after A+B | **0** |
| RPU QuikLoan rows today | 0 |

---

## 3. Untouched surfaces

| Target | Touched? |
|--------|----------|
| `quikmstr` / Issue #13 | **No** |
| `quikplan.LOANINT` | **No** |
| `quikridr` premiums / #26 | **No** |
| MPOLICY padding #25 | **No** |
| QuikLoan interest/date field formulas | **No** (selection + hold only) |

---

## 4. Regression surfaces

| Surface | Check |
|---------|-------|
| Non-ETI policies with active loans | Still emit; balances only change if same-day time tie was wrong |
| Zero-balance hold | Still holds |
| Orphan MPOLICY vs quikmstr | Existing orphan audit unchanged |
| QuikLoan schema / column order | Unchanged |

---

## 5. Fallback

If Phase B over-suppresses in UAT: feature-flag via derivation rule `suppress_quikloan_on_eti_rpu` (default **true** per approval); set false to rollback Phase B without reverting Phase A.

---

## 6. Development task (exact)

1. `select_latest_ploan_row_per_policy`: sort `LAST_CHG_TIME` as stripped zero-padded string (or int), **do not** call `parse_ploan_date` on it.  
2. `validate_quikloan_emit` / `convert_quikloan_from_ploan`: load MSTATUS map from quikmstr; hold `ETI_RPU_STATUS_HOLD` for 44/45.  
3. `quikloan_derivation_rules.json`: document `suppress_quikloan_on_eti_rpu: true`.  
4. Bump both `app.py` → **v57.59**.  
5. Evidence under `Issue_Log_Items/Issue_44/evidence/`.

---

## 7. Validation checklist (G5)

- [ ] BA 6 policies: no QuikLoan row (or MLOANBAL absent)  
- [ ] 010391876C…010525250C: Phase A alone would zero; A+B omit  
- [ ] 011226579C: Phase B omit despite open PLOAN  
- [ ] ~30 Phase A flip list audited  
- [ ] Spot-check active non-ETI loan still present  
- [ ] Schema / column order unchanged  

**Next:** Development Agent.
