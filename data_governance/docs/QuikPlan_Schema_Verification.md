# QuikPlan Schema Verification

Verified against CSO data region (`Q:\CSO\CSO_Test_6_30_2025`).

## QuikPlan (QUIKPLAN.DBF)

| Business name | Physical field | Type | Notes |
|---|---|---|---|
| PLAN | PLAN | C(6) | Unique plan code |
| PAR | PAR | C(1) | 0 or 1 |
| BASIS | BASIS | C(4) | Case-sensitive annuity codes |
| LOANINTX | LOANINTX | C(1) | A or R |
| DEPINT | DEPINT | N(6).2 | MYGA deposit interest |
| LOAGE / HIAGE | LOAGE / HIAGE | N(2) / N(3) | Plan-level issue age range (Age 1 row) |
| RENEW | RENEW | C(1) | N default; Y allowed for plans starting with 5 |
| PAYRS | **PAYYRS** | N(3) | Payment years |
| PAYAGE | PAYAGE | N(3) | Payment age |
| INSYRS | INSYRS | N(3) | Insurance years |
| INSAGE | INSAGE | N(3) | Insurance age |
| SEMI / QTRL / MTHD / MTHB | same | N(8).4 | Modal payment factors |
| INITVAL | INITVAL | N(8).2 | Default 1000 |
| COMMID | COMMID | C(4) | References QuikComm |
| MAXUNITS | **MAXUNIT** | N(6) | Maximum units |
| MINUNIT | MINUNIT | N(4) | Minimum units |
| ROUNDING | **RRULE** | C(1) | Default B |
| AUTONFO | AUTONFO | C(1) | Default 0 |
| DEFICIENCY | DEFICIENCY | C(1) | N for A–Z / 9-series plans |
| BACTIVE | BACTIVE | L(1) | New-business status |
| PLANVALOPT | PLANVALOPT | L(1) | Plan value option |
| MLAPSE | MLAPSE | N(3) | Default 0 |
| MNAICLOB | MNAICLOB | C(6) | Default N |
| VARGP / VARDB | same | C(1) | Variable GP/DB flags |
| PLANTYPE | PLANTYPE | C(3) | MEDS plan type |
| HCOMMIP / HRIGPKEY | same | L(1) | MEDS commission / rating-key flags |

## Related tables

| Table | Plan field | Notes |
|---|---|---|
| QuikGps, QuikPlGp, QuikDbs, QuikPlDb, QuikPlCv, QuikPlTv, QuikCvs, QuikTvs, QuikNps, QuikNff, QuikPl* member tables, QuikIssc | PLAN | Rate/key/member tables |
| QuikAint, QuikAing, QuikAexp, QuikAinf, QuikUint | MPLAN | Annuity / UL tables |
| QuikComm (QUIKCOMM.DBF) | COMMID | Commission Setup — QUIKCOM not present |

## Logical fields

`BACTIVE`, `PLANVALOPT`, `HCOMMIP`, `HRIGPKEY` stored as DBF Logical — Python `True` / `False` / `None` via dbfread.

## LOAGE Age 1

QuikPlan stores one LOAGE/HIAGE pair per plan representing the plan-level minimum issue age (Age 1 row): LOAGE must be 0 and LOAGE < HIAGE.
