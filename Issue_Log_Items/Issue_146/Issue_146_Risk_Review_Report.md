# Issue #146 — Risk Review Report

**Issue:** #146 — Non-VB Unit Reductions (PC / former-vanish 0561 exclude)  
**Framework stage:** Risk Agent  
**Status:** **GO — Ready for Development** (after user approval)  
**Fallback simulated:** allowlist-20 vs all-PC vs all leftover non-VB vs QuikIsrr-only  
**Generated:** 2026-08-26  
**Agent/script:** Cursor Grok 4.5 · read-only `_research_issue146_allowlist.py`

**Status note:** Risk analysis only — no production code changes unless later approved.

---

## Go / No-Go Recommendation

**GO** — Exclude the locked 20-policy allowlist from the #34 0561 emit and strip the already-written rows from current Output. On the 6/30 leftover package that removes **104** QuikIsrr rows ($32,321.25) and the matching **104** companions on each of `quikclms` / `quikclmp` / `quikbenh` type 8. Leftover QuikIsrr becomes **101** rows / **30** policies, including #145B keep golds.

**Conditions:**

1. Allowlist only (19 PC + 9010808831). Do **not** filter on `BILLING_REASON=PC`.  
2. Do **not** strip 9010761639C / 9010760840C (#145B leftover golds).  
3. Do **not** delete LifePRO PACTG.  
4. Do **not** rewrite `quikridr.MUNIT`.  
5. Do **not** set `quikspec.VANISH` on PC.  
6. Strip companions with QuikIsrr. Keep `quikbenh` types 10/11/12 (#54).  
7. Do not blindly re-run PR-7 emit against already-loaded Output (clms/clmp **append**).  
8. #145B smoke must still PASS after this change.

**Closed #145B / #34 notice:** this is a Warren-authorized **allowlist exclusion** on the leftover book #145B deferred. It does not put VB 0561s back and it does not drop the $271 / $716.40 golds.

---

## 1. Current vs Proposed Mapping

| Field | Current | Proposed | Change? |
|-------|---------|----------|---------|
| QuikIsrr (allowlist 0561) | Emitted (#34 leftover) | Not emitted / stripped | **Yes** |
| quikclms PS- (allowlist) | Appended by PR-7 | Not emitted / stripped | **Yes** |
| quikclmp phase 0 (allowlist) | Appended by PR-7 | Not emitted / stripped | **Yes** |
| quikbenh type 8 (allowlist) | Replaced by PR-7 | Not emitted / stripped | **Yes** |
| Same four tables, other leftover | Emitted | Unchanged | **No** |
| quikspec.VANISH | F on these 20 | Unchanged | **No** |

---

## 2. Premium / Related Fields Untouched

| Target | Source | Touched? |
|--------|--------|----------|
| quikridr.MPREM | #26 / #88 / #137 | **No** |
| quikmstr.MMODPREM | PPOLC.MODE_PREMIUM | **No** |
| quikridr.MUNIT | LifePRO / #143 | **No** |
| MPOLICY padding | #25 / #2 | **No** |
| quikspec.VANISH / RESSTATE / RESRVCAT / SOR_POL | #145 / #132 / #141 / #156 | **No** |
| quikbenh 10/11/12 | #54 | **No** |

---

## 3. Repo References

| Location | Role |
|----------|------|
| `qla_core/quikisrr_loader.py` | Add allowlist skip after `filter_vb_events` |
| `qla_core/issue145b_vb_isrr.py` | Pattern only — do not widen VB |
| `Issue_Log_Items/Issue_34/tools/quikisrr_pr7_emit.py` | Fail if allowlist events still candidates |
| `tools/validators/validate_issue145b_vb_isrr_exclude.py` | Must still PASS |
| `Issue_Log_Items/Issue_146/evidence/issue146_research_summary.json` | This count |

---

## 4. Population Analysis

| Metric | Count |
|--------|------:|
| QuikIsrr leftover now | 205 |
| Rows that would be removed | 104 |
| Rows unchanged | 101 |
| Allowlist policies | 20 (all have ISRR; 0 missing) |
| Companion rows removed (each table) | 104 |
| Amounts on allowlist matching annual premium | 104 / 104 |

### Breakdown

| Dimension | rows | would_change |
|-----------|-----:|-------------:|
| QuikIsrr allowlist | 104 | 104 |
| QuikIsrr keep golds | 3 | 0 |
| QuikIsrr other leftover | 98 | 0 |
| clms PS- / clmp phase0 / benh-8 allowlist | 104 each | 104 each |

### Count reconciliation (Luna item)

| Book | Policies | Rows |
|------|---------:|-----:|
| 145B analysis non-VB unreversed 0561s | 52 | 209 |
| Current leftover Output after #145B | 50 | 205 |
| Gap | 2 | 4 |
| This #146 allowlist | 20 | 104 |
| Leftover after #146 | 30 | 101 |

The 2-policy / 4-row gap is #34 eligibility (never in leftover Output). Do not chase those as #146 removes.

---

## 5. Fallback Recommendation

| Option | Rows changed | Assessment |
|--------|-------------:|------------|
| A. Allowlist-20 on all four #34 tables | 104 × 4 | **Recommended** |
| B. QuikIsrr only | 104 | Reject — Claims / UL still show fake surrenders |
| C. All leftover non-VB (50 policies) | 205 | Reject — drops real surrenders including $271 / $716.40 |
| D. All `BILLING_REASON=PC` | unknown / 169 policies | Reject — most PC have no 0561 unit-cut fingerprint |
| E. Amount = annual premium only, any policy | wider | Reject — Warren locked the 20 keys |

**Recommended fallback:** Option A. If a later batch uses a different extract, drop the same 20 keys when they appear; do not invent new members without Warren.

---

## 6. Trace Policies

| Policy | Before QuikIsrr | Proposed | MUNIT now | Pass? |
|--------|----------------:|----------|-----------|-------|
| 9011077629C | 8 / $2,208.80 | 0 | 5.00000 | Yes |
| 9010817956C | 7 / $1,040.90 | 0 | 5.00000 | Yes |
| 9010808831C | 8 / $1,106.00 | 0 | 25.00000 | Yes |
| 9010761639C | 1 / $271.00 | 1 / $271.00 | 25.00000 | Yes — keep |
| 9010760840C | 2 / $716.40 | 2 / $716.40 | 35.00000 | Yes — keep |

---

## 7. Top Changes (by 0561 dollars removed)

Anniversary unit recovery (face − Σ0561 / 1000):

| Policy | Σ 0561 | Live QLA if history stays | After exclude |
|--------|-------:|--------------------------:|--------------:|
| 9010943849C | 3,995.95 | 15 − 3.996 = 11.004 | 15 |
| 9010787639C | 3,836.00 | 20 − 3.836 = 16.164 | 20 |
| 9010777059C | 3,514.00 | 25 − 3.514 = 21.486 | 25 |
| 9010811998C | 2,740.00 | 20 − 2.740 = 17.260 | 20 |
| 9011048543C | 2,669.80 | 15 − 2.670 = 12.330 | 15 |
| 9011077629C | 2,208.80 | 5 − 2.209 = **2.791** | **5** |
| 9010808831C | 1,106.00 | 25 − 1.106 = **23.894** | **25** |

Fleet dollars removed: **$32,321.25**.

---

## 8. Material Calculation Impact

**Intentional.** We are not changing converted units. We are removing history that QLAdmin treats as a face cut. Residual leftover (30 policies / 101 rows) can still drop units after anniversary — that stays #146-out / later review, not this change.

---

## 9. Prior Fix Preservation

| Check | Result |
|-------|--------|
| Issue #25 MPOLICY padding | Preserved — no key rewrite |
| Issue #26 MPREM / MMODPREM | Preserved — not in this emit |
| Issue #34 0561 source (non-allowlist) | Preserved — 101 leftover stay |
| Issue #54 quikbenh loans | Preserved — type 8 allowlist only |
| Issue #145 VANISH | Preserved — PC stays F |
| Issue #145B VB exclude | Preserved — VB golds stay 0; keep golds stay |
| Issue #156 SOR_POL | Preserved — quikspec schema untouched |

---

## 10. Regression Testing Checklist (for Validation Agent)

- [ ] 9011077629C / 9010817956C / 9010808831C have **0** QuikIsrr rows  
- [ ] Same three have **0** PS- clms / phase-0 clmp / type-8 benh  
- [ ] 9010761639C still 1 QuikIsrr ($271); 9010760840C still 2 ($716.40)  
- [ ] QuikIsrr leftover = 101 rows / 30 policies on 6/30  
- [ ] Gold `quikridr.MUNIT` unchanged (5 / 5 / 25)  
- [ ] #145B smoke still PASS (VB golds 0; VANISH T on VB golds; loan floors)  
- [ ] `quikbenh` types 10/11/12 row count unchanged  
- [ ] #25 / #26 sample keys unchanged  

---

## 11. Recommended Development Agent Task

1. Add `qla_core/issue146_pc_isrr.py` with the locked 20 keys and `is_issue146_policy` / `filter_issue146_events`.  
2. After `filter_vb_events` in `qla_core/quikisrr_loader.py`, drop allowlist events.  
3. Strip current Output allowlist rows on QuikIsrr + PS- clms + phase-0 clmp + type-8 benh. Do not re-run PR-7 append.  
4. Fail-closed validator `QLA_Migration/_validate_issue146_pc_isrr.py` (or `tools/validators/…`) + `SMOKE_JOBS` + accountability.  
5. Bump **both** `APP_VERSION`.  
6. Do **not** change `quikridr`, `quikmstr`, `quikspec`, PACTG, keep-gold rows, or the VB filter.

---

## Appendix

- Research JSON: `Issue_Log_Items/Issue_146/evidence/issue146_research_summary.json`  
- 19-policy source: `Issue_Log_Items/Eric_QuikValf_VPU_Writeup_20260823.md`  
- 9010808831: `Issue_146_Exception_9010808831.md`  
