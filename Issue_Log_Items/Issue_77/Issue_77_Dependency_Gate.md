# Issue #77 — Dependency Gate (fleet-wide)

**Issue:** #77 — Fleet rate-table setup validation  
**Framework stage:** Dependency Gate (G2)  
**Generated:** 2026-07-17 (reframed)  
**Model:** Cursor Grok 4.5 (locked)  
**Code changes:** None  

---

## Verdict

**CONDITIONAL GO** for Risk (fleet impact sizing).  

**BLOCKED for Development** until:

| ID | Blocker |
|----|---------|
| OBQ-1 | Fleet Plan Values Options rule locked (recommend M2) |
| OBQ-2 | Invalid PLANVALOPT (`F`) remediation approved |
| OBQ-7 | Definition of “100% accuracy” for UAT (PVO+join vs also assumptions/Aint) |

Soft (can default in Risk if user accepts EX convention):

| ID | Item | Suggested default |
|----|------|-------------------|
| OBQ-4 | QuikPlSt.MLOANINT | `0.00` |
| OBQ-3 | PUA PVO without factors | Set PLANVALOPT=N unless rates exist |
| OBQ-5 | QuikPlTv assumptions | Keep in **#60 Track B** (out of #77 Dev) |
| OBQ-6 | QuikAint expansion | Keep case-by-case (#51 style), not silent EX clone |

Stop after this gate. Do **not** start Risk until user says **“Proceed to Risk Agent.”**

---

## Checklist

### Source / guide data

| Check | Met? | Notes |
|-------|------|-------|
| EX_Rate_Tables present | **Met** | `docs/EX_Rate_Tables/` |
| Current Output rates present | **Met** | 126 rated plans |
| LifePRO factor extracts present | **Met** | Existing Source package |
| EX contains Citizens plans | **Missing / N/A** | Structural guide only — accepted |
| Fleet audit evidence | **Met** | `Issue_77/evidence/` |

### Field definitions

| Check | Met? | Notes |
|-------|------|-------|
| Target tables confirmed | **Met** | Members, keys, factors, quikplan PVO |
| PVO semantics confirmed | **Partial** | M2 proposed; needs OBQ-1 lock |
| Factor value authority | **Met** | LifePRO (not EX clone) |
| Assumption field authority | **Missing** | OBQ-5 / #60 |

### Client clarification

| Check | Met? | Notes |
|-------|------|-------|
| Fleet scope agreed | **Met** | User 2026-07-17 |
| PVO rule locked | **Missing** | OBQ-1 |
| 100% accuracy definition | **Missing** | OBQ-7 |
| UAT acceptance | **Partial** | Min bar proposed below |

### Evidence / regression

| Check | Met? | Notes |
|-------|------|-------|
| Before-state measurable | **Met** | Audit CSVs |
| #25 / #26 preserved in plan | **Met** | Out of scope |
| #71 BAND preserved | **Met** | Explicit |
| Unrelated rulebooks untouched | **Met** | Blueprint |

---

## Fleet gap scoreboard (before-state)

| Check | Result | Target |
|-------|--------|--------|
| Rated plans with members | 126/126 | 100% |
| Key↔factor orphans | 1 | 0 |
| Rated plans PVO M2-perfect | 12/126 (~10%) | 100% |
| STVARYGP correct under M2 | 0/109 needed | 100% |
| PLANVALOPT alphabet Y/N only | Fail (`F` present) | 100% |
| PLANVALOPT ↔ rates consistent | 11 fails | 0 fails |
| QuikPlTv RSVINT etc. populated | 0% | Per OBQ-5/7 |
| QuikPlSt.MLOANINT defaulted | 0% | Per OBQ-4 |

---

## Minimum UAT bar (proposed until OBQ-7)

**Tier A — #77 core (recommended):**

1. Every plan with factor rates has complete QuikPlGd/Uw/Bd/St members.  
2. Zero key↔factor orphans.  
3. Every `quikplan` PLANVALOPT ∈ {Y,N} and consistent with rates.  
4. Every *VARY* flag matches locked fleet rule (M2 unless OBQ-1 changes).  
5. QuikPlSt.MLOANINT = `0.00` when blank (if OBQ-4 accepted).  

**Tier B — separate / later:**

- QuikPlTv/Cv assumption completeness (EX-like)  
- QuikAint plan coverage expansion  

---

## Deliverable paths

| Artifact | Path |
|----------|------|
| Intake | `Issue_Log_Items/Issue_77/Issue_77_Intake_Summary.md` |
| Planning | `Issue_Log_Items/Issue_77/Issue_77_Planning_Report.md` |
| Dependency Gate | `Issue_Log_Items/Issue_77/Issue_77_Dependency_Gate.md` |
| Evidence | `Issue_Log_Items/Issue_77/evidence/` |
| Audit script | `QLA_Migration/_research_issue77_fleet_rate_setup_audit.py` |
| Guide | `docs/EX_Rate_Tables/` |

---

## Recommended next prompt

```
Proceed to Risk Agent for Issue #77 (fleet-wide).

OBQ answers:
OBQ-1: [accept M2 | alternate rule]
OBQ-2: [force Y/N from rates]
OBQ-3: [PUA PVO=N without rates | keep Y]
OBQ-4: [MLOANINT=0.00 | other]
OBQ-5: [keep #60 | include in #77]
OBQ-6: [keep #51 casework | expand]
OBQ-7: [Tier A only | Tier A+B]
```
