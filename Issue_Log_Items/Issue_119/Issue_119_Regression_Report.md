# Issue #119 — Regression Report

**Date:** 2026-07-27  
**Engine:** v58.43  
**Result:** **PASS**

---

## 1. Row counts

| Table | Count | Notes |
|-------|------:|-------|
| `quikridr` | 6,936 | Unchanged (field-only fix) |
| `quikmstr` | 5,084 | Untouched |
| `quikplan` | 141 | Untouched; synthetic `*PA` still absent |

Schema: `quikridr` still **40** columns; field order unchanged.

---

## 2. Intentional change only

| Population | Change |
|------------|--------|
| Synthetic `*PA` PUA rows (494) | `MPAR` → `0` only |
| Non-PUA rows | `MPAR` unchanged vs `#105` product rule (**0** mismatches) |

PUA sample `9010310404C` / `1960PA` still has inherited dates/status/units (`MPHSTAT=41`, `MEFFDATE`/`MPAYUP`/`MAGE`/`MUNIT` intact).

---

## 3. Prior-fix spot checks

| Check | Result |
|-------|--------|
| Issue #2 MPOLICY width-11 on control `9010143726C` | **PASS** (`len=11`) |
| Issue #26 MPREM still populated on phase-1 fleet | **PASS** (4,266 / 5,084 non-zero) |
| Issue #105 non-PUA product PAR → MPAR | **PASS** (validator v1.2) |
| Issue #60 / #111 no PA plan in `quikplan` | **PASS** (`1960PA` absent) |

---

## 4. Validators re-run

| Script | Result |
|--------|--------|
| `validate_issue119_pua_mpar.py` | **PASS** |
| `validate_issue105_mpar.py` | **PASS** |

---

## Verdict

**PASS** — blast radius limited to `quikridr.MPAR` on PUA coverages. Proceed to Closure.
