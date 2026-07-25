# Issue #75 — Risk Review Report (REOPEN — PPCOM recovery)

**Issue:** #75 — Bank Acct / `MBANKNO` via PPCOM  
**Framework stage:** Risk Agent (G3)  
**Date:** 2026-07-25  
**Model:** Cursor Grok 4.5 (locked)  
**Code changes:** None (risk simulation / analysis only)

---

## Go / No-Go

**CONDITIONAL GO** for Development — rebuild PPCOM-backed ABA (and optional account-form) lookup, keep v57.92 QLA-safe emit, fill blanks where ABA is uniquely resolved.

| Condition | Requirement |
|-----------|-------------|
| C1 | Emit ABA only when **exactly 9 digits** and **ABA checksum passes** (native 9 or checksum-validated pad from 8) |
| C2 | Default Development scope = **unique ABA only** (656 fills); ambiguous (205) blank + exception unless user approves latest-date |
| C3 | Do not invent ABA when PPCOM has no match (49 stay blank) |
| C4 | Account half = digits-only; **no new account zfill**; prefer PPCOM digit form when it differs only by leading zeros |
| C5 | Regression guard: 9010713704C and other already-valid rows stay byte-identical unless intentionally corrected |

---

## Impact summary (read-only against current Output + PPCOM stream)

| Population | Count |
|------------|------:|
| Bank-draft policies | 2,132 |
| Already filled QLA-safe | 1,222 |
| Blank today | 910 |
| **Unique PPCOM ABA → fill** | **656** |
| Ambiguous PPCOM ABA | 205 |
| No PPCOM match | 49 |
| Recovered ABA checksum failures | **0** (among 861 unique+ambig resolutions) |

Evidence: `evidence/issue75_ppcom_blank_draft_recovery.csv`

### Trace examples (simulated after)

| MPOLICY | Before | After (unique path) |
|---------|--------|---------------------|
| 9010161748C | blank | `091303855/0000002000581` |
| 9010157076C | blank | `104910135/212919` |
| 9010348734C | blank | `081518113/208787` |
| 9010713704C | `104000016/47374579` | unchanged |

### Leading zeros

- ~55–91 currently filled `MBANKNO` values already carry leading zeros on what looks like an 8-digit core; those zeros come from **source extracts**, not a converter `zfill` on accounts.
- PPCOM sometimes stores a different zero-padding than PPACH/PPPAC (e.g. `0059281456` vs `59281456`).
- Risk recommendation: align emit to **PPCOM account digits** when matched; never pad accounts in code.

### ABA pad note

Blind `zfill(9)` on truncated PPACH ABA is still **unsafe** (e.g. `09130385` → `009130385` fails checksum). PPCOM often supplies the real 9th digit (`091303855`). Development must prefer PPCOM’s native 9-digit value.

---

## Blast radius

| In scope | Out of scope |
|----------|--------------|
| `quikmstr.MBANKNO` only | `MBILLFRM`, premiums, status, claims |
| `aba_routing_lookup.csv` rebuild (or streaming PPCOM cache) | Rulebook schema changes |
| Exception reason refinement | UI bank-name mapping |

---

## Fallback options

| Option | Fills | Risk |
|--------|------:|------|
| **A. Unique only (recommended)** | +656 | Lowest wrong-routing risk |
| B. Unique + latest ambiguous | +861 | 205 may get wrong bank |
| C. Status quo (no PPCOM rebuild) | +0 | Leaves 910 blank drafts |

---

## Regression surfaces

- Already-valid `MBANKNO` must not flip ABA/account except intentional PPCOM corrections
- #45 PPPAC path must still feed account into the new lookup
- v57.92 gate must still blank unsafe values
- Batch time: prefer offline lookup rebuild (PPCOM ~5.3 GB) over full scan each conversion

---

## Development checklist (when approved)

1. Rebuild `aba_routing_lookup.csv` from June PPCOM for PPACH+PPPAC in-scope accounts (unique only; optional ambig report).
2. Optionally emit `account_form_lookup.csv` (account_key → preferred digit form from PPCOM).
3. Wire converter to prefer rebuilt lookup; keep `#75` QLA-safe helpers.
4. Validator: blank-draft fill rate, checksum, traces, non-candidate unchanged.
5. Publish `quikmstr.csv` to `Output/Test_Validation/` on PASS.

---

## Recommendation

**Ask for Development approval** on Option **A** (unique ABA fills). Confirm with user whether Option B (ambiguous latest-date) and PPCOM-preferred account zeros are in scope for the same release.
