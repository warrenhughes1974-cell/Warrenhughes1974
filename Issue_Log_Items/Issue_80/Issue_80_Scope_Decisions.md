# Issue #80 — Scope Decisions

**Locked:** 2026-07-17  
**Authority:** User answers in chat + `docs/Valuation_Setup.xlsx` + QLAdmin Help code charts

| ID | Decision |
|----|----------|
| **SD-80-1** | Blank Valuation_Setup cells mean the assumption does not apply. Emit blank; do not invent. |
| **SD-80-2** | Interest / method / logical codes come from QLAdmin Help (§6.9, §6.10, QuikPltv field text). See `evidence/cso_valuation_setup_code_map.md`. |
| **SD-80-3** | For `221END` and `222END`, QuikPlCv ETIMORT loads as **`N1` (1941 CSO)** per user direction (workbook text said `1941 CET 2.5% NLP`; Help has no 1941 CET code). |
| **SD-80-4** | Four Valuation_Setup rows with no QLA Plan (`622 PUA`, `675 61 PUA`, `675 AD PUA`, `991 PUA`) are **out of #80**. Tracked as **Issue #81**. |
| **SD-80-5** | PUA QLA plans that do appear in Valuation_Setup (e.g. `121PUA`, `1POPUA`, `265PUA`) are **out of #80** for QuikPlCv / QuikPlTv key writes. Tracked as **Issue #82** (relationship to #60 / no PA plans in quikplan). |
| **SD-80-6** | #80 in-scope = Valuation_Setup rows with a QLA Plan that are **not** PUA plans (51 plans). Citizens folder remains out of scope. |
| **SD-80-7** | Where Valuation_Setup conflicts with `CSO_Mortiality_Crosswalk.csv`, Valuation_Setup wins for in-scope plans. |

---

## In-scope count

| Bucket | Count | Disposition |
|--------|------:|-------------|
| Non-PUA with QLA Plan | 51 | **#80** |
| PUA with QLA Plan | 10 | **#82** |
| PUA missing QLA Plan | 4 | **#81** |
| Total workbook rows | 65 | |
