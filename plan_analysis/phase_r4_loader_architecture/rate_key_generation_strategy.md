# R4 — Rate Key (QuikPlxx) Generation Strategy

Rate-key tables connect an authoritative `PLAN` (+ segmentation + EFFDATE) to a family's factor set, and—
for reserve/cash-value families—carry the actuarial assumptions. **Confirmed physical layouts** (DBF descriptors):

| Key table | Fields | Carries assumptions? |
|---|---|---|
| `QuikPlGp` | PLAN, GENDER, UWCLASS, BAND, ISSCNTRY, ISSUEST, EFFDATE | No (pure segmentation key) |
| `QuikPlDb` | PLAN, GENDER, UWCLASS, BAND, ISSCNTRY, ISSUEST, EFFDATE | No |
| `QuikPlDv` | PLAN, GENDER, UWCLASS, BAND, ISSCNTRY, ISSUEST, EFFDATE | No |
| `QuikPlCv` | …key… + `MORT, ETIMORT, NFOINT, INTMETHCV` | Yes (cash-value basis) |
| `QuikPlTv` | …key… + `MORT, RSVINT, RSVMETH, INTMETHTV, STOREMEANS, CALCMIDS` | Yes (reserve basis); **shared by NP** |

Field widths (CONFIRMED): `PLAN C6`, `GENDER C1`, `UWCLASS C2`, `BAND C2`, `ISSCNTRY C4`, `ISSUEST C2`, `EFFDATE D8` (YYYYMMDD date).

---

## Generation rule

For each family, the set of rate-key rows is the **distinct segmentation tuple** present in that family's transformed factor rows:

```
key = (PLAN, GENDER, UWCLASS, BAND, ISSCNTRY, ISSUEST, EFFDATE)
```

derived from:
- **PLAN** — authoritative, from `Policy Form Crosswalk` (no spaces / synthetic / passthrough).
- **GENDER** — SEX crosswalk (F/M/J). Use `0` only when the plan does not vary by gender (`GDVARY*` off).
- **UWCLASS** — UWCLASS crosswalk (00/NS/SM/PR/ST). Use `00` when `UWVARY*` off.
- **BAND** — BAND crosswalk (01/02/03). Use `00` when `BDVARY*` off.
- **ISSCNTRY / ISSUEST** — segmentation defaults (`0000` / `00`) unless `STVARY*` indicates state/country variation. **Business-supplied default required** (source carries none).
- **EFFDATE** — effective-dated generation. **Business-supplied EFFDATE required** (source carries none); one generation per load unless historical generations are requested.

One `QuikPlxx` row is generated per distinct key; the matching `Quikxxs` factor rows hang off the same key (plus AGE + CNTL paging).

## Uniqueness assumptions

| Table | Uniqueness key | Confidence |
|---|---|---|
| `QuikPlGp` / `QuikPlDb` / `QuikPlDv` | full 7-field segmentation tuple | CONFIRMED (layout) |
| `QuikPlCv` | 7-field tuple (assumptions are attributes, not key) | LIKELY |
| `QuikPlTv` | 7-field tuple (assumptions are attributes, not key) | LIKELY |
| `Quikxxs` factor rows | tuple + `AGE` + `CNTL` | CONFIRMED (R2/R3) |

**Rules:**
- No duplicate key rows within a `QuikPlxx` table (hard gate).
- Every `Quikxxs` factor row must have a parent `QuikPlxx` key row (no orphan factors).
- Every generated `QuikPlxx` key should resolve at least one factor row (no empty keys) — warn, don't necessarily block.
- `QuikPlCv`/`QuikPlTv` assumption fields (MORT, RSVINT, RSVMETH, etc.) must be **business-supplied per plan**; they cannot be derived from the rate extract. Treat missing assumptions as a blocking input for those families.

## Assumption sourcing (open)
`MORT, ETIMORT, NFOINT, INTMETHCV, RSVINT, RSVMETH, INTMETHTV, STOREMEANS, CALCMIDS` are actuarial-basis values **not present in LifePRO rate extracts**. They require an authoritative per-plan assumption mapping before CV/TV/NP key generation. This is the largest open input gap for reserve/cash-value loading.
