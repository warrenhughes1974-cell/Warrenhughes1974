# Citizens / CFIC — Access App Business Walkthrough

**Purpose:** Confirm how `CFIProposalMakerRev2.mdb` is used in production so we map the right products and columns.  
**Who should attend:** Someone who runs proposals today (agent / product / ops).  
**Time:** ~45–60 minutes with Access open.

---

## Prep

- [ ] Open `source/CFIProposalMakerRev2.mdb` in Microsoft Access
- [ ] Have `extracted/*.csv` available for side-by-side checks
- [ ] Capture screenshots or notes for each product path below

---

## 1. Products sold today

**Confirmed 2026-07-08: ALL products below are ACTIVE.**  
Still capture marketing names and any nuances during the walkthrough.

| Access object / table | Active? | Business name | Notes |
|-----------------------|---------|---------------|-------|
| 5 Year Term | Active | | |
| 5 Year Term Rider | Active | | |
| 10 Year Term | Active | | |
| 10 Year Term Rider | Active | | |
| PermaLife 8 Adult | Active | | |
| PermaLife 8 Juvenile | Active | | |
| PermaLife 7 (Before tables) | Active | | Table name says "Before" but business says active |
| Quest (WL / PdUp65 / Pay20) | Active | | |
| ALP (forms) / LPI (table) | Active | | Confirm ALP = LPI |

**Key question (resolved):** All products are active for new business / proposals.

---

## 2. ALP vs LPI

- [ ] Open **Proposal Maker – ALP**
- [ ] Confirm which table it reads (`LPI`?)
- [ ] Record: product name, issue ages, plan options (`SP`, `Pay20Life`, `PdUp65`)
- [ ] Note: is this juvenile-only, adult, or both?

**Answer:** ALP is _______________________________

---

## 3. PermaLife 7 vs 8

- [ ] Confirm PL8 is current for new business
- [ ] Confirm PL7 is archive / in-force illustration only (or still sold)
- [ ] Ask whether premiums are intentionally identical and only CV/paid-up differ

**Answer:** _______________________________________

---

## 4. Rate meaning (critical for mapping)

Walk one term quote and one whole-life quote:

### Term (5 or 10 year)

- [ ] What do `K10` … `K500` mean? (per $1,000 by face band?)
- [ ] Is rate annual / monthly / modal?
- [ ] How is `WOP` applied?
- [ ] Why do rider tables lack Sex?

### Whole life (PermaLife 8)

- [ ] What is `RateUnder100K` / `RateOver100K`? (per $1,000?)
- [ ] Are CashValue* / PaidUp* used only for illustrations?
- [ ] Smoker: how is it collected on the form?

### Quest

- [ ] Confirm three plans: WL, Paid-up at 65, 20-Pay
- [ ] Why are some ages blank for PdUp65 / Pay20?
- [ ] How are MaleWOP / FemaleWOP used?

---

## 5. Premium Adjustments screens

- [ ] Who is allowed to change rates?
- [ ] How often are rates updated?
- [ ] Is there a paper/PDF rate book that is the true authority?
- [ ] Any state / company variations not in this DB?

---

## 6. Output of a proposal

- [ ] What does the tool produce? (print form, PDF, Excel, nothing?)
- [ ] Which fields must match if we rebuild or convert rates?
- [ ] Sample: run one known quote and save the output for validation later

**Sample quote to capture:**

| Field | Value |
|-------|-------|
| Product | |
| Age / Sex / Smoker | |
| Face amount | |
| Modal premium shown | |
| WOP Y/N | |
| CV / paid-up shown (if any) | |

---

## 7. Target system (tie to decision)

Ask the business owner:

> Where should these rates live going forward — QLAdmin, LifePRO, a new proposal tool, or hybrid?

Record answer in `docs/target_platform.md`.

---

## Walkthrough outcome checklist

- [ ] Active product list signed off
- [ ] ALP/LPI naming resolved
- [ ] PL7 disposition decided
- [ ] Rate unit / modality documented
- [ ] Illustration vs premium columns classified
- [ ] Target platform option chosen (A/B/C/D)
- [ ] At least one sample quote saved for later parity testing
