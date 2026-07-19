# Policy Data Schema Verification

**Source:** Live CSO DBFs at `Q:\CSO\CSO_Test_6_30_2026` (2026-07-19)  
**Governance items:** DG-QUIKMSTR, DG-QUIKCLNT, DG-QUIKCLID

## Resolved field questions

| Business note | Physical field | Notes |
|---------------|----------------|-------|
| Policy number (not MPLAN) | **MPOLICY** C(10) on QuikMstr | MPLAN is on QuikRidr only |
| ISSDATE / MISSDT | **MISSDT** D(8) | ISSDATE does not exist |
| LASTNAME / MLNAME | **MLNAME** C(30) on QuikClnt | LASTNAME does not exist |
| MSTATDATE | Once on QuikMstr | Field #3 |
| Owner / assignee / payer IDs | **MOWNRID**, **MASGNID**, **MPAYRID** | Not MOWNERID/MASSIGID/MPAYERID |
| QuikClid MRIDRID | **Absent** | Match INSD via (MPOLICY, MPHASE) → QuikRidr |
| QuikList group key | **MGROUP** C(8) | |

## QuikMstr (quikmstr.dbf) — key fields

MPOLICY, MSTATUS, MSTATDATE, MISSDT, MPAIDTO, MBILLTO, MNFOPT, MDIVOPT, MBILLFRM, MBILLDAY, MBANKNO, MMODE, MISSUEST, MGROUP, MPRIMID, MOWNRID, MPAYRID, MASGNID, MBENPID, MBENCID, MAPPDATE, MISSCNTRY, MOWNCID, MRESSTATE, MISSCLASS

## QuikClnt (quikclnt.dbf) — key fields

MCLIENTID, MTYPE, MTAXIDTYPE, MFNAME, MLNAME, MADDR1, MCITY, MSTATE, MZIP, MDOB, MSEX, MLANGUAGE

Approved client-type codes observed in CSO: `I` (individual), `B` (business).  
Approved tax-ID types observed: `S` (SSN), `E` (EIN). Seeded in `config/policy_code_authorities.csv`.

## QuikClid (quikclid.dbf) — all fields

MCLIENTID C(12), MPOLICY C(10), MPHASE N(2), MRELATION C(4)

## QuikRidr key fields

MPOLICY, MPHASE, MRIDRID, MPLAN, …

## Deferred

- MDIVOPT (DG-QUIKMSTR-009)
- MRESSTATE (DG-QUIKMSTR-025)
