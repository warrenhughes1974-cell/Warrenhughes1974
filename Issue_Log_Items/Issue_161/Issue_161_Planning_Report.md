# Issue #161 — Planning Report

**Issue:** #161 — POA Information Missing (`quikclid.MRELATION` wrong code: `PW` vs `POFA`)
**Framework stage:** Planning Agent
**Status:** Planning Complete → Dependency Gate
**Generated:** 2026-09-08
**Agent/script:** Manual research + `dbfread` live-build inspection (Cursor, Discovery/Planning session 2026-09-08)

---

## 1. Executive Finding

The POA relationship data is **not missing** from the conversion — it is present in `quikclid` for all three example policies (and fleet-wide) — but it is emitted with the **wrong target code**. LifePRO `RELATE_CODE=PW` is passed through unchanged into `quikclid.MRELATION` as `PW`, while QLAdmin's own Names/Other-Information UI only recognizes **`POFA`** as the Power-of-Attorney relation code (confirmed live in the app's relation-type dropdown, screenshot provided by Warren). This is a **single-row value-translation correction**, confirmed root cause, low blast radius (isolated to rows sourced from `RELATE_CODE=PW`, which is a small, distinct fleet-wide subset — 412 rows / 270 policies). **Recommend GO** to Dependency Gate / Risk.

---

## 2. Confirmed LifePRO Source Table/File(s)

| Source table | File pattern | In Source/ package? | Row count |
|--------------|--------------|---------------------|----------:|
| RNA / PRELSA (Relationship Name/Address) | `RelationshipNameAddress_Extract_YYYYMMDD.csv` | Yes | 412 `RELATE_CODE=PW` rows fleet-wide / 270 distinct policies |

### Available source fields

| Field | Column / source | Populated % | Notes |
|-------|-----------------|------------:|-------|
| Policy key | `IDENTIFYING_ALPHA` (e.g. `039010442216` → `9010442216C`) | 100% for PW rows | Same crosswalk pattern as Issue #30 |
| Relationship type | `RELATE_CODE = PW` | 100% for this subset | Semantic label "Power-of-Attorney" per `claims_analysis/config/relationship_code_semantics.json` line 11 |
| Client identity | `NAME_ID` | 100% | Feeds `quikclid.MCLIENTID` and `quikclnt` client master |
| Scope / metadata | `COMM_PCNT`, `ISSUE_DATE`, `SPLIT_EFF_DATE`, `CANCEL_DATE` | Present but **not converted today** | No `quikclid` target field exists for these — out of scope this issue |

---

## 3. Confirmed QLAdmin Target Structure

| Table | Field | Type | Length | Source (Help / schema) |
|-------|-------|------|--------|------------------------|
| `quikclid` | `MRELATION` | Character | 4 | `data_governance/docs/RULE_CATALOG.md` — 4-field table (`MCLIENTID`, `MPOLICY`, `MPHASE`, `MRELATION`) |

**Correct target value confirmed live in QLAdmin** (Warren screenshot, Policy Editor → Names tab → Other Information dropdown):

```text
ASGN  - Assignee
JINS  - Joint Insured
JOWN  - Joint Owner
LAPS  - 2nd Lapse Notice
POFA  - Power of Attorney   <-- correct target
```

**Repo references** (grep results — population paths only):

| Location | Role |
|----------|------|
| `QLA_Migration/Configs/Sync_Rulebook_quikclid.csv` line 5 | `RELATE_CODE → MRELATION` (direct field mapping, unchanged, correct) |
| `QLA_Migration/Mapping/Master_Value_Translation.csv` line 49 | `PW,PW` — **wrong**, should be `PW,POFA` |
| `data_governance/config/policy_code_authorities.csv` line 58 | `MRELATION,PW,PW relationship` — **wrong**, should be `MRELATION,POFA,Power of Attorney relationship` |
| `helpdbfs.dbf` (live QLAdmin field-help table, `Q:\CSO\CSO_Test_6_30_2026\`) | Documents `MRELATION` as "Client relation (PRIM, INSD, OWNR, PAYR, ASGN)" — `PW` never listed as a known example; `POFA` confirmed valid via live dropdown instead |
| `QLA_Migration/app.py` / `app.py` lines ~764, ~5777 | Loads `Master_Value_Translation.csv` generically for all rulebook-driven value translations (not POA-specific code) |

---

## 4. Required Source-to-Target Field Mapping

| LifePRO source | LifePRO field | QLAdmin target | Transformation | Change? |
|----------------|---------------|----------------|----------------|---------|
| RNA | `RELATE_CODE = PW` | `quikclid.MRELATION` | Value translation: `PW → POFA` (was `PW → PW`) | **Yes** |
| RNA | `NAME_ID` | `quikclid.MCLIENTID` | Unchanged, direct pass-through | No |
| RNA | `IDENTIFYING_ALPHA` | `quikclid.MPOLICY` | Unchanged (Issue #30 crosswalk) | No |
| RNA | `BENEFIT_SEQ_NUMBER` | `quikclid.MPHASE` | Unchanged | No |

### Fields that must remain unchanged

| Target | Current source | Touch this issue? |
|--------|----------------|-------------------|
| quikmstr.MMODPREM | PPOLC.MODE_PREMIUM | **No** |
| quikridr.MPREM | ANN_PREM_PER_UNIT + fallback (#26) | **No** |
| MPOLICY padding | format_qladmin_mpolicy (#25) | **No** |
| All other `Master_Value_Translation.csv` rows (IN→INSD, PO→OWNR, PA→PAYR, B1/PE→BENP, B2→BENC, BK→BANK, SA→SERV, ML→MAIL, GU→GUAR, TR→TRST, WA→WAIT, GP→GRUP, CU→CUST, JE→JOIN, AS→ASGN, O1→O1) | Existing mappings | **No** — only the `PW` row changes |
| `quikbenf` PW/POFA exclusion filter (`app.py` beneficiary source filter) | Keeps only B1/B2/P/C | **No** — POA stays out of `quikbenf` by design |

---

## 5. Open Client Questions

1. None required to proceed — root cause and correct target code (`POFA`) already confirmed via Warren's live QLAdmin screenshot. (Optional, non-blocking: confirm with Eric whether he also wants POA effective-date/scope-% metadata surfaced somewhere, since `quikclid`'s 4-field schema cannot carry that — this would be a separate, larger enhancement if requested.)

---

## 6. Recommended Formatting Rules

| Rule | Recommendation |
|------|----------------|
| Policy key | Crosswalk + 10-char MPOLICY padding (#25) — unchanged |
| Relation code | `PW` (LifePRO) → `POFA` (QLAdmin), 4-char, upper-case — matches existing `MRELATION` code width/format |
| Dates | N/A — not in scope this pass |
| Money | N/A — not in scope this pass |
| Blanks / zeros | N/A — no blank-handling change; existing PW rows already fully populated |

---

## 7. Memo / Text / Special Handling

N/A. No memo/text field changes. This is a single value-translation code correction.

---

## 8. Policy Number Key Handling

1. LifePRO `IDENTIFYING_ALPHA` → `Master_Crosswalk.csv` → QLA policy key (unchanged — Issue #30 pattern)
2. `format_qladmin_mpolicy()` for CHARACTER(10) keys (unchanged — Issue #25)
3. Orphan handling: unchanged; this issue does not add or remove any relationship rows, it only corrects the emitted code value on existing rows

---

## 9. Estimated Record Counts

| Metric | Count | Basis |
|--------|------:|-------|
| Total source `RELATE_CODE=PW` rows (fleet) | 412 | `claims_analysis/output/relationship_code_frequency.csv` |
| Distinct policies affected | 270 | Same source |
| Rows expected to change in `quikclid.csv` | 412 (MRELATION value only; row count unchanged) | 1:1, no rows added/removed |
| Rows in `quikclid.csv` NOT affected (all other relation codes) | ~31,873 (32,285 total scanned in live build − 412 PW) | `quikclid.dbf` live-build scan, 2026-09-02 |

---

## 10. Sample Trace (3 policies)

| Policy (QLA) | LifePRO client | Before (`MRELATION`) | After (proposed) | Status |
|--------------|------------|--------|------------------|--------|
| 9010442216C | 712072 — MARLYS VANDER WAL | `PW` | `POFA` | Confirmed present in source + Output + live DBF |
| 9010451650C | 712326 — TIMOTHY MOUNTAIN | `PW` | `POFA` | Confirmed present in source + Output + live DBF |
| 9011045619C | 591432 — ANDREW MAZZURCO | `PW` | `POFA` | Confirmed present in source + Output + live DBF |

---

## 11. Risks and Unknowns

| Risk | Severity | Mitigation |
|------|----------|------------|
| Other unrecognized `MRELATION` codes exist besides `PW` (e.g. `O1`) that may have the same display defect | Low — out of scope, not reported by client | Flag in Risk report as a known adjacent issue; do not fix without a client-reported symptom |
| QLAdmin may filter/reject unrecognized `MRELATION` values on DBF Append load rather than just hiding them on screen | Low | Validation stage will re-append via Desktop DBF Append Tool and re-check the screen for one of the 3 example policies post-fix |
| `POFA` code may have its own display nuances (e.g. requires a companion field, effective date) not visible from the dropdown alone | Low–Medium | Validation stage will visually confirm the "Other Information" panel renders correctly for at least one trace policy post-fix, not just that the DBF value changed |

---

## 12. Dependency Gate Preview

| Check | Met? |
|-------|------|
| Source file present | Yes — RNA extract already in use by existing rulebook |
| Field definitions confirmed | Yes — `quikclid.MRELATION`, 4-char |
| Client scope clear | Yes — Eric's 3 example policies, root cause confirmed |
| Example policies available | Yes — 9010442216C, 9010451650C, 9011045619C |

---

## 13. Recommended Risk Agent Prompt

```
Run Risk review for Issue #161 (POA Information Missing). Confirm: (1) blast radius is limited
to the 412 quikclid rows sourced from LifePRO RELATE_CODE=PW (270 policies); (2) no other
Master_Value_Translation.csv row or MRELATION code is touched; (3) quikbenf PW/POFA exclusion
filter stays intact; (4) prior closed-issue fixes (#25 MPOLICY padding, #26 MPREM, #30 RNA
crosswalk keying) are not disturbed. Recommend GO if isolated to the single PW->POFA row edit
in Master_Value_Translation.csv (+ matching label update in policy_code_authorities.csv).
```

---

## 14. Recommended Development Task (Do Not Implement)

1. In `QLA_Migration/Mapping/Master_Value_Translation.csv`, change row 49 from `PW,PW` to `PW,POFA`
2. In `data_governance/config/policy_code_authorities.csv`, change row 58 from `MRELATION,PW,PW relationship` to `MRELATION,POFA,Power of Attorney relationship`
3. Re-run full batch (or `quikclid`-scoped re-emit) with the current 6/30 valuation-date source package
4. Confirm `quikclid.csv`/`.dbf` output has **zero** `MRELATION=PW` rows and **412** `MRELATION=POFA` rows (fleet-wide), including the 3 example policies
5. Version bump: next available `app.py` version (root + `QLA_Migration/app.py`, per `AGENTS.md`)
6. Validation script: `tools/validators/validate_issue161_poa_relation_code.py` — fail-closed: assert 0 `PW` rows remain and `POFA` count matches source `RELATE_CODE=PW` count; assert all 3 example policies present as `POFA`

---

## Appendix

- Diagnostic evidence: `Q:\CSO\CSO_Test_6_30_2026\quikclid.dbf` live-build scan (2026-09-08 research session); Warren's QLAdmin screenshot of Policy `9010442216C` Names/Other-Information panel showing valid dropdown codes including `POFA - Power of Attorney`
- Related issues: #30 (RNA keying — unaffected), #21I (beneficiary scope — unaffected), #159 (numbering collision only, unrelated defect)
- References: `claims_analysis/config/relationship_code_semantics.json`, `claims_analysis/output/relationship_code_frequency.csv`, `data_governance/docs/RULE_CATALOG.md`
