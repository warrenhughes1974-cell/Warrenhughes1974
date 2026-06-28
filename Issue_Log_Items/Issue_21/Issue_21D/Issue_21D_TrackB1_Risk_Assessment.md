# Issue #21D — Track B1 Risk Assessment

**Track:** B1 — quikclnt Referential Integrity  
**Date:** 2026-06-27  
**Converter version:** v57.35 (baseline)  
**Population:** ~7 policies recoverable · 14 missing NAME_IDs fleet-wide  
**Development scope:** Authorized — this assessment only  
**Excluded:** Track B2 (RNA re-extract) — client-owned; not scored here

---

## 1. Implementation summary (for risk context)

| Element | Planned approach |
|---------|------------------|
| Defect | RNA NAME_IDs with valid names not emitted to quikclnt (often NULL ADDRESS_ID) |
| Root cause hypothesis | `drop_duplicates(subset=['NAME_ID','ADDRESS_ID'])` + NULL address filtering |
| Touchpoint | `app.py` quikclnt source prep (~5011–5016); optional post-pass for quikclid-referenced IDs |
| Expected recovery | ~7 policies in blank-name set; up to 14 quikclnt rows added |
| Prohibited | Synthetic NAME_IDs; PRIMARY_PERSON=I → MPRIMID; role inference |

**Sample policies:** 010766896C (592064), 011080481C (607190), 010464869C, 010464870C, 010872417C, 011047402C, 011047403C

---

## 2. Risk evaluation

### 2.1 Incorrect client association risk

| Aspect | Rating | Analysis |
|--------|--------|----------|
| Wrong person linked to policy | **Low** | Fix emits existing RNA NAME_IDs only — no new ID assignment |
| Cross-policy ID collision | **Low** | NAME_IDs are LifePRO-native; emit preserves source identity |
| Name mismatch | **Low** | Names come from RNA bridge columns already used elsewhere |

**Mitigation:** Emit only when `INDIVIDUAL_LAST`/`INDIVIDUAL_FIRST` or `KEY_NAME` present in RNA. Validate emitted MCLIENTID matches RNA NAME_ID exactly. Golden policy checks on 010766896C, 011080481C.

---

### 2.2 Duplicate client record risk

| Aspect | Rating | Analysis |
|--------|--------|----------|
| Duplicate MCLIENTID in quikclnt | **Low–Medium** | Dedup logic change could create second row for same ID |
| NULL vs non-NULL ADDRESS_ID dupes | **Medium** | Same NAME_ID with NULL and populated ADDRESS_ID may exist in RNA |

**Mitigation:** Dedup by MCLIENTID (keep first with names); do not emit if MCLIENTID already in quikclnt output. Validator: quikclnt MCLIENTID uniqueness = 100%. Compare row count delta: expect +≤14 rows, not hundreds.

---

### 2.3 Referential integrity change risk

| Aspect | Rating | Analysis |
|--------|--------|----------|
| quikclid → quikclnt coverage | **Positive** | Closes known gap: 14 RNA IDs referenced but missing |
| Downstream quikmstr | **Low** | MPRIMID/MOWNRID already point to missing IDs; fix enables name resolution |
| Schema / field order | **None** | New rows conform to existing quikclnt schema |

**Mitigation:** Extend `validate_insured_owner_golden.py`: non-blank MPRIMID/MOWNRID must exist in quikclnt. Fleet check: RNA NAME_ID referenced by quikclid ⊆ quikclnt MCLIENTID.

---

### 2.4 Owner/insured relationship risk

| Aspect | Rating | Analysis |
|--------|--------|----------|
| rel_map priority change | **None** | No change to IN→MPRIMID, PO→MOWNRID mapping |
| v57.28 MPRIMID guard | **Critical** | Must remain — blocks PRIMARY_PERSON type flags |
| Partial fix (owner still blank) | **Medium** (expected) | 6 policies have PO in quikclid but owner blank for other reasons — B2 scope |

**Mitigation:** Preserve v57.28 guard verbatim. Validator: MPRIMID ∉ {I, single-alpha type flags}. Do **not** add role inference for missing IN/PO in RNA.

---

### 2.5 Validation complexity

| Aspect | Rating | Analysis |
|--------|--------|----------|
| Population reduction | **Low** | Compare `Issue_21D_Blank_Name_Population.csv` before/after |
| Referential check | **Low–Medium** | New/extended validators |
| Client UAT | **Low** | 7-policy partial fix; communicate 18 policies remain open |

**Mitigation:** `validate_issue21d_blank_names.py` with expected partial resolution metrics. Document B1-only release scope in release notes.

---

### 2.6 Operational impact

| Aspect | Rating | Analysis |
|--------|--------|----------|
| Partial fix messaging | **Medium** | Client must understand 18 policies still need RNA |
| QLAdmin NULL-address rows | **Low–Medium** | Sample 592064 — names without address |
| Batch order | **Low** | quikclnt before quikclid/quikmstr (unchanged) |

**Mitigation:** Reference `Issue_21D_Remaining_Client_Actions.md` for B2 list. UAT on NULL-address client row acceptance in QLAdmin.

---

## 3. Track B1 risk register (summary)

| ID | Risk | L | I | Score | Mitigation |
|----|------|---|---|-------|------------|
| B1-R01 | MPRIMID='I' leak reintroduced | L | H | **Medium** | Preserve v57.28 guard; validator check |
| B1-R02 | Duplicate quikclnt rows | L | M | **Low** | MCLIENTID dedup; row count bounds |
| B1-R03 | Wrong client emitted | L | H | **Low** | RNA NAME_ID only; no synthesis |
| B1-R04 | QLAdmin rejects NULL-address client | L | M | **Low** | UAT on 592064 |
| B1-R05 | Partial fix perceived as complete | M | M | **Medium** | Release notes; 18-policy B2 list |
| B1-R06 | Over-broad emit (fleet-wide rows) | L | M | **Low** | Bound to missing NAME_IDs with names |
| B1-R07 | Schema / field order drift | L | H | **Low** | Standard schema validator |

Full register: `Issue_21D_Risk_Register.md`

---

## 4. Track B1 risk decision

```text
GO
```

**Justification:** Change is **surgical and bounded** (~14 NAME_IDs, ~7 blank-name policies). Uses existing RNA identity data — no inference. Regression risk to rel_map and v57.28 guard is **Low** when guard is preserved and validators extended.

**Release note:** Track B1 alone resolves **partial** blank-name population. Full Track B requires client RNA delivery (B2). Do not score B2 in this decision.

**Mandatory Development conditions:**

1. Preserve v57.28 MPRIMID guard — no changes to rel_map role priority
2. No synthetic NAME_IDs or PRIMARY_PERSON=I mapping
3. Dedup by MCLIENTID before emit
4. Extend `validate_insured_owner_golden.py`; create `validate_issue21d_blank_names.py`
5. Document expected partial fix (7 of 25 policies)

---

*Track B1 risk assessment complete. Track B2 documented separately as external dependency.*
