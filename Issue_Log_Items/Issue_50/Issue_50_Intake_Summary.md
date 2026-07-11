# Issue #50 — Intake Summary

**Issue:** #50 — Policy Notes Missing  
**Date:** 2026-07-11  
**Framework stage:** Intake complete (G0)  
**Status:** Approved → Planning  
**Owner:** Conversion (Warren) · **Reporter:** Eric  
**Business status:** No-Go for Development until G1 + G2 + G3  

**Model:** Cursor Grok 4.5 (locked Intake stage)

---

## 1. Client / business symptom (verbatim + normalized)

**Issue log (verbatim):**

> 50 Active Policy Notes Missing Policy Notes are not pulling into QLAdmin. Example: Policy 018495BC does not have note in QLAdmin but has note in LifePRO. Note is on PNOTE_PolicyNotes_Extract_20260630. Issue may be limited to SAL forms (Policies that were not pulling into QLAdmin correctly previously) 7/11/2026 No-Go Eric Warren

**Normalized:**

LifePRO policy notes present on `PNOTE_PolicyNotes_Extract_20260630` are not visible (or not fully visible) in QLAdmin for at least policy **018495BC**. Client suspects concentration on **SAL** product forms that previously failed to load into QLAdmin correctly.

**Example policy:** `018495BC` (LifePRO `9018495B`, plan **1SALML** + rider **1SALMI**)

---

## 2. Suspected domain

| Layer | Path / table | Role |
|-------|--------------|------|
| Source | `QLA_Migration/Source/PNOTE_PolicyNotes_Extract_20260630.csv` | LifePRO policy notes |
| Source (companion) | `PENSE_ENSData_Extract_20260630.csv` | ENS messages (same QUIKMEMO pipeline) |
| Converter | `qla_core/quikmemo_converter.py` | PNOTE+PENSE → QUIKMEMO |
| Enrichment | Issue #21J `append_issue21j_conversion_memos` | Prepends `[CONVERSION]` modal-factor memo |
| Target | `quikmemo.csv` / `quikmemo_uat_dbf/` (`MEMOKEY`, `MEMOTEXT`) | QLAdmin Memo tab |

**Domain:** Memo / policy notes (`quikmemo`) — **not** rates, claims, or premium mapping.

---

## 3. Intake evidence (measured — Planning formalizes)

| Check | Result |
|-------|--------|
| PNOTE extract present | Yes — `Source/PNOTE_PolicyNotes_Extract_20260630.csv` |
| Example on crosswalk | `9018495B` → `018495BC` |
| Example in `quikmstr` / `quikridr` | Yes — SAL ML base + MULTPL rider |
| Example in current `quikmemo` | Yes — `MEMOKEY='  018495BC'` (10-char #25 pad) |
| Current memo content | `[CONVERSION]` (v57.46) + `[PNOTE]` **Seq 2** “Last Known Address” only |
| LifePRO note client likely means | **Seq 1** text: “Vincent J. Bauerly, if living otherwise to: Ethel R. Bauerly.” |
| Seq 1 in converted output? | **No** — row dropped by CSV reader (`on_bad_lines='skip'`) because LINE text contains an **unquoted comma** |
| Fleet parse loss | **1,939 / 7,976** PNOTE data rows malformed field-count; **374** policies lose **all** notes; **1,043** lose at least one row |
| SAL intersect | **130 / 163** SAL policies have ≥1 malformed PNOTE row; **74** SAL policies lose all PNOTE rows |
| Crosswalk orphans | **0** for current convert path |

Evidence: `Issue_Log_Items/Issue_50/evidence/` · script: `scripts/research_issue50_pnote_parse.py`

---

## 4. In scope / out of scope (first pass)

### In scope

- Recover PNOTE rows currently dropped due to unquoted commas in `LINE_*` fields
- Preserve Issue #21M / #21M-FU grain (one row per `MEMOKEY`, merged segments)
- Preserve Issue #25 `MEMOKEY` padding and #21J `[CONVERSION]` prepend behavior unless Risk explicitly changes display order
- Validate example `018495BC` emits Bauerly note + Last Known Address
- Quantify SAL vs fleet impact for Risk

### Out of scope (unless Planning expands)

- Redesigning QUIKMEMO schema or Memo tab UI
- Changing PENSE ENS filter (`ENS_KEY_TYPE=P`)
- Reopening #28 PLAN catalog or historical “SAL not loading” policy-master defects (policy **is** present now)
- Wholesale rewrite of `quikmemo_converter.py`

---

## 5. Related issues

| Issue | Relationship |
|-------|----------------|
| **#21M / #21M-FU** | Greenfield QUIKMEMO + one-row-per-MEMOKEY merge — **must not regress** |
| **#21J** | `[CONVERSION]` modal memo prepended first — present on example; may affect what UAT “sees” first |
| **#25** | `format_qladmin_mpolicy` for `MEMOKEY` — confirmed match on example |
| **#28** | SAL PLAN catalog — prior “not pulling” context; policy now converts |
| **#26** | Unrelated (MPREM) |

---

## 6. Artifact inventory

| Artifact | Status |
|----------|--------|
| Issue log row (#50 Active Policy Notes Missing) | Provided |
| Example policy `018495BC` | Provided |
| `PNOTE_PolicyNotes_Extract_20260630.csv` | Present |
| `PENSE_ENSData_Extract_20260630.csv` | Present |
| Current `Output/quikmemo.csv` + `quikmemo_uat_dbf/` | Present |
| QLAdmin Memo-tab screenshot for `018495BC` | **Missing** (soft) |
| Client confirmation of expected note text | **Missing** (soft — Bauerly text is best candidate) |

---

## 7. Immediate blockers visible at intake

| Blocker | Blocks? | Notes |
|---------|---------|-------|
| Source extract | No | Present |
| Example traceability | No | Root cause measurable |
| Screenshot of QLAdmin Memo tab | Soft | Useful for UAT; not required to plan parser fix |
| Scope: parser-only vs also reorder `[CONVERSION]` | Soft for Planning | Risk may decide display-order separately |

---

## 8. Severity / owner / priority

| Field | Value |
|-------|--------|
| Severity | **High** — 1,939 PNOTE rows dropped fleet-wide; 374 policies with zero recovered notes; SAL heavily hit (130/163) |
| Owner | **Conversion** |
| Priority | Active / No-Go until gates |
| Duplicate of open item? | **No** — #21M delivered pipeline; this is a **parse-loss defect** inside that pipeline |

---

## 9. G0 checklist

- [x] Issue folder created under `Issue_Log_Items/Issue_50/`
- [x] Intake summary written
- [x] Example policies listed (`018495BC`)
- [x] Owner and priority assigned
- [x] No code or rulebook changes made

**Recommended next status:** **Planning**  
**Next agent:** Planning Agent (Cursor Grok 4.5)
