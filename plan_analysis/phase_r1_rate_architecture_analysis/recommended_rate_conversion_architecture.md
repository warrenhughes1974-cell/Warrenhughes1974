# Recommended Rate Conversion Architecture (Future Implementation)

**This is a recommendation document for a LATER phase. Nothing here is built in Phase R1.**
It is intentionally lightweight — no governance bureaucracy, no excess manifests — and is designed to stay
**fully isolated** from the stable claims/plan conversion so it cannot regress production conversions.

---

## 1. Guiding principles (aligned to AGENTS.md)

- **Isolation first.** A separate rate engine module + separate config + separate output tree. Zero changes to the
  stable `app.py` claims/plan paths to load rates.
- **Configuration-driven**, like the existing rulebook architecture (`Sync_Rulebook_*.csv`) — one rulebook per rate
  family, not hardcoded logic.
- **Plan config before factors.** Enforce the dependency order; never emit a factor row whose plan/key does not
  exist.
- **Deterministic + replay-safe + rollback-safe**, matching the existing platform's guarantees.
- **Smallest viable surface.** Six families share one engine; differences are data, not code.

---

## 2. Dependency order (MUST precede any rate load)

```
1. QuikPlan present & correct            (plan identity, PVO=Y, *VARY* matrix)
2. Plan Values Options members defined   (gender / UW class / band / state-country lists)
3. Plan assumptions set                  (mortality code, reserve method, interest methods, ETI, deficiency)
4. Mortality tables available            (QuikQxs codes referenced by the plan exist)
5. Rate-file-option KEYS built           (QUIKPLxx rows = the segmentation combinations)
   ─────────────────────────────────────────────────────────────────────────────
6. THEN factor VALUES loaded             (QUIKxxS grids: GP, DB, CV, TV, NP, DV)
```

Steps 1–2 already exist in today's quikplan conversion. Steps 3–6 are the new work. **Reserve workstream (TV+NP+GP
deficiency + mortality/assumptions) should be delivered as one coordinated unit**, since the manual couples them.

---

## 3. Proposed module layout (isolated)

```
rate_conversion/                        ← new, isolated; does not touch app.py claims/plan paths
  config/
    rate_families.json                  ← GP/DB/CV/TV/NP/DV family registry (suffix, target table, par-gated?)
    Sync_Rulebook_quikgps.csv           ← per-family source→target field map (mirrors existing rulebook style)
    Sync_Rulebook_quiktvs.csv
    ... (one per family)
    rate_segmentation_rules.json        ← how to derive gender/UW/band/state keys + EFFDATE handling
    mortality_code_map.json             ← LifePRO mortality basis → QLAdmin mortality code (appendix 6.9)
    reserve_method_map.json             ← LifePRO reserve method → {1,2,3,4} + interest method {0,1}
  engine/
    rate_engine.py                      ← generic: read source → normalize → key → stage → validate
    key_builder.py                      ← builds QUIKPLxx keys from plan *VARY* matrix + member lists
    factor_builder.py                   ← builds QUIKxxS factor grids (AGE × CNTL × xx0..xx9)
    rate_validation.py                  ← coverage/orphan/uniqueness/round-trip checks
  staging/                              ← intermediate CSVs (human-reviewable, pre-DBF)
  output/                               ← final per-family outputs (NOT production-authorized DBFs in early phases)
  reports/                              ← validation + reconciliation reports
```

> Rationale: the six rate families are structurally identical (PLAN + segmentation + EFFDATE + AGE + duration grid).
> A **single generic engine + per-family rulebook/adapter** avoids six near-duplicate scripts and keeps blast radius
> tiny.

---

## 4. Staging strategy

- **Two staged artifacts per family:** (a) a **keys** staging CSV (→ QUIKPLxx) and (b) a **values** staging CSV
  (→ QUIKxxS). Keys are produced from the plan's VARY matrix + member lists; values are produced from the actuarial
  source.
- Staging CSVs are **target-schema-only and human-reviewable** before any DBF generation — mirrors the existing
  canonical staging pattern used for claims.
- DBF generation is a **separate, later, explicitly-gated step** (no production-authorized DBFs during discovery /
  prototype phases).

---

## 5. Validation architecture (the heart of correctness)

| Check | What it proves | Confidence basis |
|---|---|---|
| **Plan/key existence** | every factor row's (PLAN+segmentation+EFFDATE) has a QUIKPLxx key | derived from key/value 2-layer model |
| **Coverage / orphan** | every active policy resolves to a populated factor; no policy hits a missing grid | CONFIRMED via Error Valuation behavior |
| **Uniqueness** | no duplicate (PLAN+seg+EFFDATE+AGE+CNTL) rows | LIKELY uniqueness key |
| **VARY consistency** | segmentation columns populated iff the plan's VARY flag = Y | CONFIRMED matrix semantics |
| **Mortality resolvability** | every plan mortality code exists in QuikQxs / appendix code list | CONFIRMED code list |
| **Reserve internal consistency** | TV/NP/GP + method/interest present together for valuation | CONFIRMED NP↔TV coupling |
| **Deficiency sanity** | flag plans where net premium > gross premium (expected deficiency) | CONFIRMED deficiency rule |
| **Round-trip** | re-reading staged output reproduces source factors within tolerance | standard |
| **Gold standard** | a QLAdmin statutory valuation runs with an **empty Error Valuation report** | CONFIRMED |

---

## 6. Versioning & effective-date handling

- Treat **EFFDATE as a first-class part of the key**, not metadata. QLAdmin supports multiple rate generations by
  effective date (CONFIRMED for state/country rate files).
- The loader must support **multiple generations coexisting** per plan and never overwrite an older generation when
  loading a newer one.
- **Decide target QLAdmin version up front (V4 vs V5).** This determines the single biggest structural rule:
  - **V5:** reserve/net-premium factors are **per full PLAN** (no basis+subplan sharing) — replicate factors per
    plan. (CONFIRMED)
  - **V4:** TV/NP shared by basis+subplan (first 4 chars of plan). (CONFIRMED legacy behavior)

---

## 7. Batch strategy

- **Family-parallel, plan-partitioned.** Process each rate family independently; within a family, partition by PLAN
  so reruns are surgical and a single plan can be reloaded without touching others.
- **Keys built once per (plan, family); values streamed.** Avoids recomputing the segmentation lattice per row.
- **Idempotent reruns** keyed on (PLAN+segmentation+EFFDATE) so a rerun replaces only that slice.

---

## 8. Rollback safety & auditability

- Every run writes a **pre-load snapshot reference** and a **per-family generation manifest** (small, not
  bureaucratic) so any plan/family/EFFDATE slice can be reverted independently.
- All emission is **append-or-replace by slice**, never global truncate.
- Keep the rate engine's outputs in their **own tree** so a rate rollback can never disturb claims/plan outputs.
- Log counts at each stage (source rows → keys → values → validated) for a defensible audit trail, consistent with
  the existing platform's logging style.

---

## 9. Recommended phasing

| Phase | Goal | Output |
|---|---|---|
| **R1 (this)** | Architecture discovery | the six analysis docs in this folder |
| **R2** | Confirm physical layouts | real `QUIKxxS`/`QUIKPLxx` DBF headers; resolve CNTL/STOREMEANS/CALCMIDS; field dictionary upgraded CONFIRMED |
| **R3** | Key-layer prototype | build QUIKPLxx keys from plan VARY matrix for a pilot plan; validate cardinality |
| **R4** | Single-family value prototype | load **Terminal Reserves (TV)** for one pilot plan end-to-end; validate via valuation |
| **R5** | Generalize | extend engine to GP/NP/CV/DB/DV; full validation suite |
| **R6** | Enterprise load | all plans, all families, with versioning + rollback + audit |

> **Recommended next implementation phase = R2** (confirm the physical DBF layouts). Do **not** skip to loaders;
> the unknown factor-grid columns (`CNTL`, `xx0–xx9`, `STOREMEANS`, `CALCMIDS`) are blocking and must be confirmed
> first.
