# Issue #169 — Client asks (drafts for Warren)

Two separate asks. They go to different people and shouldn't be combined — one is an
assumptions request, the other is a "is zero correct?" question.

Figures below come from `docs/Valuation/analysis/reserve_gap_population.csv`
(ValX vs QuikValf, 6/30 valuation).

| QL code | LifePRO plan | Description | Policies | LifePRO | QL |
|---|---|---|---:|---:|---:|
| `7619PU` | 619 SPS PU | Decreasing term paid up for spouse | 1 | $90.47 | $0.00 |
| `901ADB` | 1596 L01 | Accidental death benefit rider | 4 | $261.45 | $98.00 |
| `996ADB` | 1596 | Accidental death benefit rider | 1 | $54.00 | $25.00 |
| `9595WP` | 1595 | Disability waiver of premium | 3 | $0.00 | $56.00 |
| `967ADB` | 1596 667 | Accidental death benefit rider | 2 | $0.00 | $43.00 |
| `9SLADB` | SAL ADB | SAL accidental death benefit | 5 | $0.00 | $5.00 |

All six have blank `MORT` / `RSVINT` / `RSVMETH` in `QuikPlTv` because none of them has a row
in `CSO_Valuation_Setup.csv`. The first three matter (LifePRO reserves them, we don't fully);
the last three are the reverse case and only need a yes/no.

---

## 1. To CSO — valuation assumptions for three plans

**Subject:** Three plans missing from the valuation setup workbook

Hi [name],

I'm working through the reserve differences on the conversion and three plans have no row in
the CSO Valuation Setup workbook, so there's nothing for us to set the mortality table, reserve
interest, or reserve method from:

- 619 SPS PU — decreasing term paid up for spouse
- 1596 L01 — accidental death benefit rider
- 1596 — accidental death benefit rider

Without those three values the reserve can't compute on a CSO basis. LifePRO is holding about
$406 total across six policies on them, so it's small money, but I don't want to guess at the
assumptions and have it come back at us later.

Can you send the mortality table, reserve interest rate, and reserve method for each one? If any
of them intentionally aren't reserved on a CSO basis, that's fine too — just say so and I'll set
them up that way.

Thanks,
Warren

---

## 2. To Jill — three riders where LifePRO shows zero

**Subject:** Three riders showing a reserve in QL but not in LifePRO

Hi Jill,

On the missing reserves issue, three of the plans on your list are actually the opposite of the
rest — LifePRO's own valuation shows zero on them and QL is the one showing a reserve:

- 1595, disability waiver of premium — LifePRO $0, QL $56, 3 policies
- 1596 667, accidental death benefit — LifePRO $0, QL $43, 2 policies
- SAL ADB — LifePRO $0, QL $5, 5 policies

That's $104 total so it isn't a money problem, but I want to set them up the right way. Should
these carry a reserve or not? If LifePRO's zero is correct we'll turn the reserve off for them.
If they should be reserved, then LifePRO has been under-reserving and I'd rather flag that now
than after go-live.

The rest of that issue is moving separately — 667 ART is fixed, and I have a question in to CSO
on the other three.

Thanks,
Warren
