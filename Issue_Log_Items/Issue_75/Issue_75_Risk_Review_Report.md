# Issue #75 — Risk Review Report

**Issue:** #75 — Bank Acct / `MBANKNO` QLA validation  
**Framework stage:** Risk Agent  
**Status:** **Conditional Go → Ready for Development** (pending explicit user approval)  
**Generated:** 2026-07-15  
**Model:** Cursor Grok 4.5 (locked)  
**Status note:** Risk analysis only — no production code changes.  
**Evidence:**  
- `evidence/issue75_risk_impact_summary.csv`  
- `evidence/issue75_risk_mbankno_simulation.csv`  
- `evidence/issue75_risk_trace_masked.csv`  
- `evidence/issue75_mbankno_format_defects.csv`  
- `scripts/risk_review_issue75_mbankno.py`

---

## Go / No-Go Recommendation

**CONDITIONAL GO** — Tighten `MBANKNO` emit to QLA-safe `9digitABA/accountDigits` (strip punct / kill multi-slash / refuse truncated ABA). Impact is quantified from Output + Issue #21 lookup; full Source re-recovery may improve ABA fill rates at Development time.

| Factor | Assessment |
|--------|------------|
| Scope | `quikmstr.MBANKNO` emit path only (`app.py` PPACH/PPPAC cache + #45 gate) |
| Already valid (unchanged) | **1,662** filled rows |
| Cleanup only (punct / slash) | **88** |
| Lookup recovers truncated ABA | **2** (floor — Source/RNA may add more in Dev) |
| Truncated ABA → blank | **984** (of which **948** are `MBILLFRM=2`) |
| Total `MBANKNO` value changes | **1,074** |
| #25 / #26 / `MBILLFRM` | Untouched |
| Client example **010161748C** | Lookup cannot recover 9-digit ABA → **would blank** unless Dev Source/RNA finds it |

**Conditions before / during Development:**

1. **Accept blanking unrecovered truncated ABA** (OBQ-75-1) — same pattern as Issue #45 incomplete banking; policy still converts; exception CSV lists them.  
2. **Dev runs against full Source** (PPACH, PPPAC, `aba_routing_lookup`, RNA) — Risk simulation used Output + lookup only; recovery count is a **lower bound**.  
3. **Do not invent ABA** (no leading-zero guess). Check-digit pad-`0` would “pass” only ~98/779 eight-digit cases and **fails** on 010161748C — **rejected**.  
4. Explicit user phrase: **Approved for Development** + switch to **Composer 2.5**.

---

## 1. Current vs Proposed Mapping

| Field | Current | Proposed | Change? |
|-------|---------|----------|---------|
| `quikmstr.MBANKNO` | `ABA/ACCOUNT` even if ABA is 7–8 digits; may include hyphens/spaces; some `//` | Emit only if ABA digits **len==9** and account is digits-only; else blank | **Yes** |
| PPACH cache | `use_aba = full_aba if full_aba else truncated` | Prefer full 9-digit; **never** emit truncated | **Yes** |
| PPPAC fallback (#45) | Account + lookup/RNA ABA | Same + 9-digit gate + strip punct | **Yes** |
| `#45` gate | Blank when account or ABA missing | Extend reasons: `ABA_NOT_9`, `ACCT_INVALID` | **Yes** |
| `MBILLFRM` | unchanged | unchanged | **No** |

---

## 2. Premium / Related Fields Untouched

| Target | Touched? |
|--------|----------|
| MPOLICY padding (#25) | **No** |
| quikridr.MPREM / MMODPREM (#26) | **No** |
| `MBILLFRM` / `MBILLDAY` / `MACCTNO` | **No** |
| `MMODE` / `MMODEPREM` / `MSTATUS` | **No** |
| Rulebooks (except no rulebook change expected) | **No** |
| Claims `quikclmp.MBANKNO` | **No** (out of scope) |

---

## 3. Repo References

| Location | Role |
|----------|------|
| `QLA_Migration/app.py` / root `app.py` ~5946–6084 | PPACH / PPPAC → `_ppach_bank_map` (`f"{use_aba}/{acct}"`) |
| Same ~6548–6552 | `MBANKNO` override from map |
| Same ~4817–4859 | Issue #45 bank-draft gate + exceptions |
| `Configs/Sync_Rulebook_quikmstr.csv` `MBANKNO` | Blank rulebook; runtime override |
| `Issue_Log_Items/Issue_21/evidence/aba_routing_lookup.csv` | 2,692 account→ABA keys (Risk sim) |
| QLAdmin Help Bank Acct | Routing + `/` + account; routing validated; optional `/S` `/A` |

---

## 4. Population Analysis (simulated)

**Inputs:** `Output/quikmstr.csv` (5,083) + `aba_routing_lookup.csv` (2,692).  
**No live PPACH/RNA in this workspace** — recovery via lookup only.

| Metric | Count |
|--------|------:|
| quikmstr rows | 5,083 |
| `MBANKNO` filled (before) | 2,736 |
| `MBANKNO` blank (before) | 2,347 |
| **Would change** | **1,074** |
| Unchanged (incl. already blank) | 4,009 |
| Action `UNCHANGED` (already valid) | **1,662** |
| Action `CLEANUP` | **88** |
| Action `RECOVER_ABA` (lookup) | **2** |
| Action `BLANK` (was filled, becomes blank) | **984** |
| PAC (`MBILLFRM=2`) would change | **961** |
| PAC filled → blank | **948** |
| After filled (estimate) | **1,752** (= 1,662 + 88 + 2) |
| After valid 9-digit (estimate) | **1,752** |

### Breakdown by action

| ACTION | Meaning | rows | would_change |
|--------|---------|-----:|-------------:|
| UNCHANGED | Already `9digit/digits` | 1,662 | 0 |
| CLEANUP | Strip punct / fix slash; ABA already 9 | 88 | 88 |
| RECOVER_ABA | Truncated → lookup 9-digit | 2 | 2 |
| BLANK | Cannot form QLA-safe value | 984 | 984 |
| BLANK_KEEP | Already blank | 2,347 | 0 |

### Defect inventory (before — from Planning)

| Defect | Count |
|--------|------:|
| ABA ≠ 9 | 986 |
| Multi-slash | 15 |
| Account punctuation | 165 |

---

## 5. Fallback Recommendation

| Option | Approx impact | Assessment |
|--------|---------------|------------|
| **A. Strict 9-digit gate + punct cleanup + blank unrecovered (recommended)** | ~1,074 changes; ~984 blank | Fixes QLA validation; aligns Help + #21H intent |
| B. Cleanup only (keep truncated ABA) | ~88–165 | **Reject** — does **not** fix client routing error on 010161748C |
| C. Leading-zero invent when check digit passes | ~98 of 779 eights | **Reject** — speculative; fails client example |
| D. Leave as-is | 0 | **Reject** — UAT blocked on edit |

**Recommended:** **Option A**. Soft assumptions OBQ-75-1 (blank) and OBQ-75-2 (strip hyphens/spaces) remain in force.

---

## 6. Trace Policies (masked)

| Policy | Before (masked) | After (sim) | Action | Pass vs intent? |
|--------|-----------------|-------------|--------|-----------------|
| **010161748C** | `****0385/*********0581` | blank | BLANK | Fixes invalid routing **if** blank acceptable; needs Source/RNA hope for fill |
| 010157076C | `****1013/**2919` | blank | BLANK | Same |
| 010348734C | `****1811/**8787` | blank | BLANK | Same |
| 010464590C | `****0068/…` (`//` case) | blank | BLANK | Removes literal `//` |
| **010713704C** | `*****0016/****4579` | same | UNCHANGED | Regression guard (#21H) |

Full masked file: `evidence/issue75_risk_trace_masked.csv`.

---

## 7. Top change classes (not numeric deltas)

| Class | Count | Example pattern |
|-------|------:|-----------------|
| Truncated ABA → blank | 984 | 8-digit routing kept today |
| Punctuation / multi-slash cleanup | 88 | hyphenated account with good ABA |
| Lookup ABA recovery | 2 | rare Output+lookup hit |

---

## 8. Material Calculation Impact

Not a premium field. Material ops impact:

- **Positive:** QLA policy-change validation stops failing on invalid routing / `//`.  
- **Tradeoff:** ~948 bank-draft policies may lose a **bad** `MBANKNO` and appear on the exception list until a true 9-digit ABA is available. Governance still wants a bank value when `MBILLFRM=2` — blank is incomplete but preferable to an invalid routing that blocks edits.  
- **Intentional** corrections only on `MBANKNO`; no accidental premium/status drift expected.

---

## 9. Prior Fix Preservation

| Check | Result |
|-------|--------|
| Issue #25 MPOLICY padding | **Preserve** — no key formatting change |
| Issue #26 MPREM / MMODPREM | **Preserve** — untouched |
| Issue #21H ABA recovery path | **Preserve and harden** — stop falling back to truncated ABA |
| Issue #45 PPPAC fallback + exceptions | **Preserve** — extend exception reasons |

---

## 10. Regression Testing Checklist (Validation Agent)

- [ ] Trace **010161748C**: after reload, no `Invalid routing number`; `MBANKNO` is either valid `9digit/digits` or blank + exception row  
- [ ] Traces 010157076C, 010348734C, 010464590C: no multi-slash / hyphen emit  
- [ ] **010713704C** (and sample of 1,662 UNCHANGED): `MBANKNO` byte-identical where already valid  
- [ ] Zero filled `MBANKNO` with ABA digit length ≠ 9  
- [ ] Zero filled `MBANKNO` with `/` count ≠ 1 (except future approved `/S` `/A` only if added)  
- [ ] Zero hyphens/spaces in account half of filled values  
- [ ] `MBILLFRM`, `MACCTNO`, `MMODEPREM`, `MSTATUS` unchanged vs before for non-`MBANKNO` columns  
- [ ] Exception CSV lists blanked bank-draft policies with clear reason  
- [ ] #25 width / #26 MPREM spot checks PASS  
- [ ] Publish `Output/Test_Validation/quikmstr.csv` on PASS  

---

## 11. Recommended Development Agent Task

1. In PPACH / PPPAC banking cache build (`app.py` both copies):  
   - Normalize ABA to digits; **emit only if len==9**.  
   - Prefer `aba_routing_lookup` / RNA (existing #45) over truncated PPACH ABA.  
   - Normalize account: strip spaces/hyphens; reject if `/` remains in account body.  
   - Emit `f"{aba9}/{acct_digits}"` only when both pass.  
2. Extend `_apply_issue45_bank_draft_gate` / exception reasons for `ABA_NOT_9` / `ACCT_INVALID`.  
3. Add `Issue_Log_Items/Issue_75/scripts/validate_issue75_mbankno.py` asserting format invariants + traces.  
4. Version-bump **both** `app.py` files.  
5. Do **not** change `MBILLFRM`, #25, #26, or invent ABA via padding.  
6. On validator PASS, copy `quikmstr.csv` → `Output/Test_Validation/`.

**Do not implement until:** user says **Approved for Development** and uses **Composer 2.5**.

---

## Appendix

| Artifact | Path |
|----------|------|
| Impact summary | `Issue_Log_Items/Issue_75/evidence/issue75_risk_impact_summary.csv` |
| Full simulation | `Issue_Log_Items/Issue_75/evidence/issue75_risk_mbankno_simulation.csv` |
| Masked traces | `Issue_Log_Items/Issue_75/evidence/issue75_risk_trace_masked.csv` |
| Risk script | `Issue_Log_Items/Issue_75/scripts/risk_review_issue75_mbankno.py` |
| Planning | `Issue_75_Planning_Report.md` |
| Dependency Gate | `Issue_75_Dependency_Gate.md` (PASS) |
