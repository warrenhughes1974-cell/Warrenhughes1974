# Issue #45 — Intake Summary

**Issue:** #45 — Bank Draft Account Validation / PPPAC Account Fallback  
**Date:** 2026-07-12  
**Framework stage:** Intake complete (G0)  
**Status:** Approved → Planning  
**Owner:** Conversion (Warren) · **Reporter:** Eric  
**Priority:** High (bank-draft UAT / client ask)  
**Business status:** No Development until G1 + G2 + G3  

**Model:** Cursor Grok 4.5 (locked Intake stage)

---

## 1. Client / business symptom (verbatim + normalized)

**Client ask (verbatim from Eric, 2026-07-12):**

> Is there a way that the PPPAC_PACDetail_Extract_20260630 can be incorporated? This Extract appears to have the E_ACCOUNT_NUMBER information that is currently not being imported.

**Normalized:**

Bank-draft policies (`PPOLC.BILLING_FORM = PAC` → `quikmstr.MBILLFRM = 2`) currently pull banking from **PPACH** only. When PPACH has no usable account, Issue #45 blanks `MBANKNO` and writes `Reports/bank_draft_account_exceptions.csv` (763 policies). A new LifePRO extract **PPPAC** (PAC Detail) contains `E_ACCOUNT_NUMBER` for most of those exceptions. Eric asks to incorporate PPPAC so those account numbers are imported.

**Prior Issue #45 work already in production path (v57.61):** exception reporting + blank `MBANKNO` when PPACH account missing. This intake extends #45 to **add PPPAC as a fallback account source**.

---

## 2. Example policies

From source investigation (masked accounts only):

| QLAdmin MPOLICY | LifePRO POLICY_NUMBER | Current | PPPAC account (masked) |
|-----------------|----------------------|---------|-------------------------|
| 010157076C | 9010157076 | Exception — no PPACH account | ****2919 |
| 010161748C | 9010161748 | Exception — no PPACH account | ****0581 |
| 010348734C | 9010348734 | Exception — no PPACH account | ****8787 |

Fleet evidence: **750 / 763** exceptions have usable PPPAC `E_ACCOUNT_NUMBER`; **13** remain missing in both PPACH and PPPAC.

---

## 3. Suspected domain

| Layer | Path / table | Role |
|-------|--------------|------|
| Source (current) | `PPACH_PACHistory_Extract_*.csv` | Primary ABA + account (Issue #21H) |
| Source (new) | `PPPAC_PACDetail_Extract_20260630.csv` | Current PAC detail — account only |
| Source (billing) | `PPOLC` `BILLING_FORM=PAC` | Identifies bank-draft population |
| Target | `quikmstr.MBANKNO` | `ABA/ACCOUNT` string |
| Exceptions | `Reports/bank_draft_account_exceptions.csv` | Missing-account audit |

**Domain:** Policy master banking / bank draft — **not** premiums, riders, rates, loans, or claims.

---

## 4. In scope / out of scope (first pass)

### In scope

- Load PPPAC and join on `POLICY_NUMBER`
- Use PPPAC `E_ACCOUNT_NUMBER` **only when PPACH has no usable account**
- Recover ABA for PPPAC-fallback policies via existing Issue #21H chain (`aba_routing_lookup` → truncated fallback sources as planned)
- Refresh exception CSV reasons (missing account vs missing routing)
- Preserve: policy still converts when banking incomplete; `MBILLFRM` unchanged

### Out of scope

- Replacing PPACH as primary banking source
- Changing the 6 PPACH≠PPPAC conflict policies (PPACH present → untouched)
- Redesigning Issue #21H ABA recovery architecture
- Changing `MBILLFRM` mapping or PAC detection
- Emitting full unmasked accounts in reports

---

## 5. Related issues

| Issue | Relationship |
|-------|--------------|
| **#45** (v57.61) | Exception gate for blank PPACH account — this work extends it |
| **#21H** | ABA/account → `MBANKNO`; lookup recovery — must preserve |
| **#21J** | PAC → `MBILLFRM=2` — do not change |
| **#25 / #26** | MPOLICY padding / MPREM — unrelated; must not regress |

---

## 6. Artifact inventory

| Artifact | Status |
|----------|--------|
| Eric email ask | Received |
| `PPPAC_PACDetail_Extract_20260630.csv` | Present in `QLA_Migration/Source/` (2,122 rows) |
| `PPACH_PACHistory_Extract_20260630.csv` | Present |
| `bank_draft_account_exceptions.csv` | Present (763 rows) |
| Source investigation report | `Issue_45_Source_Investigation_Report.md` |
| Analysis scripts | `_analyze_pppac_source.py`, `_analyze_aba_coverage.py` |
| Screenshots | Not required for this fleet-proven gap |

---

## 7. Owner / severity / immediate blockers

| Item | Value |
|------|-------|
| Owner | Conversion |
| Severity | High (client UAT banking completeness) |
| Immediate blockers at intake | None for research — PPPAC present; target field known (`MBANKNO`) |
| Business decision still needed at Planning | Exact ABA rule when PPPAC supplies account but PPACH has no ABA |

---

## 8. Gate G0 checklist

- [x] Issue folder exists under `Issue_Log_Items/Issue_45/`
- [x] Intake summary written
- [x] Example policies listed
- [x] Owner and priority assigned
- [x] No code or rulebook changes made

**Next:** Planning Agent.
