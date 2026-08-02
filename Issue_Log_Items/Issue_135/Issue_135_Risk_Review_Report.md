# Issue #135 — Risk Review Report

**Issue:** #135 — Claims Settlement vs CSO Total_Paid  
**Framework stage:** Risk Agent  
**Status:** Ready for Development (pending user approval)  
**Generated:** 2026-08-02  
**Agent/script:** Cursor Grok 4.5 (locked); Discovery/Output population evidence  
**Status note:** Risk analysis only — no production code changes unless later approved.

---

## Go / No-Go Recommendation

**CONDITIONAL GO** — Proceed to Development only with **phased** scope:

| Phase | Scope | Gate to start |
|---|---|---|
| **A** | Force `MINTAMT=0` on all `quikclms` | Immediate on Dev approval |
| **B** | CSO hard-control reverse-engineering + teacher defect fixes | After Phase A validator; reconciliation workbook required |
| **C** | Non-death `DTOFDEATH` clear + surrender completeness | After Phase B teacher cases PASS or parallel if isolated |

Unresolved residuals after reverse-engineering must **hold** (not force `MPAID` to `Total_Paid` without PACTG evidence).

---

## 1. Current vs Proposed Mapping

| Field | Current | Proposed | Change? |
|---|---|---|---|
| `quikclms.MPAID` (death) | Mixed vs CSO | = CSO `Total_Paid` when PACTG-proven | **Yes** (Phase B) |
| `quikclmp.MAMOUNT` | May duplicate / miss | Deduped economic payments | **Yes** (Phase B) |
| `quikclms.MINTAMT` | 487 nonzero rows | **Always 0.00** | **Yes** (Phase A) |
| `quikclms.DTOFDEATH` | Set on many STAT 99 / PS rows | Death families only | **Yes** (Phase C) |
| `quikclms.MEMOTEXT` | #134 notes | Untouched | **No** |

---

## 2. Premium / Related Fields Untouched

| Target | Touched? |
|---|---|
| `quikmstr.MMODPREM` | **No** |
| `quikridr.MPREM` (#26) | **No** |
| MPOLICY width (#25) | **No** |
| `#134` MEMOTEXT | **No** |
| Non-claims emit | **No** |

---

## 3. Repo References

| Location | Role |
|---|---|
| `claims_analysis/` phases 4–10, 17, 22–24 | Reconstruction / balancing / derivation |
| `claims_analysis/config/client_issue_log_decision_rules.json` | Items 14–19 — extend |
| `QLA_Migration/app.py` claims orchestration | Emit / post-process hooks |
| `qla_core/claims_emit_enhancements.py` | Emit enhancements |
| `qla_core/issue78_*` / `issue84_*` / `issue85_*` | Payee / header structure — preserve |
| New validator | `_validate_issue135_*.py` — CSO hard control + MINTAMT=0 |

---

## 4. Population Analysis

| Metric | Count (approx) |
|---|---:|
| CSO death claims | 1,656 |
| Amount OK today | 1,111 |
| Amount mismatch | 86 |
| Missing from Output | 459 |
| `quikclms` rows | 5,594 |
| `MINTAMT` nonzero → zero | **487** |
| `CLAIMSTAT=99` with `DTOFDEATH` set | 3,670 |

### Teacher defect impact (verified)

| Policy | Delta if fixed |
|---|---|
| `9011156098C` | MPAID 45000 → 15000 (−30,000) |
| `9010914301C` | MPAID 50039.96 → 25019.98 (−25,019.98) |
| `9010391359C` | MPAID 0 → 1260.06 (+ payee) |
| Interest examples with correct MPAID | MINTAMT → 0 only |

---

## 5. Fallback Recommendation

| Option | Assessment |
|---|---|
| A. Phased A→B→C with residual hold | **Recommended** |
| B. Force all MPAID = Total_Paid without PACTG proof | **Reject** — invents money |
| C. Fix only teacher examples, ignore CSO population | **Reject** — hard control requires population |
| D. Full claims rewrite | **Reject** — violates AGENTS.md |

**Recommended:** Option A.

---

## 6. Trace Policies (expected after)

| Policy | After MPAID | After MINTAMT | Notes |
|---|---:|---:|---|
| `9011156098C` | 15000.00 | 0 | Drop reinstate duplicates |
| `9010914301C` | 25019.98 | 0 | Dedup intra-co path |
| `9010391359C` | 1260.06 | 0 | Emit loan-death payee |
| `9010402010C` | 8920.15 | 0 | Amount already OK |
| `9010150740C` | 3213.59 | 0 | Add missing payee if evidence |

---

## 7. Regression Surfaces

- Claims already matching CSO must stay matched (1,111).
- `#134` memo overlay must remain.
- Item 16 div-deposit exclusion / Item 18 loan combine must not regress.
- `#78/#84/#85` payee/header structure.
- Non-candidate policies / non-claims tables unchanged.
- ISWL `PS-*` rows: death-date clear must not wipe legitimate death headers.

---

## 8. Recommended Development Agent Task

1. **Phase A:** Surgical force `MINTAMT=0` at claims emit; bump `APP_VERSION` (root + `QLA_Migration/app.py`); validator PASS on full Output.
2. **Phase B:** Build reconciliation workbook (CSO × PACTG × Output); implement include/exclude for teacher classes; hard-gate death emit; hold residuals with audit CSV in Reports/.
3. **Phase C:** Clear `DTOFDEATH` where claim family ≠ death; surrender completeness per examples.
4. Publish modified `quikclms`/`quikclmp` to `Output/Test_Validation/` on PASS.
5. Do **not** Close until G7: validator PASS + accountability IN_DATA on full Output.

---

## 9. Validation / Regression Checklist

- [ ] All `quikclms.MINTAMT` == 0
- [ ] Teacher policies match expected paid amounts
- [ ] CSO hard control: match count rises; mismatches classified; no silent invent
- [ ] Payee sum aligns with header for changed claims
- [ ] `#134` MEMOTEXT spot-check unchanged
- [ ] Non-death rows have blank `DTOFDEATH` (Phase C)
- [ ] Unrelated tables byte-stable or intentional-only diffs
- [ ] Accountability IN_DATA for #135 before Closure

---

## 10. Implementation confidence (Risk view)

| Scope | Confidence |
|---|---:|
| Phase A (`MINTAMT=0`) safe | **95%** |
| Teacher defect fixes with evidence | **85%** |
| Full 1,656 CSO hard control in one Development pass | **70%** |
| Overall safe delivery if phased + residual hold | **80%** |

Confidence is on **safe, gated delivery**, not on one-shot perfecting every residual without holds.
