# Issue #134 — Planning Report

**Issue:** #134 — Death Benefit Notes  
**Framework stage:** Planning Agent  
**Status:** Planning complete → Dependency Gate  
**Generated:** 2026-08-01  
**Agent/script:** Cursor Grok 4.5 (locked); read-only PNOTE/`quikclms` counts  
**Code changes:** None  

---

## 1. Executive Finding

PNOTE **`FILE_TYPE=B`** (~4,149 rows / 1,504 policies) are death-benefit notes already wrongly emitted to **Policy Memo** (`quikmemo`). Client wants them on **Claims Tab Memo**, which for life claims is **`quikclms.MEMOTEXT`** (Help Claims Tab field 16; schema “Claim memo”). **`QuikHcmm` is Health Claim Memos only** — out of scope.

Plan: (1) exclude B from QUIKMEMO; (2) overlay formatted B note text onto matching death-claim `quikclms` rows, **replacing** lineage audit text in the UI field; (3) orphan-log B notes with no claim header. Safe to Dependency Gate / Risk.

---

## 2. Confirmed LifePRO Source Table/File(s)

| Source table | File pattern | In Source/ package? | Row count |
|--------------|--------------|---------------------|----------:|
| PNOTE Policy Notes | `PNOTE_PolicyNotes_Extract_*.csv` | Yes — `20260630` | 7,976 |

### Available source fields

| Field | Column / source | Populated % | Notes |
|-------|-----------------|------------:|-------|
| File type | `FILE_TYPE` | 100% | Filter **`B`** only for this issue |
| Policy | `POLICY_NUMBER` | ~100% | LifePRO numeric key |
| Date / name | `DATE_OR_NAMEID` | High | Reuse `_parse_pnote_date` |
| Time | `TIME_OR_UW_REQ_SEQ` | High | Reuse `_format_time_hhmmss` |
| Seq | `RECORD_SEQ` | High | Ordering / header |
| Benefit seq | `BENEFIT_SEQ` | Varies | Optional in header |
| Body | `LINE_1`–`LINE_4` | High | 13 B rows all-blank lines |

`FILE_TYPE` breakdown: B 4,149 · P 3,746 · R 75 · M 4 · H 2.

---

## 3. Confirmed QLAdmin Target Structure

| Table | Field | Type | Length | Source (Help / schema) |
|-------|-------|------|--------|------------------------|
| `QUIKCLMS` | `MEMOTEXT` | MEMO | 10 (pointer) | Help Claims Tab (16) Death claim memos; `docs/claims_conversion_reference/quikclms_quikclmp`; schema_manifest |
| `QUIKMEMO` | `MEMOTEXT` | MEMO | — | **Exclude B** only (non-B unchanged) |

**Not targets:** `QuikHcmm.MMEMO` (health); `quikclmp` (no memo column).

**Repo references** (population paths):

| Location | Role |
|----------|------|
| `qla_core/quikmemo_converter.py` | Emits all PNOTE → `quikmemo` (no FILE_TYPE filter) |
| `QLA_Migration/Configs/Sync_Rulebook_quikclms.csv` | `mlineage → MEMOTEXT` |
| `app.py` claims transform / Phase 10B path | Copies lineage into `MEMOTEXT` |
| `qla_core/quikisrr_loader.py` | Synthetic surrender memos on some claim rows — do not broadly rewrite |

---

## 4. Required Source-to-Target Field Mapping

| LifePRO source | LifePRO field | QLAdmin target | Transformation | Change? |
|----------------|---------------|----------------|----------------|---------|
| PNOTE | `FILE_TYPE=B` + LINE_* + date/time/seq | `quikclms.MEMOTEXT` | Format like `_format_pnote_memotext` (prefix `[PNOTE-B]` or `[PNOTE]`); multi-note join with `\n---\n`; **replace** lineage | **Yes** |
| PNOTE | `FILE_TYPE=B` | `quikmemo` | **Do not emit** | **Yes** (exclude) |
| PNOTE | `FILE_TYPE` ≠ B | `quikmemo` | Existing #21M/#50 path | **No** |
| Phase 10B | `mlineage` | `quikclms.MEMOTEXT` | Stop using as UI Claims Memo when B overlay applies; keep lineage in Reports/Validation | **Yes** |
| PENSE | ENS rows | `quikmemo` | Unchanged | **No** |

### Fields that must remain unchanged

| Target | Current source | Touch this issue? |
|--------|----------------|-------------------|
| `quikmstr.MMODPREM` | PPOLC.MODE_PREMIUM | **No** |
| `quikridr.MPREM` | ANN_PREM_PER_UNIT + fallback (#26) | **No** |
| MPOLICY padding | `format_qladmin_mpolicy` (#25) | **No** (use for join only) |
| `quikclms` money / CLAIMSTAT / dates | Existing claims path | **No** |
| `quikclmp` | Payees | **No** |
| Non-B `quikmemo` bodies | PNOTE P/R/M/H + PENSE | **No** |

---

## 5. Open Client Questions

1. **Lineage replace** — Discovery default **replace** UI lineage with B notes (lineage → Reports). Confirm with Eric if append preferred. **Does not block** if default accepted.
2. **B notes on non-death claim-only policies** — Planning default: **orphan / skip** (do not put death notes on surrender/disbursement-only headers). ~218 B policies have no `quikclms` row at all.
3. **Multiple claim rows per policy** (214 B-matched policies have >1 claim row) — Planning default: attach to **`DEATH_CLAIM` family row** when present; if multiple death rows (rare in current Output — death is 1:1 policy), use latest `PDDATE`/`RPTDATE`.

---

## 6. Recommended Formatting Rules

| Rule | Recommendation |
|------|----------------|
| Policy key | `POLICY_NUMBER` → `format_qladmin_mpolicy()` (#25); match `quikclms.MPOLICY` |
| Note format | Reuse PNOTE header pattern; tag `[PNOTE-B]` (or `[PNOTE]`) + Date/Time/User/Seq/BenSeq + LINE body |
| Multi-note | Sort by date/seq ascending or newest-first to match Memo UX; join with `\n---\n` |
| Blanks | Skip all-blank LINE rows (13 B rows) |
| Dates/times | Existing `_parse_pnote_date` / `_format_time_hhmmss` |

---

## 7. Memo / Text / Special Handling

- `MEMOTEXT` is MEMO type — CSV string payload same as today; DBF/FPT path for claims already coerces MEMO.
- Claims Memo is **one blob per claim header** (not a separate multi-row memo table for life claims).
- Help: claim memos retained when claim deleted — life path still documents `QuikClms`, not `QuikHcmm`.

---

## 8. Policy Number Key Handling

1. LifePRO `POLICY_NUMBER` → `format_qladmin_mpolicy()` (same as claims/memo fleet).
2. Join to `quikclms.MPOLICY` stripped compare.
3. Orphan B (no claim row or no death family per defaults): **log, do not invent claims**.

---

## 9. Estimated Record Counts

| Metric | Count | Basis |
|--------|------:|-------|
| PNOTE rows total | 7,976 | Extract 20260630 |
| B source rows | 4,149 | FILE_TYPE=B |
| B distinct policies | 1,504 | |
| B policies ∩ any quikclms | 1,286 | format_qladmin_mpolicy join |
| B policies ∩ DEATH_CLAIM | 1,233 | of 1,237 death headers |
| B source rows on matched policies | 3,436 | |
| B policies with no clms | 218 | orphan candidates |
| Multi-claim policies among B∩clms | 214 | max 9 claim rows |
| Current quikmemo rows | 5,084 | will drop B segments |
| Current quikclms rows | 5,594 | MEMOTEXT rewrite on candidates |

---

## 10. Sample Trace (5 policies)

| Policy (QLA) | LifePRO LP | Before (`quikclms.MEMOTEXT`) | After (proposed) | Status |
|--------------|------------|------------------------------|------------------|--------|
| `9010150740C` | 9010150740 | Lineage DEATH_CLAIM… | `[PNOTE-B]`… PB = VIOLA FAYE WALKER… (+2nd note) | Plan |
| `9010150910C` | 9010150910 | Lineage DEATH_CLAIM… | PB = SUSAN SWANSON… | Plan |
| `9010331157C` | 9010331157 | Lineage DEATH_CLAIM… | PB = DOROTHY L REIDERER… | Plan |
| `9010335038C` | 9010335038 | Lineage DEATH_CLAIM… | PB = PATSY MILLER…; remove B from quikmemo | Plan |
| `9010363098C` | 9010363098 | Lineage DEATH_CLAIM… | PB = SANDRA KAY ANNA… | Plan |

Also verify: sample non-B policy memo unchanged; B text absent from `quikmemo` after fix.

---

## 11. Risks and Unknowns

| Risk | Severity | Mitigation |
|------|----------|------------|
| Wiping lineage used for ops debugging | Medium | Keep lineage in Reports/Validation CSVs; document replace |
| Multi-claim attach to wrong header | Medium | Prefer DEATH_CLAIM only |
| Orphan B notes invisible in QLAdmin | Low | Orphan log; no invented claims |
| QUIKMEMO row-count / merge regression | Medium | Validator: non-B PNOTE+PENSE preserved; #50 pad unchanged |
| `quikisrr` synthetic MEMOTEXT overlap | Low | Only overlay B on death-claim candidates; leave surrender-only alone per defaults |

---

## 12. Dependency Gate Preview

| Check | Met? |
|-------|------|
| Source file present | Yes |
| Field definitions confirmed | Yes (`quikclms.MEMOTEXT`; QuikHcmm ruled out) |
| Client scope clear | Yes (Claims Tab; FILE_TYPE B) |
| Example policies available | Yes |

---

## 13. Recommended Risk Agent Prompt

```
Proceed to Risk Agent for Issue 134.
Read Issue_134_Planning_Report.md and Issue_134_Dependency_Gate.md.
Quantify quikmemo B exclusion impact and quikclms.MEMOTEXT replace population.
No code. Go/Conditional-Go/No-Go for Development.
```

---

## 14. Recommended Development Task (Do Not Implement)

1. In `quikmemo_converter.py`: skip `FILE_TYPE=B` (count as skipped_b); keep #50 fixed-width reader.
2. Add post-emit (or claims-path) overlay: load PNOTE B → format → join death `quikclms` → set `MEMOTEXT`; orphan log CSV under Reports/Validation (not Output root).
3. Stop treating `mlineage` as the Claims Tab memo when B overlay applies (rulebook note or post-step overwrite).
4. Version bump `APP_VERSION` in root + `QLA_Migration/app.py` (from current v58.46).
5. Validator `QLA_Migration/_validate_issue134_claim_memos.py`: B not in quikmemo; B text on death quikclms; quikclmp untouched; non-B memo sample unchanged.
6. On PASS: publish modified `quikclms.csv` + `quikmemo.csv` to `Output/Test_Validation/`.

---

## Appendix

- Related: Discovery notes; #21M, #50  
- References: QLAdmin Help §5.1.1.6 Claims Tab; §7.107 QuikHcmm (health only); `Sync_Rulebook_quikclms.csv` mlineage row  
