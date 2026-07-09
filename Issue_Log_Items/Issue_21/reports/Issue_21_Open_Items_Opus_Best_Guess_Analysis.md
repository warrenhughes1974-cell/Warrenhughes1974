# Issue #21 — Open Items (D / E / F / G / I): Best-Guess Analysis

**Prepared:** 2026-07-09 · **Analyst:** Opus (analysis only — no code, rulebook, crosswalk, source, or output changes)
**Scope:** Provide reasoned best-guess answers for the five items still marked **AWAITING CLIENT** so conversion can proceed on documented assumptions rather than stall.
**Status of this document:** RECOMMENDATION. Each answer is a defensible default derived from source evidence + current output state. Client confirmation is still requested before any answer is treated as final, but each item now has a *proposed* resolution and a *do-this-now* path.

**Evidence base (read-only, this session):**
- `QLA_Migration/Output/quikdvdp.csv`, `quikbenf.csv`, `quikridr.csv`, `quikprmh.csv` (current full-batch output)
- `docs/Copy of Premium Paid Fields.xlsx` (client-supplied source mapping — Non-ISWL + ISWL sheets)
- `docs/research/ISWL_LifePRO_to_QLAdmin_Master_Reference.md`
- `Issue_Log_Items/Issue_21/reports/Issue_21_Final_Analysis.md`
- `Issue_Log_Items/Issue_21/Issue_21D/Issue_21D_Interest_Rate_Strategy.md`, `Issue_21D_Decision_Matrix.md`
- `QLA_Migration/Configs/Sync_Rulebook_quikbenf.csv`, `Sync_Rulebook_quikdvdp.csv`

---

## Executive verdict

| Item | Topic | Best-guess answer | Confidence | Action state |
|---|---|---|:--:|---|
| **21D** | Interest crediting rate | **4.50% for ISWL, 4.00% for non-ISWL** (already implemented, CSO-driven) | **High** | **Effectively RESOLVED (v57.36)** — needs client sign-off only |
| **21E** | Cash value | **QLAdmin computes from rate tables (do NOT load MCV); load fund value for UL** | **Med-High** | Depends on rate load (Issue #41 QuikCvs) — no quikmstr change |
| **21F** | Premium history depth | **Accept source floor (~2017-01-01); full history needs re-extract** | **High** | Source-side decision; conversion already correct |
| **21G** | Total premium / cost basis | **Source now known** (client workbook); needs QLAdmin target field | **Med-High** | Awaiting target field only — source resolved |
| **21I** | Beneficiary | **Type + split already correct; only `MRELATION` needs mapping** | **High** | One surgical rulebook/enrichment fix remains |

**Bottom line:** Three of the five (D, F, I) are essentially answerable and low-risk *today*. E and G each hinge on exactly one confirmation (compute-vs-load for E; QLAdmin target field for G), and the source side of both is already understood.

---

## 21D — Interest crediting rate (4.00% vs 4.50%)

**Question on file:** *What is the authoritative interest crediting rate — 4.00% or 4.50%? Guaranteed, current, or both?*

**Evidence:**
- Current output `quikdvdp.MDEPINT` is already split: **2,268 rows = 4.50** (ISWL) and **2,815 rows = 4.00** (non-ISWL). This is the v57.36 CSO-crosswalk allowlist implementation (Issue #21D Track A).
- `PPBEN.FV_GUAR_RATE = 4.50` on **2,159 ISWL rows**; CSO Mortality Crosswalk independently supports 4.50% guarantee (per ISWL Master Reference §5.5).
- Rulebook `Sync_Rulebook_quikdvdp.csv` line 6: default `4.00`, "ISWL override at emit → 4.50".

**Best-guess answer:**
1. **ISWL = 4.50%** is authoritative (client annotation + `FV_GUAR_RATE` + CSO crosswalk all agree). **Already applied.**
2. **Non-ISWL retains 4.00%** until separately governed. Changing the 2,815 non-ISWL rows fleet-wide has no business sign-off and is out of scope.
3. QLAdmin **Dividend Accum Int Rate** should display the **current credited rate** used for dividend accumulation; for ISWL that equals the guaranteed 4.50% (guaranteed == credited on these plans).

**Confidence:** High. The number is corroborated three independent ways and is already in the shipped output.

**Recommended action:** Treat 21D as **resolved pending sign-off**. The only open governance item is a one-line client confirmation that non-ISWL products should stay at 4.00% (rate authority for those products was never in scope for this issue). No further code needed.

---

## 21E — Cash value ($0 / wrong non-zero in QLAdmin)

**Question on file:** *Load LifePRO cash/fund value at conversion, or compute from rate tables after load? Should day-one values match LifePRO exactly?*

**Evidence:**
- Policy-level cash-value fields on the rider (`quikridr.MCV0 / MCV1 / MCV2`) are **0 on all 6,934 rows** — the converter loads no per-policy cash value today.
- QLAdmin's design (ISWL Master Reference §5.1, §1.7) routes cash value through the **`QUIKCVS` rate table** (`PDAGE TYPE_CODE=CV`, 12,084 ISWL rows) — i.e., QLAdmin **computes** displayed CV from tabular per-$1,000 values at attained age/duration/band.
- The inconsistency noted in the Final Analysis (zero on two policies, wrong non-zero `$7,204.30` on another) is the classic signature of a **compute path with missing/mismatched rate rows**, not a load path.
- For the two UL policies (010713704C fund $45,567.58; 010818663C fund $12,481.13) LifePRO carries a real **fund value / gross deposits** (`PPBEN.FV_GUAR_DEPOSITS`), which is an account balance, not a tabular CV.

**Best-guess answer — split by product model:**
1. **Traditional / ISWL par whole life → COMPUTE.** Do **not** stuff `MCV0-2`. The correct fix is to ensure `QUIKCVS` (and supporting `QUIKGPS`/rate) tables are loaded so QLAdmin computes CV — this is **Issue #41 (QuikCvs)** territory, not a `quikmstr`/`quikridr` change. Once rate tables load, the `$0` and wrong-non-zero displays resolve together.
2. **Universal Life (fund-value policies) → LOAD the fund balance.** UL cash value is an account balance, so the converted account value should be **loaded** from `PPBEN.FV_GUAR_DEPOSITS` / fund balance so day-one matches LifePRO ($45,567.58 etc.). This is a distinct, smaller population.
3. **Day-one expectation:** exact match for UL fund-value policies (loaded); for traditional policies, match within rounding once the CV rate tables are validated for parity (April `Rate_Table` vs May `PDAGE CV`).

**Confidence:** Medium-High on the compute-vs-load split; Medium on exact UL target field until the fund-balance column is confirmed against the QLAdmin UL value field.

**Recommended action:** Do **not** treat 21E as a `quikmstr` cash-value population defect. Route it as: (a) complete/validate `QUIKCVS` rate load (Issue #41) for the traditional book, and (b) a small, separate UL fund-balance load. Keep 21E open until rate-table parity is signed off — but the model question is answered: **compute for traditional, load for UL.**

---

## 21F — Premium history truncation (~Jan 2018)

**Question on file:** *How far back must premium history be converted — full to issue, a fixed date, or paid-to only?*

**Evidence:**
- Current `quikprmh.csv` has **206,861 rows** with `DATEPAID` spanning **2017-01-01 → 2027-04-17**. The old-end floor is **2017-01-01**, matching the client's "~Jan 2018" annotation (the extract floor is ~2017).
- The Final Analysis confirms this is a **source-side** limitation: the LifePRO accounting extract was pulled with a date floor; the `quikprmh` mapping itself is correct.

**Best-guess answer:**
1. **The conversion is not defective** — it faithfully loads every accounting row present in the source extract. The floor is imposed upstream.
2. **Recommended default: accept the ~2017 floor** for go-live. Ten years of payment history covers virtually all servicing, reinstatement, and recent-activity needs. Tax/cost basis (the usual reason to need full history) is captured **independently** via 21G totals, so a full replay to 2001/2002 is not required to preserve basis.
3. **If the client mandates full history to issue**, that is a **source re-extract request** to the LifePRO accounting team (remove the date floor), not an engine change.

**Confidence:** High that it is source-limited and the engine is correct; the only judgment is the business policy on depth.

**Recommended action:** Adopt the ~2017 floor as the working assumption and proceed. Log a single client question: "Is 10 years (2017→present) of premium history acceptable, or is full-to-issue required?" — the answer only triggers a re-extract, never blocks the rest of the dataset.

---

## 21G — Total Premium Paid / Cost (Tax) Basis

**Question on file:** *Where should Total Premium Paid and Cost/Tax Basis appear in QLAdmin? Which field(s)? Informational-only?*

**Evidence — the source is now client-provided** (`docs/Copy of Premium Paid Fields.xlsx`):

| Book | Component | Premiums Paid | Tax/Cost Basis | Extract |
|---|---|---|---|---|
| Non-ISWL (BF whole life) | Base (`BA`) | `PREMIUMS_PAID` (col J) | `TAX_BASIS` (col N) | `PPBENTYP_BenefitType_Extract` |
| Non-ISWL | Paid-Up Adds (`PU`) | `PU_PREMIUMS_PAID` (col CC) | `PU_TAX_BASIS` (col CE) | `PPBENTYP_BenefitType_Extract` |
| Non-ISWL | **Total** | BA + PU premiums | BA + PU basis | (computed) |
| ISWL (UL) | Fund (`FV`) | `FV_GUAR_DEPOSITS` (col BQ) | `FV_BASIS2` (col BG) | `PPBEN_PolicyBenefit_Extract` |

So **Total Premiums Paid = BA `PREMIUMS_PAID` + PU `PU_PREMIUMS_PAID`** and **Total Tax Basis = BA `TAX_BASIS` + PU `PU_TAX_BASIS`** (traditional); ISWL uses the single `FV` deposit/basis pair.

- **Gap:** there is **no dedicated total-premium or cost-basis field** in the current `quikmstr`, `quikridr`, or `quikbenf` schemas. The source is resolved; the **QLAdmin target field is the only open piece.**

**Best-guess answer:**
1. **Source is settled** — use the client workbook mapping above (sum BA+PU per policy for traditional; single FV pair for ISWL). No source ambiguity remains.
2. **Most likely QLAdmin target:** cost/tax basis and cumulative premium in QLAdmin typically live on a **policy values / dividend-values record** (candidate: `quikdvpr` / a policy cost-basis field) rather than on `quikmstr` core. Recommend confirming the QLAdmin field name from the QLAdmin Help (cost-basis / premiums-paid values screen) before emitting.
3. **Interim default:** treat as **informational at go-live** if no QLAdmin field is confirmed — i.e., stage the computed totals in a report (`Reports/`) so they are available for verification, and add the load once the target field is named. This avoids blocking the batch.

**Confidence:** Medium-High. Source mapping is now concrete and client-authored; only the destination field is unconfirmed.

**Recommended action:** Single narrow client/SME question: *"Which QLAdmin field/screen stores cumulative Premiums Paid and Cost (Tax) Basis?"* Everything else for 21G is ready. If the answer is "informational only," 21G closes with a staged report.

---

## 21I — Beneficiary (type / relationship / split / "Unknown 100%")

**Question on file:** *Which beneficiary attributes are mandatory — name, type, relationship, split %, primary/contingent? Should "Unknown 100%" ever appear?*

**Evidence — current output is much healthier than the original screenshots suggested:**
- `quikbenf` schema: `MPOLICY, MBENFID, MTYPE, MRELATION, MSPLIT` (5,916 rows).
- **`MTYPE` is populated correctly:** P (primary) = 3,985, C (contingent) = 1,931. No blank/"Unknown" types remain.
- **`MSPLIT` carries real percentages** (100, 50, 25, 33.33, 20, 16.66, 14.28…) — **not** a hard 100% default.
- **Splits reconcile exactly:** every policy's **Primary** rows sum to **100%** (3,027/3,027) and every policy's **Contingent** rows sum to **100%** (1,418/1,418). Zero mis-summed policies.
- **The one real remaining defect:** `MRELATION` is **`1000` on all 5,916 rows** — the rulebook (`Sync_Rulebook_quikbenf.csv` line 5) hardcodes `MRELATION,1000,Default Relationship Code`, while `MTYPE`/`MSPLIT` are enriched from source in `app.py`.

**Best-guess answer:**
1. **Type, split, and primary/contingent sequencing are already correct** — the original "Unknown 100%" defect has effectively been remediated in the current build. "Unknown 100%" should **not** appear and does not appear in current output.
2. **Only relationship needs work:** map `MRELATION` from the source **`RELATE_CODE`** (already read for `MTYPE` via `DERIVE_BENF_TYPE`) to the QLAdmin relationship code set, defaulting to `1000` ("Other/Unknown") **only when the source relationship is genuinely blank** — instead of hardcoding `1000` for everyone.
3. **Mandatory attributes (recommended rule):** name (`MBENFID`) + type (`MTYPE`) + split (`MSPLIT`) are mandatory and currently satisfied; relationship is desirable but may legitimately fall back to `1000` when the source lacks it.

**Confidence:** High. The output is directly measured; the residual issue is isolated to one hardcoded field.

**Recommended action:** One surgical enrichment: derive `MRELATION` from `RELATE_CODE` (reuse the existing benf-type derivation path), keep `1000` only as the unmapped fallback. Type/split/sequence need **no** change. This is a low-risk, self-contained fix that can proceed without further client input beyond confirming the LifePRO→QLAdmin relationship-code crosswalk.

---

## Consolidated recommendation

| Item | Can proceed now? | What it needs | Blocks full dataset? |
|---|:--:|---|:--:|
| 21D | **Yes (done)** | Client sign-off on non-ISWL staying 4.00% | No |
| 21E | Partially | Finish/validate `QUIKCVS` rate load (Issue #41) + small UL fund-balance load | No (rates run separately) |
| 21F | **Yes** | Business choice on depth; re-extract only if full history required | No |
| 21G | Partially | One answer: QLAdmin target field for premium/basis totals | No (can stage as report) |
| 21I | **Yes** | Relationship-code crosswalk; surgical `MRELATION` enrichment | No |

**Net:** None of the five blocks producing a full dataset. 21D/21F/21I have defensible answers ready today; 21E and 21G each need exactly one confirmation and their source sides are already solved. Recommend proceeding with the batch on these documented assumptions and routing the two single-question items (E compute-vs-load already answered → rate-load task; G target field) to the client in parallel.

---

---

## Adoption (2026-07-09)

These recommendations were **adopted as official decisions** and implemented in engine **v57.63**.

See: `Issue_Log_Items/Issue_21/Issue_21_Open_Items_Official_Decisions.md`

| Item | Adoption note |
|---|---|
| 21D | Confirmed — already implemented v57.36 |
| 21E | Confirmed — UL `FV_BALANCE2` → `MCV0` coded; traditional remains QuikCvs compute |
| 21F | Confirmed — accept ~2017 floor |
| 21G | Confirmed — source locked; staged to `Reports/issue21g_premium_basis_totals.csv` |
| 21I | **Refined:** `MRELATION=1000` retained intentionally (RNA has no kinship field for B1/B2); type/split already correct |

*Originally analysis-only; now superseded by Official Decisions + v57.63 code.*
