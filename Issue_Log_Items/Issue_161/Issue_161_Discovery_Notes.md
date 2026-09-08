# Issue #161 — Discovery Notes

**Issue:** #161 — POA Information Missing (client short name: "POA Information Missing")
**Framework stage:** Discovery (Stage 0 — Search & Discuss)
**Status:** Discovery complete → Proceed to Intake (user-approved 2026-09-08)
**Generated:** 2026-09-08
**Raised by:** Eric — 2026-09-03 — Priority: No Go — Assigned: Warren

**Numbering note:** Client-provided row referenced "159" in the raw log line, but repo Issue #159 is already **Closed** for an unrelated defect (L10/L14 `quikridr.MUWCLASS` reserve remap — see `Issue_Log_Items/Issue_159/`). This item is assigned **new issue ID #161** (next free ID; #160 is also taken by the PUA Terminal Status Remap issue).

---

## Client symptom (verbatim)

"Power of Attorney information is not in QLAdmin. Examples of active policies with POAs on file in LifePRO are 9010442216, 9010451650, and 9011045619."

## Investigation summary

1. **LifePRO source of POA:** Not a dedicated POA table. It is a row on the **RNA/PRELSA** extract (`RelationshipNameAddress_Extract_YYYYMMDD.csv`) with **`RELATE_CODE = PW`**. Documented in `claims_analysis/config/relationship_code_semantics.json` ("PW" = "Power-of-Attorney"). Fleet-wide: **412 PW rows across 270 policies** (`claims_analysis/output/relationship_code_frequency.csv`).

2. **QLAdmin conversion target:** `RELATE_CODE=PW` → `quikclid.MRELATION` via `QLA_Migration/Configs/Sync_Rulebook_quikclid.csv` line 5 (`RELATE_CODE,MRELATION` direct pass-through) → value-translated via `QLA_Migration/Mapping/Master_Value_Translation.csv` line 49: **`PW,PW`** (passthrough, unchanged) → approved in `data_governance/config/policy_code_authorities.csv` line 58: **`MRELATION,PW,PW relationship`**.

3. **Output CSV/DBF confirmed populated for all 3 example policies** — verified twice: once against `QLA_Migration/Output/quikclid.csv` and once by directly reading the **live current QLAdmin build** at `Q:\CSO\CSO_Test_6_30_2026\quikclid.dbf` (dated 2026-09-02) with `dbfread`:

 | Policy | Client (`quikclid.dbf`) | `MRELATION` |
 |---|---|---|
 | 9010442216C | 712072 — MARLYS VANDER WAL | `PW` |
 | 9010451650C | 712326 — TIMOTHY MOUNTAIN | `PW` |
 | 9011045619C | 591432 — ANDREW MAZZURCO | `PW` |

 Matching `quikclnt.dbf` client-master rows exist for all three (full name/address/phone/SSN/DOB) — not blank shells.

4. **Root cause — confirmed by live QLAdmin screenshot (Warren, 2026-09-08):** Editing Policy `9010442216C` → **Names** tab → **Other Information** panel. The panel's relation-type dropdown lists valid codes: `ASGN - Assignee`, `JINS - Joint Insured`, `JOWN - Joint Owner`, `LAPS - 2nd Lapse Notice`, **`POFA - Power of Attorney`**. **`PW` is not a recognized code in this list.** The "Other Information" grid on screen was **empty** for this policy even though `quikclid.dbf` has the `MRELATION='PW'` row for client 712072 tied to this policy — QLAdmin does not render relation rows whose code it doesn't recognize.

 `POFA` does not appear anywhere else in the repo (`grep -r POFA` → no hits) — it has never been a conversion target before now.

5. **No prior POA/attorney issue-log or git history** — this is net-new (confirmed via `Issue_Log_Items/` search and `git log --all --grep`).

## Conclusion

This is **not** a missing-data defect. It is a **value-translation mapping defect**: the LifePRO `PW` relate code is passed through unchanged instead of being translated to QLAdmin's actual recognized code `POFA`. The relationship rows are present in `quikclid`/`quikclnt` for all affected policies but are invisible in the QLAdmin UI because `PW` isn't a value QLAdmin's Names/Other-Information panel recognizes.

## Decision

User said **"Proceed to Intake"** on 2026-09-08. Continuing Pre-Development Auto-Chain: Intake → Planning → Dependency Gate → Risk, then stop for Development approval per `AI_Agents/Framework.md`.
