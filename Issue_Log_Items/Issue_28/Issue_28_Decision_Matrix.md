# Issue #28 — Decision Matrix

**Planning date:** 2026-06-24  
**Scoring:** 1 (poor) – 5 (excellent) per criterion

---

## Options evaluated

| ID | Option |
|----|--------|
| A | Promote `crosswalk_ql_plan_code` in runtime loader |
| B | Enable `CROSSWALK_OVERLAY=1` by default |
| C | Update `ql_plan_code` in catalog CSV (data-only) |
| D | New `PLAN_MAPPING_MODE` feature flag |
| E | **Hybrid recommended:** A + Phase 2 P3E MPLAN alignment |

---

## Criteria scores

| Criterion | Weight | A | B | C | D | E |
|-----------|--------|---|---|---|---|---|
| Technical complexity (lower = better) | 15% | **5** | 4 | 5 | 2 | 4 |
| Regression risk (lower = better) | 20% | 4 | 3 | 4 | 2 | 4 |
| Maintainability | 15% | **5** | 2 | 3 | 2 | 4 |
| Operational simplicity | 15% | **5** | 2 | 4 | 2 | 3 |
| Architecture compatibility (P3C/P3E) | 15% | **5** | 2 | 3 | 3 | **5** |
| Crosswalk 5/22/2026 alignment | 10% | **5** | 4 | 5 | 4 | **5** |
| Future conversion impact | 5% | **5** | 3 | 3 | 3 | **5** |
| Implementation effort (lower = better) | 5% | 4 | 3 | 4 | 2 | 3 |
| **Weighted total** | 100% | **4.70** | 2.75 | 3.85 | 2.35 | **4.45** |

---

## Detailed scoring rationale

### Technical complexity
- **A (5):** ~20 lines in one function; aligns with existing P3C column priority logic.
- **B (4):** Env/default changes only, but dual-path testing required.
- **C (5):** No code; CSV edits + sync.
- **D (2):** New mode matrix, docs, tests across 3 behaviors.
- **E (4):** A plus P3E enablement sequencing and validation.

### Regression risk
- **A/C (4):** Same PLAN output delta; manageable with validators.
- **B (3):** Flag drift + quikridr still broken without P3E.
- **D (2):** Multiple modes multiply test surface.
- **E (4):** Phased approach reduces simultaneous blast radius.

### Maintainability
- **A (5):** Single code authority rule; compat column retained for audit.
- **B (2):** Two sources of truth (catalog + xlsx overlay).
- **C (3):** Generator regen can undo fixes.
- **D (2):** Permanent mode branching.

### Operational simplicity
- **A (5):** No operator flags; batch behavior deterministic.
- **B (2):** Must enforce overlay on all runs.
- **C (4):** Deploy CSV; no env config.
- **D (2):** Operators must understand modes.

### Architecture compatibility
- **A/E (5):** Implements P3C intent — catalog authoritative column drives emit.
- **B (2):** Bypasses catalog; scaffold overlay parallel path.
- **C (3):** Data aligns but code still reads wrong column semantically.
- **D (3):** Partial — still encodes dual behavior.

### Crosswalk alignment
- All viable options achieve 141/141 PLAN alignment **if** DISCHO25 catalog row added and quikridr addressed in Phase 2.

### Implementation effort (person-days estimate)

| Option | Estimate |
|--------|----------|
| A | 0.5–1 day dev + 0.5 day validation |
| B | 0.25 day config + 1 day validation (incomplete fix) |
| C | 0.25 day CSV + 0.5 day validation + generator update |
| D | 1.5–2 days dev + 1 day validation |
| E Phase 1 (A) | Same as A |
| E Phase 2 (P3E) | +0.5 day dev + 0.5 day validation |

---

## Ranking

| Rank | Option | Weighted score | Recommendation |
|------|--------|----------------|----------------|
| **1** | **A — Promote crosswalk_ql_plan_code** | **4.70** | **Primary recommendation** |
| 2 | E — A + P3E Phase 2 | 4.45 | **Full remediation path** |
| 3 | C — Catalog data promotion | 3.85 | Fallback if code change blocked |
| 4 | B — Overlay default ON | 2.75 | Not recommended |
| 5 | D — PLAN_MAPPING_MODE flag | 2.35 | Not recommended |

---

## Recommendation

**Adopt Option A as Phase 1**, with **Option E Phase 2** (P3E MPLAN alignment) after quikplan validation passes.

### Rationale

1. Intake proved the authoritative values **already exist** in catalog — Option A activates them at the single runtime choke point without manual CSV surgery.
2. Option A **aligns runtime with P3C** closed product authority design already in `product_catalog_authority.py`.
3. Option C achieves the same output but **does not fix the semantic bug** in the loader and remains vulnerable to P2E regeneration.
4. Option B is **incomplete** (quikridr), **operationally fragile**, and uses a module explicitly marked scaffold/disabled.
5. Option D adds complexity **without client requirement** for dual-mode operation.

### Fallback

If enterprise change control blocks `qla_core/` modification in this release window, **Option C** is acceptable as a **temporary** measure with mandatory P2E generator update in the same change set.

---

## DISCHO25 disposition

**Separate catalog add** required in all options — not an alias of DISCHO247C. See `Issue_28_DISCHO25_Investigation.md`.

---

## Client decision points (for Dependency Gate)

1. Confirm binding authority of Policy Form Crosswalk 5.22.2026 for all 33 PLAN changes.
2. Accept re-UAT scope for product catalog / plan review.
3. Confirm Phase 2 P3E enablement for quikridr MPLAN (recommended).
4. Confirm FORM column changes remain **out of scope** for #28 unless explicitly added.
