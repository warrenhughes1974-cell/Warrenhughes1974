# Issue #45 — Planning Report

**Issue:** #45 — Incorporate PPPAC `E_ACCOUNT_NUMBER` as bank-draft account fallback  
**Framework stage:** Planning Agent  
**Status:** Ready for Dependency Gate  
**Generated:** 2026-07-12  
**Agent/script:** Planning Agent (Cursor Grok 4.5) · evidence in `Issue_45_Source_Investigation_Report.md`

**Model:** Cursor Grok 4.5 (locked Planning stage)

---

## 1. Executive Finding

Eric asked whether `PPPAC_PACDetail_Extract_20260630` can be incorporated because it holds `E_ACCOUNT_NUMBER` values not currently imported. **Confirmed:** PPPAC is a current PAC detail extract (2,122 rows, one per policy) with usable electronic account numbers on 2,120 rows. It has **no ABA/routing columns**.

Of **763** Issue #45 exception policies (MBILLFRM=2, no PPACH account):

- **750** have a usable PPPAC account
- **13** remain missing in both PPACH and PPPAC
- **0** can get routing from PPPAC alone

**Recommended direction:** Keep **PPACH as primary** ABA+account pair (Issue #21H). Add **PPPAC as fallback account** only when PPACH has no usable account. Recover ABA for those policies via existing `aba_routing_lookup` first, then RelationshipNameAddress `ELEC_ABA_NUMBER` with Issue #21H truncation handling. Emit `MBANKNO` only when **both** account and usable ABA are available; otherwise keep blank `MBANKNO` + exception (refined reason).

**Do not implement in Planning.** Development is surgical to `app.py` PPACH banking cache + Issue #45 gate only.

---

## 2. Confirmed LifePRO Source Table/File(s)

| Source table | File pattern | In Source/? | Row count |
|--------------|--------------|-------------|----------:|
| **PPPAC** (new) | `PPPAC_PACDetail_Extract_20260630.csv` | Yes | **2,122** |
| **PPACH** (primary) | `PPACH_PACHistory_Extract_20260630.csv` | Yes | **7,819** / 1,997 policies |
| **PPOLC** | `PPOLC_PolicyMaster_Extract_20260630.csv` | Yes | PAC=`BILLING_FORM` → 2,132 |
| ABA lookup | `aba_routing_lookup.csv` | Yes | 2,692 |
| RNA (ABA aid) | `RelationshipNameAddress_Extract_20260630.csv` | Yes | fleet |

### PPPAC fields used

| Field | Populated | Notes |
|-------|-----------|-------|
| `POLICY_NUMBER` | 100% | Join key (10-digit) |
| `PAC_ID` | 100% | = `COMPANY_CODE` + `POLICY_NUMBER` |
| `E_ACCOUNT_NUMBER` | 2,120 usable | May contain internal spaces; strip non-digits for compare / lookup |
| `P_ACCOUNT_NUMBER` | 0% | Blank — do not use |
| ABA / routing | **Absent** | Must not invent |

### PPACH fields (unchanged primary)

| Field | Notes |
|-------|-------|
| `POLICY_NUMBER` | Join key |
| `E_ACCOUNT_NUMBER` / `E_ABA_NUM` | Last complete pair by `CHANGE_DATE`/`CHANGE_TIME` |
| `STATUS_CODE` | History marker (`D` present); current last-wins logic retained |

---

## 3. Confirmed QLAdmin Target Structure

| Table | Field | Role | Source |
|-------|-------|------|--------|
| quikmstr | `MBANKNO` | Bank routing/account as `ABA/ACCOUNT` | Issue #21H path |
| quikmstr | `MBILLFRM` | `2` = PAC / bank draft | **Do not change** |
| quikmstr | `MACCTNO` | Separate field — **Do not change** this issue |

**Repo references:**

| Location | Role |
|----------|------|
| `app.py` / `QLA_Migration/app.py` ~5761–5810 | PPACH banking cache + ABA lookup |
| Same ~6259–6263 | `MBANKNO` override from `_ppach_bank_map` |
| Same ~4719–4768 | Issue #45 gate + exception CSV writer |
| `Reports/bank_draft_account_exceptions.csv` | Client/audit exception list |

---

## 4. Required Source-to-Target Field Mapping

| LifePRO source | LifePRO field | QLAdmin target | Transformation | Change? |
|----------------|---------------|----------------|----------------|---------|
| PPACH (primary) | `E_ABA_NUM` + `E_ACCOUNT_NUMBER` | `MBANKNO` | Existing #21H: lookup full ABA when unique; `ABA/ACCOUNT` | **No** (preserve) |
| PPPAC (fallback) | `E_ACCOUNT_NUMBER` | `MBANKNO` account half | Only if PPACH account missing; strip spaces; reject blank/zero/masked/&lt;4 digits | **Yes** |
| aba_routing_lookup | `FULL_ABA` by account digits | `MBANKNO` ABA half | Prefer when PPPAC fallback used | **Yes** (extend use) |
| RNA (fallback ABA) | `ELEC_ABA_NUMBER` | `MBANKNO` ABA half | Only if lookup miss; apply #21H truncation rules; skip if multiple distinct ABAs | **Yes** (conditional) |
| PPOLC | `BILLING_FORM=PAC` | `MBILLFRM=2` | Existing | **No** |

### Fields that must remain unchanged

| Target | Current source | Touch this issue? |
|--------|----------------|-------------------|
| quikmstr.MBILLFRM | Billing form translate | **No** |
| quikmstr.MACCTNO | Existing mapping | **No** |
| quikmstr.MMODPREM / mode premiums | PPOLC | **No** |
| quikridr.MPREM | #26 ANN_PREM_PER_UNIT + fallback | **No** |
| MPOLICY padding | #25 `format_qladmin_mpolicy` | **No** |
| PPACH-banked policies (~1,369) | PPACH last pair | **No** (fallback only when PPACH account absent) |

---

## 5. Open Client Questions

| ID | Question | Blocks Development? | Proposed default if waived |
|----|----------|---------------------|----------------------------|
| Q1 | For PPPAC-rescued accounts, may we emit `MBANKNO` when ABA comes from `aba_routing_lookup` or RNA (not PPACH)? | Soft — Eric asked for account import; ABA is required for current `MBANKNO` format | **Yes — use lookup then RNA; else leave blank + exception** |
| Q2 | Prefer PPACH or PPPAC when both exist but accounts differ (6 policies)? | **No** if fallback-only when PPACH missing | **PPACH wins** (those 6 untouched) |
| Q3 | Disposition of 13 PAC policies in neither extract? | No | Remain exceptions; client research |
| Q4 | Treat RNA multi-ABA policies as unusable routing? | Soft | **Yes — do not guess; exception** |

**Planning recommendation:** Proceed with defaults above; Eric’s email is scope approval for PPPAC account incorporation. Document Q1/Q4 as Conditional-Go assumptions for Risk.

---

## 6. Recommended Formatting Rules

| Rule | Recommendation |
|------|----------------|
| Policy key | Existing normalize + crosswalk + #25 MPOLICY padding |
| Account usable | Non-blank; digits after strip; not all zeros; not masked; **≥4 digits** for new PPPAC fallback |
| ABA usable | Prefer 9-digit from lookup; else RNA with #21H recovery; reject blank/zero/masked |
| `MBANKNO` emit | Only when **both** usable ABA and usable account exist: `{ABA}/{ACCOUNT}` |
| Spaces in PPPAC account | Strip internal spaces / non-digits for storage consistency with PPACH path |
| Future `PAC_DATE` | Do **not** filter (schedule date, not inactive flag) |
| Exceptions | Still write CSV; refine `EXCEPTION_REASON` / detail when account found but ABA missing |

---

## 7. Memo / Text / Special Handling

N/A — no memo fields. Mask accounts in all reports (`****1234`).

---

## 8. Policy Number Key Handling

1. LifePRO `POLICY_NUMBER` → `self.normalize()` (same as PPACH cache)
2. Crosswalk → QLA `MPOLICY` via existing quikmstr path (#25)
3. Exception CSV retains `SOURCE_POLICY` + `MPOLICY`
4. Orphans: if PPPAC policy not in conversion set, ignore (no new rows)

---

## 9. Estimated Record Counts

| Metric | Count | Basis |
|--------|------:|-------|
| PPOLC PAC / bank-draft policies | 2,132 | BILLING_FORM=PAC |
| Currently banked via PPACH | ~1,369 | Non-exception PAC |
| Current exceptions | 763 | Exception CSV |
| PPPAC fallback candidates (usable account) | **750** | Investigation |
| Of those with lookup ABA | 41 | Analysis |
| Of those with RNA ABA (any) | 748 | Analysis |
| Of those with lookup **or** RNA | **748** | Analysis |
| Account+ABA recoverable under plan (est.) | **~748** | If RNA accepted per Q1 default |
| Still exception after change (est.) | **~15** | 13 neither + ~2 no ABA |
| PPACH≠PPPAC conflicts touched | **0** | Fallback-only design |
| Non-candidate policies changed | **0** | Surgical fallback |

---

## 10. Sample Trace (proposed)

| Policy (QLA) | LifePRO | Before `MBANKNO` | After (proposed) | Status |
|--------------|---------|------------------|------------------|--------|
| 010157076C | 9010157076 | blank + exception | `*****1013/****2919` form if RNA/lookup ABA OK* | Candidate rescue |
| 010161748C | 9010161748 | blank + exception | ABA/****0581 if ABA OK* | Candidate rescue |
| 010348734C | 9010348734 | blank + exception | ABA/****8787 if ABA OK* | Candidate rescue |
| (any PPACH-banked) | — | existing `ABA/ACCOUNT` | **unchanged** | Regression guard |

\*Exact ABA digits masked in Planning; Validation will prove full values privately.

---

## 11. Risks and Unknowns

| Risk | Severity | Mitigation |
|------|----------|------------|
| Emit account without good ABA | High | Require both halves before `MBANKNO` |
| RNA ABA truncated | Medium | Prefer lookup; apply #21H padding/recovery; log source |
| Accidental overwrite of PPACH banked policies | High | Fallback **only** when PPACH account absent |
| `find_extract('ppach')` vs PPPAC filename collision | Low | Use distinct keyword `pppac`; verified no substring clash |
| Short accounts (&lt;4 digits) | Low | Reject for PPPAC fallback (2 short PAC rows already banked via PPACH `238` — leave alone) |

---

## 12. Dependency Gate Preview

| Check | Met? |
|-------|------|
| PPPAC source file present | Yes |
| PPACH / lookup / RNA present | Yes |
| Target field `MBANKNO` confirmed | Yes |
| Client scope (incorporate PPPAC account) | Yes (Eric email) |
| Example policies available | Yes |
| ABA default when PPACH missing | Documented assumption (Q1) |

---

## 13. Recommended Risk Agent Prompt

```
Proceed to Risk Agent for Issue 45.

Read AI_Agents/Risk_Agent.md and Issue_Log_Items/Issue_45/Issue_45_Planning_Report.md.
Also read Issue_45_Source_Investigation_Report.md and Issue_45_Dependency_Gate.md.

Model: Cursor Grok 4.5 (locked). Do not code.

Quantify before/after impact for PPPAC fallback (expected ~750 candidates;
~748 with recoverable ABA under Planning defaults). Confirm zero change to
PPACH-banked policies. Issue Go / Conditional Go / No-Go.
```

---

## 14. Recommended Development Task (Do Not Implement)

1. After PPACH cache build, load PPPAC via `find_extract('pppac')` (1 row/policy).
2. For each policy with usable PPPAC `E_ACCOUNT_NUMBER` and **no** PPACH usable account:
   - Resolve ABA: `aba_routing_lookup` by account digits → else RNA `ELEC_ABA_NUMBER` (skip if multiple distinct) with #21H recovery helpers.
   - If ABA + account usable → add to `_ppach_bank_map` / `_ppach_acct_meta` (or parallel fallback map merged at MBANKNO pull).
3. Update `_apply_issue45_bank_draft_gate` to treat recovered fallback as valid account; refine exception reasons (`MISSING_BANK_ACCOUNT` vs `MISSING_ROUTING` vs still missing).
4. Log counts: PPPAC loaded, fallback applied, ABA source breakdown.
5. Version bump **both** `app.py` and `QLA_Migration/app.py` (next version after current v57.76).
6. Add `QLA_Migration/_validate_issue45_pppac_fallback.py`:
   - 750 candidates: account presence
   - Sample traces masked
   - Non-exception PPACH policies unchanged vs baseline snapshot if available
7. Do **not** change rulebooks, MBILLFRM, MACCTNO, #25/#26 paths.

---

## Appendix

- Source investigation: `Issue_Log_Items/Issue_45/Issue_45_Source_Investigation_Report.md`
- Analysis scripts: `_analyze_pppac_source.py`, `_analyze_aba_coverage.py`
- Related: Issue #21H, #45 v57.61 exception gate
- Recommendation from investigation: **USE AS FALLBACK SOURCE**
