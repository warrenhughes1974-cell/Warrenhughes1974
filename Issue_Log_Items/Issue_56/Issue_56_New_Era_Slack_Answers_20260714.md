# Issue #56 — New Era / Client Answers (Slack 2026-07-14)

**Source:** Slack support thread (Warren ↔ Robert) + Eric verbal confirm  
**Recorded:** 2026-07-14

---

## Plain-language answers

| Question | Answer |
|----------|--------|
| Do PA plans need to be in the QLA plan file? | **Only if** they use **their own** CV rates. If the PA plan is **not** in the plan file, QLA **uses the base** plan rates. |
| Do these PUAs use their own CV (not base)? | **Yes** — Eric confirmed per **policy forms** (cash values are different from base). |
| What must we load if different? | Add the **PA plan** to the plan files, then load **full CV and TV** rates for that plan, **including basis info**. |
| Naming pattern | Confirmed conversion pattern: keep first four of base + **`PA`** (e.g. `1960PO` → `1960PA`). |
| Suggested UAT path (Robert) | (1) Add one PA plan, copy base CV/TV, Build CV → should match base behavior; (2) replace with PA-specific CV rates, Build CV again → confirm values change to new rates. |

---

## Verbatim points (compressed)

- Robert: Confirm PA should have own CV and not follow base; if so, create/add PA plans and load full CV/TV + basis. Most other clients’ PAs follow base and omit PA from plan file → system uses base.
- Warren: Rates exist in LifePRO rate table (screenshot).
- Robert: Still wanted client confirmation rates *should* differ (forms/memo); if truly required, add plan + CV/TV.
- Warren: Eric confirmed this morning — cash values are different according to the policy forms.

---

## Implication for conversion

**Option A confirmed by New Era:** keep `1960PA`, **add plan setup**, emit **QuikCvs + QuikTvs** (and basis) from LifePRO PUA attained-age tables — not base `1960PO` rates.
