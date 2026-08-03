# Issue #136 — Locked Acceptance Criteria (Real-rate-only variance)

**Authority:** Warren 2026-08-02 + Luna independent concurrence  
**Track:** Internal Issue A / A11 correction  
**Coding:** Not started — awaiting Development approval after Risk

---

## Locked business rule

**Variation follows real rate differentiation, not the presence of default keys.**

Default / structural keys may exist (TESTRD-style: Band `00`, State `00` / Country `0000`, UW `00`, gender `0`, Eff `19000101`) so QLAdmin has a valid rate structure. Those defaults must **not** turn on category checkboxes or `*VARY*` flags.

Applies **fleet-wide** to every plan, for each rate family independently: **GP, DB, CV, TV, DV**.

| Dimension | Enable flag only when… |
|-----------|-------------------------|
| Gender (`GDVARY*`) | That family’s **real factor values** differ across more than one gender |
| UW Class (`UWVARY*`) | That family’s **real factor values** differ across more than one UW class |
| Band (`BDVARY*`) | Genuine **band-specific** rates exist and differ (Band `00` / NOT APPLICABLE alone = **never** enable) |
| State (`STVARY*`) | Genuine **state/country-specific** rates exist and differ (`0000`/`00` / ALL alone = **never** enable) |
| DV family | Real dividend factor rows exist in `QuikDvs` (no DV factors → all `*VARYDV` = **N**; `PAR=0`) |
| `PLANVALOPT` | **Y** only if at least one legitimate VARY flag is **Y** after the rules above; else **N** |

### Explicit non-triggers

- Presence of a default key row
- Values=Y on a default-only key
- Band `00` “NOT APPLICABLE”
- Country/State ALL / `0000` / `00`
- Dividends button / UI alone without `QuikDvs` factors
- “Any real factor row exists” without multi-value differentiation on that dimension

### Independent families

GP, DB, CV, TV, DV are analyzed separately from their own real factor grids. CV/TV UW collapse remains family-specific (prior A11). Evidence in one family must not invent flags in another.

### Prior rule superseded (Band / State)

Issue #77’s historical emit rule that set `BDVARY*=Y` whenever a family had any real row, and `STVARYGP=Y` whenever GP was present, is **superseded** by this #136 rule for Band and State.

Gender / UW multi-value rules from Issue #77 remain valid **only** when backed by real factor differentiation (not default-only stubs).

---

## Acceptance criteria (UAT / Validation)

1. Across every plan, default keys alone never set `PLANVALOPT` or any GP/DB/CV/TV/DV variation flag.
2. Plans with no real rate factors retain required default keys but have `PLANVALOPT=N` and all variation flags `N`.
3. Band flags are enabled only when genuine band-specific rates differ.
4. State flags are enabled only when genuine state-specific rates differ.
5. DV is enabled only when real dividend factors are loaded; no dividend factors → all DV flags `N` and `PAR=0`.
6. Each family’s Gender/UW/Band/State flags are calculated independently from that family’s actual rate grid.
7. **1658C1 gold check after fix:**
   - No Band variation flags (`BDVARY*` all `N`)
   - No DV variation flags (`*VARYDV` all `N`; `PAR=0` already correct)
   - No State variation flags (`STVARY*` all `N`)
   - Gender/UW for GP/CV/TV remain `Y` only if factor grids truly differ (spot-check factors, not keys alone)
   - No DB/DV flags invented without `QuikDbs` / `QuikDvs` factor rows

---

## UAT screenshot defect (pre-fix evidence)

Plan **1658C1** Plan Values Options (2026-08-02 Q deploy): Band `00` with all checkboxes on; DV checked with no dividends; State ALL with GP/DB checked — violates this locked rule.