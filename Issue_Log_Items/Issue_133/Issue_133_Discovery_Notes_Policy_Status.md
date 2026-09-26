# Issue 133 (client Active row) — Discovery Notes: Policy Status / PUA vs Status 50

**Stage:** Discovery (Search & Discuss)  
**Date:** 2026-08-06  
**Code changes:** None

> **ID collision note:** Local `Issue_133_Tracking_Sheet_Row.tsv` is already **Closed** as “Conversion Rule Book delivery” (2026-07-30). The client sheet row pasted for this research is a **new Active** item with the same ID 133 (“Policy Status's Incorrect”). Confirm with Warren whether this is a reused ID, a sheet typo, or a reopen before Intake.

---

## Client ask (verbatim)

> Two policies are in Active status in QLAdmin due to the PUAs not moving to Pending Death Benefit status (Status 50) when the base phase moved to status 50. The policies are 9010439999C and 9010468945C.

**Normalized:** On death-claim-pending contracts, base coverage shows status 50, but the PUA phase stays in-force (Active / &lt;50), so QLAdmin policy status stays Active instead of Death Claim Pending (50).

---

## Source findings (2026-07-31 LifePRO extract)

### Policy master (PPOLC)

| Policy | CONTRACT_CODE | CONTRACT_REASON | PAID_UP_TYPE | CONTRACT_DATE |
|--------|---------------|-----------------|--------------|---------------|
| 9010439999 | **S** | **DP** | (blank) | 20260518 |
| 9010468945 | **S** | **DP** | (blank) | 20260618 |

`ST_S_DP` → **50** (Death Claim Pending) in `Master_Value_Translation.csv`.

### Benefits (PPBEN) — both still Active with DP reason

| Policy | Seq | Type | PLAN | STATUS_CODE | STATUS_REASON |
|--------|-----|------|------|-------------|---------------|
| 9010439999 | 1 | BA | 960 PO | **A** | **DP** |
| 9010439999 | 2 | PU | 960 PO PUA | **A** | **DP** |
| 9010468945 | 1 | BA | 670 GL85-M | **A** | **DP** |
| 9010468945 | 2 | PU | 670 PUA | **A** | **DP** |

### Midyear contrast (2026-06-30)

Both policies were still **Active** on the 6/30 cut (`CONTRACT_CODE=A`, blank reason; PPBEN `A` with blank reason). Death-pending is a **7/31 cut change**.

### Fleet scope on 7/31

- **14** policies are PPOLC `S/DP`.
- **All 14** still have base benefit `STATUS_CODE=A` (reason DP).
- **Only these 2** of the 14 also have a PUA (`BENEFIT_TYPE=PU`) still at `STATUS_CODE=A`.

So LifePRO itself did **not** move PUA (or base benefit code) off Active — only the **policy master** is Suspended/Death Pending. Client expects QLAdmin phases/header to follow master status 50 anyway.

---

## Current Output (workspace `QLA_Migration/Output/`)

Looks like a pre–7/31 Active package:

| Policy | quikmstr.MSTATUS | Ph1 MPHSTAT | Ph2 (PUA) MPLAN / MPHSTAT |
|--------|------------------|-------------|---------------------------|
| 9010439999C | 22 | 22 | 1960PA / **41** |
| 9010468945C | 22 | 22 | 1708PA / **41** |

PUA at 41 here is Issue **#60** (Paid Up when base &lt; 50). This Output does **not** yet show the client’s “base=50 / PUA Active” picture; that appears after converting the **7/31 S/DP** source through current rules.

---

## Rules that cause / amplify this

### 1. Issue #60 PUA inheritance — **direct cause for PUA not becoming 50**

`_apply_pua_rider_inheritance` (app.py):

- If base `MPHSTAT` in (44, 45) → PUA **54** (#108D).
- Else if base **&lt; 50** → PUA **41** (Paid Up) — Chris SD-60-12.
- Else (base **≥ 50**, including **50**) → **leave PUA MPHSTAT unchanged**.

On an S/DP convert, phase 1 becomes 50 (inherit from master). Base is **not** &lt; 50, so #60 does **not** rewrite PUA. PUA keeps benefit-mapped Active status from PPBEN `STATUS_CODE=A`.

**Locked intent (SD-60-12):** do not force Paid Up (41) on terminated bases — leave prior status. It does **not** say “copy base status 50 onto PUA.”

### 2. Issue #49 — **why the policy header stays Active**

When phase 1 display status ≥ 50 and a later phase is still &lt; 50, `quikmstr.MSTATUS` takes that later active phase. PUA at 22 (or 41) is &lt; 50 → header becomes Active/Paid Up instead of 50.

### 3. Issue #59 — **narrow exception only**

#59 blocks #49 from replacing Death Claim Pending (50) with a later PUA Active phase — but **only** for allowlisted `9010521213C` / `010521213C`.  
**9010439999C and 9010468945C are not on that list**, so #49 will still promote them to Active on a full 7/31 batch.

### 4. Rulebook gap — PPBEN reason ignored on phases

`Sync_Rulebook_quikridr.csv` maps **STATUS_CODE → MPHSTAT** only (no STATUS_REASON). There is **no** `ST_A_DP` composite. Even though source reason is DP on both benefits, phase emit follows bare **A** → Active, while master uses **S_DP** → 50.

### 5. Related Closed guidance (Robert / #108)

#108 Intake: if policy status is terminated (≥50), all coverages should be terminated. These two policies violate that once base is 50 and PUA stays &lt;50 — same class of defect #108D fixed for NFO (41→54), but **status 50 was never given a PUA force-to-50 rule**.

---

## Suspected target

| Layer | Table / field | Desired (client) |
|-------|---------------|------------------|
| Phase | `quikridr.MPHSTAT` on PUA | **50** when base (or policy) is Death Claim Pending |
| Header | `quikmstr.MSTATUS` | **50** (not overridden by #49) |

UI: Policy status + coverage/phase status.

---

## Current vs desired

| | Current rule behavior on 7/31 S/DP + Active PUA | Client desired |
|--|--------------------------------------------------|----------------|
| Master (provisional) | 50 from `S/DP` | 50 |
| Base phase | Inherits 50 | 50 |
| PUA phase | Stays Active (A); #60 does not touch ≥50 bases | 50 |
| Final master | #49 → Active because PUA &lt;50 | 50 |

---

## Proposed work list (for Planning — no code yet)

1. Confirm issue ID (new vs reuse of Closed 133 Rule Book).
2. Decide authority: force PUA `MPHSTAT=50` when base/policy is 50 (mirror #108D pattern for death-pending), and/or extend #59-style #49 block for these two (or all S/DP).
3. Check Closed-row conflicts: #49, #59, #60 SD-60-12, #108D — Warren approval if any Closed behavior must change.
4. Scope: only the 2 cited policies vs all future S/DP+PUA (fleet today = exactly these 2).
5. Rebatch on `QLA_VALUATION_DATE=20260731` before Validation (current Output is Active-cut).

---

## Open questions

1. Should PUA copy **any** base status ≥50 (50/53/54/…), or only Death Claim Pending (50)?
2. Fix phase only, or also hard-block #49 on S/DP like #59?
3. Is LifePRO leaving benefits at `A/DP` intentional, or a source defect to raise with CSO?

---

## Stop

Discovery complete. Awaiting **"Proceed to Intake"** (or ID clarification).

---

## Update 2026-09-22 — fix + smoke shipped (Warren: "make the fix and the smoke")

Warren directed moving straight to the fix. Implemented at the header layer
(quikmstr.MSTATUS via #49's PPBEN phase cache), mirroring #160's existing
row-layer PUA terminal-status inheritance. Does not disturb Closed #49's
35-policy SU/OR override population. ID collision with the Closed "Rule
Book delivery" 133 is still unresolved — tracked as `133-PS` pending Warren.
See `Issue_133_PUA_Header_Status_Fix_Note.md` for full detail; smoke:
`tools/validators/validate_issue133_pua_header_status.py`. **Not Closed** —
current `Output/quikmstr.csv` is stale; needs an 8/31 full batch before G7.
