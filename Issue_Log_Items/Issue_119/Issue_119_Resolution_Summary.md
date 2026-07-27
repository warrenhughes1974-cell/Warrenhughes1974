# Issue #119 — Resolution Summary (Stage 8, Closure)

**Closed:** 2026-07-27  
**Engine:** v58.43  
**Status:** Closed — G7 gate satisfied  

---

Resolution: Paid-Up Addition coverages now set QuikRidr.MPAR to 0 (non-participating), matching QLAdmin PA-add behavior instead of copying the base coverage’s participating flag.

---

## The problem, in plain terms

Robert corrected the PUA design note: a PUA is not participating. When QLAdmin adds a PA rider it sets the coverage PAR/`MPAR` to 0 even if the base is participating. Our conversion had left PUA `MPAR` matching the base (493 of 494 rows at `1`), and Issue #111 validators had required that match.

## Fix (v58.43)

- `_apply_pua_rider_inheritance` forces `MPAR = "0"` for every PUA rider.
- `#105` / accountability validators expect PUA `MPAR=0` (no base inherit for participation).
- Briefing §10 check text aligned with §7.2.

## Validation / G7 (full Output 2026-07-27)

| Check | Result |
|---|---|
| `validate_issue119_pua_mpar.py` | **PASS** — 494/494 PUA `MPAR=0` |
| `validate_issue105_mpar.py` | **PASS** — non-PUA product PAR intact |
| Accountability `#119` / `#105` | **IN_DATA** |
| Regression | **PASS** — only PUA `MPAR` changed |
| `Test_Validation/quikridr.csv` | Published |

## Trace

| MPOLICY | MPLAN | MPAR |
|---------|-------|------|
| 9010310404C | 1960PA | 0 |
| 9010150910C | 221EPA | 0 |
| 9010360290C | 1708PA | 0 |
| 9010143726C | 221END (base control) | 1 |

## Non-changes

Base coverage `MPAR`, `quikplan` (no PA plan emit), PUA date/age/status inheritance, MPREM, MPOLICY width.

## Rollback

Revert v58.43 `MPAR="0"` line in `_apply_pua_rider_inheritance` (both `app.py` copies) and restore prior `quikridr.csv` / validators if needed.

## Git release

- Branch: `issue-34-pr7-quikisrr`
- Commit: *(filled after push)*
- Network machines: pull, then re-emit `quikridr` (or full batch) — Output is gitignored.
