# Issue #134 — Risk Review Report

**Issue:** #134 — Death Benefit Notes  
**Framework stage:** Risk Agent  
**Status:** Ready for Development (pending user approval)  
**Fallback simulated:** N/A (routing change, not premium calc)  
**Generated:** 2026-08-01  
**Agent/script:** Cursor Grok 4.5 (locked); read-only join counts vs Output  
**Status note:** Risk analysis only — no production code changes unless later approved.

---

## Go / No-Go Recommendation

**CONDITIONAL GO** — Target and sources are confirmed; impact is bounded and reversible; proceed to Development only with the locked rules below (death-claim attach, lineage replace, B exclude from quikmemo, no QuikHcmm).

---

## 1. Current vs Proposed Mapping

| Field | Current | Proposed | Change? |
|-------|---------|----------|---------|
| `quikmemo` from PNOTE B | Emitted (wrong tab) | **Excluded** | **Yes** |
| `quikmemo` from PNOTE non-B + PENSE | Emitted | Unchanged | **No** |
| `quikclms.MEMOTEXT` | Phase 10B `mlineage` audit string | Formatted PNOTE B text (multi-note `\n---\n`) | **Yes** (death candidates) |
| `QuikHcmm` | Not converted | Still not converted | **No** |
| `quikclmp` | Payees | Untouched | **No** |

---

## 2. Premium / Related Fields Untouched

| Target | Source | Touched? |
|--------|--------|----------|
| `quikmstr.MMODPREM` | MODE_PREMIUM | **No** |
| `quikridr.MPREM` | #26 mapping | **No** |
| MPOLICY width | #25 `format_qladmin_mpolicy` | **No** (join only) |
| `quikclms` money / CLAIMSTAT / dates | Claims path | **No** |
| `quikclmp` | Payees | **No** |

---

## 3. Repo References

| Location | Role |
|----------|------|
| `qla_core/quikmemo_converter.py` | Must filter FILE_TYPE=B |
| `QLA_Migration/Configs/Sync_Rulebook_quikclms.csv` | `mlineage → MEMOTEXT` overwritten by overlay |
| `app.py` claims emit | Overlay hook or post-step |
| `qla_core/quikisrr_loader.py` | Avoid clobbering non-death synthetic memos |
| Validators (new) | `_validate_issue134_*.py` |

---

## 4. Population Analysis

| Metric | Count |
|--------|------:|
| PNOTE B source rows | 4,149 |
| B distinct policies | 1,504 |
| B policies with a `quikclms` row | 1,286 |
| B policies with DEATH_CLAIM header | 1,233 |
| Death headers in Output | 1,237 |
| Death headers that would gain B text | **1,233** |
| B policies orphaned (no clms) | 218 |
| Multi-claim policies among B∩clms | 214 |
| B source rows on policies with some clms | 3,436 |
| `quikclms` rows total | 5,594 |
| `quikclms` rows expected MEMOTEXT rewrite | ~1,233 death (+0 if non-death skipped) |
| `quikmemo` rows today | 5,084 |
| `quikmemo` content change | Drop B segments; row count may fall if policy was B-only |

### Breakdown (B-matched claim rows by family)

| Family (lineage tag) | Claim rows on B-matched policies |
|----------------------|---------------------------------:|
| DEATH_CLAIM | 1,233 |
| PARTIAL | 769 |
| DISBURSEMENT_CLAIM | 28 |
| SURRENDER_CLAIM | 7 |

**Attach rule (locked):** write B text only on **DEATH_CLAIM** rows → ~1,233 MEMOTEXT updates; do not stamp death notes onto PARTIAL/SURRENDER/DISBURSEMENT headers.

---

## 5. Fallback Recommendation (if applicable)

| Option | Rows changed | Assessment |
|--------|-------------:|------------|
| A. Replace lineage with B on DEATH only (Planning default) | ~1,233 | **Recommended** |
| B. Append B after lineage | ~1,233 | Acceptable if Eric requires audit in UI |
| C. Also stamp non-death claim headers | +804 family rows | **Reject** — wrong claim context |
| D. Emit B to QuikHcmm | N/A | **Reject** — health table |
| E. Leave B on quikmemo as well | Dual display | **Reject** — client wants Claims Tab |

**Recommended fallback:** Option A. Orphan log for 218 policies with B and no clms.

---

## 6. Trace Policies

| Policy | Before | Proposed | Pass? |
|--------|--------|----------|-------|
| `9010150740C` | Lineage DEATH… | B notes (PB = VIOLA…) on Claims Memo; B gone from Policy Memo | Expect |
| `9010150910C` | Lineage DEATH… | PB = SUSAN SWANSON… | Expect |
| `9010335038C` | Lineage DEATH…; B also in quikmemo today | Claims Memo only for B; keep any non-B/PENSE on quikmemo | Expect |
| `9010331157C` | Lineage DEATH… | PB = DOROTHY… | Expect |
| `9010363098C` | Lineage DEATH… | PB = SANDRA… | Expect |

---

## 7. Top Changes (content)

Not numeric. Largest multi-note policies: up to **18** B source rows per policy — MEMOTEXT blobs will be long; acceptable for MEMO type; Validation should spot-check a high-count policy.

---

## 8. Material Calculation Impact

None — text routing only. No premium, reserve, or claim money fields.

---

## 9. Prior Fix Preservation

| Check | Result |
|-------|--------|
| Issue #25 MPOLICY padding | **Preserve** — join via `format_qladmin_mpolicy` only |
| Issue #26 MPREM / MMODPREM | **Untouched** |
| Issue #50 PNOTE fixed-width | **Preserve** — filter after read |
| Issue #21M merge grain | **Preserve** for non-B + PENSE |

---

## 10. Regression Testing Checklist (for Validation Agent)

- [ ] Trace policies above: B text on `quikclms.MEMOTEXT`; death family only
- [ ] Sample B LINE text **absent** from `quikmemo`
- [ ] Non-B policy memo sample unchanged (PNOTE P + PENSE)
- [ ] `quikclmp` row count and schema unchanged
- [ ] Non-death `quikclms.MEMOTEXT` unchanged when policy has no B / not death attach
- [ ] Orphan B count logged (~218 policies)
- [ ] #25 MPOLICY width still valid on touched tables
- [ ] Publish `quikclms.csv` + `quikmemo.csv` to `Test_Validation/` on PASS

---

## 11. Recommended Development Agent Task

1. `quikmemo_converter.py`: skip `FILE_TYPE` strip-equals `B`; stats `skipped_file_type_b`.
2. New surgical helper (preferred) e.g. `qla_core/issue134_claim_memo_overlay.py`: read PNOTE B via existing fixed-width reader; format notes; join death `quikclms`; replace `MEMOTEXT`; write orphan audit under `QLA_Migration/Reports/` or `Validation/` (not Output root).
3. Wire overlay after claims emit in `app.py` (minimal hook); bump **both** `APP_VERSION` (current v58.46 → next).
4. Do **not** create QuikHcmm converter; do **not** edit `quikclmp`; do **not** change money/CLAIMSTAT.
5. Add `_validate_issue134_claim_memos.py` covering checklist §10.
6. Full Output validation before Closure (G7).

---

## Appendix

- Planning: `Issue_134_Planning_Report.md`  
- Dependency Gate: **PASS**  
- Discovery: QuikHcmm discussion closed (health-only)  
