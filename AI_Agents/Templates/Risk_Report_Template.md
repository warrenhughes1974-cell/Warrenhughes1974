# Issue [ID] — Risk Review Report

**Issue:** [ID] — [Title]  
**Framework stage:** Risk Agent  
**Status:** Ready for Development | No-Go | Conditional Go  
**Fallback simulated:** [if applicable]  
**Generated:** [YYYY-MM-DD]  
**Agent/script:** [name and version]

**Status note:** Risk analysis only — no production code changes unless later approved.

---

## Go / No-Go Recommendation

**[GO | CONDITIONAL GO | NO-GO]** — [one sentence rationale]

---

## 1. Current vs Proposed Mapping

| Field | Current | Proposed | Change? |
|-------|---------|----------|---------|
| | | | |

---

## 2. Premium / Related Fields Untouched

| Target | Source | Touched? |
|--------|--------|----------|
| | | **No** |

---

## 3. Repo References

| Location | Role |
|----------|------|
| | |

---

## 4. Population Analysis

| Metric | Count |
|--------|------:|
| Total rows analyzed | |
| Rows that would change | |
| Rows unchanged | |
| Blank / zero source rows | |

### Breakdown

| Dimension | rows | would_change |
|-----------|-----:|-------------:|
| [plan / seq / status] | | |

---

## 5. Fallback Recommendation (if applicable)

| Option | Rows changed | Assessment |
|--------|-------------:|------------|
| | | recommended / reject |

**Recommended fallback:** [rule]

---

## 6. Trace Policies

| Policy | Before | Proposed | Pass? |
|--------|-------:|---------:|-------|
| | | | |

---

## 7. Top [N] Largest Changes

| Policy | Before | After | Delta |
|--------|-------:|------:|------:|
| | | | |

---

## 8. Material Calculation Impact

[Intentional corrections vs accidental drift]

---

## 9. Prior Fix Preservation

| Check | Result |
|-------|--------|
| Issue #25 MPOLICY padding | |
| Issue #26 MPREM / MMODPREM | |

---

## 10. Regression Testing Checklist (for Validation Agent)

- [ ] Trace policies: [list]
- [ ] Untouched fields: [list]
- [ ] Row counts stable: [tables]
- [ ] Edge cases: [list]

---

## 11. Recommended Development Agent Task

1. [Exact surgical steps]
2. Do NOT change: [list]
3. Version bump: v[xx.xx]

---

## Appendix

- Blank / edge-case sample CSV: [path]
- Simulation script: [path]
