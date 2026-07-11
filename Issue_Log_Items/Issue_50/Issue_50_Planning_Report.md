# Issue #50 — Planning Report

**Issue:** #50 — Policy Notes Missing  
**Framework stage:** Planning Agent (G1)  
**Status:** Planning complete → Dependency Gate  
**Generated:** 2026-07-11  
**Agent/script:** Planning Agent · `scripts/research_issue50_pnote_parse.py`  
**Model:** Cursor Grok 4.5 (locked)  
**Code changes:** None

---

## 1. Executive Finding

Policy **018495BC** has LifePRO notes on `PNOTE_PolicyNotes_Extract_20260630`, but the **primary note** (“Vincent J. Bauerly, if living otherwise to: Ethel R. Bauerly.”) never reaches QUIKMEMO because `quikmemo_converter._read_csv` uses pandas `on_bad_lines="skip"`, which **drops any PNOTE row whose unquoted `LINE_*` text contains commas**. A secondary note (“Last Known Address”) does emit and is present in current `quikmemo.csv` / DBF after the `#21J` `[CONVERSION]` segment.

This is a **source-reader defect**, not a missing extract, not a crosswalk orphan, and not a SAL-only emit filter. SAL forms are **disproportionately affected** (130 of 163 SAL policies have ≥1 dropped row; 74 lose all PNOTE rows) because many SAL notes contain commas in free text — matching the client’s suspicion without requiring a separate SAL code path.

**Recommended direction:** Surgical resilient PNOTE parse (fixed-width or comma-tolerant LINE reconstruction) inside the existing #21M converter; re-emit QUIKMEMO; validate `018495BC` contains Bauerly + Last Known Address. **Do not proceed to Development until Risk (G3).**

---

## 2. Confirmed LifePRO Source Table/File(s)

| Source table | File pattern | In Source/ package? | Row count |
|--------------|--------------|---------------------|----------:|
| PNOTE | `PNOTE_PolicyNotes_Extract_20260630.csv` | Yes | 7,976 data rows (raw); **6,037** after pandas skip |
| PENSE | `PENSE_ENSData_Extract_20260630.csv` | Yes | 23,346 (ENS path unchanged for this issue) |

### Available source fields (PNOTE)

| Field | Column | Populated % | Notes |
|-------|--------|------------:|-------|
| Policy number | `POLICY_NUMBER` | ~100% | LifePRO key; crosswalk → QLA |
| Benefit seq | `BENEFIT_SEQ` | partial | Embedded in `[PNOTE]` BenSeq line |
| Date / name | `DATE_OR_NAMEID` | high | MMDDYYYY or user |
| Time | `TIME_OR_UW_REQ_SEQ` | partial | HHMMSS |
| Record seq | `RECORD_SEQ` | high | Note sequence |
| Note lines | `LINE_1`…`LINE_4` | body | **Unquoted commas break CSV field count** |
| Keys | `NOTE_UPD_COUNT`, `NOTE_KEY0`, `ROW_COLUMN` | present | Not mapped to QLAdmin columns |

### Parse-loss population

| Metric | Count |
|--------|------:|
| Raw PNOTE data rows | 7,976 |
| Rows with exact 14 fields (kept) | 6,037 |
| Rows with field count ≠ 14 (dropped) | **1,939** |
| Distinct LP with any dropped row | 1,043 |
| Distinct LP with **only** dropped rows (total note loss) | **374** |
| SAL policies in `quikridr` | 163 |
| SAL ∩ any dropped row | **130** |
| SAL ∩ total note loss | **74** |

---

## 3. Confirmed QLAdmin Target Structure

| Table | Field | Type | Length | Source |
|-------|-------|------|--------|--------|
| QUIKMEMO | MEMOKEY | C | 10 | #21M / #25 padding |
| QUIKMEMO | MEMOTEXT | M (memo) | DBT/FPT | #21M; merged segments #21M-FU |

**Repo references:**

| Location | Role |
|----------|------|
| `qla_core/quikmemo_converter.py` | PNOTE+PENSE merge |
| `qla_core/quikmemo_dbf_generator.py` | DBF+DBT packaging |
| `qla_core/modal_premium_factors.py` / `append_issue21j_conversion_memos` | `[CONVERSION]` prepend |
| `QLA_Migration/app.py` quikmemo batch branch | Orchestration |
| `data_governance/constants/schema_manifests.py` | `quikmemo`: MEMOKEY, MEMOTEXT |

---

## 4. Required Source-to-Target Field Mapping

| LifePRO source | LifePRO field | QLAdmin target | Transformation | Change? |
|----------------|---------------|----------------|----------------|---------|
| PNOTE | POLICY_NUMBER | MEMOKEY | Crosswalk + `format_qladmin_mpolicy` (#25) | **No** (keep) |
| PNOTE | DATE/TIME/SEQ + LINE_1–4 | MEMOTEXT `[PNOTE]` segment | Existing formatter | **No** (keep) |
| PNOTE | CSV physical row | (read path) | **New resilient parse** so comma-in-text rows are kept | **Yes** |
| PENSE | (unchanged) | MEMOTEXT `[ENS]` | Existing | **No** |
| #21J | plan factors | MEMOTEXT `[CONVERSION]` first | Existing prepend | **No** unless Risk changes display order |

### Fields / behaviors that must remain unchanged

| Target | Current source | Touch this issue? |
|--------|----------------|-------------------|
| MPOLICY / MEMOKEY padding | `format_qladmin_mpolicy` (#25) | **No** |
| quikridr.MPREM | #26 | **No** |
| One row per MEMOKEY | #21M-FU merge | **No** |
| PENSE `ENS_KEY_TYPE=P` filter | #21M | **No** |
| Unrelated rulebooks / quikmstr / quikplan | — | **No** |

---

## 5. Open Client Questions

1. **Expected text for `018495BC`:** Confirm the missing LifePRO note is the Bauerly beneficiary wording (Seq 1), not only “Last Known Address” (Seq 2 — already in QUIKMEMO).
2. **Memo display:** After fix, is it acceptable that `[CONVERSION]` still appears **above** policy notes on the Memo tab, or should notes be ordered first for UAT clarity? (Engineering can change order only if client requests.)
3. **UAT load path:** Confirm QLAdmin UAT loads **both** `quikmemo.dbf` + `quikmemo.dbt` from `Output/quikmemo_uat_dbf/` together (historical #21M packaging failure mode).

Questions 1–3 are **soft** for Dependency Gate if Risk accepts Bauerly text as the acceptance criterion and keeps `[CONVERSION]` order unchanged.

---

## 6. Recommended Formatting Rules

| Rule | Recommendation |
|------|----------------|
| Policy key | Crosswalk + 10-char MPOLICY padding (#25) — unchanged |
| Dates | Existing PNOTE MMDDYYYY → YYYY-MM-DD — unchanged |
| Segment headers | Keep `[PNOTE]` / `[ENS]` / `[CONVERSION]` |
| Separator | Keep `\n---\n` (#21M-FU) |
| Blank LINE rows | Continue skip blank text blobs |
| Malformed CSV rows | **Do not skip** — reconstruct LINE_1–4 by consuming extra comma-split fragments into line fields before trailing key columns |

---

## 7. Policy Key Handling

| Step | Behavior |
|------|----------|
| LifePRO key | `POLICY_NUMBER` strip |
| Crosswalk | `Master_Crosswalk.csv` Old→New |
| MEMOKEY | `format_qladmin_mpolicy(qla)` |
| Example | `9018495B` → `018495BC` → `'  018495BC'` — matches `quikmstr.MPOLICY` |

Orphan rate on current path: **0** (`skipped_orphan=0`).

---

## 8. Estimated Record Counts (after fix — approximate)

| Population | Before (current) | After (expected direction) |
|------------|------------------|----------------------------|
| PNOTE rows ingested | 6,037 | ~7,976 (all non-blank) |
| Distinct policies with any PNOTE | 3,307 | ~3,681 |
| QUIKMEMO rows (with #21J fleet) | 5,083 | **5,083** (same grain; richer MEMOTEXT) |
| `018495BC` `[PNOTE]` segments | 1 (Last Known only) | **2** (Bauerly + Last Known) |

Exact post-fix counts require Development dry-run; Risk should treat **+1,939 PNOTE segments** as upper bound on added text volume (DBT size increase).

---

## 9. Sample Trace (≥3 policies)

| QLA | LP | Plan | Source notes | Current QUIKMEMO | Defect class |
|-----|-----|------|--------------|------------------|--------------|
| **018495BC** | 9018495B | 1SALML | Seq1 Bauerly (comma); Seq2 Last Known | CONVERSION + Last Known only | **PARTIAL_MALFORMED** |
| **01159D276C** | (SAL) | 1SALOL | All PNOTE rows malformed | CONVERSION only (no `[PNOTE]`) | **ONLY_MALFORMED** |
| **010335038C** | 9010335038 | (prior #21M UAT) | Clean 14-field rows | Has `[PNOTE]` | Control — should stay unchanged |

Full SAL impact list: `evidence/issue50_sal_malformed_impact.csv`

---

## 10. Risks and Unknowns

| Risk | Level | Notes |
|------|-------|-------|
| Incorrect LINE reconstruction (mis-assigning comma fragments) | Medium | Need deterministic rule: first 7 cols fixed; last 3 cols fixed from right; middle = LINE blob split into ≤4 lines |
| DBT size growth | Low–Med | +~1.9k segments into merged texts |
| `[CONVERSION]`-first UX confusion | Low | Example already has secondary note; client may still say “missing” if they expect Bauerly and don’t scroll |
| False “SAL-only” scope | Low | Fix must be fleet-wide parser — SAL is impact concentration, not exclusive filter |
| Regression on clean 6,037 rows | Medium | Validator must assert byte-stable or text-stable MEMOTEXT for control policies |

---

## 11. Recommended Risk Agent Prompt

```
Proceed to Risk Agent for Issue #50.

Read AI_Agents/Risk_Agent.md and Issue_Log_Items/Issue_50/Issue_50_Planning_Report.md.
Model: Cursor Grok 4.5. Do not code.

Quantify before/after impact of resilient PNOTE CSV parse:
- 1,939 recovered rows; 374 total-loss policies; 130 SAL partial/full
- DBT size / MEMOTEXT growth
- Regression surface limited to quikmemo_converter read path + quikmemo emit
- Preserve #21M-FU grain, #25 padding, #21J CONVERSION prepend, #26 untouched

Recommend Go / Conditional-Go / No-Go for Development.
```

---

## 12. Recommended Development Task (do not implement)

1. Replace or wrap `_read_csv` for PNOTE with a **comma-tolerant reader** that keeps rows when `LINE_*` free text contains commas (prefer fixed-width / from-right key parse over `on_bad_lines='skip'`).
2. Leave PENSE reader unchanged unless proven same defect.
3. Keep merge / `[CONVERSION]` / DBF packaging unchanged.
4. Bump `APP_VERSION` in root `app.py` and `QLA_Migration/app.py`.
5. Add `tools/validators/validate_issue50_pnote_parse.py`:
   - `018495BC` MEMOTEXT contains `Bauerly` and `Last Known Address`
   - Control `010335038C` still has expected `[PNOTE]` content
   - PNOTE ingested row count ≥ prior 6,037 and approaches raw non-blank count
   - `#25` MEMOKEY width still 10
6. Publish updated `quikmemo.csv` + `quikmemo_uat_dbf/` to `Output/Test_Validation/` on validator PASS.

---

## G1 checklist

- [x] Planning report published
- [x] Source/target mapping documented
- [x] Open questions listed
- [x] Sample traces ≥3
- [x] No code or rulebook changes
