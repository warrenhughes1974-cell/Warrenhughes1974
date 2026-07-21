# Issue #85 — Risk Review Report

**Issue:** #85 — Duplicate claim headers (same policy + phase)  
**Framework stage:** Risk Agent (G3)  
**Status:** **Conditional Go → Ready for Development** (pending explicit Development approval)  
**Generated:** 2026-07-17  
**Model:** Cursor Grok 4.5 (locked)  
**Status note:** Risk analysis only — no production code changes.  
**Decisions:** D1–D5 **client-approved 2026-07-17** (`Issue_85_Decisions_For_Review.md`)  
**Evidence:**  
- `evidence/issue85_risk_summary.csv`  
- `evidence/issue85_risk_merge_drops.csv`  
- `evidence/issue85_risk_rephase.csv`  
- `scripts/risk_review_issue85_header_structure.py`  
**Scope:** `Issue_85_Scope_Decisions.md` (SD-85 + locked D1–D5)

---

## Go / No-Go Recommendation

**CONDITIONAL GO** — Client approved D1–D5; simulation under the hybrid rule clears all duplicate policy+phase headers; Development may proceed under the locks below.

| Factor | Assessment |
|--------|------------|
| Decisions | **Approved** 2026-07-17 |
| Headers before → after | **5,624 → 5,447** (−177 true-duplicate drops) |
| Rephase moves | **3,034** claim headers get a new phase |
| Duplicate pol+phase after | **0** (structure goal met) |
| `quikclmp` row count | **6,151 unchanged** (no invent / no delete) |
| CLAIMSTAT (#79) | Untouched |
| Policy $ balance | Unchanged by structure alone (898 unbalanced remain → **#84 Track B**) |
| #84 Track A | May proceed independently (D5 carve-out) |

Development may proceed after user says **Approved for Development** and switches to **Composer 2.5**.

---

## 1. Current vs Proposed Mapping

| Situation | Current | Proposed (D1–D4) | Change? |
|-----------|---------|------------------|---------|
| Same CLAIMNUM repeated on one phase | Multiple headers | **Merge** to one; sum MPAID; keep face/dates per D2 | **Yes** (−177 rows) |
| Different CLAIMNUMs on one phase | Crowded | **Re-phase** each claim to unique phase (book pattern 0/2/3/…) | **Yes** (3,034 moves) |
| Payees | Attached by pol+phase (ambiguous) | Follow claim by date/amount; unmatched → survivor + exception flag | **Yes** (phase updates only) |
| CLAIMSTAT | Post-#79 | Unchanged | **No** |
| New payees | Post-#78 | Unchanged count | **No** |
| Money components (DIVIDENDS etc.) | — | Out of scope (#84) | **No** |

---

## 2. Premium / Related Fields Untouched

| Target | Touched? |
|--------|----------|
| MPOLICY padding (#25) | **No** |
| MPREM (#26) | **No** |
| CLAIMSTAT (#79) | **No** |
| Payee invent (#78) | **No** |
| `quikmstr` / `quikridr` / rates | **No** |
| DIVIDENDS / PREMIUM / SUSPENSE / MINTRATE (#84 Track B) | **No** |

---

## 3. Repo References

| Location | Role |
|----------|------|
| `docs/Policy/quikclms.dbf` | Authority: 0 duplicate pol+phase; multi-claim uses distinct phases |
| `QLA_Migration/Output/quikclms.csv` | Before-state 5,624 headers |
| `QLA_Migration/Output/quikclmp.csv` | Payees 6,151 — re-phase / re-attach only |
| `Issue_85_Decisions_For_Review.md` | Client-approved plain-English decisions |
| Future Dev hook | Post-emit surgical structure fix + Reports audit |

---

## 4. Population Analysis (simulated)

| Metric | Count |
|--------|------:|
| Headers before | 5,624 |
| Headers after | **5,447** |
| Merge groups (same CLAIMNUM) | 150 |
| Merge losers dropped | **177** |
| Rephase moves | **3,034** |
| Dup pol+phase rows before | 3,770 |
| Dup pol+phase rows after | **0** |
| Non-unique pol+phase groups after | **0** |
| `quikclmp` rows | 6,151 (must stay) |
| Policy-level MPAID vs payee balance before | 1,352 balanced / 898 unbalanced |
| Same after merge-only | 1,352 / 898 (expected — money recon is #84) |

### Why policy $ balance does not move here

Merging same-claim headers **sums** Net Payment, so policy totals stay the same. The 898 unbalanced policies are a **money** defect (#84 Track B / payee matching), not fixed by structure alone. Structure must land first so Track B can attribute payees to the right claim.

---

## 5. Fallback Recommendation

| Option | Assessment |
|--------|------------|
| **A. Hybrid D1–D5 as approved (recommended)** | Clears structure; preserves real multi-claim history |
| B. Merge-all (one header per phase only) | **Reject** — erases distinct claim numbers (e.g. yearly PS-* events) |
| C. Rephase-only, keep same-CLAIMNUM dups | **Reject** — leaves true duplicates |
| D. Defer until #84 Track B | **Reject** — Track B needs unique claim identity first |

**Recommended:** Option A (approved).

---

## 6. Trace Policies

| Policy | Before | After (sim) | Pass? |
|--------|--------|-------------|-------|
| `010914301C` | 2 headers, same CLAIMNUM, $25,019.98 each | **1** header, MPAID **$50,039.96**, MFACE 25,000 | **Yes** (merge) |
| `011156098C` | 2 headers, same CLAIMNUM, $30K + $15K | **1** header, MPAID **$45,000**, MFACE 45,000 | **Yes** (merge) |
| `011014579C` | 11 headers, **same** CLAIMNUM, MPAID 0 | **1** header (merge); 15 payees re-attach; MPAID still 0 until #84 Track A | **Yes** (structure) |
| `011054606C` | 10 headers (1 RC dup + 8 PS + …) | RC merged; PS-* **re-phased** to 0,2,3… | **Yes** (hybrid) |
| `010150740C` | 1 clean header | Unchanged | **Yes** (control) |
| `010391359C` | 1 header, MPAID 0 | Unchanged structure; Track A money later | **Yes** |

---

## 7. Material Structure Moves

| Move | Count | Meaning |
|------|------:|---------|
| Drop true-duplicate headers | 177 | Same claim written twice |
| Rephase distinct claims | 3,034 | Separate events get own phase |
| Net header reduction | 177 | 5,624 → 5,447 |

---

## 8. Material Calculation Impact

- **Intentional:** Unique policy+phase claim identity; multi-claim policies readable like the real book.  
- **Not accidental:** No CLAIMSTAT rewrite; no payee invent/delete; money component fields not filled here.  
- **Residual:** 898 policy-level MPAID≠payee cases remain for **#84**; Track A still needed for ~300 header-zero cases.  
- **Payee risk:** Development must update `quikclmp.MPHASE` when headers re-phase, with exception audit for unmatched checks (D4).

---

## 9. Prior Fix Preservation

| Check | Result |
|-------|--------|
| Issue #25 MPOLICY | **Preserve** |
| Issue #26 MPREM | **Untouched** |
| Issue #78 payees | **Preserve** row count; phase may update |
| Issue #79 CLAIMSTAT | **Preserve** |
| Issue #84 Track B | **Deferred** until after #85 (D5) |
| Issue #84 Track A | **Allowed** in parallel |

---

## 10. Regression Testing Checklist (for Validation Agent)

- [ ] Fleet: **0** duplicate `MPOLICY`+`MPHASE` in `quikclms`
- [ ] Header count ≈ **5,447** (or documented audit delta = 177 drops)
- [ ] `quikclmp` still **6,151** rows; no invent/delete
- [ ] Trace `010914301C`: 1 header, MPAID 50039.96, MFACE 25000
- [ ] Trace `011156098C`: 1 header, MPAID 45000
- [ ] Trace `011054606C`: distinct PS claimnums on distinct phases
- [ ] Trace `010150740C` unchanged
- [ ] CLAIMSTAT distribution still post-#79 (2≈1290 / 99≈4334 / 1=0 / 3=0) on survivors
- [ ] Audit CSVs in `Reports/`: merge drops + rephase + payee exceptions
- [ ] No quikmstr/quikridr/rates changes
- [ ] On PASS: `Test_Validation/quikclms.csv` (+ `quikclmp.csv` if phases updated)

---

## 11. Recommended Development Agent Task

1. Implement hybrid post-emit structure fix per approved D1–D4.  
2. Merge same-CLAIMNUM duplicates (D2 sum/date/face rules); drop losers with audit.  
3. Re-phase distinct CLAIMNUMs to unique phases within policy (book-like 0/2/3/…).  
4. Update `quikclmp.MPHASE` so payees follow claims (D4); exception-flag unmatched.  
5. Do **not** change CLAIMSTAT; do **not** invent/delete payees; do **not** fill #84 components.  
6. Write `QLA_Migration/Reports/issue85_*_audit.csv` files.  
7. Version bump both `app.py` copies (next after current claims version).  
8. Validator covering §10; on PASS publish modified tables to `Output/Test_Validation/`.

---

## Appendix

| Item | Path |
|------|------|
| Decisions (approved) | `Issue_85_Decisions_For_Review.md` |
| Scope | `Issue_85_Scope_Decisions.md` |
| Summary evidence | `evidence/issue85_risk_summary.csv` |
| Related | #78, #79, #84 |

**G3 Risk:** **PASS — Conditional Go**  
**Next:** User says **Approved for Development** (Composer 2.5).
