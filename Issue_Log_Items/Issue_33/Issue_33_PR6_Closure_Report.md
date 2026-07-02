# Issue #33 — PR-6 Closure Report (QUIKISSC)

**Issue:** #33 — ISWL Phase 6 QUIKISSC (Surrender Charges)  
**PR:** PR-6  
**Closure date:** 2026-07-01  
**Epic status:** **CLOSED — APPROVED**

---

## Final authority

`QLA_Migration/Output/rates/QuikIssc.csv` is the **approved final authority** for ISWL full surrender charge schedules. No further QuikIssc code changes unless a future review identifies a defect.

**Approved semantic review:** [`Issue_33_Phase6_QUIKISSC_Semantic_Review.md`](Issue_33_Phase6_QUIKISSC_Semantic_Review.md)

---

## Approved mapping decisions (locked)

| Decision | Value |
|----------|-------|
| Target MPLANs (8) | `1658C1`, `1658CS`, `1659C2`, `1659CR`, `1659CS`, `1659SR`, `1669SR`, `1679CS` |
| Source schedule | LifePRO `Rate_Table` hub **`659 CEN II`**, **`TYPE_CODE=SL`** |
| Source dimensions | `AGE=0`, `SEX=M`, `BAND=1`, `UNDERWRITING_CLASS=S` |
| QLAdmin UWCLASS | **`SM`** (source `S` = **Smoker**, not Standard) |
| Duration pivot | Durations 1–14 → `SCHG01`–`SCHG14` |
| Trailing columns | `SCHG15`–`SCHG20` **blank** |
| Segmentation | `ISSCNTRY=0000`, `ISSUEST=00`, `BAND=01`, `GENDER=M` |
| Replication | Same hub schedule replicated to **all 8 ISWL MPLANs** |
| Percent format | Percent literals (`100.0000` = 100%) |

---

## Validation evidence (preserved)

| Artifact | Result |
|----------|--------|
| `QuikIssc.csv` | **8 data rows** |
| `iswl_quikissc_reconcile_summary.json` | V-ISSC-01 through V-ISSC-12 **ALL PASS** |
| `iswl_quikissc_regression_baseline.json` | Phase 1–5 factor counts unchanged |
| Phase 1–5 independent re-run | **ALL PASS** |

**Reconcile command:**

```text
python tools/validators/iswl_quikissc_reconcile.py --write-baseline --emit-csv
```

---

## Post-development fix (non-business)

| Fix | Scope |
|-----|-------|
| Validator print `PSEGT→SL` → `PSEGT->SL` | Windows cp1252 console encoding only; no loader/emit logic change |

---

## Issue #33 scope boundary

Issue #33 covered **QUIKISSC (full surrender)** only. **No remaining work under Issue #33.**

Deferred items explicitly out of scope for Issue #33:

| Item | Track |
|------|-------|
| QuikIsrr (partial surrender) | New issue / PR-7 planning |
| Expenses (UF/U1/U2/U3/G2/G3/GF) | New issue — product expense setup |
| QuikIswl values | Separate |
| Production DBF / `app.py` integration | Separate integration issue |

---

## ISWL program — what remains after Issue #33

All six phased ISWL **rate-table** emit targets are complete:

| Phase | Table | Status |
|-------|-------|--------|
| 1 | QUIKCVS → QuikCvs | APPROVED |
| 2 | QUIKGPS → QuikGps | APPROVED |
| 3 | QUIKCOI → QuikCoi | APPROVED |
| 4 | QUIKGCOI → QuikGcoi | APPROVED |
| 5 | QUIKUINT → QuikUint | APPROVED |
| 6 | QUIKISSC → QuikIssc | **APPROVED** |

### Remaining ISWL table (rate-family)

**`QuikIsrr`** — Partial surrender values for UL/ISWL (QLAdmin Help §7.143).

- Adjacent to closed `QuikIssc` (full surrender) but a **separate** QLAdmin table.
- No planning package, loader, or segment-to-source proof exists in repo.
- Explicitly deferred from Issue #33 Phase 6 scope.

### Also remaining (broader UL setup — not a single rates CSV)

**ISWL Expenses** — UF/U1/U2/U3/G2/G3/GF segments per Product Book.

- PSEGT: **UF wired 8/8**; U1/U2/U3/G2/G3/GF **0/8** in PSEGT.
- Rate_Table: sparse UF row on hub (`659 CEN II`, value 0); no authoritative U1/U2/U3 rate grids in extracts.
- Partial policy-fee coverage via `quikridr.MANNLFEE` (Issue #21C) — does not satisfy full expense requirement.
- QLAdmin targets: monthly expense per policy, percent of premium, per-$1,000 load.

---

## Recommended next step

**Open Issue #34 (or equivalent) — QUIKISRR planning pass** (research only, mirror Issue #33 pattern):

1. Confirm QLAdmin `QuikIsrr` schema (Help §7.143).
2. Trace LifePRO partial-surrender segment path on all 8 ISWL coverages (PCOVRSGT → PSEGT → rate source).
3. Determine whether partial surrender reuses hub `659 CEN II` schedule, a distinct segment, or policy-level fields.
4. SME gates for dimensional scope, percent format, and row-count estimate.
5. Do **not** begin development until planning + SME closure (same gate pattern as QUIKISSC).

**Parallel track (separate issue):** ISWL expense research — trace UF rate pointer, inspect BP/BI nesting for U1/U2/U3, SME confirmation of three expense components.

---

## Closure recommendation

**Issue #33 — CLOSED.** PR-6 QUIKISSC approved as final authority for full surrender charges.
