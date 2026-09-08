# Issue #161 — Intake Summary

**Issue:** #161 — POA Information Missing (`quikclid.MRELATION` wrong code: `PW` vs `POFA`)
**Framework stage:** Intake Agent (G0)
**Status recommendation:** Intake Complete → Planning → Dependency Gate → Risk
**Generated:** 2026-09-08
**Owner:** Conversion — Assigned: Warren
**Priority:** No Go — Eric, raised 2026-09-03

---

## Client symptom (verbatim)

"Power of Attorney information is not in QLAdmin. Examples of active policies with POAs on file in LifePRO are 9010442216, 9010451650, and 9011045619."

## Symptom (normalized)

QLAdmin's Policy Editor → **Names** tab → **Other Information** panel shows no POA entry for active policies that have a Power-of-Attorney person on file in LifePRO. Confirmed by screenshot for `9010442216C`: panel empty, even though a relationship record for the POA client already exists in `quikclid`. Root cause is a **value-translation defect**, not a missing extract or missing conversion step: LifePRO's `RELATE_CODE=PW` is being passed through unchanged into `quikclid.MRELATION` as `PW`, but QLAdmin's Other-Information panel only recognizes `POFA` as the Power-of-Attorney code (confirmed live in the app's own relation-type dropdown). Since `PW` isn't a code QLAdmin recognizes there, the row is present in the table but invisible on screen.

## Example policies

| Policy | Client (POA person) | Current `MRELATION` (wrong) | Required `MRELATION` |
|---|---|---|---|
| 9010442216C | 712072 — MARLYS VANDER WAL | `PW` | `POFA` |
| 9010451650C | 712326 — TIMOTHY MOUNTAIN | `PW` | `POFA` |
| 9011045619C | 591432 — ANDREW MAZZURCO | `PW` | `POFA` |

All three confirmed present (as `PW`) in both `QLA_Migration/Output/quikclid.csv` and the **live current QLAdmin build** DBF at `Q:\CSO\CSO_Test_6_30_2026\quikclid.dbf` (2026-09-02).

## Suspected domain

Client-relationship value translation — `QLA_Migration/Mapping/Master_Value_Translation.csv` (row: `PW,PW`) feeding `quikclid.MRELATION` via `QLA_Migration/Configs/Sync_Rulebook_quikclid.csv` (`RELATE_CODE → MRELATION`). Approved-code authority list at `data_governance/config/policy_code_authorities.csv` (row: `MRELATION,PW,PW relationship`) also reflects the wrong target code.

## In scope (first pass)

- Correct the value-translation target for LifePRO `RELATE_CODE=PW` from `PW` to `POFA` in `Master_Value_Translation.csv`
- Update the approved-code authority entry in `policy_code_authorities.csv` (`MRELATION,PW,...` → `MRELATION,POFA,Power of Attorney relationship`)
- Re-emit `quikclid` and confirm all fleet-wide PW-sourced rows (**412 rows / 270 policies**, per `claims_analysis/output/relationship_code_frequency.csv`) now emit `MRELATION=POFA`
- Fail-closed validator confirming no `MRELATION=PW` rows remain in Output and `POFA` count matches source PW count
- Publish `Output/Test_Validation/quikclid.csv` on PASS

## Out of scope (first pass)

- Any other unmapped/low-confidence `MRELATION` codes in the authority list (e.g. `O1` → "O1 relationship") — not reported by client, not touched
- POA metadata not carried by `quikclid`'s 4-field schema (effective date, `COMM_PCNT` scope, document-on-file flag) — `quikclid` has no columns for these; flag as a possible follow-on enhancement only if Eric asks
- `quikbenf` — intentionally excludes PW/POFA by design (beneficiary-only table); not changing that filter
- Any DBF Append Tool / template changes — Append Tool copies whatever `quikclid.csv` contains; no template schema change needed since `MRELATION` is already a generic 4-char field

## Related issues

| Issue | Relationship |
|---|---|
| #30 | Closed — RNA `IDENTIFYING_ALPHA` → `quikclid` keying; enabled IN/PO/PA and all `RELATE_CODE` rows including PW. This issue builds on that pipeline, does not reopen it. |
| #21I | Beneficiary (`quikbenf`) scope — PW/POFA intentionally excluded there; not affected |
| #159 | Closed, unrelated (L10/L14 `MUWCLASS`) — numbering collision only, no functional relationship |

## Immediate blockers

None identified for Intake. Source RNA extract already on file and already used by the existing rulebook; no new client data request needed. Root cause and fix location are already confirmed via live-build DBF read + Warren's QLAdmin screenshot.

## Artifact inventory

| Have | Missing |
|---|---|
| RNA/PRELSA extract with `RELATE_CODE=PW` rows for all 3 example policies | — |
| Current `quikclid.csv` / `quikclid.dbf` (Output + live build) confirming `PW` rows present | — |
| Live QLAdmin screenshot confirming valid code is `POFA`, not `PW` | — |
| `Master_Value_Translation.csv` + `policy_code_authorities.csv` — exact rows to change identified | — |
| Fleet-wide PW row count (412 rows / 270 policies) from `claims_analysis/output/relationship_code_frequency.csv` | — |

## Owner / priority

Conversion. No Go priority (client). No client data request — proceeding on internal evidence + Warren's screenshot confirmation.
