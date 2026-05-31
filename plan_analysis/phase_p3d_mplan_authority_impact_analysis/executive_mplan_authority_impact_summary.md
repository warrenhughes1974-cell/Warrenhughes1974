# Executive Summary — Phase P3D MPLAN Authority Impact Analysis

Generated: 2026-05-26 11:24:01

## Governance Risk Rating: **HIGH**

P3C closed product catalog authority successfully governs **quikplan.PLAN** emission, but **quikridr.MPLAN** and **quikactg.MPLAN** continue to derive plan codes independently via legacy flat `Master_Crosswalk.csv` passthrough. Referential integrity `quikridr.MPLAN → quikplan.PLAN` is **not enforced at runtime**.

## Key Metrics (current outputs)

| Metric | Value |
|--------|-------|
| quikplan.PLAN rows (P3C) | 133 |
| quikplan unique PLAN | 133 |
| quikplan PLAN outside closed catalog | 0 |
| quikplan PLAN with spaces | 0 |
| quikridr rows | 11698 |
| quikridr unique MPLAN | 139 |
| quikridr blank MPLAN | 2348 |
| Orphan MPLAN (not in quikplan.PLAN) | 39 |
| MPLAN containing spaces | 31 |

## Direct Answers

| Question | Answer |
|----------|--------|
| Can quikmstr/quikridr emit MPLAN not in authoritative quikplan? | **YES** — quikridr/quikactg unchanged by P3C; 39 orphan MPLAN codes observed |
| Does quikmstr populate MPLAN? | **NO** — no MPLAN column |
| Do quikridr/quikactg consume quikplan output? | **NO** — derive from PPBEN/PACTG PLAN_CODE independently |
| Are rider PLANs failing authority resolution? | **YES** for 31 space-containing passthrough MPLANs and 39 orphan codes |
| Do rules still generate passthrough PLAN identities? | **YES** — `app.py` `cw_map.get(val,val)` for MPLAN on quikridr/quikactg |
| Assumptions that PLANs may contain spaces? | **YES** — quikridr still emits 31 spaced MPLAN values |
| Does rider phase logic depend on COVERAGE_ID? | **NO** — MPHASE from BENEFIT_SEQ; MPLAN from PLAN_CODE regardless of phase |
| Claims/governance replay obsolete PLAN risk? | **LOW direct** — claims use MPOLICY; indirect via product screens |
| Is MPLAN closed-authority required next? | **YES** — P3C creates authority split that must be closed on quikridr |

## MPLAN Governance Cutover Safety

**NOT SAFE NOW.** Additional hardening required before MPLAN governance cutover.

Required first: P3D referential governance gate + P3E quikridr authority alignment.

## Recommended Phase Order

1. **P3D** — MPLAN Referential Governance (diagnostics + batch gate, no engine rewrite)
2. **P3E** — quikridr Authority Alignment (closed catalog MPLAN resolution)
3. **P3F** — Product Referential Validation Layer (quikactg + DBF pre-emit checks)
4. **P3G** — Batch Product Authority Parity (optional batch quikplan closed authority)
