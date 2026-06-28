# Issue #21D — Risk Assessment

**Date:** 2026-06-27  
**Converter version:** v57.35  
**Scope:** Independent risk analysis for Track A and Track B

---

## Track A — Interest crediting rate (MDEPINT)

| Risk dimension | Rating | Analysis |
|----------------|--------|----------|
| **Technical complexity** | **Low–Medium** | Option B reuses CSO loader; one surgical app.py branch at quikdvdp emit |
| **Regression risk** | **Low** (Option B) / **High** (Option A) | Fleet-wide constant change hits 2,815 non-ISWL policies; plan-aware lookup scopes change |
| **Client impact** | **High visibility / positive** | All ISWL policies show wrong rate today; fix is client-requested |
| **Maintainability** | **Strong** (Option B) | Single CSO crosswalk authority matches NFOINT pattern |
| **Data governance** | **Strong** (Option B) | Actuarial CSV is delivered governance artifact; rulebook fallback only |
| **Operational simplicity** | **Medium** | Requires batch re-run + validator; no external extract wait |
| **Long-term ownership** | Actuarial owns CSO rates; conversion reads | Clear |

### Track A — Specific risks

| ID | Risk | Likelihood | Impact | Mitigation |
|----|------|------------|--------|------------|
| A-R1 | Non-ISWL policies incorrectly changed to 4.50% | High if Option A | High | **Reject Option A**; use plan-aware CSO lookup |
| A-R2 | MDEPINT fix does not resolve cash value (#21E) | Medium | Medium | Joint UAT with #21E; document field separation |
| A-R3 | CSO row missing for new ISWL plan | Low | Medium | Validator flags missing CSO match; fail QA not silent default |
| A-R4 | QLAdmin reads different field than assumed | Low | High | Client UAT on `010713704C` Dividend Accum Int Rate before fleet sign-off |
| A-R5 | NFOINT regression during MDEPINT work | Low | Medium | Assert NFOINT unchanged in validator diff |

### Track A — Rollback

| Item | Rollback action |
|------|-----------------|
| app.py MDEPINT enrichment | Revert branch; restore v57.35 |
| Rulebook comment change | Revert CSV row |
| Output | Re-run batch from v57.35 baseline |

---

## Track B — Blank owner / insured names

| Risk dimension | Rating | Analysis |
|----------------|--------|----------|
| **Technical complexity** | **Medium** | Two sub-defects; quikclnt fix bounded; RNA depends on client |
| **Regression risk** | **Low–Medium** | quikclnt change touches 14 IDs; rel_map unchanged if guard preserved |
| **Client impact** | **High on samples / low fleet %** | 25 policies; includes high-visibility Issue #21 examples |
| **Maintainability** | **Strong** (hybrid) | Referential integrity pattern is durable |
| **Data governance** | **Mixed** | RC-B2 fix uses RNA names (good); RC-B1 requires extract (best) |
| **Operational simplicity** | **Medium** | Split: converter fix internal; extract fix external |
| **Long-term ownership** | Conversion owns quikclnt integrity; client owns RNA completeness | Clear |

### Track B — Specific risks

| ID | Risk | Likelihood | Impact | Mitigation |
|----|------|------------|--------|------------|
| B-R1 | PRIMARY_PERSON type-flag leak reintroduced | Low | High | Preserve v57.28 guard; validator checks MPRIMID ∉ {I, single alpha} |
| B-R2 | Wrong person inferred via fallback heuristics | High if Option A | High | **Reject broad fallback**; require extract for missing IN/PO |
| B-R3 | quikclnt fix emits duplicate clients | Low | Medium | Dedup by MCLIENTID; schema validator |
| B-R4 | NULL-address clients break QLAdmin | Low | Medium | UAT on 592064 after emit; minimal row with names only |
| B-R5 | RNA re-extract delayed | Medium | Medium | Ship B1 independently; B2 when extract arrives |
| B-R6 | Partial fix leaves owner blank (RC-B3) | Medium | Low | Track HAS_PO in population CSV; validate per role |

### Track B — Rollback

| Item | Rollback action |
|------|-----------------|
| quikclnt emit logic | Revert app.py; re-run batch |
| New RNA extract | Restore prior extract file; re-run |
| rel_map | No change anticipated |

---

## Cross-track note (not combined analysis)

| Question | Answer |
|----------|--------|
| Can Track A fix mask Track B on sample policy? | No — independent fields |
| Can tracks ship in one release? | Yes, but **separate validators** and **separate rollback** |
| Shared dependency | Full batch run order: quikclnt → quikclid → quikmstr → quikdvdp |

---

## Protected issues — do not regress

| Issue | Protection |
|-------|------------|
| **#25** MPOLICY width | No MPOLICY schema change |
| **#26** MPREM | No quikridr MPREM change |
| **#28** Plan mapping authority | No crosswalk authority change |
| **#21M** QUIKMEMO | No quikmemo grain change |
| **v57.28** MPRIMID guard | Must remain active |

---

*Risk assessment complete. Mitigations assigned in `Issue_21D_Implementation_Strategy.md`.*
