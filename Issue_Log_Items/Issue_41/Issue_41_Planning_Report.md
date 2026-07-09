# Issue #41 — Planning Report

**Issue:** #41 — CV Age/Duration Endpoint Off by One (`1960PO`)  
**Framework stage:** Planning Agent (G1)  
**Status:** Planning complete — proceed to Dependency Gate  
**Generated:** 2026-07-06  
**Agent:** Planning Agent (read-only analysis)

---

## 1. Executive finding

**Confirmed client symptom:** For `960 PO` / `1960PO`, Male issue age `26`, CV value `784.65` is reported by the client as LifePRO duration **57**, while QLAdmin currently displays that same value at duration **56**. The client also states the QLAdmin grid is ending at **age 99**, not **age 100**.

**Planning interpretation:** The rate values themselves are not the immediate problem. The issue is the **duration index / endpoint rule** used when converting LifePRO CV rates to QLAdmin `QuikCvs`.

**Most likely source:** Issue #37 intentionally introduced the current CV grid builder and terminal rule:

```text
last_duration = 100 - issue_age
```

For this new client example, that rule appears to exclude the age-100 inclusive terminal duration. The result is a one-duration-short QLAdmin display at later durations.

**Recommended direction:** Treat Issue #41 as a surgical follow-up to Issue #37. Adjust the CV endpoint / displayed duration convention only after Dependency Gate confirms the expected QLAdmin age-100-inclusive rule. Do not alter non-CV rate families or product plan mappings.

---

## 2. Evidence from prior Issue #37

Issue #37 closed the earlier defect where `1960PO` CV values were placed too early in the grid. That fix:

| Behavior | Issue #37 result |
|----------|------------------|
| CV leading zero handling | Added |
| Variable first-rate offset by issue age | Added |
| Non-CV rate families | Unchanged |
| Terminal rule | `100 - issue_age` |
| Example accepted at the time | Male age 22, first and last rates matched proof matrix |

Relevant Issue #37 decision:

```text
CV: lp_duration = source_d + lp_first - fnz
QL slot = lp_duration - 1
drop rows past 100 - issue_age
```

The new client example indicates the **drop rule** or **QL slot/display convention** is still one year short for the terminal age.

---

## 3. Business explanation

LifePRO and QLAdmin are showing the same actuarial value series, but they appear to be using a different policy-year / duration endpoint convention.

Client expectation:

```text
Issue age 26 + duration endpoint = age 100 inclusive
```

Current QLAdmin behavior:

```text
Issue age 26 + loaded/displayed endpoint = age 99
```

That means values near the end of the table show one duration too early. The visible symptom is not isolated to the `784.65` value; it is the same underlying endpoint rule across issue ages.

---

## 4. Proposed validation plan

### 4.1 Proof case

Validate `1960PO` / `CV` / Male / issue age `26` / band `01` / UW `00`:

| Check | Expected after fix |
|-------|--------------------|
| Value `784.65` | Displays at client-confirmed duration **57** |
| Final non-zero maturity row | Extends through age **100**, not age 99 |
| Existing early-duration zeros | Preserved |
| First non-zero duration | Still aligns with LifePRO |

### 4.2 Fleet proof

Run the same endpoint validation across Issue #37 proof ages:

| Product | Sex / issue ages |
|---------|------------------|
| `1960PO` | M: `0`, `18`, `20`, `22`, `24`, `26`, `29`, `33`; F: `0` |

Add issue age `26` as a required proof case because it is the new client-reported example.

### 4.3 Regression guards

| Guard | Requirement |
|-------|-------------|
| QuikCvs values | Numeric values unchanged except duration placement / endpoint extension |
| QuikCvs field order | Unchanged |
| QuikNps / QuikGps / QuikDbs / QuikDvs / QuikTvs | Unchanged |
| Issue #31 baseline | Rebaseline if key counts intentionally change |
| Issue #37 first-rate placement | Must remain PASS |
| Issue #25 / #26 | Must remain PASS |

---

## 5. Resolution options

| Option | Description | Pros | Cons | Planning recommendation |
|--------|-------------|------|------|-------------------------|
| **A — Age-100 inclusive endpoint** | Change CV terminal rule so QLAdmin includes the age-100 duration. | Matches client symptom and likely corrects all ages. | Requires rebaseline of QuikCvs row/key counts. | **Preferred if Dependency Gate confirms convention.** |
| **B — Product-specific override for `1960PO`** | Apply endpoint correction only to `1960PO`. | Smallest immediate scope. | Risks leaving same defect on other CV products; client says other ages have same issue. | Not preferred. |
| **C — Revert Issue #37** | Restore pre-Issue #37 behavior. | None for current symptom. | Reintroduces known duration-placement defect. | Rejected. |
| **D — Change all rate families** | Apply endpoint convention globally. | None without evidence. | High regression risk. | Rejected for now. |

---

## 6. Recommended implementation scope

After G2/G3 approval:

1. Locate the CV-only grid builder introduced for Issue #37.
2. Adjust only the CV terminal duration calculation / QL display slot mapping needed to include age 100.
3. Add `1960PO` Male age `26` to the validation matrix.
4. Re-emit `QuikCvs.csv` only.
5. Run Issue #37 validators plus the new Issue #41 proof case.
6. Rebaseline QuikCvs regression counts only if the endpoint extension changes row/key counts as expected.

Do not change `quikplan`, `quikridr`, product crosswalks, inherited-rate logic, or non-CV rate emits.

---

## 7. Open questions

| # | Question | Blocks |
|---|----------|--------|
| 1 | Does QLAdmin CV duration display need to represent age 100 inclusively for all CV plans? | Development |
| 2 | Should the corrected terminal duration be formulaically `101 - issue_age`, or should it be derived from LifePRO max benefit / maturity metadata? | Implementation design |
| 3 | Are any LifePRO products intentionally maturity-age 99 or 103 exceptions? | Fleet guard |
| 4 | Should Issue #37 proof matrix be revised to include the client's new Male age 26 screenshots as authority? | Validation |

---

## 8. Next framework stage

**Dependency Gate (G2)** should confirm the target QLAdmin CV duration convention and approve a CV-only endpoint correction. After that, run Risk Review (G3) before development.

**Do not code until G2 + G3 are satisfied.**
