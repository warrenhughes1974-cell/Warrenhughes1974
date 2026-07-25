# Issue #108 — Intake Summary

**Issue:** #108 — Statuses and NFO (ETI/RPU) conversion conformance
**Date:** 2026-07-25
**Framework stage:** Intake complete (G0)
**Status:** Open — Planning
**Owner:** Conversion (Warren) + Client/SME (Robert De Sarro) for source confirmations
**Priority:** High — affects cash values and reserves on the entire NFO book (400 policies)
**Raised by:** Robert De Sarro, email 2026-07-25

---

## Client symptom (verbatim)

> For conversion purposes, I do not think we should put rules in the generic conversion program to force the policy and rider statuses. There should be a crosswalk of some kind to convert policy level and coverage level statuses from the source system to QL. After that is done, in the data governance or data validation program, I would add something to check for inconsistencies to include:
>
> Terminated policy status, QuikMstr:MSTATUS > "50", with an active coverage status, QuikRidr:MPHSTAT < "50" (this would be wrong as if the policy status is terminated, all coverages should be terminated).
>
> NFO policy status, QuikMstr:MSTATUS of "44" or "45" (ETI or RPU), with (1) phase 1 coverage status that does not equal the policy status (this would be wrong as the phase 1 status should match the policy status of ETI or RPU), and (2) phases 2+ with an in-force coverage status, QuikRidr:MPHSTAT < "50" (this could be wrong as typically all other coverages should be terminated, this should be validated with the source system to see if it is legit or not).
>
> Active policy status, QuikMstr:MSTATUS < "44", with no active coverages, QuikRidr:MPHSTAT > "50" (this would be wrong as the policy cannot be in-force with no in-force coverage).
>
> I don't think these have to match, but might be good to at least check for and question if you find any policies where the NFO selection on the policy does not match the policy status, where the policy status is "44" or "45". I.e., if the policy status, QuikMstr:MSTATUS, is "44" and the NFO selection, QuikMstr:MNFOPT, is not "2" (ETI), or the policy status, QuikMstr:MSTATUS, is "45" and the NFO selection, QuikMstr:MNFOPT, is not "3" (RPU). If this is found, should probably confirm with the source system if this is legit or not.
>
> [...] FYI. The "save" fields should maybe be empty for conversion purposes, not sure if you can see if those were in Chris' code that I gave you to see what he did with them. Or maybe default to the current values, but for ETI or RPU, those should be the prior values (which we may not have) or maybe left empty. You can also ask Greg how he handled those.

---

## Normalized statement

Two distinct asks:

1. **Architectural.** Statuses should be crosswalk-driven in the converter; consistency should be enforced by data governance, not by forcing rules inside `app.py`.
2. **Conformance.** Converted ETI (`MSTATUS` 44) and RPU (`MSTATUS` 45) policies must land in the same field state QLAdmin would produce, per the attached specification.

---

## Client artifacts received

| Artifact | Location | Role |
|---|---|---|
| `QLAdmin_ETI_RPU.docx` | `docs/research/Conversion - Statuses, NFO/` | Authoritative ETI/RPU field specification |
| `Example_ETI.xlsx` | `docs/research/Conversion - Statuses, NFO/` | Worked before/after: QuikMstr + QuikRidr, policy `010367133C` |
| `Example_RPU.xlsx` | `docs/research/Conversion - Statuses, NFO/` | Worked before/after: QuikMstr + QuikRidr, policy `010367133C` |
| Client-side copy | `M:\QL32\Support\SupportTools\Xample_NFO_ETI_RPU` | Referenced in email; not required |

Nothing material is missing for the conversion-side work. Three items require SME/source answers (see Dependency Gate).

---

## Affected QLAdmin tables

| Table | Role |
|---|---|
| `quikmstr` | `MSTATUS`, `MNFOPT`, `MPAIDTO` |
| `quikridr` | `MPHSTAT`, `MAGE`, `MLASTANN`, `MPAYUP`, `MEXPRY`, `MUNIT`, `MPREM`, `MCV0/1/2`, `MSAVEAGE`, `MSAVEUNIT`, `MSAVEVPU`, `MSAVEPREM`, `MSAVESTAT` |
| `quikloan` | Loan balance on NFO policies (1 exception) |
| `quikdvdp` / `quikdvpr` | Dividend accumulations on NFO policies (already clean) |
| Data governance | New cross-table item — no QuikRidr status item exists today |

---

## Population under review

Measured against `QLA_Migration/Output/` as at 2026-07-25 (`quikmstr.csv` 2026-07-23, `quikridr.csv` 2026-07-24, app `v58.31`).

| Metric | Count |
|---|---:|
| Policies in `quikmstr` | 5,083 |
| Coverages in `quikridr` | 6,934 |
| `MSTATUS` = 44 (ETI) | 206 |
| `MSTATUS` = 45 (RPU) | 194 |
| **NFO policies in scope** | **400** |

---

## Work tracks (first pass)

| Track | Subject | Population | Type |
|---|---|---:|---|
| **108A** | Phase-1 `MSAVE*` fields carry post-NFO values | 400 | Conversion defect |
| **108B** | Phase-1 `MAGE` = issue age, not attained age at paid-to; `MLASTANN` off-by-one and non-deterministic | 400 / 167 | Conversion defect |
| **108C** | ETI phase-1 `MPREM` not zeroed | 204 of 206 | Conversion defect |
| **108D** | PUA riders on NFO policies at status 41, not 54; units not folded | 27 | Conversion defect (rule collision with #60) |
| **108E** | Non-PUA riders in force on NFO policies; ETI `MEXPRY` may be unrecalculated | 82 rows / 92 policies | **Source question** |
| **108F** | `MNFOPT` — PPBENTYP election enrichment inert; #72 force should be a warning | 1,933 / 400 | Conversion defect + policy change |
| **108G** | Governance: add Robert's four cross-table checks; retire in-program forcing | Fleet | Architecture |

---

## In scope

- `quikridr` phase-1 field conformance for `MSTATUS` 44/45 policies
- `quikmstr.MNFOPT` derivation and the Issue #72 force
- PUA rider treatment when the base phase is on NFO
- New data governance item carrying Robert's four consistency checks
- Documented inventory of in-program status forcing, with a retirement recommendation

## Out of scope (this issue)

- Recomputing `MCV0/1/2` inside the converter. Robert's specification has QLAdmin computing these from plan NFO mortality and interest (`QuikPlcv`); our job is to supply correct driver fields. Track 108B is the enabler, not a CV calculation.
- `MDIVOPT` fleet-zero. Discovered during intake and shares the 108F root cause, but it is a dividend-option issue, not NFO. Raise separately.
- Emitted `MPOLICY` key convention. See Dependency Gate — the Output under test does not match `Master_Crosswalk.csv` `New_Value`, which gates 108F measurement.
- ETI/RPU **transaction** processing in QLAdmin (`QuikPolx`, `QuikAudt`, `QuikDocs`, `QuikBene` entries). Robert's document describes the live transaction; conversion lands the resulting state, it does not replay the event.

---

## Related issues

| Issue | Status | Relationship |
|---|---|---|
| **#13** | CLOSED v57.48 | MSTATUS composite key — `T` wins over `PAID_UP_TYPE`. Origin of the in-program interceptor Robert objects to |
| **#21A** | CLOSED v57.47 | PPBENTYP `BF_NON_FORFEITURE` enrichment — **appears inert in current Output; re-verify** |
| **#44** | CLOSED v57.60 (Phase A only) | Phase B (suppress QuikLoan on 44/45) was withdrawn — residue in 108E |
| **#49** | CLOSED v57.71 | MSTATUS overridden from first active later phase — inverts Robert's model |
| **#57** | CLOSED v57.78 | `NF_3/4/5 → 1/2/3` mapping — **re-verify, same inert-enrichment concern** |
| **#59** | Shipped v57.84 | Hardcoded 7-policy allowlist inside the MSTATUS interceptor |
| **#60** | UAT-ready v57.85 | PUA → `MPHSTAT` 41 when base < 50 — **direct collision with 108D** |
| **#72** | Ready for Validation v57.91 | Forces `MNFOPT` from `MSTATUS` — **contradicted by this email; see 108F** |
| **#76** | CLOSED v57.93 | Phase-1 `MPAYUP`/`MLASTANN` on 44/45 — correct concept, arithmetic defect in 108B |

**Regression flag:** #21A, #57, #60, #72 and #76 are all closed or UAT-ready and are all touched by this issue. #60 and #72 will need their validators amended, not just re-run.

---

## Immediate blockers visible at intake

1. ~~**Output key convention.**~~ **Resolved 2026-07-25, same day.** Emitted `MPOLICY` (`9010143726C`, 11 chars) has zero overlap with `Master_Crosswalk.csv` `New_Value` (`010143726C`, 10 chars). This is the mechanical cause of the inert PPBENTYP enrichment. Settled by inspection, no re-batch: Issue **#2** (v58.29, 2026-07-23) intentionally adopted source + `C` at width 11 and **superseded** Issue #25. The Output is a valid batch; the crosswalk column is retired. 108F is therefore a confirmed code defect — a bounded regression from Issue #2 — and is unblocked.
2. **Three source questions** for Robert (units fold, `1SALMI` riders, ETI expiry) — detailed in the Dependency Gate.
3. **Save-field convention** needs Greg's input per Robert's email.
4. **New, spun out of the above:** Issue #71's provisional-status cache resolves **0 of 5,194** keys for the same reason, so #71 is inert and phase-1 `MPHSTAT` inherits the post-#49 status. Raise as its own issue; not part of #108.

---

## Intake disposition

Open with seven tracks. Tracks 108A–108D and 108G are self-contained and measurable from current Output. Track 108E is a source question. Track 108F is gated on the key-convention blocker.

Proceed to Planning.
