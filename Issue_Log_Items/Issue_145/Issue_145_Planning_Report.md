# Issue #145 — Planning Report

**Issue:** #145 — Vanish Flag (VB)  
**Framework stage:** Planning Agent  
**Status:** Planning  
**Generated:** 2026-08-19  
**Agent/script:** Cursor Grok 4.5 · read-only PPOLC / quikspec join (no production code)

---

## 1. Executive Finding

QuikSpec already emits `VANISH` as **F** on all 5,083 policies. LifePRO `PPOLC.BILLING_REASON = VB` is the locked on-vanish source: **636** policies on the 2026-06-30 extract (all present on current Output as `…C` keys). Set `VANISH` to logical **T** for those rows only. Leave `VANISHDT` blank. Do not use 659-plan eligibility, `BA_OR_VANISH_FLAG`, or #146 leftovers. Ready for Dependency Gate.

CSV emit is **T / F** (logical length 1, matching today’s `F`). Client language “TRUE” means the flag is on, not the four-character string `TRUE`.

---

## 2. Confirmed LifePRO Source Table/File(s)

| Source table | File pattern | In Source/ package? | Row count |
|--------------|--------------|---------------------|----------:|
| PPOLC | `PPOLC_PolicyMaster_Extract*.csv` | Yes (20260630 root; 20260731 folder) | 636 VB / 635 VB |

### Available source fields

| Field | Column / source | Populated % | Notes |
|-------|-----------------|------------:|-------|
| Policy | PPOLC.POLICY_NUMBER | 100% of VB | Join with `format_qladmin_mpolicy` / trailing `C` |
| On vanish | PPOLC.BILLING_REASON | VB = 636 (6/30) | Exact code `VB` after trim/upper |
| Billing form | PPOLC.BILLING_CODE | 341 A / 295 blank among VB | **Do not filter** — all VB get the flag |
| Status | PPOLC.CONTRACT_CODE | 340 A / 295 T / 1 S among VB | **Do not filter** |

7/31 difference: **9011085421** is VB on 6/30 and **PC** on 7/31. Count must follow the extract used for that batch (`QLA_VALUATION_DATE` / `find_extract`), not a frozen 636.

---

## 3. Confirmed QLAdmin Target Structure

| Table | Field | Type | Length | Source (Help / schema) |
|-------|-------|------|--------|------------------------|
| quikspec | MPOLICY | C | 10/11 emit | Existing |
| quikspec | VANISH | L | 1 | User Defined Vanish; currently default F |
| quikspec | VANISHDT | D | 8 | Stay blank this issue |
| quikspec | RESSTATE | C | 2 | #132 — do not change |
| quikspec | RESRVCAT | C | 2 | #141 Closed — do not change |

**Repo references** (population paths only):

| Location | Role |
|----------|------|
| `QLA_Migration/Configs/Sync_Rulebook_quikspec.csv` | VANISH default `F`; VANISHDT blank |
| `app.py` + `QLA_Migration/app.py` TABLE_SCHEMAS `quikspec` | Column order already includes VANISH |
| `qla_core/quikspec_resrvcat.py` | Post-emit #141 RESRVCAT; call **after** this stays intact |
| `app.py` quikspec write hook (~9867) | Chain a vanish enrich next to RESRVCAT |
| `tools/validators/validate_quikspec_resident_state.py` | Existing RESSTATE smoke — do not weaken |

---

## 4. Required Source-to-Target Field Mapping

| LifePRO source | LifePRO field | QLAdmin target | Transformation | Change? |
|----------------|---------------|----------------|----------------|---------|
| PPOLC | POLICY_NUMBER | quikspec.MPOLICY | Existing #2/#25 key | No |
| PPOLC | BILLING_REASON | quikspec.VANISH | `VB` → `T`; else `F` | **Yes** |
| — | — | quikspec.VANISHDT | Remain blank | No |
| PPOLC | RES_STATE | quikspec.RESSTATE | Existing #132 | No |
| PCOVR/PPBEN | PRODUCT_TYPE via seq-1 | quikspec.RESRVCAT | Existing #141 | No |

### Fields that must remain unchanged

| Target | Current source | Touch this issue? |
|--------|----------------|-------------------|
| quikmstr.MMODPREM | PPOLC.MODE_PREMIUM | **No** |
| quikridr.MPREM | ANN_PREM_PER_UNIT + fallback (#26) | **No** |
| MPOLICY padding | format_qladmin_mpolicy (#25 / #2) | **No** |
| quikspec.RESSTATE | PPOLC.RES_STATE (#132) | **No** |
| quikspec.RESRVCAT | PCOVR.PRODUCT_TYPE (#141) | **No** |
| quikspec.VANISHDT | blank | **No** |
| quikplan MKTG/PRODUCT/HLOB | #99 ISWLFE | **No** |
| QuikIsrr | #34 | **No** |

---

## 5. Open Client Questions

Locked at Intake / Planning (Warren 2026-08-18 / 08-19):

1. **VB means on vanish** — not the internal “Variable Billing” label.  
2. **VANISHDT stays blank** — no locked LifePRO date; #22 keeps the date/licensee research.  
3. **#22 stays open** as eligible-vs-on-vanish / New Era research. #145 is the VB flag only.  
4. **Emit T/F** — logical 1-char matching current `F`; UI/Help “TRUE” is the same flag.

No remaining client questions that block Risk.

---

## 6. Recommended Formatting Rules

| Rule | Recommendation |
|------|----------------|
| Policy key | Existing crosswalk + `format_qladmin_mpolicy()` |
| VANISH | Trim/upper `BILLING_REASON`; exact `VB` → `T`; all other codes and blank → `F` |
| VANISHDT | Always blank |
| Dates / money | N/A |
| Extract vintage | Resolve PPOLC from the same source folder as the batch |

---

## 7. Memo / Text / Special Handling

N/A.

---

## 8. Policy Number Key Handling

1. LifePRO `POLICY_NUMBER` → existing QuikSpec row (same as RESSTATE / RESRVCAT).  
2. Join on stripped LifePRO number and `…C` Output key.  
3. Orphan: log if a VB policy has no QuikSpec row; do not invent a spec row. (Sim: 0 misses on 6/30 Output.)

---

## 9. Estimated Record Counts

| Metric | Count | Basis |
|--------|------:|-------|
| QuikSpec rows | 5,083 | Current Output |
| VANISH F → T (6/30) | 636 | PPOLC BILLING_REASON=VB |
| VANISH stay F (6/30) | 4,447 | Non-VB |
| VANISH T (7/31 extract) | 635 | Same rule; 9011085421 no longer VB |
| VANISHDT populated | 0 | Locked blank |

Plan mix of 6/30 VB: 659 CEN II 387; 659 CEN SR 242; 659 SR GD 5; 659 CEN SD 1; 669 CENSI 1.

---

## 10. Sample Trace (5 policies)

| Policy (QLA) | LifePRO LP | Before | After (proposed) | Status |
|--------------|------------|--------|------------------|--------|
| 9010815236C | 9010815236 VB | F | T | On vanish |
| 9011050114C | 9011050114 VB | F | T | On vanish |
| 9011069610C | 9011069610 VB | F | T | On vanish |
| 9010761639C | blank BR | F | F | #146 leftover |
| 9010760840C | blank BR | F | F | #146 leftover |

Also keep: 9010143726C / 9010148272C / 9010713704C RESRVCAT 03 / 03 / 05 unchanged (#141).

---

## 11. Risks and Unknowns

| Risk | Severity | Mitigation |
|------|----------|------------|
| Frozen 636 on a 7/31 batch | Medium | Smoke counts VB on the extract used, not a hardcoded 636 |
| Writing TRUE (4 chars) into L(1) | Medium | Emit T/F only |
| Overwriting RESRVCAT / RESSTATE | High | Enrich VANISH only; assert other columns equal |
| Mixing #22 eligible-to-vanish | High | VB only; no 659-plan list |
| Mixing #146 | Medium | Negative traces stay F |
| Later quikspec rebuild drops the flag | High | Fail-closed smoke + SMOKE_JOBS at Close (rule 14) |

---

## 12. Dependency Gate Preview

| Check | Met? |
|-------|------|
| Source file present | Yes — PPOLC 6/30 and 7/31 |
| Field definitions confirmed | Yes — quikspec.VANISH L(1) |
| Client scope clear | Yes — VB only; VANISHDT blank |
| Example policies available | Yes |

---

## 13. Recommended Risk Agent Prompt

```
Risk Agent — Issue 145 Vanish Flag (VB)

Read-only before/after: PPOLC BILLING_REASON=VB → quikspec.VANISH T else F.
Do not change production mapping.

Preserve RESSTATE, RESRVCAT, VANISHDT, #25/#26.
```

---

## 14. Recommended Development Task (Do Not Implement)

1. Add `qla_core/quikspec_vanish.py`: load PPOLC from the batch source folder; set VANISH `T` iff BILLING_REASON is VB; else `F`.  
2. Call it from the existing quikspec write hook in **both** `app.py` and `QLA_Migration/app.py` (after or beside `apply_quikspec_resrvcat`). Do not rewrite RESRVCAT logic.  
3. Update `Sync_Rulebook_quikspec.csv` note: VANISH from PPOLC VB; VANISHDT still blank.  
4. Version bump: **v58.99** in both `app.py` files.  
5. Validator: `QLA_Migration/_validate_issue145_vanish.py` — T count = VB count on resolved PPOLC; gold T; #146 F; VANISHDT blank; RESRVCAT still filled.  
6. At Close only: register fail-closed `SMOKE_JOBS` (Framework rule 14).

---

## Appendix

- Related issues: #22, #34, #132, #141, #146  
- Rulebook: `Sync_Rulebook_quikspec.csv`  
- Closed #141 must not be undone (RESRVCAT)
