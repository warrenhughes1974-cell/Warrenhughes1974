# Issue #55 — Dependency Gate

**Issue:** #55 — Unit Issues (RPU / reduced base units)  
**Framework stage:** Dependency Gate (G2)  
**Generated:** 2026-07-13  
**Model:** Cursor Grok 4.5 (locked)  
**Gate result:** **CONDITIONAL PASS** — QLAdmin mismatch proven for `018495BC`; converter mapping still not implicated  
**Updated:** 2026-07-13 (Coverage screenshot received)

---

## Decision

| Gate | Result |
|------|--------|
| G0 Intake | **Pass** |
| G1 Planning | **Pass** (source/target/trace complete) |
| G2 Dependencies | **Conditional Pass** — screenshot proves QLAdmin ≠ CSV; still need load-path confirmation (OBQ-2) |
| G3 Risk | **Ready** — quantify load vs converter blast radius; default still **No-Go for `NUMBER_OF_UNITS→MUNIT` code change** |

**Development on Sync_Rulebook / MUNIT emit must not start** until Risk confirms a converter defect (evidence so far points to **UAT DBF contents**, not CSV emit).

---

## Source data

| Check | Met? | Notes |
|-------|------|-------|
| Required LifePRO extract(s) present | **Met** | `PPBEN_PolicyBenefit_Extract_20260630.csv` |
| Extract row count > 0 | **Met** | |
| Column headers documented | **Met** | Col AC = `NUMBER_OF_UNITS` |
| Extract date/version matches batch | **Met** | 20260630 package with current Output |
| Re-extract required? | **N/A** | Source already has expected units |

## Field definitions

| Check | Met? | Notes |
|-------|------|-------|
| QLAdmin target table confirmed | **Met** | `quikridr.MUNIT` |
| QLAdmin target field semantics | **Met** | Units; face = MUNIT×MVPU |
| LifePRO source field semantics | **Met** | `NUMBER_OF_UNITS` |
| Transformation notes | **Met** | Direct map; preserve decimals |

## Client clarification

| Check | Met? | Notes |
|-------|------|-------|
| Scope boundary (expected units) | **Met** | Three policies + expected values |
| Business rule for `.00001` base | **Partial** | Assumed intentional; confirm OBQ-5 |
| UAT acceptance criteria | **Partial** | Need stored-field pass criteria |
| Proof of QLAdmin wrong value | **Met** | `018495BC` Coverage: Units **1.00000** / **3000.00000** vs CSV **.00001** / **.53000** |

## Evidence

| Check | Met? | Notes |
|-------|------|-------|
| Example policies identified | **Met** | |
| Screenshots or docx | **Met** | `evidence/018495BC_QLAdmin_Coverage_Units.png` |
| Before-state from current output | **Met** | CSV correct; **every archived `quikridr.csv` in repo** also shows `.00001` / `.53000` for this policy |

## Regression guards

| Check | Met? |
|-------|------|
| Plan preserves #25 MPOLICY padding | **Met** (no change planned) |
| Plan preserves #26 MPREM | **Met** |
| Plan does not alter unrelated rulebooks | **Met** |

---

## Open business questions

| ID | Question | Status |
|----|----------|--------|
| OBQ-1 | Exact Units shown in QLAdmin? | **Cleared for `018495BC`:** Ph1=**1.00000**, Ph2=**3000.00000** |
| OBQ-2 | Which QUIKRIDR load / DBF path produced those values? | **Open** — values **never appear** in repo conversion CSVs |
| OBQ-3 | `018499CC` / `018510C` same pattern in this UAT DB? | **Open** (helpful, not blocking Risk) |

---

## Recommended status (tracking sheet)

**Ready for Risk Review** (load/UAT mismatch proven; converter emit not implicated)

Suggested next check:

> Reload `Output/quikridr.csv` into the UAT QUIKRIDR for `018495BC` and re-open Coverage. Expected Units: Ph1 **0.00001**, Ph2 **0.53**. If still 1 / 3000 after reload, capture the import tool/steps used (column map).

---

## Next agent

| If… | Then… |
|-----|--------|
| User says **Proceed to Risk Agent** | Risk (Grok 4.5) — formal No-Go for converter vs Go for UAT reload / import-path investigation |
| Reload fixes Units | Closure (converter N/A; UAT reload) |
| Reload fails / import remaps units | Risk + possible import/DBF tooling only — still avoid rulebook MUNIT change |

**Do not** switch to Composer 2.5 for Sync_Rulebook/`app.py` MUNIT emit changes on current evidence.
