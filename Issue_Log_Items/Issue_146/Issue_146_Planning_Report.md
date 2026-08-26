# Issue #146 — Planning Report

**Issue:** #146 — Non-VB Unit Reductions (PC / former-vanish 0561 exclude)  
**Framework stage:** Planning Agent  
**Status:** Planning  
**Generated:** 2026-08-26  
**Agent/script:** Cursor Grok 4.5 · read-only `_research_issue146_allowlist.py` (no production code)

---

## 1. Executive Finding

#145B already pulled 0561s off current VB policies. Twenty leftover policies still carry anniversary 0561s that equal the annual premium. LifePRO units never dropped. QLAdmin anniversary treats those dollars as surrenders.

**Direction:** reuse the #145B four-table exclude, scoped to a locked allowlist (19 PC + 9010808831). Keep 9010761639C and 9010760840C. Do not set VANISH. Do not strip the rest of the 50 non-VB leftover book. Ready for Dependency Gate.

Current 6/30 Output: remove **104** QuikIsrr rows ($32,321.25) and the matching 104 companions on each of clms / clmp / type-8 benh. Leftover QuikIsrr becomes **101** rows / **30** policies.

---

## 2. Confirmed LifePRO Source Table/File(s)

| Source table | File pattern | In Source/ package? | Row count |
|--------------|--------------|---------------------|----------:|
| PPOLC | `PPOLC_PolicyMaster_Extract*.csv` | Yes — 20260630 | 19 of 20 allowlist = PC; 9010808831 blank |
| PACTG | `PACTG_Accounting_Extract*.csv` | Yes | Unreversed 0561s already in leftover Output |

### Available source fields

| Field | Column / source | Populated % | Notes |
|-------|-----------------|------------:|-------|
| Allowlist identity | Locked policy keys (not BILLING_REASON alone) | 20 / 20 | PC is evidence, not the emit key |
| Event | PACTG.DEBIT_CODE 561/0561 | 100% of this emit | #34 candidate rule unchanged for non-allowlist |
| Reversal | PACTG.REVERSAL_CODE | Y already dropped | Do not reopen |
| Amount | PACTG.TRANS_AMOUNT | 100% | Fingerprint = annual premium; do not recompute |
| Policy key | POLICY_NUMBER | 100% | Existing `#2` / `#25` `format_qladmin_mpolicy` |

Do **not** treat `BILLING_REASON=PC` as a fleet exclude (169 PC policies on 6/30; only 19 are on this list).

---

## 3. Confirmed QLAdmin Target Structure

| Table | Field | Type | Length | Source (Help / schema) |
|-------|-------|------|--------|------------------------|
| QuikIsrr | MPOLICY / MSURRDATE / MSURRAMT | C / D / N | #34 | Help §7.143 |
| quikclms | CLAIMNUM / CAUSE / MPHASE | — | — | PR-7 PS- / SRR / phase 0 |
| quikclmp | MPHASE | — | — | PR-7 phase 0 companions |
| quikbenh | MBENTYP / MBEN | — | — | Type **8** only (ISRR). Types 10/11/12 are #54 loans. |

**Repo references** (population paths only):

| Location | Role |
|----------|------|
| `qla_core/quikisrr_loader.py` `filter_vb_events` | Existing #145B skip — **add allowlist skip after this** |
| `qla_core/issue145b_vb_isrr.py` | Pattern to copy for a small #146 helper |
| `Issue_Log_Items/Issue_34/tools/quikisrr_pr7_emit.py` | Fail if allowlist events still candidates |
| `Issue_Log_Items/Issue_145B/tools/apply_issue145b_vb_isrr_exclude.py` | Pattern for current-Output strip |
| `tools/validators/validate_issue145b_vb_isrr_exclude.py` | Must still PASS after #146 (keep golds) |

---

## 4. Required Source-to-Target Field Mapping

| LifePRO source | LifePRO field | QLAdmin target | Transformation | Change? |
|----------------|---------------|----------------|----------------|---------|
| Locked allowlist | 20 policy keys | (filter) | Drop all #34 0561 events for those policies | **Yes** |
| PACTG | 0561 unreversed, not allowlist | QuikIsrr + companions | Existing #34 + #145B | **No** |
| PACTG | 0561 on allowlist | (none) | Do not emit; strip if already written | **Yes** |
| PACTG extract | all rows | LifePRO file | Never delete source | **No** |

### Fields that must remain unchanged

| Target | Current source | Touch this issue? |
|--------|----------------|-------------------|
| quikmstr.MMODPREM | PPOLC.MODE_PREMIUM | **No** |
| quikridr.MPREM | #26 / #88 / #137 | **No** |
| quikridr.MUNIT | LifePRO units / #143 | **No** |
| MPOLICY padding | format_qladmin_mpolicy | **No** |
| quikspec.VANISH / VANISHDT / RESSTATE / RESRVCAT / SOR_POL | #145 / #132 / #141 / #156 | **No** |
| QuikIsrr non-allowlist leftover | #34 / #145B | **No** — keep golds $271 / $716.40 |
| quikbenh MBENTYP 10/11/12 | #54 | **No** |

---

## 5. Open Client Questions

None that block Planning. Locked 08/26:

1. Allowlist is the 19 PC unit-cut policies plus 9010808831.  
2. Keep 9010761639 and 9010760840.  
3. Do not set VANISH on PC.  
4. Do not generalize to all PC or all non-VB 0561s.

---

## 6. Recommended Formatting Rules

| Rule | Recommendation |
|------|----------------|
| Policy key | Existing `format_qladmin_mpolicy()` only. Match allowlist on digit / C keys. |
| Dates | Unchanged on leftover rows |
| Money | Unchanged on leftover rows |
| Blanks / zeros | An allowlist policy may have **zero** QuikIsrr rows after. That is success. |
| Identity | Hard allowlist, not `BILLING_REASON=PC` |

---

## 7. Memo / Text / Special Handling

PR-7 `MEMOTEXT` on PS- claim rows is generated from the same 0561 events. Those allowlist rows come out with the claim companions. No memo concatenation change.

---

## 8. Policy Number Key Handling

1. LifePRO `POLICY_NUMBER` → existing `#2` / `#25` formatter.  
2. Allowlist test: policy in the locked 20 keys (with/without C).  
3. Unknown / not on list: **keep** the 0561.

---

## 9. Estimated Record Counts

Current 6/30 leftover Output after #145B (`issue146_research_summary.json`):

| Metric | Count | Basis |
|--------|------:|-------|
| QuikIsrr leftover now | 205 / 50 policies | After #145B |
| Allowlist policies | 20 | All present in QuikIsrr |
| QuikIsrr rows to remove | 104 | $32,321.25 |
| Companion rows to remove (each of clms / clmp / benh-8) | 104 | 1:1 with QuikIsrr |
| QuikIsrr rows to keep | 101 | 30 policies, including keep golds |
| Keep golds | 1 + 2 rows | $271 and $716.40 |
| Source non-VB 0561 policies (145B analysis) | 52 / 209 rows | 2 policies / 4 rows never made leftover Output (#34 eligibility) |

Gold after: 9011077629C / 9010817956C / 9010808831C QuikIsrr = **0**. `MUNIT` stays 5 / 5 / 25.

---

## 10. Sample Trace (5 policies)

| Policy (QLA) | Before QuikIsrr | After (proposed) | Status |
|--------------|----------------:|------------------|--------|
| 9011077629C | 8 / $2,208.80 | 0 | Allowlist — remove |
| 9010817956C | 7 / $1,040.90 | 0 | Allowlist — remove |
| 9010808831C | 8 / $1,106.00 | 0 | Approved blank — remove |
| 9010761639C | 1 / $271.00 | 1 / $271.00 | Keep — real surrender |
| 9010760840C | 2 / $716.40 | 2 / $716.40 | Keep — real surrender |

Expected live QLAdmin units after anniversary once history is gone: 5 / 5 / 25 on the three remove golds (vs 2.791 / ~3.959 / 23.894 with current history).

---

## 11. Risks and Unknowns

| Risk | Severity | Mitigation |
|------|----------|------------|
| Using `BILLING_REASON=PC` as the filter | High | Hard allowlist of 20 keys only |
| Re-running PR-7 emit appends clms/clmp | High | Filter in loader + strip current rows. Do not blindly re-emit on loaded Output |
| Strip `quikbenh` wholesale | High | Remove type **8** on allowlist only. Keep #54 types 10/11/12 |
| Closed #145B leftover floor 205 / 50 in old Risk checklist | Medium | #145B validator does **not** hardcode 205; it requires the two keep golds. Update #146 smoke separately |
| True surrender hiding on an allowlist policy | Low | Fingerprint is 104/104 amounts = annual premium. Warren locked the list |

---

## 12. Dependency Gate Preview

| Check | Met? |
|-------|------|
| Source file present | Yes — PPOLC + current leftover Output |
| Field definitions confirmed | Yes — same four #34 tables as #145B |
| Client scope clear | Yes — 20-policy allowlist; keep golds named |
| Example policies available | Yes — 9011077629 / 9010808831 / keep pair |

---

## 13. Recommended Risk Agent Prompt

Quantify 104-row / $32,321.25 remove vs 101-row leftover. Simulate allowlist-only vs all-PC vs all-non-VB. Confirm #145B keep golds and loan benh floors stay.

---

## 14. Recommended Development Task (do not implement)

1. Add a small helper (allowlist keys + `is_issue146_policy`) next to `issue145b_vb_isrr.py`.  
2. After `filter_vb_events` in `quikisrr_loader.py`, drop allowlist events.  
3. Strip current Output allowlist rows on QuikIsrr + PS- clms + phase-0 clmp + type-8 benh (mirror 145B apply; do not re-run PR-7 append).  
4. Fail-closed validator + `SMOKE_JOBS`.  
5. Bump both `APP_VERSION`.  
6. Do not change `quikridr`, `quikmstr`, `quikspec`, PACTG, or keep-gold rows.

### Locked allowlist (20)

9010758550, 9010765198, 9010770062, 9010771070, 9010773468, 9010776813, 9010777059, 9010787639, 9010788679, 9010810228, 9010811998, 9010816969, 9010817956, 9010821435, 9010826551, 9010849882, 9010943849, 9011048543, 9011077629, **9010808831**.

### Locked keep (2)

9010761639, 9010760840.
