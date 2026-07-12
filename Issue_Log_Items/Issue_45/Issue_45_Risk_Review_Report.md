# Issue #45 — Risk Review Report

**Issue:** #45 — PPPAC `E_ACCOUNT_NUMBER` fallback for bank-draft `MBANKNO`  
**Framework stage:** Risk Agent  
**Status:** **Conditional Go — Ready for Development** (after user approval + Composer 2.5)  
**Fallback simulated:** Read-only fleet analysis (`Issue_45_Source_Investigation_Report.md`)  
**Generated:** 2026-07-12  
**Agent/script:** Risk Agent (Cursor Grok 4.5)

**Status note:** Risk analysis only — no production code changes in this stage.

**Model:** Cursor Grok 4.5 (locked Risk stage)

---

## Go / No-Go Recommendation

**CONDITIONAL GO** — Safe to implement as a **PPACH-primary / PPPAC-fallback** change with emit-only-when-ABA-present and zero intended change to already-banked PPACH policies.

Conditions:

1. Touch only banking cache + Issue #45 exception gate in `app.py` / `QLA_Migration/app.py`.
2. PPPAC used **only** when PPACH has no usable account.
3. Emit `MBANKNO` only when usable **account and ABA** both resolve.
4. Do not alter the 6 PPACH≠PPPAC conflict policies (PPACH present → untouched).
5. Validation must prove non-candidate `MBANKNO` unchanged and exception count declines as expected.

---

## 1. Current vs Proposed Mapping

| Field | Current | Proposed | Change? |
|-------|---------|----------|---------|
| `MBANKNO` (PPACH account present) | PPACH ABA+account via #21H | Same | **No** |
| `MBANKNO` (PPACH account absent, PPPAC account + ABA recoverable) | blank + exception | `ABA/ACCOUNT` from PPPAC + lookup/RNA | **Yes** (~748 est.) |
| `MBANKNO` (PPACH absent, PPPAC account, ABA not recoverable) | blank + exception | blank + refined exception (`MISSING_ROUTING`) | **Yes** (reason only; ~2) |
| `MBANKNO` (neither source) | blank + exception | unchanged | **No** (13) |
| `MBILLFRM` | PAC→2 | unchanged | **No** |

---

## 2. Premium / Related Fields Untouched

| Target | Source | Touched? |
|--------|--------|----------|
| quikmstr.MBILLFRM | Billing translate | **No** |
| quikmstr.MACCTNO | Existing | **No** |
| quikmstr.MMODEPREM / mode fields | PPOLC | **No** |
| quikridr.MPREM | #26 | **No** |
| MPOLICY padding | #25 | **No** |
| Rulebooks / crosswalk | Configs | **No** |

---

## 3. Repo References

| Location | Role |
|----------|------|
| `app.py` / `QLA_Migration/app.py` PPACH cache (~5761–5810) | Extend after PPACH load with PPPAC fallback merge |
| `MBANKNO` pull (~6259–6263) | Consume merged map (no schema change) |
| `_apply_issue45_bank_draft_gate` (~4719–4746) | Recognize fallback meta; refine exception reasons |
| `_write_bank_draft_account_exceptions` | Possibly add columns for PPPAC/ABA source (optional; keep backward compatible header if possible) |
| `find_extract('pppac')` | New load — keyword must not collide with `ppach` (verified) |

---

## 4. Population Analysis

| Metric | Count |
|--------|------:|
| Bank-draft policies (PPOLC PAC) | 2,132 |
| Current exceptions (no PPACH account) | 763 |
| PPPAC fallback candidates (usable account) | **750** |
| Candidates with ABA via lookup or RNA | **748** |
| Candidates with account but no ABA source | **2** |
| Still no account in either source | **13** |
| Expected exception rows after fix (approx.) | **~15** |
| Expected new `MBANKNO` fills (approx.) | **~748** |
| Already-banked PPACH policies expected unchanged | **~1,369** |
| PPACH≠PPPAC conflicts intentionally untouched | **6** |

### Breakdown (exception fleet)

| Segment | rows | would_change MBANKNO? |
|---------|-----:|----------------------:|
| Exception + PPPAC acct + ABA recoverable | ~748 | Yes (blank → ABA/ACCOUNT) |
| Exception + PPPAC acct + no ABA | ~2 | No value; reason may change |
| Exception + not in PPPAC | 13 | No |
| Non-exception PAC (PPACH banked) | ~1,369 | **No** |

---

## 5. Fallback Recommendation

| Option | Rows affected | Assessment |
|--------|-------------:|------------|
| A. PPACH primary; PPPAC account fallback; require ABA | ~748 fills | **Recommended** |
| B. PPPAC primary replace PPACH | ~1,369 + conflicts | **Reject** — loses ABA pairing; 6 conflicts |
| C. PPPAC account without ABA emit | 750 | **Reject** — breaks #21H `MBANKNO` contract |
| D. Do nothing | 0 | Reject — Eric ask unanswered |

**Recommended fallback:** Option A.

---

## 6. Trace Policies

| Policy | Before | Proposed | Pass? |
|--------|--------|----------|-------|
| 010157076C | blank + MISSING_BANK_ACCOUNT | Fill if ABA resolves from RNA/lookup | Expect Yes |
| 010161748C | blank + exception | Fill if ABA resolves | Expect Yes |
| 010348734C | blank + exception | Fill if ABA resolves | Expect Yes |
| Known PPACH-banked control (any of 1,369) | existing MBANKNO | identical | Must Yes |
| One of 13 neither-source (e.g. 9015000043) | blank + exception | still blank + exception | Must Yes |

Exact ABA/account digits remain masked in this report.

---

## 7. Top Changes

Not a numeric premium field. Largest impact is **count of newly populated `MBANKNO`** (~748). No “largest delta” ranking applies.

Conflict set (PPACH vs PPPAC account digits differ) — **not changed** under Option A:

| SOURCE_POLICY | Note |
|---------------|------|
| 9010749041 | PPACH present — untouched |
| 9010880951 | PPACH present — untouched |
| 9011118400 | PPACH present — untouched |
| 9011120163 | PPACH present — untouched |
| 9011194622 | PPACH present — untouched |
| 9011194623 | PPACH present — untouched |

---

## 8. Material Calculation Impact

- Intentional: import missing bank account numbers Eric identified.
- Not accidental premium/status/rider drift.
- Banking quality still depends on ABA recovery quality (lookup preferred over truncated RNA).

---

## 9. Prior Fix Preservation

| Check | Result |
|-------|--------|
| Issue #25 MPOLICY padding | **Preserved** — not in change set |
| Issue #26 MPREM / MMODPREM | **Preserved** — not in change set |
| Issue #21H ABA path for PPACH-banked | **Preserved** — primary path unchanged |
| Issue #45 exception gate | **Extended** — still blanks when incomplete |

---

## 10. Regression Testing Checklist (for Validation Agent)

- [ ] Trace 010157076C, 010161748C, 010348734C: `MBANKNO` populated only with both halves; values masked in reports
- [ ] Spot-check ≥10 previously banked PPACH policies: `MBANKNO` byte-identical to pre-change output (or same run baseline without PPPAC file)
- [ ] Exception CSV row count drops from 763 toward ~15 (± small ABA edge variance)
- [ ] All remaining exceptions still `MBILLFRM=2`; policy rows still present in quikmstr
- [ ] No change to quikridr / quikplan / premium fields on sample policies
- [ ] `MBILLFRM` unchanged for PAC population
- [ ] Log shows PPPAC load count and fallback applied count
- [ ] Publish modified `quikmstr.csv` only to `Output/Test_Validation/` on PASS

---

## 11. Recommended Development Agent Task

**Switch model to Composer 2.5.** Read `AI_Agents/Development_Agent.md`.

1. Surgical edit to **both** `app.py` and `QLA_Migration/app.py` (keep in sync).
2. After existing PPACH banking cache build:
   - `find_extract('pppac')` → load PPPAC (`on_bad_lines='skip'`, strip columns).
   - Build policy→account map from `E_ACCOUNT_NUMBER` (usable-account rules).
   - For policies **not** already in `_ppach_bank_map` / without usable PPACH account: resolve ABA via existing `aba_lookup`, then RNA if needed (single distinct ABA only).
   - On success, set `_ppach_bank_map[pol] = f"{aba}/{acct}"` and update `_ppach_acct_meta`.
3. Update Issue #45 gate messages to reflect PPPAC/ABA outcomes without blanking valid recovered banks.
4. Version bump both app.py files (next after v57.76 → **v57.77** unless concurrent bumps).
5. Add `QLA_Migration/_validate_issue45_pppac_fallback.py`.
6. Do **not** change Sync_Rulebook, crosswalk, MBILLFRM mapping, or unrelated functions.
7. Do **not** regress #25 / #26 / #21H PPACH primary path.

**User must explicitly approve Development** after reviewing this Risk report.

---

## Appendix

- Planning: `Issue_45_Planning_Report.md`
- Dependency Gate: `Issue_45_Dependency_Gate.md` (**PASS**)
- Source investigation: `Issue_45_Source_Investigation_Report.md`
- Analysis: `_analyze_pppac_source.py`, `_analyze_aba_coverage.py`
