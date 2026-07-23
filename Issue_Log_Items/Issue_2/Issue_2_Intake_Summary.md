# Issue #2 — Intake Summary

**Issue:** #2 — 11 Character Policy Number  
**Date:** 2026-07-23  
**Framework stage:** Intake complete (G0)  
**Status:** Proceed to Planning  
**Owner:** Conversion (Warren) · Reporter: Warren (Active-QLA Testing)  
**Business status:** Go direction given — scrap current transform; source policy number + trailing `C`; right-justify in 11-char QLA fields  
**Tracking (client sheet):** Active-QLA Testing · Raised 5/5/2026 · Priority No-Go historically (blocked on QLA schema); schema now widened by Warren

---

## Client / business symptom (verbatim)

> Active-QLA Testing — 11 Character Policy Number  
> 7/14 — Testing program to modify all of the places we store the plan code in QLA. have the program. Need to convert into it.

**Warren direction (2026-07-23):**

1. QLA extract/load tables have already been modified to allow **11 characters**.
2. **Scrap** the current LifePRO → QLA policy-number conversion approach.
3. New rule: **keep the source-system policy number and append a single `C`**.
4. Policy number must be **right-justified** when imported into DBFs from CSVs.

---

## Normalized finding

Today the converter does **not** keep the LifePRO policy number. Typical path:

| Step | Today | Example |
|------|-------|---------|
| Source | LifePRO `POLICY_NUMBER` | `9010143726` |
| Crosswalk | Strip leading `9` + append `C` (via `Master_Crosswalk`) | `010143726C` |
| Width (#25) | `format_qladmin_mpolicy()` → exactly **10** chars, left-pad / right-justify | `010143726C` |

**Required after #2:**

| Step | New | Example |
|------|-----|---------|
| Source | LifePRO `POLICY_NUMBER` (stripped of trailing extract pad only) | `9010143726` |
| Transform | Append `C` | `9010143726C` |
| Width | Right-justify in **11**-character field | `9010143726C` (exact 11) or shorter keys left-padded to 11 |

This **supersedes Issue #25** (10-char MPOLICY pad). Framework “preserve #25” does **not** apply as a freeze — #2 replaces the width/identity contract by explicit business direction.

---

## Example policies (before → proposed)

| LifePRO source | Current QLA MPOLICY | Proposed QLA MPOLICY |
|----------------|---------------------|----------------------|
| `9010143726` | `010143726C` | `9010143726C` |
| `9010148272` | `010148272C` | `9010148272C` |
| `901222DC` | `  01222DCC` | `  901222DCC` (rjust 11) |
| `9014059` | `   014059C` | `   9014059C` (rjust 11) |
| `9014100C` | `  014100CC` | edge — see Planning (already ends with C) |

---

## Suspected domain

**Cross-cutting policy key** — every table that stores policy number:

`MPOLICY` on quikmstr, quikridr, quikclid, quikbenf, quikprmh, quikdvdp, quikdvpr, quikloan, quikbenh, quikrmst, QuikIsrr, quikclms, quikclmp; `MEMOKEY` on quikmemo.

Not: plan codes (MPLAN), rates content, premium amounts (#26).

---

## Related issues

| Issue | Relationship |
|-------|--------------|
| **#25** | Current 10-char pad — **superseded by #2** |
| **#50** | MEMOKEY DBF left-pad / SEEK — must retarget to 11-char |
| **#78 / #84 / claims** | Join/lookup helpers that strip/rebuild `…C` keys |
| **Framework hard rule** | “Preserve #25” — **override documented** for this issue |

---

## In scope / out of scope

| In scope | Out of scope |
|----------|--------------|
| Replace LP→QLA policy identity: source + `C` | Changing LifePRO extracts |
| Emit right-justified 11-char keys in CSVs | Redesigning non-policy crosswalk (product/entity) |
| Update `format_qladmin_mpolicy` width/contract | Unrelated field mapping (#26 MPREM, etc.) |
| Parallel strip9+C paths (QuikIsrr, helpers) | Client UAT of non-key business fields |
| Validators / DBF writers assuming C(10) | |
| **Full conversion batch as Validation proof** (user-required) | |

---

## Immediate blockers visible at intake

| Item | Status |
|------|--------|
| QLA tables widened to 11 | **Met** (Warren confirmed) |
| Business rule | **Met** (source + `C`, right-justify) |
| Issue folder | Creating with this Intake |
| Edge cases (source already ends with `C`; garbage `-------------`) | Open for Planning defaults |

---

## Artifact inventory

| Artifact | Status |
|----------|--------|
| Client tracking row (Active-QLA Testing) | Provided in chat |
| QLA schema change to 11 chars | Done outside repo (Warren) |
| Source PPOLC / PPBEN | Present (`…_20260630`) |
| Current Output keys (10-char) | Present — before-state |
| Prior Issue_2 package | None (greenfield) |

---

## Severity / owner

| | |
|--|--|
| Severity | **Critical** — fleet-wide key change; blocks correct QLA load identity |
| Owner | Conversion |
| Priority | Go for framework; historical sheet No-Go was schema-blocked (now cleared) |

---

## Gate G0

- [x] Issue folder under `Issue_Log_Items/Issue_2/`
- [x] Intake summary written
- [x] Example policies listed
- [x] Owner and priority assigned
- [x] No code or rulebook changes made

**Proceed to Planning (Pre-Development Auto-Chain).**
