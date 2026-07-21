# Issue #56 — Intake Summary

**Issue:** #56 — PUA CV is incorrect  
**Framework stage:** Intake Agent (G0)  
**Status after intake:** Planning  
**Generated:** 2026-07-13  
**Model:** Cursor Grok 4.5 (locked)  
**Owner:** Conversion (primary) — rates / QuikCvs / rider CV path  
**Priority:** Active / client-reported  
**Tracking note:** Log row shows Risk = **No-Go** (Eric) — treat as pre-research flag; re-evaluate after Planning/Dependency Gate  

---

## Client symptom (verbatim)

> Cash Values are not correct for PUAs. For example policy number 010310404C the cash value of PUAs is $6,628.32, which is greater than the PUA death benefit. PUA values appear to be connected with PUA attained Age Rates in LifePRO (960 PO PUA for this policy). Note the base cash value calculation closely matches the CV in LifePRO

## Normalized symptom

QLAdmin-computed (or displayed) **PUA rider cash value** for traditional policies does not match LifePRO. On golden sample **010310404C**:

| Observation | Client value / note |
|-------------|---------------------|
| PUA CV shown | **$6,628.32** |
| Anomaly | PUA CV **>** PUA death benefit |
| Suspected cause | Wrong use of **PUA attained-age rates** for plan **960 PO PUA** (crosswalk → `1POPUA`) |
| Control | **Base** coverage CV closely matches LifePRO |

This is a **rates / QuikCvs (or rider CV computation)** domain issue, not a claim that base traditional CV logic (#21E / #37) is broadly broken.

---

## Example policies

| QLA | LifePRO (crosswalk) | Notes |
|-----|---------------------|-------|
| `010310404C` | `9010310404` | Primary client example; also #21F golden |

Additional PUA policies: **none provided at intake** — Planning should sample peers on `960 PO PUA` / `1POPUA`.

---

## Suspected domain

**Rates / rider cash value** — PUA plan rate tables (`QuikCvs` / PAAGERAT / Rate_Table for `960 PO PUA` → `1POPUA`) and how QLAdmin applies attained-age CV rates to PUA units/face. Possible touchpoints: rate emit, duration/age index (#37/#41), plan inheritance (#40), or policy `quikridr` units/PLAN for the PUA phase.

**Not primarily:** claims, memo, premium history (#21F already used this policy), bank draft.

---

## In scope (first pass)

- Trace `010310404C` base vs PUA rows in `quikridr` (PLAN, MUNIT, MVPU, face, MAGE, MPHASE)  
- Confirm LifePRO PUA plan `960 PO PUA` ↔ QLA `1POPUA` and which CV rate keys exist in Rate_Table / PAAGERAT / `Output/rates/QuikCvs*`  
- Compare LifePRO source CV (if extractable) vs QLAdmin-displayed $6,628.32  
- Determine whether defect is **rate content**, **age/duration placement**, **wrong rate table attachment**, or **policy units/face**  
- Document what must not change: base CV path that client says already matches  

## Out of scope (first pass)

- Changing base traditional CV computation that already matches LifePRO  
- UL `MCV0` / FV_BALANCE2 path (#21E UL) unless Planning proves coupling  
- PUA non-CV inheritance (`261PUA`/`265PUA`/`280PUA` NP/RV/DV) — separate actuarial track  
- Wholesale QuikCvs redesign  

---

## Related issues

| Issue | Relevance |
|-------|-----------|
| **#21E** | Cash value decision: traditional = QuikCvs compute; UL = FV_BALANCE2→MCV0 |
| **#37** | QuikCvs age/duration grid placement |
| **#40** | Inherited CV for CV-capable plans (incl. PUA CV inheritance approved) |
| **#41** | CV age-100 endpoint / duration index |
| **#21K** | PUA amount / MUNIT precision (face), not CV rates |
| **#21F** | Same policy golden for premium history — preserve; unrelated |
| **#25 / #26** | Must not regress MPOLICY / MPREM |

---

## Artifact inventory

| Artifact | Present? |
|----------|----------|
| Client narrative + dollar example | Yes ($6,628.32 PUA CV) |
| Example policy | Yes (`010310404C`) |
| LifePRO PUA plan ID cited | Yes (`960 PO PUA`) |
| Screenshots (QLAdmin CV / LifePRO CV) | **No** |
| LifePRO “correct” PUA CV dollar | **No** (only wrong QLA value given) |
| PUA death benefit dollar | **No** (only stated CV > DB) |
| Rate extracts (Rate_Table / PAAGERAT) | Expected in Source — confirm at Planning |
| Current `quikridr` / QuikCvs output | Expected in Output — confirm at Planning |
| Existing `Issue_56/` analysis | Created this intake |

---

## Immediate blockers visible at intake

1. No screenshot / LifePRO correct PUA CV amount for acceptance criteria.  
2. No PUA death benefit amount stated (needed to quantify “CV > DB”).  
3. Client Risk column **No-Go** may mean “do not code until researched” — not necessarily permanent reject.  
4. Need to confirm whether $6,628.32 is from QLAdmin UI compute (QuikCvs) vs a loaded policy field.

---

## Severity / owner

| Field | Value |
|-------|--------|
| Severity | **High** for PUA policies — CV > DB is actuarially implausible and blocks UAT trust on rider values |
| Owner | Conversion (rates/CV path); Client for LifePRO CV proof + UAT acceptance dollars |
| AGENTS.md | Surgical only; **no code at Intake** |

---

## Gate G0 checklist

- [x] Issue folder `Issue_Log_Items/Issue_56/`  
- [x] Intake summary written  
- [x] Example policies listed  
- [x] Owner and priority assigned  
- [x] No code or rulebook changes  

**Next:** Planning Agent (same model) + Dependency Gate assessment.
