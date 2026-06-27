# Issue [ID] — Planning Report

**Issue:** [ID] — [Title]  
**Framework stage:** Planning Agent  
**Status:** Planning | Blocked — Awaiting Client Data | Blocked — Awaiting Client Clarification  
**Generated:** [YYYY-MM-DD]  
**Agent/script:** [name and version]

---

## 1. Executive Finding

[2–4 sentences: what is wrong, confirmed vs hypothesized, recommended direction, go/no-go for next stage]

---

## 2. Confirmed LifePRO Source Table/File(s)

| Source table | File pattern | In Source/ package? | Row count |
|--------------|--------------|---------------------|----------:|
| | | Yes / No | |

### Available source fields

| Field | Column / source | Populated % | Notes |
|-------|-----------------|------------:|-------|
| Policy number | | | |
| | | | |

---

## 3. Confirmed QLAdmin Target Structure

| Table | Field | Type | Length | Source (Help / schema) |
|-------|-------|------|--------|------------------------|
| | | | | |

**Repo references** (grep results — population paths only):

| Location | Role |
|----------|------|
| | |

---

## 4. Required Source-to-Target Field Mapping

| LifePRO source | LifePRO field | QLAdmin target | Transformation | Change? |
|----------------|---------------|----------------|----------------|---------|
| | | | | Yes / No |

### Fields that must remain unchanged

| Target | Current source | Touch this issue? |
|--------|----------------|-------------------|
| quikmstr.MMODPREM | PPOLC.MODE_PREMIUM | **No** |
| quikridr.MPREM | ANN_PREM_PER_UNIT + fallback (#26) | **No** |
| MPOLICY padding | format_qladmin_mpolicy (#25) | **No** |
| | | |

---

## 5. Open Client Questions

1. [Question]
2. [Question]

---

## 6. Recommended Formatting Rules

| Rule | Recommendation |
|------|----------------|
| Policy key | Crosswalk + 10-char MPOLICY padding (#25) |
| Dates | |
| Money | |
| Blanks / zeros | |

---

## 7. Memo / Text / Special Handling

[N/A or details for long text, MEMO/FPT, concatenation]

---

## 8. Policy Number Key Handling

1. LifePRO `POLICY_NUMBER` → `Master_Crosswalk.csv` → QLA
2. Apply `format_qladmin_mpolicy()` for CHARACTER(10) keys
3. Orphan policy handling: [skip / log / fail]

---

## 9. Estimated Record Counts

| Metric | Count | Basis |
|--------|------:|-------|
| Total source rows | | |
| Rows expected in target | | |
| Policies affected | | |

---

## 10. Sample Trace ([N] policies)

| Policy (QLA) | LifePRO LP | Before | After (proposed) | Status |
|--------------|------------|--------|------------------|--------|
| | | | | |

---

## 11. Risks and Unknowns

| Risk | Severity | Mitigation |
|------|----------|------------|
| | | |

---

## 12. Dependency Gate Preview

| Check | Met? |
|-------|------|
| Source file present | |
| Field definitions confirmed | |
| Client scope clear | |
| Example policies available | |

---

## 13. Recommended Risk Agent Prompt

```
[Paste ready-to-use Cursor prompt for Risk Agent]
```

---

## 14. Recommended Development Task (Do Not Implement)

1. [Step]
2. [Step]
3. Version bump: v[xx.xx]
4. Validation script: `QLA_Migration/_validate_issue[id]_*.py`

---

## Appendix

- Diagnostic script: [path]
- Related issues: [list]
- References: [QLAdmin Help pages, rulebooks]
