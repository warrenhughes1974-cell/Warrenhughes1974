# Issue #60 — Intake Summary

**Issue:** #60 — PUA phase fields + base plan interest (Chris / New Era 7/14/2026)  
**Working alias:** Issue Z (user)  
**Framework stage:** Intake Agent (G0)  
**Status after intake:** Planning  
**Generated:** 2026-07-14  
**Model:** Cursor Grok 4.5 (locked)  
**Owner:** Conversion (primary) — `quikridr` PUA inheritance + base-plan rate assumptions (`QuikPlCv` / `QuikPlTv`)  
**Priority:** High — blocks correct PUA / PUA-value calc; **directly conflicts with Issue #56 Development path**  
**Reporter chain:** Chris → Robert (email 7/14/2026); screenshots of QLAdmin Coverage + plan Cash Values / Reserves  

---

## Client symptom (verbatim)

> Do not add factors. Let the system calculate them. And I wouldn’t add the PA plans to the plan file unless there’s some really good reason to do so. It makes it more complicated to keep mortality/interest rates up to date if/when they change on the base plan.
>
> Here’s your problem. The status should be 41, effdate and age should be the same as the base phase: Payup date should also be the effdate or effdate + one year.
>
> Pretty obvious if you look at the data. You’re never going to calc good PUA values if the interest rate is zero. You’ll also need to fix mlastann in quikridr to match the base phase. Fix these and the run data admin, rebuild CVs on this policy and you should have better results.

Screenshots (Coverage Information + `1960PO` Cash Values / Reserves keys) saved as:

`Issue_Log_Items/Issue_60/evidence/chris_email_pua_screenshots_20260714.png`

---

## Normalized symptom

On the PUA sample (same policy family as #56 — **`010310404C`**, base `1960PO` / phase-2 `1960PA`), New Era (Chris) says bad PUA values are caused by **wrong PUA phase setup** and **zero interest on the base plan**, not by missing a separate PA plan file.

| Area | Current (Output / UI) | Chris expected |
|------|------------------------|----------------|
| Phase-2 `MPHSTAT` | **22** (Active) | **41** (Paid Up) |
| Phase-2 `MEFFDATE` | **20110128** (attained / PUA issue) | Same as base: **19690128** |
| Phase-2 `MAGE` | **68** | Same as base: **26** |
| Phase-2 `MPAYUP` | **20460128** (= base expiry/payup) | **Eff date** or **eff date + 1 year** |
| Phase-2 `MLASTANN` | **15** (from PUA eff 2011) | Match base phase (**57**) |
| Base `1960PO` Cash Values `NFOInt` | **0.00** / blank in emit | Non-zero (needed for PUA calc) |
| Base `1960PO` Reserves `IntRate` / methods | **0.00** / blank `RvMeth`/`IntMeth` (M) | Non-zero int + methods populated |
| PA plan in plan file | #56 was about to **add** `1960PA` | **Do not add** unless strong reason |
| Factors | (implied conversion/plan factors) | **Do not add** — let QLAdmin calculate |

Post-fix UAT path per Chris: fix data → run Data Admin → rebuild CVs on the policy.

---

## Example policies

| QLA | LifePRO | Notes |
|-----|---------|-------|
| **`010310404C`** | `9010310404` | Primary — matches screenshot (base age 26, face 15,000; PUA face ~5,943; PUA age 68 / eff 2011) |

Additional PUA peers: not cited in this email; Planning should decide fleet vs sample-only after field rules are locked.

---

## Intake verification (read-only, 2026-07-14)

### `quikridr` — `010310404C`

| Ph | `MPHSTAT` | `MLASTANN` | `MPLAN` | `MEFFDATE` | `MPAYUP` | `MAGE` | Face (`MUNIT`×1000) |
|----|-----------|------------|--------|------------|---------|--------|---------------------|
| 1 | 22 | **57** | 1960PO | 19690128 | 20460128 | **26** | 15,000 |
| 2 | **22** | **15** | 1960PA | **20110128** | 20460128 | **68** | 5,942.78 |

Matches Chris’s screenshot exactly. Inheritance today (`_apply_pua_rider_inheritance`) copies only **`MPLAN` (→ `*PA`), `MEXPRY`, `MPAYUP`** from phase 1 — **not** `MEFFDATE`, `MAGE`, `MPHSTAT`, or `MLASTANN`. `MLASTANN` is derived from each row’s own `MEFFDATE`, so wrong PUA eff date → wrong `MLASTANN`.

### Base plan rate keys — `1960PO` in `Output/rates`

| Table | Interest / method fields observed |
|-------|-----------------------------------|
| `QuikPlCv` | `NFOINT` **blank**; `INTMETHCV` = **0** |
| `QuikPlTv` | `RSVINT` / `RSVMETH` / `INTMETHTV` **blank** |

Aligned with gap grid: `1960PO` NFOINT / QuikPlTv assumptions **MISSING** (issue-year CRVM). Chris’s UI showing **0.00** interest is consistent with empty/zero assumption keys.

---

## Suspected domain

1. **`quikridr` PUA phase rules** — status, dates, age, payup, mlastann relative to base  
2. **Base-plan rate assumptions** — `QuikPlCv.NFOINT` (+ related) and `QuikPlTv` reserve interest/methods for `1960PO` (and likely peer traditional plans)  
3. **Product-setup philosophy** — omit PA from plan file; PUA values from base + correct phase metadata (conflicts with #56 Option A)

**Not primarily:** claims, memo, premium history (#21F), MSTATUS on `quikmstr` (#59 closed).

---

## In scope (first pass)

- Lock Chris’s PUA phase field rules vs current `_apply_pua_rider_inheritance` + `MLASTANN` logic  
- Confirm whether `MPHSTAT=41` is phase-2 only or also drives header status  
- Confirm `MPAYUP` = eff vs eff+1 year (open business choice)  
- Trace zero `NFOINT` / reserve int on `1960PO` to rate emit / CSO crosswalk gap  
- Reconcile **#56 Development plan** (add `1960PA` + own CV/TV) with Chris (“don’t add PA plans”)  
- Document UAT: Data Admin + rebuild CV on `010310404C`

## Out of scope (first pass)

- Coding / rulebook changes (Intake)  
- Wholesale redesign of all rate assumption grids  
- Changing base traditional CV grids that already match LifePRO (client #56 control) until Planning proves coupling  
- Adding conversion “factors” Chris told us not to add  

---

## Related issues

| Issue | Relevance |
|-------|-----------|
| **#56** | Same policy / PUA CV symptom. Robert Slack: **add** `1960PA` + own CV/TV. **Chris email: do not add PA plans.** **Hold #56 Development until this conflict is resolved.** |
| **#40 / #41** | Base `1960PO` QuikCvs present; interest assumptions still missing |
| **#21K** | PUA face / MUNIT precision — preserve |
| **#21E / #37** | Traditional CV compute path |
| **#25 / #26** | Must not regress MPOLICY / MPREM |
| Rate gap grid | `1960PO` NFOINT / QuikPlTv MISSING — same Chris interest finding |

---

## Artifact inventory

| Artifact | Present? |
|----------|----------|
| Chris email guidance (7/14/2026) | Yes (pasted) |
| Screenshots (coverage + CV/reserve keys) | Yes — `evidence/chris_email_pua_screenshots_20260714.png` |
| Example policy | Yes — `010310404C` (inferred + Output-matched) |
| Current `quikridr` before-state | Yes (verified) |
| Current `QuikPlCv`/`QuikPlTv` for `1960PO` | Yes (NFOINT/RSVINT blank) |
| Correct non-zero interest rate value(s) | **No** — need actuarial / CSO source |
| Explicit “eff vs eff+1” payup choice | **Open** |
| Written confirmation that #56 path is withdrawn | **No** — treat as conflict until Planning/client lock |

---

## Immediate blockers visible at intake

1. **#56 vs #60 strategy conflict** — Robert (add PA plan + rates) vs Chris (omit PA plan; fix phase + base interest). Do **not** approve #56 Development until reconciled.  
2. Correct **NFO / reserve interest values** for `1960PO` (and scope of peer plans) not specified in email.  
3. **`MPAYUP` rule** ambiguous: eff date **or** eff + 1 year.  
4. Whether phase-2 `MPHSTAT=41` is universal for all PUA phases or conditional.

---

## Severity / owner

| Field | Value |
|-------|--------|
| Severity | **High** — Chris: PUA values cannot calc correctly with zero interest + wrong phase dates/status/age/mlastann |
| Owner | Conversion (`quikridr` + rate assumptions); Client/New Era for interest sources and #56 path confirmation |
| AGENTS.md | Surgical only; **no code at Intake** |

---

## Gate G0 checklist

- [x] Issue folder `Issue_Log_Items/Issue_60/`  
- [x] Intake summary written  
- [x] Example policies listed  
- [x] Owner and priority assigned  
- [x] No code or rulebook changes  

**Next:** Planning Agent (same model) + Dependency Gate — **must open with #56 conflict resolution**.
