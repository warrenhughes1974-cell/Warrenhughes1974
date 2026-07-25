# Issue #108 — Dependency Gate

**Issue:** #108 — Statuses and NFO (ETI/RPU) conversion conformance
**Framework stage:** Dependency Gate (G2)
**Date:** 2026-07-25
**Result:** **CONDITIONAL PASS** — 108A, 108B, 108C, 108D, 108F, 108G cleared to Risk; **108E BLOCKED**

> **Revised 2026-07-25 (same day).** The original gate blocked **108F** pending a canonical re-batch to settle the `MPOLICY` key convention. That question has since been answered **by inspection — no batch required** — and 108F is **unblocked and reclassified as a confirmed code defect**. See §"108F — resolved" below. The original blocker text is retained there for audit.

---

## Gate decision by track

| Track | Subject | Gate | Reason |
|---|---|---|---|
| **108A** | `MSAVE*` blanked on NFO | **PASS** | Spec explicit; population measurable; self-contained |
| **108B** | `MAGE` attained age + `MLASTANN` accuracy | **PASS** | Both inputs 400/400 populated; spec explicit |
| **108C** | ETI `MPREM` → 0.00 | **PASS** | Spec explicit and confirmed by worked example |
| **108D** | PUA `MPHSTAT` 41 → 54 on NFO | **PASS** (status only) | Status change cleared; **units fold excluded** pending Q1 |
| **108E** | Rider terminations + ETI expiry | **BLOCKED** | Awaiting SME — Q2, Q3, Q4 |
| **108F** | `MNFOPT` enrichment + #72 force | **PASS** (revised) | Root cause confirmed as a regression from Issue #2 v58.29; sized exactly |
| **108G** | Governance checks + de-forcing | **PASS** (build), **CONDITIONAL** (enable) | Checks can be built; check 2b must exclude `1SALML`/`1SALMI` until Q2 answers |

---

## Source data

| Check | Status |
|---|---|
| Required LifePRO extracts present in `QLA_Migration/Source/` | **Met** — PPOLC, PPBEN, PPBENTYP all present |
| Extract row count > 0 | **Met** — PPBENTYP 7,003 rows; 4,346 policies with an NFO election |
| Column headers documented | **Met** |
| Extract date matches batch under test | **Met** — all `20260630`; Output emitted 2026-07-23/24 |
| Re-extract required | **No** — and the re-batch originally proposed for 108F is no longer needed (resolved by inspection) |

> `PPOLC_PolicyMaster_Extract_20260630.csv` is not UTF-8 clean (byte `0xFF` at offset 740). Read with `latin-1`. Noted, not a blocker.

## Field definitions

| Check | Status |
|---|---|
| QLAdmin target table confirmed | **Met** — `quikmstr`, `quikridr` |
| QLAdmin target field semantics confirmed | **Met** — `QLAdmin_ETI_RPU.docx` is an authoritative, field-level specification |
| LifePRO source field semantics confirmed | **Met** for `MPAIDTO`, `MPHDOB`, `ISSUE_AGE`, `NON_FORFEITURE`; **Missing** for `NUMBER_OF_UNITS` on already-NFO policies (Q1) |
| Transformation notes identified | **Met** — age, duration, blank conventions in Planning §6 |

> Documentation nit for the client reply: the specification writes `MCVO`; the schema field is `MCV0`.

## Client clarification

| Check | Status |
|---|---|
| Scope boundary agreed | **Partial** — conversion lands NFO *state*; it does not replay the ETI/RPU *transaction* (`QuikPolx`, `QuikAudt`, `QuikDocs`, `QuikBene`). Confirm with Robert |
| Business rule for edge cases | **Missing** — Q1 (units fold), Q5 (RPU `MPREM`), Q6 (save-field convention, Greg) |
| Retention / filtering rules | **N/A** |
| UAT acceptance criteria stated | **Missing** — CV/reserve movement on 400 policies needs an agreed tolerance before reload |

## Evidence

| Check | Status |
|---|---|
| Example policies identified | **Met** — client `010367133C`; our traces `9010391355C`, `9010407670C`, `9010149295C`, `9018313AC`, `9010820645C` |
| Client artifacts support the claim | **Met** — docx + two before/after workbooks |
| Before-state measurable from current Output | **Met** for all tracks (108F measurable once the key rule was confirmed — see §108F resolved) |

## Regression guards

| Check | Status |
|---|---|
| Preserves Issue #2 `MPOLICY` identity (source + `C`, width 11) | **Met** — no track touches the key. Issue #25 width-10 is superseded by #2 and is not a live contract |
| Preserves Issue #26 `MPREM` mapping | **Met** — 108C narrows to ETI phase-1 only; RPU and all non-NFO rows untouched |
| Preserves Issue #55 `MUNIT` floor | **Met** — no units change in scope |
| Does not alter unrelated rulebooks | **Met** — no rulebook edits proposed |
| Closed/UAT-ready issues disturbed | **#60 and #72 require validator amendments.** #60 is UAT-ready (v57.85) and #72 is Ready for Validation (v57.91); neither is a client-closed gate, so no closure is broken |

---

## 108F — resolved (revised 2026-07-25)

### Original blocker (retained for audit)

> Emitted `MPOLICY` matches neither `Master_Crosswalk.csv` column. Overlap with `New_Value` = 0; with `Old_Value` = 0; with `Old_Value + "C"` = 5,083 of 5,083. 4,954 of 5,083 keys are 11 characters against Issue #25's 10-character rule. We cannot distinguish a code defect from a misconfigured batch. **Action:** re-run a canonical full batch and re-measure.

### Resolution — no batch required

The emitted key convention is **correct, current, and intentional**. Issue **#2** ("11 Character Policy Number", closed 2026-07-23 at **v58.29**, commit `1c7fc0a`) deliberately replaced the strip-9 crosswalk with source + trailing `C`, right-justified to 11:

```
qla_core/normalize_utils.py:23–46
"Issue #2: keep source policy number, append C, right-justify to 11 characters.
 Supersedes Issue #25 (10-char pad after strip-9 crosswalk)."
```

`QLA_Migration/app.py:3950` states it plainly: `# Issue #2: source + C (no strip-9 crosswalk)`.

**Correction to the original gate:** the 11-character keys do **not** violate Issue #25 — Issue #25 is formally superseded and documented as such in `Issue_2_Resolution_Summary.md` ("Issue #25 width-10 contract — **superseded**"). The Output under test is a valid v58.29+ batch. `Master_Crosswalk.csv` `New_Value` (`010143726C`) is the retired convention.

### What Issue #2 missed

Issue #2 realigned the parallel identity paths it knew about (claims, prmh, loan, benh, isrr, memo). It did **not** update the two places that still resolve keys through the retired crosswalk columns:

| Path | Location | Built from | Live keys resolved |
|---|---|---|---:|
| `reverse_cw_map` → PPBENTYP `MNFOPT`/`MDIVOPT` enrichment | `app.py:6118`, consumed `app.py:7695` | crosswalk `New_Value` | **0 of 5,083** |
| `cw_map` → Issue #71 phase-1 provisional status cache | `app.py:7867` | crosswalk `New_Value`, then re-formatted | **0 of 5,194** |

The second path double-appends the suffix: `cw_map['9010143726']` returns `010143726C`, which `format_qladmin_mpolicy` then turns into `010143726CC` — a key that exists nowhere in the Output.

**Verdict: 108F is a confirmed code defect and a bounded regression introduced by Issue #2 v58.29.** `reverse_cw_map` has exactly one consumer, so the blast radius is three fields, not the whole conversion.

### Exact sizing (exact-key join, `MPOLICY` minus trailing `C`)

| Metric | Count |
|---|---:|
| Policies matched to a PPBENTYP election | 4,346 of 5,083 |
| **`MNFOPT` values 108F would populate** | **4,112** |
| In-force policies (`MSTATUS` < 44) holding an election, emitting 0 | **1,933 of 1,933** |
| NFO policies where the election disagrees with the #72-forced value | **111 of 234** |
| `MDIVOPT` currently zero fleet-wide | 5,083 |

### Consequential finding — Issue #71 is inert

The same defect means the Issue #71 provisional-status cache never populates, so the phase-1 `MPHSTAT` inherit silently falls back to `_qm_status_cache` (the **post-#49** status) — precisely the behaviour Issue #71 was written to prevent. #71 is marked closed. **Raise as a separate issue; do not fold into #108.**

### Remaining action

None gating. 108F advances to Risk with the fix direction: key the PPBENTYP cache off `src_row['POLICY_NUMBER']` directly rather than through `reverse_cw_map`. Retiring or regenerating `Master_Crosswalk.csv` `New_Value` is a separate cleanup.

---

## Blockers

### 108E — SME confirmation required

| Question | Population | Owner |
|---|---|---|
| Q2 — is the `1SALML` (zero-unit phase 1) / `1SALMI` (face on phase 2) structure intended? | 147 rows, 77 of them RPU | Robert / source |
| Q3 — should the `9595WP` and `967ADB` riders on 4 ETI policies terminate at 54? | 5 rows, 4 policies | Robert / source |
| Q4 — are the 92 ETI policies with expiry at attained age ≥ 95 carrying an unrecalculated expiry? | 92 of 206 | Robert / source |

### 108D — partial

Status change (41 → 54) is cleared. The **units fold is not** — Q1 must be answered first, because if LifePRO has already folded PUA into the base, adding again double-counts the face amount.

---

## Recommended status update

**Open — Risk (108A–108D, 108F, 108G) / Blocked — Awaiting Client Clarification (108E).**

Per the framework's Pre-Development Auto-Chain, the cleared tracks advance to Risk in this session. 108E does not advance and is excluded from any Development approval.

---

## Gate G2 checklist

- [x] Dependency gate document published
- [x] Status recorded per track; blocked tracks do not advance
- [x] Tracking sheet row prepared
- [x] No code changes
