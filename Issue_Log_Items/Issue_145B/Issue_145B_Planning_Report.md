# Issue #145B — Planning Report

**Issue:** #145B — Vanish 0561s Out of ISRR  
**Framework stage:** Planning Agent  
**Status:** Planning  
**Generated:** 2026-08-23  
**Agent/script:** Cursor Grok 4.5 · read-only join of `quikspec.VANISH` to Output QuikIsrr / claims companions (no production code)

---

## 1. Executive Finding

#145 already flags 636 VB policies `VANISH=T`. Conversion Output still holds LifePRO units. QLAdmin anniversary then subtracts QuikIsrr 0561 dollars / $1,000 and cuts face. Those 0561s are vanish premium, not surrenders.

The #34 emit writes the same event to **four** tables. On current Output the VB book is a 1:1 match: **3,452** QuikIsrr rows, **3,452** `quikclms` PS- rows, **3,452** `quikclmp` phase-0 rows, and **3,452** `quikbenh` type-8 rows. Pulling QuikIsrr only would leave fake partial-surrender history on the Claims / UL screens.

**Direction:** exclude VB at the #34 candidate load (`load_pactg_events` / `build_emit`), then strip those already-written rows from current Output. Non-VB 0561s stay (**205** rows / **50** policies). Ready for Dependency Gate.

---

## 2. Confirmed LifePRO Source Table/File(s)

| Source table | File pattern | In Source/ package? | Row count |
|--------------|--------------|---------------------|----------:|
| PPOLC | `PPOLC_PolicyMaster_Extract*.csv` | Yes (via `resolve_table_source` / current `quikspec`) | 636 VB |
| PACTG | `PACTG_Accounting_Extract*.csv` | Yes | 3,452 unreversed VB 0561s already in Output |

### Available source fields

| Field | Column / source | Populated % | Notes |
|-------|-----------------|------------:|-------|
| On vanish | PPOLC.BILLING_REASON | VB = 636 | Same lock as #145. Reuse `load_ppolc_billing_reason`. |
| Event | PACTG.DEBIT_CODE 561/0561 | 100% of this emit | #34 candidate rule unchanged for non-VB |
| Reversal | PACTG.REVERSAL_CODE | Y already dropped | Do not reopen |
| Amount | PACTG.TRANS_AMOUNT | 100% | Do not recompute |
| Policy key | POLICY_NUMBER | 100% | Existing `#2` / `#25` `format_qladmin_mpolicy` |

Reuse `qla_core/quikspec_vanish.py` `load_ppolc_billing_reason` — do not invent a second VB list.

---

## 3. Confirmed QLAdmin Target Structure

| Table | Field | Type | Length | Source (Help / schema) |
|-------|-------|------|--------|------------------------|
| QuikIsrr | MPOLICY | C | 10/11 | Help §7.143; #34 |
| QuikIsrr | MSURRDATE | D | 8 | Event date |
| QuikIsrr | MSURRAMT | N | 10.2 | Dollars anniversary subtracts |
| quikclms | CLAIMNUM / CAUSE / MPHASE | — | — | PR-7 PS- / SRR / phase 0 |
| quikclmp | MPHASE | — | — | PR-7 phase 0 companions |
| quikbenh | MBENTYP / MBEN | — | — | Type **8** only (ISRR). Types 10/11/12 are #54 loans. |

**Repo references** (population paths only):

| Location | Role |
|----------|------|
| `qla_core/quikisrr_loader.py` `load_pactg_events` | #34 0561 candidate filter — **add VB exclude here** |
| `qla_core/quikisrr_loader.py` `build_emit` | Builds isrr + clms + clmp + benh from the same events |
| `Issue_Log_Items/Issue_34/tools/quikisrr_pr7_emit.py` | Writes Output; **EXPECTED** floor 3657/637 must be restated |
| `app.py` `_execute_batch_quikisrr_finale` | Calls the emit at end of batch |
| `qla_core/quikspec_vanish.py` | Authoritative VB set |

---

## 4. Required Source-to-Target Field Mapping

| LifePRO source | LifePRO field | QLAdmin target | Transformation | Change? |
|----------------|---------------|----------------|----------------|---------|
| PPOLC | BILLING_REASON = VB | (filter) | Drop all #34 0561 events for that policy | **Yes** |
| PACTG | 0561 unreversed, non-VB | QuikIsrr + companions | Existing #34 emit | **No** |
| PACTG | 0561 on VB | (none) | Do not emit; strip if already written | **Yes** |
| PACTG extract | all rows | LifePRO file | Never delete source | **No** |

### Fields that must remain unchanged

| Target | Current source | Touch this issue? |
|--------|----------------|-------------------|
| quikmstr.MMODPREM | PPOLC.MODE_PREMIUM | **No** |
| quikridr.MPREM | #26 / #88 / #137 | **No** |
| quikridr.MUNIT | LifePRO units / #143 RPU | **No** — we stop anniversary from changing live units |
| MPOLICY padding | format_qladmin_mpolicy (#25 / #2) | **No** |
| quikspec.VANISH / VANISHDT / RESSTATE / RESRVCAT | #145 / #132 / #141 | **No** |
| QuikIsrr non-VB rows | #34 | **No** |
| quikbenh MBENTYP 10/11/12 | #54 | **No** |
| #146 examples | 0561 still emit | **No** |

---

## 5. Open Client Questions

None that block Planning. Locked at Discovery / 08/23:

1. **All** 0561s on a VB policy come out, including the ~128 that do not match today’s billed premium.  
2. Scope is VB only. #146 stays.  
3. Warren is implementing without waiting on the unused A/B anniversary package.

---

## 6. Recommended Formatting Rules

| Rule | Recommendation |
|------|----------------|
| Policy key | Existing `format_qladmin_mpolicy()` only. Join VB on digit key / lookup keys from `load_ppolc_billing_reason`. |
| Dates | Unchanged on leftover rows |
| Money | Unchanged on leftover rows |
| Blanks / zeros | A VB policy may have **zero** QuikIsrr rows. That is success, not a defect. |
| Emit floor | Update `EXPECTED` in `quikisrr_pr7_emit.py` to leftover book (205 / 50 / 75,119.87 on 6/30). Do not keep 3657. |

---

## 7. Memo / Text / Special Handling

PR-7 `MEMOTEXT` on PS- claim rows is generated from the same 0561 events. Those VB rows come out with the claim companions. No memo concatenation change.

---

## 8. Policy Number Key Handling

1. LifePRO `POLICY_NUMBER` → existing `#2` / `#25` formatter.  
2. VB test: `load_ppolc_billing_reason(src_dir)` value `== "VB"`.  
3. Orphan / unknown billing reason: **keep** the 0561 (not vanish).

---

## 9. Estimated Record Counts

Current 6/30 Output (`quikspec.VANISH=T` join):

| Metric | Count | Basis |
|--------|------:|-------|
| VB policies | 636 | #145 already in Output |
| VB with QuikIsrr | 587 | 49 VB have no 0561 |
| QuikIsrr rows to remove | 3,452 | $1,157,482.66 |
| Companion rows to remove (each of clms / clmp / benh-8) | 3,452 | 1:1 with QuikIsrr |
| QuikIsrr rows to keep | 205 | 50 non-VB policies, $75,119.87 |
| Gold VB QuikIsrr after | 0 | 9010815236C / 9011050114C / 9011069610C |

`quikridr.MUNIT` on the golds is already 25 / 25 / 50. Do not rewrite units.

---

## 10. Sample Trace (5 policies)

| Policy (QLA) | Before QuikIsrr | After (proposed) | Status |
|--------------|----------------:|------------------|--------|
| 9010815236C | 8 / $1,402.56 | 0 | VB — remove |
| 9011050114C | 1 / $136.00 | 0 | VB — remove |
| 9011069610C | 1 / $406.00 | 0 | VB — remove |
| 9010761639C | 1 / $271.00 | 1 / $271.00 | #146 — keep |
| 9010760840C | 2 / $716.40 | 2 / $716.40 | #146 — keep |

Expected live QLAdmin units **after** anniversary once history is gone: 25 / 25 / 50 on the three VB golds (vs 23.597 / 24.864 / 49.594 with current history).

---

## 11. Risks and Unknowns

| Risk | Severity | Mitigation |
|------|----------|------------|
| Re-running PR-7 emit **appends** clms/clmp and would duplicate leftover 205 | High | Do not blindly re-emit on already-loaded Output. Filter in loader + strip current VB rows. Fresh batch is safe because emit runs once. |
| #34 EXPECTED floor still 3657 → emit FAIL | High | Restate EXPECTED to leftover book in the same change. |
| Strip `quikbenh` wholesale | High | Remove type **8** on VB only. Keep #54 types 10/11/12. |
| A/B anniversary never run | Medium | Formula already matches live listing; Warren waived wait. |
| True surrender hiding on a VB policy | Low | Warren locked “completely.” Residual is #146, not a second vanish rule. |

---

## 12. Dependency Gate Preview

| Check | Met? |
|-------|------|
| Source file present | Yes — PPOLC + PACTG + current Output |
| Field definitions confirmed | Yes — QuikIsrr §7.143; companions are the same #34 events |
| Client scope clear | Yes — VB only; all 0561s on those policies |
| Example policies available | Yes — three VB golds + two #146 negatives |

---

## 13. Recommended Risk Agent Prompt

```
Risk Agent — Issue 145B: Vanish 0561s Out of ISRR

Read-only before/after on QLA_Migration/Output/. Do not change app.py or emit.

Quantify: QuikIsrr / quikclms PS- / quikclmp phase-0 / quikbenh type-8 rows
removed vs kept. Join VB from quikspec.VANISH=T.

Traces: 9010815236C, 9011050114C, 9011069610C must go to 0.
Negatives: 9010761639C, 9010760840C must stay.

Preserve #25 padding, #26 MPREM, #145 VANISH, #54 loan benh, #146 leftovers.
```

---

## 14. Recommended Development Task (Do Not Implement)

1. In `qla_core/quikisrr_loader.py`, after an event is #34-eligible, skip it when PPOLC billing reason is **VB** (reuse `load_ppolc_billing_reason`).  
2. Update `EXPECTED` in `quikisrr_pr7_emit.py` to the leftover non-VB book.  
3. Strip current Output: drop VB rows from `QuikIsrr.csv`, matching PS- / phase-0 clms+clmp, and `quikbenh` type 8 only.  
4. Version bump **both** `app.py` and `QLA_Migration/app.py` (v59.00 → v59.01).  
5. Validator: golds 0 QuikIsrr; #146 still present; VANISH T still 636; MUNIT unchanged on golds; leftover QuikIsrr count 205 on 6/30.  
6. Do **not** change `quikridr.MUNIT`, `quikspec`, or PACTG.

---

## Appendix

- Prior analysis: `Issue_145B_Analysis_Report.md`  
- Related: #145, #34, #146, #54  
- Help: QLAdmin §7.143 QuikIsrr  
