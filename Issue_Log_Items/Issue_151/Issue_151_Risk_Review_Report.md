# Issue #151 — Risk Review Report

**Issue:** #151 — Val X Modal Prem Outlier (9010969231C former-vanish 0561 leftover)  
**Framework stage:** Risk Agent  
**Status:** **GO — Ready for Development** (after **separate** user Development approval)  
**Fallback simulated:** allowlist+1 vs all-PC vs all leftover 0561 vs premium remap vs QuikIsrr-only  
**Generated:** 2026-09-22  
**Agent/script:** Cursor Grok 4.6 (Warren stage-model override 2026-09-22; Grok 4.5 unavailable) · read-only Output / Source / `docs/Valuation/QuikValf.dbf`

**Status note:** Risk analysis only — no production code changes unless later approved. Development still requires a separate user “Approved for Development” (or equivalent).

---

## Go / No-Go Recommendation

**GO** — Add `9010969231` to the existing Closed #146 allowlist (20 → 21) and strip the already-written eight 0561 events from current Output. On the 20260831 leftover package that removes **8** QuikIsrr rows ($1,504.80) and the matching **8** companions on each of `quikclms` / `quikclmp` / `quikbenh` type 8. Leftover QuikIsrr becomes **102** rows / **30** policies, including #146 keep golds. Conversion premium and rider fields stay put.

**Conditions:**

1. One new hard key only. Do **not** filter on `BILLING_REASON=PC` (171 PC policies).  
2. Do **not** strip 9010761639C / 9010760840C.  
3. Do **not** delete LifePRO PACTG.  
4. Do **not** rewrite `quikridr.MUNIT` / `MPREM` / `MCV0` (5.00000 / 37.62 / -812.49000).  
5. Do **not** change `quikmstr.MMODEPREM` **163.10** (Closed **#139**).  
6. Do **not** set `quikspec.VANISH`.  
7. Strip companions with QuikIsrr. Keep `quikbenh` types 10/11/12 (#54).  
8. Do not blindly re-run PR-7 emit against already-loaded Output (clms/clmp **append**).  
9. #145B and #146 smokes must still PASS.  
10. Closure of #151 requires a **named fail-closed always-on smoke** for 9010969231C, plus an honest #146 guide update 20→21 citing Warren **2026-09-22**. Extending the #146 validator is necessary and not sufficient by itself.  
11. Do **not** claim the current 2026-06-30 QuikValf as a passed fresh valuation. That run is a UAT criterion after the conversion exclude.

**Closed #146 notice:** this is a Warren-authorized **allowlist expansion**, not a silent override. Pre-Development did not edit #146 Closed files.

---

## 1. Current vs Proposed Mapping

| Field | Current | Proposed | Change? |
|-------|---------|----------|---------|
| QuikIsrr (9010969231C 0561) | 8 × $188.10 emitted | Not emitted / stripped | **Yes** |
| quikclms PS- (same policy) | 8 PS-…-001..008 / SRR / phase 0 | Not emitted / stripped | **Yes** |
| quikclmp phase 0 (same) | 8 × $188.10 | Not emitted / stripped | **Yes** |
| quikbenh type 8 (same) | 8 × $188.10 (20180221–20250221) | Not emitted / stripped | **Yes** |
| Same four tables, other leftover | 110 − 8 = 102 QuikIsrr | Unchanged | **No** |
| quikmstr.MMODEPREM | 163.10 | 163.10 | **No** |
| quikridr phase 1 | MUNIT 5.00000; MPREM 37.62; MCV0 -812.49000 | Unchanged | **No** |
| quikspec.VANISH | F | Unchanged | **No** |

---

## 2. Premium / Related Fields Untouched

| Target | Source | Touched? |
|--------|--------|----------|
| quikridr.MPREM | 37.62 | **No** |
| quikridr.MUNIT | 5.00000 | **No** |
| quikridr.MCV0 | -812.49000 | **No** |
| quikridr.MANNLFEE | 0.0000 (#139) | **No** |
| quikmstr.MMODPREM / MMODEPREM | 163.10 after #139 | **No** |
| MPOLICY padding | #25 / #2 | **No** |
| quikspec.VANISH / RESRVCAT / SOR_POL | #145 / #141 / #156 | **No** |
| quikbenh 10/11/12 | #54 | **No** |

---

## 3. Repo References

| Location | Role |
|----------|------|
| `qla_core/issue146_pc_isrr.py` | Add `9010969231` to `ALLOWLIST_SOURCE` |
| `qla_core/quikisrr_loader.py` | Existing `filter_issue146_events` after VB filter — no new logic expected |
| `Issue_Log_Items/Issue_146/tools/apply_issue146_pc_isrr_exclude.py` | Strip current Output after the key is added |
| `Issue_Log_Items/Issue_34/tools/quikisrr_pr7_emit.py` | Already fails on allowlist leak |
| `tools/validators/validate_issue146_pc_isrr.py` | Auto-covers new key via `ALLOWLIST_SOURCE`; update “20” comments |
| `tools/validators/validate_release_closed_issues.py` | Add a **named #151** `SMOKE_JOBS` entry at Closure |
| `Issue_Log_Items/Issue_145B/evidence/issue145b_vpunit_listing_join.csv` | Row 134: `146_OTHER`, 8 events, 3.4952 counterfactual |
| `docs/Valuation/QuikValf.dbf` | Before-state valuation only (2026-06-30) |

---

## 4. Population Analysis

| Metric | Count |
|--------|------:|
| QuikIsrr leftover now | 110 / 31 policies |
| Rows that would be removed | 8 |
| Rows unchanged | 102 |
| Policies in scope | 1 |
| Companion rows removed (each of clms / clmp / benh-8) | 8 |
| Amounts matching annual premium | 8 / 8 |
| Current #146 allowlist still in leftover | 0 |
| PPOLC PC policies (8/31) | 171 |

### Breakdown

| Dimension | rows | would_change |
|-----------|-----:|-------------:|
| QuikIsrr 9010969231C | 8 | 8 |
| QuikIsrr keep golds | 3 | 0 |
| QuikIsrr other leftover | 99 | 0 |
| clms PS- / clmp phase0 / benh-8 this policy | 8 each | 8 each |
| This policy other benh types | 0 | 0 |

### Valuation fingerprint (not a conversion field)

| Item | Value |
|------|------:|
| Load units | 5.00000 |
| Σ 0561 | 8 × 188.10 = 1,504.80 |
| `5.0000 − 1504.80/1000` | **3.4952** |
| QuikValf MUNIT | 3.4952 |
| QuikValf MEXTCODE | 4 (Extended Term) |
| QuikValf MPREM1 / MANNLZD | 2899.79 |
| QuikValf MVALDATE | 2026-06-30 |

### Natural controls (already on #146 allowlist)

| Policy | Load MUNIT / MCV0 | QuikValf MEXTCODE / MUNIT / MPREM1 |
|--------|-------------------|-----------------------------------|
| 9010817956C | 5.00000 / -496.10 | 1 / 5.0 / 148.70 |
| 9010943849C | 15.00000 / -1154.33 | 1 / 15.0 / 570.90 |

Both controls still have negative fund on the load and valued premium-paying at full units after their false 0561s were removed. That supports the same exclude; it is **not** a passed fresh valuation of 9010969231C.

---

## 5. Fallback Recommendation

| Option | Rows changed | Assessment |
|--------|-------------:|------------|
| A. Add 9010969231 to #146 allowlist; strip four tables | 8 × 4 | **Recommended** |
| B. QuikIsrr only | 8 | Reject — Claims / UL still show fake surrenders |
| C. All leftover 0561s (31 policies) | 110 | Reject — drops real surrenders including $271 / $716.40 |
| D. All `BILLING_REASON=PC` | 171 policies | Reject — most PC have no 0561 unit-cut fingerprint |
| E. Remap MMODEPREM to 188.10 or 2899.79 | 1 policy premium | Reject — undoes #139; $2,899.79 is not a load premium |
| F. Set VANISH=TRUE | 1 | Reject — #145 stays VB-only |

**Recommended fallback:** Option A. Do not invent further members without Warren.

---

## 6. Trace Policies

| Policy | Before QuikIsrr | Proposed | Load MUNIT / MMODEPREM | Pass? |
|--------|----------------:|----------|------------------------|-------|
| 9010969231C | 8 / $1,504.80 | 0 | 5.00000 / 163.10 stay | Yes — in scope |
| 9010817956C | 0 | 0 | 5.00000 / 123.70 | Yes — #146 control |
| 9010943849C | 0 | 0 | 15.00000 / 545.85 | Yes — #146 control |
| 9010761639C | 1 / $271.00 | 1 / $271.00 | 25.00000 | Yes — keep |
| 9010760840C | 2 / $716.40 | 2 / $716.40 | 35.00000 | Yes — keep |

---

## 7. Top Changes

Only one policy changes.

| Policy | Σ 0561 | Live QLA units if history stays | After exclude (conversion) |
|--------|-------:|--------------------------------:|---------------------------:|
| 9010969231C | 1,504.80 | 5 − 1.5048 = **3.4952** (matches current QuikValf) | Load units stay **5.00000**; history gone |

Fleet dollars removed: **$1,504.80**.

---

## 8. Material Calculation Impact

**Intentional on history only.** We are not changing converted units or billed premium. We are removing history that QLAdmin treats as a face cut, which is why valuation currently shows 3.4952 units and $2,899.79.

A later QLAdmin valuation is expected (UAT, not proven here) to restore units to 5.0000 and drop the $2,899.79 figure. Controls with the same negative-fund pattern valued MEXTCODE 1 at full units after #146. If a fresh valuation still shows Extended Term after the 0561s are gone, that is a **separate** valuation / negative-fund question — not a reason to put the 0561s back, and not a reason to change MMODEPREM.

---

## 9. Prior Fix Preservation

| Check | Result |
|-------|--------|
| Issue #25 MPOLICY padding | Preserved — no key rewrite |
| Issue #26 MPREM / MMODPREM | Preserved — rider MPREM 37.62 stays |
| Issue #34 0561 source (non-allowlist) | Preserved — 102 leftover stay |
| Issue #54 quikbenh loans | Preserved — type 8 this policy only |
| Issue #139 ISWL fee withhold | Preserved — MMODEPREM 163.10; MANNLFEE 0 |
| Issue #145 VANISH | Preserved — this policy stays F |
| Issue #145B VB exclude | Preserved — VB golds stay 0; keep golds stay |
| Issue #146 20-policy lock | **Authorized expansion** to 21 (Warren 2026-09-22); guide/docs must be updated at Development/Closure, not silently left at 20 |

---

## 10. Regression Testing Checklist (for Validation Agent)

- [ ] 9010969231C has **0** QuikIsrr rows  
- [ ] Same policy has **0** PS- clms / phase-0 clmp / type-8 benh  
- [ ] 9010969231C `quikridr` phase 1 still MUNIT **5.00000**, MPREM **37.62**, MCV0 **-812.49000**  
- [ ] 9010969231C `quikmstr.MMODEPREM` still **163.10**  
- [ ] 9010761639C still 1 QuikIsrr ($271); 9010760840C still 2 ($716.40)  
- [ ] 9010817956C / 9010943849C / 9011077629C / 9010808831C still 0 QuikIsrr  
- [ ] QuikIsrr leftover = **102** rows / **30** policies on this 8/31 Output  
- [ ] #145B smoke still PASS  
- [ ] #146 smoke still PASS (21 keys after the add)  
- [ ] Named **#151** fail-closed smoke PASS (required before Closure)  
- [ ] `quikbenh` types 10/11/12 row count unchanged  
- [ ] #25 / #26 sample keys unchanged  
- [ ] **UAT (not claimed here):** fresh QLAdmin valuation of 9010969231C — MUNIT 5.0000 and $2,899.79 gone; compare control pattern MEXTCODE 1 / ~$188.10 LifePRO annual. Current 2026-06-30 QuikValf is before-state only.

---

## 11. Recommended Development Agent Task

1. Add `"9010969231"` to `ALLOWLIST_SOURCE` in `qla_core/issue146_pc_isrr.py`. Change “20-policy” comments to 21 and document Warren **2026-09-22**.  
2. Do **not** add new loader logic unless a dry-run shows `filter_issue146_events` missed the key.  
3. Strip current Output with `Issue_Log_Items/Issue_146/tools/apply_issue146_pc_isrr_exclude.py`. Do not re-run PR-7 append.  
4. Update `validate_issue146_pc_isrr.py` 20→21 wording (loop already uses `ALLOWLIST_SOURCE`).  
5. Add `tools/validators/validate_issue151_pc_isrr.py` (or equivalent thin gold) and, at Closure, register `#151 9010969231 former-vanish 0561s out of ISRR` in `SMOKE_JOBS` and accountability. Reusing only the #146 smoke label does **not** satisfy Framework rule 14 for closing #151.  
6. Dual `APP_VERSION` bump from **v59.17**. No other `app.py` logic.  
7. Update Completed Issues guide: **new #151 row** + **#146 row 20→21** with Warren 2026-09-22 approval. Publish QuikIsrr / quikclms / quikclmp / quikbenh to `Test_Validation/`.  
8. Do **not** change `quikridr`, `quikmstr`, `quikspec`, PACTG, keep-gold rows, or the VB filter.  
9. Do **not** Close until issue validator PASS on full Output, accountability **IN_DATA**, named #151 smoke PASS, and a fresh QLAdmin valuation is either proven or explicitly waived by Warren.

### Rollback

Revert the single `ALLOWLIST_SOURCE` string (and version bump). Existing PACTG still holds the eight 561s, so a re-emit without the new key restores history. Do not wipe DBFs; APPEND-only remains.

---

## Appendix

- #145B join: `Issue_Log_Items/Issue_145B/evidence/issue145b_vpunit_listing_join.csv` (9010969231, bucket `146_OTHER`)  
- Closed #146 allowlist helper: `qla_core/issue146_pc_isrr.py`  
- Before-state valuation: `docs/Valuation/QuikValf.dbf` (MVALDATE 2026-06-30 — **not** a fresh PASS)  
- Approvals dated **2026-09-22:** (1) expand #146 allowlist 20→21 by adding 9010969231C; (2) Cursor Grok 4.6 stage-model override
