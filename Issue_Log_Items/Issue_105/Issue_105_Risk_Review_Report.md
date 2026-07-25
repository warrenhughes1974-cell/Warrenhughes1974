# Issue #105 — Risk Review Report

**Issue:** #105 — QuikRidr MPAR must be True for participating products  
**Framework stage:** Risk Agent (G3)  
**Status:** **GO** — awaiting Development approval  
**Generated:** 2026-07-24  
**Agent:** Risk Agent (Cursor Grok 4.5, read-only)

**Status note:** Risk analysis only — no production code changes.

---

## Go / No-Go Recommendation

**GO** — Clear product-level defect: all `MPAR` values are `0` while 2,895 coverage rows sit on participating products (`quikplan.PAR=1`). Fix is a single-field override with a hard join to existing product PAR. Blast radius is bounded and measurable.

---

## 1. Is this actually an issue?

**Yes.** QLAdmin participating UI flag (`quikridr.MPAR`) never turns on. Product participating is already correct on `quikplan.PAR` for 56 plans. Current `PPBENTYP.PAR_TYPE` path does not implement the client’s product rule (and can disagree with product PAR).

---

## 2. Current vs proposed mapping

| Item | Current | Proposed |
|------|---------|----------|
| Authority | `PPBENTYP.PAR_TYPE` → MPAR (miss → 0) | `quikplan.PAR[MPLAN]` → MPAR |
| Par product rows | MPAR `0` | MPAR `1` |
| Non-par product rows | MPAR `0` | MPAR `0` (unchanged) |

---

## 3. Before / after impact (current Output simulation)

| Metric | Count |
|--------|------:|
| Rows changing `MPAR` `0 → 1` | **2,895** |
| Distinct policies affected | **2,683** |
| Rows expected unchanged at `0` | **4,039** |
| Rows that would incorrectly go `0 → 1` on non-par plans | **0** (by construction if lookup uses plan PAR) |
| Reverse defects today (`PAR=0` but `MPAR=1`) | **0** |

Top MPLANs among flips: `1L10SO` (441), `1L1095` (378), `170858` (283), `1L14SC` (232), `5L0110` (216), …

---

## 4. Blast radius

| Item | Assessment |
|------|------------|
| Tables | `quikridr` only |
| Columns | **`MPAR` only** |
| Plan setup | Untouched (consumes existing `PAR`) |
| Rates / claims / fees / MPREM | Untouched |
| #25 / #26 | Unaffected |

---

## 5. Regression risks

| Risk | Level | Mitigation |
|------|-------|------------|
| Ridr-only rebatch without plan PAR map | Medium | Load/cache product PAR map on every quikridr emit path |
| Emitting `True`/`False` text | Low | Force `"1"`/`"0"` |
| Accidental MPREM/fee churn | Medium if coded broadly | Touch only MPAR assignment block |
| Client expected PAR_TYPE election | Low–Med | Symptom says product; UAT confirms |

---

## 6. Validation plan (post-Dev)

1. Zero `quikridr` rows with plan PAR=1 and MPAR≠1.
2. Zero rows with plan PAR=0 and MPAR=1.
3. Non-candidate columns unchanged vs pre-fix snapshot (or field-scoped diff).
4. Schema / field order unchanged.
5. Publish `Output/Test_Validation/quikridr.csv` on PASS.
6. Accountability **IN_DATA** before Closure (G7).

---

## 7. Development constraints

- Surgical only; bump `APP_VERSION` in root + `QLA_Migration/app.py`.
- Prefer override after existing MPAR assignment (minimal diff).
- Do not change `quikplan.PAR`, Issue A rules, or #25/#26 paths.
- Do not start until: **“Approved for Development.”**

---

## Gate G3

**GO** — Ask for Development approval.
