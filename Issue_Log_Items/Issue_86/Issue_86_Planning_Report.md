# Issue #86 — Planning Report

**Issue:** #86 — QuikDate full rebuild (prior-month-end dates + screenshot defaults)  
**Framework stage:** Planning Agent (G1)  
**Status:** Planning Complete → Dependency Gate  
**Generated:** 2026-07-19  
**Model:** Cursor Grok 4.5 (locked)  
**Code changes:** None  
**Scope authority:** `Issue_86_Scope_Decisions.md`

---

## 1. Executive Finding

QuikDate is wrong in the client region because stale historical dates remain, and conversion’s DG-R-003 emit only fills three bill dates + ACH/ESC — leaving VERSION, UPDATENUM, PDUEDAYS, and other date columns blank. Client wants a **total rebuild**: every date field follows Governance prior-month-end (except `ESC_DATE` blank); every non-date field defaults to the screenshot (`PDUEDAYS=31`, `VERSION=5.318`, `UPDATENUM=359`, `ACHFILEID=0`, `ACHFILEID2=A`). **Go for Dependency Gate / Risk** under planning defaults D1-A / D2-A / D3-A; confirm those three before Development.

---

## 2. Confirmed LifePRO Source Table/File(s)

| Source table | File pattern | In Source/ package? | Row count |
|--------------|--------------|---------------------|----------:|
| *(none)* | N/A — system control rebuild | N/A | 0 |

No LifePRO extract. Authority is:

- `QLA_Migration/Data_Goverence.txt` (QuikDate section)  
- `data_governance` Item 5 (`DG-QUIKDATE-001..006`)  
- Client screenshot of `Q:\CSO\CSO_TEST_6_30_2026_ROBERT\QUIKDATE.DBF`  
- Schema: `data_governance/docs/QuikDate_Schema_Verification.md`

---

## 3. Confirmed QLAdmin Target Structure

| Table | Field | Type | Length | Source |
|-------|-------|------|--------|--------|
| QuikDate | PROCDATE | D | 8 | Schema verification / live DBF |
| QuikDate | ESC_DATE | D | 8 | Schema + DG-006 |
| QuikDate | ANNDATE | D | 8 | Schema |
| QuikDate | DIRBILL | D | 8 | Schema + DG-002 |
| QuikDate | PDUEDAYS | N | 2 | Schema (screenshot = 31) |
| QuikDate | PACBILL | D | 8 | Schema + DG-001 |
| QuikDate | GRPBILL | D | 8 | Schema |
| QuikDate | APLBILL | D | 8 | Schema |
| QuikDate | LOANBILL | D | 8 | Schema |
| QuikDate | REINBILL | D | 8 | Schema + DG-003 |
| QuikDate | CPNBILL | D | 8 | Schema |
| QuikDate | VERSION | C | 10 | Schema (screenshot = 5.318) |
| QuikDate | UPDATENUM | N | 5 | Schema (screenshot = 359) |
| QuikDate | CCBILL | D | 8 | Schema |
| QuikDate | ACHFILEID | N | 1 | Schema + DG-004 |
| QuikDate | ACHFILEID2 | C | 1 | Schema + DG-005 |

**Repo references:**

| Location | Role |
|----------|------|
| `qla_core/quikdate_converter.py` | Current partial emit |
| `app.py` / `QLA_Migration/app.py` (~v58.07 block) | Batch hook calling `emit_quikdate_csv` |
| `data_governance/data_access/normalization.py` | Shared `prior_month_end()` |
| `QLA_Migration/Output/quikdate.csv` | Before-state (partial) |
| `QLA_Migration/QLAdmin_Converted_Tables.txt` | Lists quikdate as governance emit |

---

## 4. Required Source-to-Target Field Mapping

| LifePRO source | LifePRO field | QLAdmin target | Transformation | Change? |
|----------------|---------------|----------------|----------------|---------|
| *(none)* | — | All QuikDate fields | Deterministic defaults (see Scope Decisions matrix) | **Yes — full row** |

### Fields that must remain unchanged

| Target | Current source | Touch this issue? |
|--------|----------------|-------------------|
| quikmstr / quikridr / claims / rates | various | **No** |
| MPOLICY padding | format_qladmin_mpolicy (#25) | **No** |
| quikridr.MPREM | #26 mapping | **No** |
| QuikDate field names / order | QUIKDATE_SCHEMA | **No** (values only) |

---

## 5. Open Client Questions

1. **D1** — PROCDATE = prior month end (recommended) or conversion run date?  
2. **D2** — Force prior month end onto historically blank date columns (CPNBILL)?  
3. **D3** — Hard-code VERSION=`5.318` and UPDATENUM=`359` from screenshot?  

See `Issue_86_Scope_Decisions.md`. Non-blocking for Risk with recommended defaults.

---

## 6. Recommended Formatting Rules

| Rule | Recommendation |
|------|----------------|
| Policy key | N/A (no policy grain) |
| Dates | `YYYYMMDD` via existing `format_qla_date`; blank → `""` for ESC_DATE |
| Prior month end | Reuse `data_governance.data_access.normalization.prior_month_end` |
| Non-dates | PDUEDAYS=31; VERSION=`5.318`; UPDATENUM=359; ACHFILEID=0; ACHFILEID2=`A` |
| Row grain | Exactly **1** row per batch emit |

---

## 7. Memo / Text / Special Handling

N/A.

---

## 8. Policy Number Key Handling

N/A — system control table. #25 / #26 unaffected.

---

## 9. Estimated Record Counts

| Metric | Count | Basis |
|--------|------:|-------|
| Target rows | 1 | Single control row |
| Policies affected | 0 | Not policy-grained |
| Before-state gaps | 10 blank columns in current `quikdate.csv` | Output inspection 2026-07-19 |

### Before → after (run date 2026-07-19, defaults D1-A/D2-A/D3-A)

| Field | Current emit | Proposed |
|-------|--------------|----------|
| PROCDATE | blank | 20260630 |
| ESC_DATE | blank | blank |
| ANNDATE | blank | 20260630 |
| DIRBILL | 20260630 | 20260630 |
| PDUEDAYS | blank | 31 |
| PACBILL | 20260630 | 20260630 |
| GRPBILL | blank | 20260630 |
| APLBILL | blank | 20260630 |
| LOANBILL | blank | 20260630 |
| REINBILL | 20260630 | 20260630 |
| CPNBILL | blank | 20260630 |
| VERSION | blank | 5.318 |
| UPDATENUM | blank | 359 |
| CCBILL | blank | 20260630 |
| ACHFILEID | 0 | 0 |
| ACHFILEID2 | A | A |

---

## 10. Sample Trace

N/A at policy level. System-row trace = table above. Client region screenshot is the visual before-state for non-date defaults.

---

## 11. Risks and Unknowns

| Risk | Severity | Mitigation |
|------|----------|------------|
| PROCDATE semantics (run date vs PME) | Medium | Confirm D1 before Development |
| Hard-coding VERSION/UPDATENUM may drift from QLAdmin install | Low | Screenshot is client-requested authority; document constants |
| Governance rules only audit 6 fields today | Low | Emit still satisfies DG-001..006; optional rule expansion later |
| Overwriting intentional blank CPNBILL | Low | Confirm D2 |

---

## 12. Dependency Gate Preview

| Check | Met? |
|-------|------|
| Source file present | N/A (system defaults) |
| Field definitions confirmed | Yes (schema verification + screenshot) |
| Client scope clear | Yes (rebuild + PME dates + screenshot non-dates); D1–D3 soft |
| Example policies available | N/A |

---

## 13. Recommended Risk Agent Prompt

```
Proceed to Risk Agent for Issue #86.

Read:
- Issue_Log_Items/Issue_86/Issue_86_Intake_Summary.md
- Issue_Log_Items/Issue_86/Issue_86_Planning_Report.md
- Issue_Log_Items/Issue_86/Issue_86_Scope_Decisions.md
- Issue_Log_Items/Issue_86/Issue_86_Dependency_Gate.md
- qla_core/quikdate_converter.py
- data_governance/docs/RULE_CATALOG.md (DG-QUIKDATE)
- QLA_Migration/Data_Goverence.txt (QuikDate section)

Model: Cursor Grok 4.5 (locked). Do not code.

Quantify before/after for the single QuikDate row under defaults D1-A / D2-A / D3-A.
Confirm DG-QUIKDATE-001..006 still pass.
Go/no-go for Development.
```

---

## 14. Recommended Development Task (Do Not Implement)

1. Extend `build_quikdate_governance_row` / `emit_quikdate_csv` to populate **all** schema fields per Scope Decisions matrix.  
2. Keep shared `prior_month_end()` import; do not hardcode 20260630.  
3. Leave batch hook in `app.py` / `QLA_Migration/app.py` (already calls emit); version-bump both `APP_VERSION`s.  
4. Add validator `QLA_Migration/_validate_issue86_quikdate.py` (1 row; dates = PME; ESC blank; non-date constants; DG-001..006).  
5. On PASS, publish `quikdate.csv` to `Output/Test_Validation/`.  
6. Do not touch policy/claims/rate converters.

---

## Appendix

- Related: DG-R-003 (partial), Governance Item 5  
- Screenshot evidence: client chat attachment (2026-07-19)  
- Current before-state: `QLA_Migration/Output/quikdate.csv`
