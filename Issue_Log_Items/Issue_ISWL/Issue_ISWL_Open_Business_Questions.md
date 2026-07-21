# Issue ISWL — Open Business Questions (CSO ISWL Setup / Sujitha Email 2026-07-20)

**Status:** OPEN
**Opened:** 2026-07-21
**Source:** Email thread "UL/ISWL Processing and Guide Line Premiums" (Warren 7/10 → Robert 7/10 → Sujitha 7/13 → Sujitha 7/20)
**Scope:** ISWL CSO plan setup questions raised by Sujitha (QLAdmin dev) — COI, Guaranteed COI, surrender charges, guideline premiums, loan credited rate, monthly expense per $1,000.
**Tracking:** `Issue_ISWL_Tracking_Sheet.csv`

ISWL fleet (8 MPLANs): `1658C1`, `1658CS`, `1659C2`, `1659CR`, `1659CS`, `1659SR`, `1669SR`, `1679CS`
Coverage segments: `658 CEN I`, `658 CEN SD`, `659 CEN II` (hub), `659 CEN SR`, `659 CEN SD`, `659 SR GD`, `669 SR GD`, `679 CEN SD` (+ non-ISWL `668 SPWL`)

---

## Answered from source data / repo evidence

### OBQ-1 — COI setup: QX0-only, CNTL=00 (Sujitha Q1, part 1) — ANSWERED

**Question:** QUIKCOI values appear only under QX0 and CNTL is always 00 — is this correct?
**Answer:** **Yes, by design.** PAAGERAT U6 has no duration column; each attained-age row emits one QuikCoi row (SEQ→AGE, rate→QX0, QX1–QX9 blank, CNTL fixed `00`), matching the VARGP=3 attained-age scalar pattern also used for QUIKGPS (GP0). `quikplan.VARGP = 3` for these plans.
**Evidence:** `qla_core/paagerat_ul_coi_loader.py`; `docs/research/ISWL_Implementation/ISWL_Table_By_Table_Design.md` §3.3; Issue #31 validators V-COI-04 / V-GCOI-03.

### OBQ-2 — Surrender charges: no age values (Sujitha Q3, part 1) — ANSWERED

**Question:** QUIKISSC has no age values. Should the same surrender charges apply to all issue ages?
**Answer:** **Yes.** The LifePRO Rate_Table `SL` schedule varies by policy duration only (14 durations, 100%→2%); it carries no age dimension. SME Gate C approved one all-age row per plan (`AGE=0`).
**Evidence:** `Issue_Log_Items/Issue_33/Issue_33_QUIKISSC_SME_Answers.md` (Gate C); `QLA_Migration/Source/Rate_Table_Extract_Txt.txt` (`659 CEN II` / `SL` = 14 duration rows, AGE=0 only).

### OBQ-3 — Surrender charges: no female rows (Sujitha Q3, part 2) — ANSWERED (with one confirm)

**Question:** No female surrender-charge data. Should the same values apply to both genders?
**Answer:** **Yes — the LifePRO SL schedule is not gender-differentiated** (source rows exist under SEX=M only; effectively unisex). Emit is a single `GENDER=M` row per plan per SME-approved design.
**Residual confirm (Sujitha):** does QLAdmin resolve female policies against the M QuikIssc key, or does it require an explicit F row? If a literal F key row is required, we will emit F companions with identical SCHG values.
**Evidence:** `Issue_33_Phase6_QUIKISSC_Implementation_Notes.md` §8; `qla_core/quikissc_loader.py`.

### OBQ-4 — Surrender charges missing for 1659CR / 1659SR / 1669SR (Sujitha Q3, part 3) — CLOSED (Issue #88)

**Question:** Plans 1659CR, 1659SR, 1669SR have no surrender-charge data. Should they?
**Answer:** **Yes — all 8 ISWL plans carry the identical hub 659 CEN II SL schedule.** Delivery was empty due to D1/D2; **fixed and closed under Issue #88** (QuikIssc = 8 rows, QuikUint = 32). Redeliver from `Output/rates/` or `Output/Test_Validation/rates/`.

### OBQ-5 — Monthly expense per $1,000 set to 0.00 — ANSWERED (confirm as 0.00)

**Question (implicit, from her intro):** Monthly Expense per $1,000 had no value and was set to 0.00 — correct?
**Answer:** **Yes.** No U1/U2/U3 per-thousand expense segments exist for any of the 8 ISWL coverages (0/8 in segment trace). The locked expense decisions are: $25 annual policy fee (~$2.08/month) + 3.5% premium load; per-$1,000 monthly expense = 0.00.
**Evidence:** `docs/research/ISWL_Segment_Trace/ISWL_Segment_Trace_Addendum_20260629.md`; `Issue_Log_Items/Issue_43/Issue_43_Meeting_Decisions_20260713.md`; `PCOVR.POLICY_FEE = 25.00` on all 8 coverages.

---

## Open questions

### OBQ-6 — COI factor basis: per $1,000? (Sujitha Q1, part 2) — OPEN

**Question:** For PFSA, COI factors were per $1,000. Should the same basis apply to these ISWL plans?
**What we know:** The loader passes PAAGERAT `VALUE_INFO` through with **no scaling** (e.g. 1679CS M/SM: .73 @ 54 → 57.65 @ 99; 1658CS: .08 @ 2 → 66.89 @ 99). Magnitudes are consistent with annual mortality charges per $1,000 NAR, but no repo document confirms the LifePRO U6/U5 unit basis, and the "per-thousand" note in prior research applied to the withdrawn NC segment, not U6. Phase R2 "confirm value scale" item is still open.
**Need:** Actuarial/SME confirmation of U6/U5 unit basis (per $1,000 vs per unit) and whether QLAdmin QUIKCOI expects the same basis as PFSA.
**Why it matters:** A basis mismatch scales every ISWL COI deduction by 1000×.

### OBQ-7 — Should the other 6 ISWL plans have COI factors? (Sujitha Q1/Q2) — OPEN (SME/client)

**Question:** Only 1658CS and 1679CS have QUIKCOI values. Should the others?
**What we know:**
- PAAGERAT U6 rate rows exist only for `658 CEN I`, `659 CEN II` (hub), and `678 CEN SD` (added in the 2026-07-13 source refresh). The other coverages have PSEGT U6 *capability* but zero rate rows.
- The emit already treats hub rates as inheritable in one direction: emitted 1679CS COI combines `678 CEN SD` (M/SM) with hub `659 CEN II` rows (F/PR, F/SM, M/PR) — verified by value trace (.7346960→.73 from 678 CEN SD; .3187500→.32 F/P from 659 CEN II).
- Emit allowlist is frozen to `1658CS`, `1679CS` (`iswl_phase3.coi_mplan_allowlist`), documented as "partial fleet — SME/client confirmation required."
- Standing SME question (`ISWL_Segment_Trace/ISWL_Segment_SME_Question_List.md` #3): where are COI/gross premium rates for the senior/grandfathered plans (659 SR GD, 669 SR GD)?
**Need decision:** (a) replicate hub 659 CEN II U6 rates to the remaining plans (as done for QUIKISSC), (b) obtain plan-specific COI rates from the client, or (c) confirm those plans genuinely run without COI (and how QLAdmin should process an ISWL plan with no QUIKCOI row).

### OBQ-8 — Should other plans have Guaranteed COI (QUIKGCOI)? (Sujitha Q2) — OPEN (SME/client)

**Question:** Only 1679CS has Guaranteed COI values. Should other ISWL plans have them?
**What we know:** PAAGERAT U5 rows exist only for `659 CEN II` (hub, M+F, S class), `678 CEN SD` (M/S), and non-ISWL `668 SPWL`. Emit allowlist is frozen to 1679CS. 7/8 plans have PSEGT U5 capability but no rate rows. Same decision fork as OBQ-7 (hub replication vs client data vs confirmed-absent).
**Also confirm:** what QLAdmin does when QUIKCOI exists but QUIKGCOI does not (guaranteed = current? guaranteed = 0?). That behavior determines how urgent full-fleet GCOI is.

### OBQ-9 — Guideline premiums GLP_LEVEL / GLP_SINGLE / GLP_7PAY (Sujitha Q4) — OPEN (client + QLAdmin)

**Question:** How are QUIKSPEC.GLP_LEVEL / GLP_SINGLE established for a CSO policy? Can QLAdmin recalculate them for converted in-force policies, or do we need source-system values?
**What we know from source data:**
- LifePRO **has** the fields — `PPBENTYP` `BF_GUIDELIN_LVL_PR`, `BF_GUIDELIN_SNG_PR`, `BF_TAMRA_AMOUNT` — but in the CSO extracts they are **all zero/blank** (0 nonzero across 2,348 BF rows). `BA_TAMRA_PREM` is populated but with a single sentinel value (5,389,762.88) on 2,297 rows — not real 7-pay premiums. Only MEC flags (`PPOLC.TAMRA_MEC_FLAG` etc.) carry real data.
- The UZ (Guideline Premium Rules) segment has zero rate rows for all 8 ISWL coverages.
- The conversion currently does **not** emit quikspec at all.
- Per Sujitha's own code review, `GLPCheck()` does not calculate GLP — it only consumes stored values, and **skips the check entirely when both GLP_LEVEL and GLP_SINGLE are 0** (i.e., converting with blanks silently disables guideline premium validation).
**Need decisions:**
1. **QLAdmin side (Robert/Chris):** confirm GLP values are user/actuary-maintained (no issue-time calc in QLAdmin) — i.e., converted policies need supplied values.
2. **Client side:** can CSO supply original guideline premiums from outside these extracts (LifePRO 7702 compliance module, filing/actuarial records)?
3. **Business:** are these ISWL plans even subject to §7702 guideline premium testing? Plan eras (CEN I/II, SPWL, SR GD) may predate DEFRA/TAMRA grandfathering; if grandfathered, blank GLP (validation disabled) may be the *correct* converted state. Needs actuarial/compliance ruling.
4. If values are required: define the QUIKSPEC conversion source and add quikspec emit scope (currently none).

### OBQ-10 — Credited interest rate on loan balance set to 0.00 — OPEN

**Question (implicit, from her intro):** No value found for Credited Interest Rate on Loan Balance; set to 0.00 — correct?
**What we know:** The LN segment is wired on all 8 coverages but its `SEGT_DATA` payload has not been decoded to a rate. `PLOAN.INTEREST_RATE` (e.g. .0500) is the **charged** loan rate, not the credited-on-loan-balance rate. PDINT/PDINTTBL carry A1 fund credited rates only (no LN rows). Related standing item: QuikPlan `LOANINT = 0.00` on many life/ISWL plans (Go-Live Open Items #11, with Eric).
**Need:** decode LN segment payload or obtain the credited-on-loan-balance rate from the client; confirm whether 0.00 is acceptable interim UAT behavior.
**Reference:** `docs/research/ISWL_LifePRO_to_QLAdmin_Master_Reference.md` §5.5.

---

## Internal defects found during this review (repo-side, not questions for Sujitha)

### D1 — Batch CSV emit drops QuikIssc/QuikUint rows — CLOSED (Issue #88)

Fixed in `qla_core/rate_emit.py` CSV branch. See `Issue_88_Resolution_Summary.md`.

### D2 — Stale PDINT/PDINTTBL config paths → QuikUint emitted empty — CLOSED (Issue #88)

Config repointed to `*_20260630.csv`. See `Issue_88_Resolution_Summary.md`.

### D3 — Verify COI coverage→plan resolution after 7/13 source refresh — OPEN (verification)

The 2026-07-13 PAAGERAT refresh added `678 CEN SD` U6/U5 rows (400/400, M/S only, previously absent). Current 1679CS emit mixes `678 CEN SD` and hub `659 CEN II` rows. Issue #31 evidence and validators were built against the 800-U6/200-U5 row inventory of the older extract; re-run `tools/validators/iswl_quikcoi_reconcile.py` / `iswl_quikgcoi_reconcile.py` against the 20260714 extract and confirm the mapping (and duplicate handling — 678 CEN SD carries 4 duplicate copies per SEQ) is intended.

---

## Summary table

| ID | Topic | Status | Owner / next step |
|----|-------|--------|-------------------|
| OBQ-1 | COI QX0/CNTL=00 layout | ANSWERED (by design) | Reply to Sujitha |
| OBQ-2 | Surrender charge ages | ANSWERED (all-age by design) | Reply to Sujitha |
| OBQ-3 | Surrender charge gender | ANSWERED (unisex source) | Sujitha: confirm QLAdmin F-key lookup |
| OBQ-4 | 1659CR/1659SR/1669SR surrender charges | CLOSED (#88) | Redeliver QuikIssc to Sujitha |
| OBQ-5 | Monthly expense per $1,000 = 0.00 | ANSWERED (confirmed 0.00) | Reply to Sujitha |
| OBQ-6 | COI per-$1,000 basis | OPEN | Actuarial/SME |
| OBQ-7 | COI for other 6 plans | OPEN | SME/client decision |
| OBQ-8 | GCOI for other plans | OPEN | SME/client + QLAdmin behavior |
| OBQ-9 | GLP_LEVEL/GLP_SINGLE/7-pay source | OPEN | Client + QLAdmin + actuarial (7702 applicability) |
| OBQ-10 | Loan credited rate = 0.00 | OPEN | Decode LN segment / client |
| D1 | Batch CSV emit drops QuikIssc/QuikUint | CLOSED (#88) | Redeliver package |
| D2 | Stale PDINT config paths | CLOSED (#88) | Redeliver package |
| D3 | COI resolution vs 7/13 refresh | OPEN | Re-run COI/GCOI reconcile validators |
