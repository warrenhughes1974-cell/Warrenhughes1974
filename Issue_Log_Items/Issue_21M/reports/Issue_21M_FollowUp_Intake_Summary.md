# Issue 21M-FU — Intake Summary (Multiple Memo Display Defect)

**Issue ID:** 21M-FU (follow-up to closed 21M greenfield)  
**Framework stage:** Intake Agent (Stage 1)  
**Status:** Intake complete → Planning / Research in progress  
**Generated:** 2026-06-24  
**Engine version at report:** v57.33  
**Owner:** Conversion (investigation); Client (UAT confirmation required)

---

## Issue Title

QLAdmin Memo tab displays only one memo per policy although QUIKMEMO contains multiple rows for the same MEMOKEY.

---

## Client Symptom

**Verbatim (normalized):**

- Policy **010335038C** has **two rows** in `QUIKMEMO.DBF` where `MEMOKEY = 010335038C`.
- QLAdmin **Policy Display → Memo tab** shows **only one** `[PNOTE]` entry.
- The second PNOTE is **not visible** in QLAdmin.

**Example policy:** `010335038C`

---

## Domain

| Item | Value |
|------|-------|
| **Domain** | Policy memo conversion / QLAdmin UI read behavior |
| **QLAdmin table** | `QUIKMEMO` (`MEMOKEY`, `MEMOTEXT`) |
| **LifePRO sources** | PNOTE (policy notes); PENSE not involved for this example |
| **Conversion component** | `qla_core/quikmemo_converter.py`, `quikmemo_dbf_generator.py` (v57.32–v57.33) |

---

## Severity and Priority

| Attribute | Assessment |
|-----------|------------|
| **Severity** | **High** — if systemic, ~79% of converted policies (3,466 / 4,380 MEMOKEYs) have multiple memo rows that may not display |
| **Priority** | **UAT blocker** for Issue 21M sign-off until root cause and correction path are confirmed |
| **Owner** | Conversion (research); Client (confirm QLAdmin native behavior and which memo text is visible) |

---

## Artifact Inventory

| Artifact | Provided? | Location |
|----------|-----------|----------|
| Client defect report | Yes | User query / UAT observation |
| Example policy | Yes | `010335038C` |
| QUIKMEMO CSV output | Yes | `QLA_Migration/Output/quikmemo.csv` |
| QUIKMEMO DBF + DBT | Yes | `QLA_Migration/Output/quikmemo_uat_dbf/` |
| QLAdmin Help extract | Yes (repo) | `docs/claims_conversion_reference/QLAdmin_Help.pdf`, `_qladmin_table_defs.txt`, `_qladmin_pdf_extract.txt` |
| QLAdmin screenshot of Memo tab | **Missing** | Needed to confirm which of two memos displays |
| Native QLAdmin multi-memo reference DBF | **Missing** | No production `quikmemo.dbf` sample in repo |
| Prior 21M closure docs | Yes | `Issue_21M_Resolution_Summary.md`, Risk/Validation reports |

---

## In Scope / Out of Scope

### In scope (this follow-up)

- Determine **why** QLAdmin shows one memo when DBF has multiple rows
- Evaluate hypotheses 1–8 from client research brief
- Recommend correction approach **without implementing**
- Trace policies: `010335038C` + ≥5 multi-memo + ≥2 single-memo samples

### Out of scope (guardrails)

- **No code changes** to converter, DBF generator, rulebooks, or batch
- **No** changes to Issue #25 MPOLICY / MEMOKEY padding
- **No** changes to Issue #26 MPREM logic
- **No** DBF/DBT packaging changes until root cause approved
- **No** assumption that concatenation is correct until QLAdmin behavior is proven

---

## Related Issues

| Issue | Relationship |
|-------|--------------|
| **21M** (parent) | Greenfield QUIKMEMO pipeline — **Ready for Client UAT** at v57.33; this defect blocks full UAT acceptance |
| **#25** | MEMOKEY uses `format_qladmin_mpolicy()` — must not alter |
| **#26** | Unrelated (MPREM) |

---

## Immediate Blockers Visible at Intake

1. **Unknown which memo QLAdmin displays** for `010335038C` (Seq 2 “LETTER & CHECK…” vs Seq 1 “PB = PATSY MILLER…”).
2. **No native QLAdmin reference** in repo showing whether manually added memos create one or many `QUIKMEMO` rows.
3. **QLAdmin application source** not available — index SEEK / scan behavior cannot be verified in code.

---

## Gate G0 — Intake Complete

- [x] Issue folder exists (`Issue_Log_Items/Issue_21M/`)
- [x] Intake summary written
- [x] Example policy listed
- [x] Owner and priority assigned
- [x] No code or rulebook changes made

**Next stage:** Planning / Research → `Issue_21M_Multiple_Memo_Display_Research_Report.md`
