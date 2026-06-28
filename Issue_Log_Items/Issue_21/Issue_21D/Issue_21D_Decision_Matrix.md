# Issue #21D — Decision Matrix

**Date:** 2026-06-27  
**Converter version:** v57.35  
**Scoring:** 1 (poor) – 5 (excellent) · **Bold** = selected

---

## Track A — MDEPINT authority options

| Criterion | **B: CSO plan-aware** | A: Constant 4.50 | C: Extract-driven |
|-----------|:--:|:--:|:--:|
| Correctness for ISWL (2,268) | **5** | 5 | 4 |
| Safety for non-ISWL (2,815) | **5** | 1 | 4 |
| Technical complexity (inverse) | 4 | **5** | 2 |
| Regression risk (inverse) | **4** | 1 | 3 |
| Maintainability | **5** | 2 | 4 |
| Data governance | **5** | 2 | 5 |
| Time to implement | 4 | **5** | 1 |
| Operational simplicity | 4 | **5** | 2 |
| Alignment with NFOINT path | **5** | 2 | 3 |
| Client dependency | **5** | 5 | 1 |
| **Total** | **46** | 29 | 29 |

### Track A decision

| Decision | Choice |
|----------|--------|
| **Recommended option** | **B — Derive MDEPINT from CSO Mortality Crosswalk by MPLAN** |
| **Rejected** | A — fleet constant (non-ISWL blast radius) |
| **Deferred** | C — until LifePRO extract column identified |

---

## Track B — Blank name remediation options

| Criterion | **D: Hybrid** | B: quikclnt only | C: Extract only | A: Converter fallback |
|-----------|:--:|:--:|:--:|:--:|
| RC-B1 coverage (RNA gap) | **5** | 1 | 5 | 3 |
| RC-B2 coverage (quikclnt gap) | **5** | 5 | 1 | 2 |
| Regression risk (inverse) | **4** | 4 | 5 | 1 |
| Data governance | **5** | 4 | 5 | 1 |
| Client dependency (inverse) | 3 | **5** | 1 | 4 |
| Time to first value | **4** | 5 | 1 | 4 |
| Maintainability | **5** | 4 | 4 | 1 |
| Identity accuracy | **5** | 5 | 5 | 1 |
| Operational ownership clarity | **5** | 3 | 4 | 2 |
| **Total** | **41** | 31 | 27 | 18 |

### Track B decision

| Decision | Choice |
|----------|--------|
| **Recommended option** | **D — Hybrid: Phase B1 quikclnt integrity + Phase B2 RNA re-extract** |
| **Phase 1 (converter)** | B — emit missing quikclnt rows (14 NAME_IDs) |
| **Phase 2 (client)** | C — RNA re-pull for policies missing IN/PO |
| **Rejected** | A — broad missing-RNA tolerance without signed rules |

---

## Combined release decision

| Question | Decision |
|----------|----------|
| Single issue or two? | **Two independent remediations** under Issue #21D |
| Same release train? | **Allowed** if validators pass independently |
| Same code change? | **No** — separate app.py branches |
| Dependency Gate required? | **Yes** — before Development |

---

## Approval gates (pre-Development)

| Gate | Track A | Track B |
|------|---------|---------|
| Planning approved | Required | Required |
| Dependency Gate pass | Required | Required |
| Client non-ISWL rate confirmation | Recommended | — |
| RNA re-extract request issued | — | Required for RC-B1 |
| #21E joint UAT plan | Required | — |

---

*Decision matrix complete.*
