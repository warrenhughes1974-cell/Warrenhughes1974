# Issue #21D — Trace Samples

**Intake date:** 2026-06-27  
**Converter version:** v57.35  
**Primary example policy:** `010713704C` (legacy `9010713704`)

---

## Sample 1 — Track A: Interest rate (010713704C)

### Client observation

| System | Field | Value |
|--------|-------|-------|
| QLAdmin | Dividend Accum Int Rate | **4.00%** |
| LifePRO / business | Expected ISWL crediting rate | **4.50%** |

### End-to-end trace

```
LifePRO policy 9010713704
  └─ PCOVR / quikridr base MPLAN ──► 1659C2 (659 CEN II)  [ISWL]
        │
        ├─ quikplan (plan template 1659C2)
        │     NFOINT = A          ◄── CSO Mortiality Crosswalk (4.50% code)
        │     VARGP = 4           ◄── Sync_Rulebook_quikplan.csv default
        │     DEPINT = 0.00       ◄── rulebook default
        │
        └─ quikdvdp (policy row 010713704C)
              MDEPINT = 4.00      ◄── Sync_Rulebook_quikdvdp.csv HARDCODED ★
              MDEPOSIT = 0.00
              MINTYTD = 0.00
```

### Rulebook smoking gun

**File:** `QLA_Migration/Configs/Sync_Rulebook_quikdvdp.csv`

```csv
,MDEPINT,4.00,Hardcoded Product Rate (Change Default_Value to your actual rate),,
```

### CSO crosswalk (authoritative 4.50%)

**File:** `plan_analysis/source_data/rates/CSO_Mortiality_Crosswalk.csv` (row: 659 CEN II → 1659C2)

| Field | Value |
|-------|-------|
| `nfo_interest_source` | 4.50% |
| `nfo_interest_code` | A |
| `cv_int_rate_source` | 4.50% |
| `qla_cv_int_rate_code` | A |

### Output evidence (010713704C)

**quikdvdp.csv**

```text
MPOLICY     MDEPOSIT  MINTYTD  MDEPINT  MINTDATE
010713704C  0.00      0.00     4.00     
```

**quikplan.csv (template 1659C2)**

```text
PLAN    NFOINT  VARGP  DEPINT
1659C2  A       4      0.00
```

### Fleet confirmation

All **2,268 ISWL policies** in `Issue_21D_Interest_Rate_Population.csv` show `QUIKDVDP_MDEPINT = 4.00`.

---

## Sample 2 — Track B: Blank names (010713704C)

### Client observation

QLAdmin Policy Display shows **blank insured and owner names** (comma placeholders).

### End-to-end trace

```
PPOLC (9010713704)
  PRIMARY_PERSON = "I"          ◄── type flag, NOT client ID
        │
        ├─ v57.28 guard (app.py) ──► MPRIMID cleared (would have leaked "I" pre-v57.28)
        │
        └─ rel_map from quikclid
              quikclid rows for 010713704C:
                MCLIENTID=44748  MRELATION=SERV  (from RNA SA)
                MCLIENTID=17040  MRELATION=BANK  (from RNA BK)
              ◄── NO IN / NO PO rows
        │
        └─ quikmstr result
              MPRIMID = (blank)
              MOWNRID = (blank)
              QLAdmin name display = blank
```

### RNA extract (policy 9010713704)

**File:** `QLA_Migration/Source/RelationshipNameAddress_Extract_20260530.csv`

| NAME_ID | RELATE_CODE | KEY_NAME |
|---------|-------------|----------|
| 44748 | SA | CENTRAL STATES HEALTH & LIFE |
| 17040 | BK | FIRST NATIONAL BANK OF OMAHA |

**Missing from RNA extract for this policy:** `IN`, `PO`, `PA`, `B1`, `B2` (present in LifePRO hierarchy per `claims_analysis/output/relationship_hierarchy_analysis.csv`).

### quikclid output

```text
MCLIENTID  MPOLICY     MPHASE  MRELATION
44748      010713704C  1       SERV
17040      010713704C  1       BANK
```

### quikmstr output

```text
MPOLICY     MPRIMID  MOWNRID
010713704C           (blank)  (blank)
```

---

## Sample 3 — Track B: ID not in quikclnt (010766896C)

### Trace

```
quikmstr
  MPRIMID = 592064
  MOWNRID = 592064
        │
        ├─ quikclid ──► IN + PO rows exist for 592064
        │
        └─ quikclnt lookup for 592064 ──► NOT FOUND ★
              RNA for NAME_ID 592064:
                INDIVIDUAL_LAST = JOHNSON
                INDIVIDUAL_FIRST = PENNY
                RELATE_CODE = IN, PA
```

**Root cause:** Client ID promoted to quikmstr via rel_map; **quikclnt conversion did not emit client 592064**, so QLAdmin name join fails despite RNA having names.

---

## Sample 4 — Track B: Partial owner gap (011080481C)

### Trace

```text
MPRIMID = 607190  ──► RNA: YOUNTS, JOSHUA (IN) — but 607190 NOT IN quikclnt ★
MOWNRID = 713150  ──► quikclnt: YOUNTS, JOSHUA (owner resolves)
```

Insured side fails (missing quikclnt row); owner side displays correctly.

---

## Sample 5 — Track A: ISWL plan template (1658C1)

**quikplan.csv**

```text
PLAN    DESCR                           NFOINT  VARGP  DEPINT
1658C1  INTEREST-SENSITIVE WHOLE LIFE   A       4      0.00
```

**CSO crosswalk:** 658 CEN I → 1658C1 → 4.50% / code A

**quikdvdp:** every policy on 1658C1 carries `MDEPINT = 4.00` (hardcoded).

---

## Sample 6 — Negative control: PRIMARY_PERSON guard

| Check | Fleet result |
|-------|--------------|
| PPOLC `PRIMARY_PERSON = 'I'` rows | 4,929 |
| quikmstr `MPRIMID = 'I'` | **0** |
| v57.28 guard | Active in `app.py` / `QLA_Migration/app.py` (~lines 5442–5446) |

The type-flag leak is **fixed**; remaining blank names are **ID population gaps**, not flag mis-mapping.

---

## Related Issue #21 golden policies (blank-name cohort)

| MPOLICY | MPLAN | Track B pattern |
|---------|-------|-----------------|
| 010713704C | 1659C2 | RNA missing IN/PO |
| 010713705C | 1659C2 | RNA missing IN/PO |
| 010826551C | 1659CR | RNA missing IN/PO |
| 010766896C | 1659C2 | ID not in quikclnt |
| 011080481C | 1659C2 | Insured ID not in quikclnt |

See full population: `Issue_21D_Blank_Name_Population.csv`
