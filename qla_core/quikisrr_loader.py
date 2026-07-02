"""
Issue #34 PR-7 — ISWL partial surrender history loader.

Builds QuikClms, QuikClmp, QuikBenh, and QuikIsrr rows from PACTG 0561 events.
Planning reference: Issue_Log_Items/Issue_34/Issue_34_Final_SME_Signoff_Package.md
"""
from __future__ import annotations

import csv
import re
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

from qla_core.cso_mortality_crosswalk import ISWL_MPLAN_ALLOWLIST

HOLD_POLICIES = frozenset({"9010780411"})
ORIGSTATUS_FIXED = "22"
MPHASE_PARTIAL = "0"
CLAIMSTAT_SURRENDER = "99"
CAUSE_PARTIAL = "SRR"
BENH_TYPE_PARTIAL = "8"

COVERAGE_TO_MPLAN = {
    "658 CEN I": "1658C1",
    "658 CEN SD": "1658CS",
    "659 CEN II": "1659C2",
    "659 CEN SR": "1659CR",
    "659 CEN SD": "1659CS",
    "659 SR GD": "1659SR",
    "669 SR GD": "1669SR",
    "679 CEN SD": "1679CS",
}

QUIKCLMS_FIELDS = [
    "MPOLICY", "MPHASE", "CLAIMNUM", "CLAIMSTAT", "DTOFDEATH", "RPTDATE", "PDDATE",
    "MPAID", "MFACE", "DIVIDENDS", "LOAN", "NETDB", "PREMIUM", "SUSPENSE", "ADJUST",
    "CAUSE", "MEMOTEXT", "ORIGSTTUS", "ACCPTDATE", "MCONTEST", "MINTST", "MINTDAYS",
    "MINTRATE", "MINTAMT", "MSURRCHG", "MSEQ", "MHOLDINT", "MFEDTAX", "MSTTAX",
    "MCLMPNDLTR", "MFACPMT", "MPHPAIDTO",
]

QUIKCLMP_FIELDS = [
    "MPOLICY", "MPHASE", "MCHECKNO", "MAMOUNT", "MPAYNAME", "MPAYADDR1", "MPAYADDR2",
    "MPAYCITY", "MPAYST", "MPAYZIP", "MPAYZIP2", "MTIN", "MBANKNO", "MHDPMT", "MHDCODE",
    "MCHKDATE", "MPMTDATE", "MSEQ", "MHOLDINT", "MFEDTAX", "MSTTAX", "MGROSS", "MDOB",
    "MGENDER", "MCOUNTRY",
]

QUIKBENH_FIELDS = ["MPOLICY", "MBENTYP", "MDATE", "MBEN"]

QUIKISRR_FIELDS = ["MPOLICY", "MSURRDATE", "MSURRAMT"]


def norm(v: str) -> str:
    s = (v or "").strip()
    return "" if s and set(s) == {"-"} else s


def norm_date(v: str) -> str:
    d = re.sub(r"[^0-9]", "", norm(v))
    return d[:8] if len(d) >= 8 else ""


def norm_policy_digits(v: str) -> str:
    return re.sub(r"[^0-9]", "", norm(v))


def xwalk_policy(pactg_policy: str) -> str:
    pol = norm_policy_digits(pactg_policy)
    if len(pol) == 10 and pol.startswith("9"):
        return pol[1:] + "C"
    return pol


def parse_amount(v: str) -> float | None:
    s = norm(v)
    if not s:
        return None
    try:
        return float(s)
    except ValueError:
        return None


def fmt_amount(v: float | None) -> str:
    if v is None:
        return "0.00"
    return f"{v:.2f}"


def map_mplan(plan_code: str, product_id: str) -> tuple[str, str]:
    pc = norm(plan_code)
    pid = norm(product_id)
    if pc in COVERAGE_TO_MPLAN:
        return COVERAGE_TO_MPLAN[pc], "PLAN_CODE"
    if pid in COVERAGE_TO_MPLAN:
        return COVERAGE_TO_MPLAN[pid], "PRODUCT_ID"
    return "", ""


@dataclass
class PartialSurrenderEvent:
    policy_number: str
    mpolicy: str
    mplan: str
    mplan_source: str
    effective_date: str
    date_added: str
    trans_amount: float
    record_sequence: str
    benefit_seq: str
    debit_code: str
    reversal_code: str
    mseq: int = 0


@dataclass
class PayeeInfo:
    client_id: str
    source: str  # OWNR | INSD
    payname: str
    addr1: str
    addr2: str
    city: str
    state: str
    zip5: str
    zip2: str
    tin: str


@dataclass
class EmitResult:
    clms_rows: list[dict] = field(default_factory=list)
    clmp_rows: list[dict] = field(default_factory=list)
    benh_rows: list[dict] = field(default_factory=list)
    isrr_rows: list[dict] = field(default_factory=list)
    candidates: list[PartialSurrenderEvent] = field(default_factory=list)
    emitted_events: list[PartialSurrenderEvent] = field(default_factory=list)
    hold_rows: list[dict] = field(default_factory=list)
    reversal_excluded: list[dict] = field(default_factory=list)
    payee_exceptions: list[dict] = field(default_factory=list)
    sequence_audit: list[dict] = field(default_factory=list)
    product_id_fallbacks: list[dict] = field(default_factory=list)


def _blank_clms_row() -> dict:
    return {f: "" for f in QUIKCLMS_FIELDS}


def _blank_clmp_row() -> dict:
    return {f: "" for f in QUIKCLMP_FIELDS}


def load_pactg_events(pactg_path: Path) -> tuple[list[PartialSurrenderEvent], list[dict], list[dict], list[dict]]:
    """Return (eligible_events, hold_rows, reversal_excluded, product_id_fallbacks)."""
    eligible: list[PartialSurrenderEvent] = []
    hold_rows: list[dict] = []
    reversal_excluded: list[dict] = []
    product_id_fallbacks: list[dict] = []
    iswl_rows_non_hold = 0

    with open(pactg_path, encoding="latin-1", newline="") as f:
        reader = csv.DictReader(f)
        cols = {c.strip(): c for c in reader.fieldnames or []}

        def g(raw: dict, name: str) -> str:
            col = cols.get(name)
            return norm(raw.get(col, "")) if col else ""

        for raw in reader:
            dc = re.sub(r"[^0-9]", "", g(raw, "DEBIT_CODE"))
            if not dc or str(int(dc)) != "561":
                continue

            pol = norm_policy_digits(g(raw, "POLICY_NUMBER"))
            plan_code = g(raw, "PLAN_CODE")
            product_id = g(raw, "PRODUCT_ID")
            mplan, mplan_source = map_mplan(plan_code, product_id)
            if mplan not in ISWL_MPLAN_ALLOWLIST:
                continue

            rev = g(raw, "REVERSAL_CODE")
            eff = norm_date(g(raw, "EFFECTIVE_DATE"))
            da = norm_date(g(raw, "DATE_ADDED"))
            amt = parse_amount(g(raw, "TRANS_AMOUNT"))
            rec = {
                "policy_number": pol,
                "mpolicy": xwalk_policy(pol),
                "mplan": mplan,
                "mplan_source": mplan_source,
                "effective_date": eff,
                "date_added": da,
                "trans_amount": fmt_amount(amt),
                "record_sequence": g(raw, "RECORD_SEQUENCE"),
                "benefit_seq": g(raw, "BENEFIT_SEQ"),
                "reversal_code": rev,
            }

            if rev == "Y":
                reversal_excluded.append(rec)
                continue

            if pol in HOLD_POLICIES:
                hold_rows.append(rec)
                continue

            if mplan_source == "PRODUCT_ID":
                product_id_fallbacks.append({
                    **rec,
                    "plan_code": plan_code,
                    "product_id": product_id,
                })

            event = PartialSurrenderEvent(
                policy_number=pol,
                mpolicy=xwalk_policy(pol),
                mplan=mplan,
                mplan_source=mplan_source,
                effective_date=eff,
                date_added=da,
                trans_amount=amt if amt is not None else 0.0,
                record_sequence=g(raw, "RECORD_SEQUENCE"),
                benefit_seq=g(raw, "BENEFIT_SEQ"),
                debit_code=g(raw, "DEBIT_CODE"),
                reversal_code=rev,
            )
            eligible.append(event)
            iswl_rows_non_hold += 1

    return eligible, hold_rows, reversal_excluded, product_id_fallbacks


def load_payee_index(
    clid_path: Path,
    clnt_path: Path,
) -> tuple[dict[str, PayeeInfo], dict[str, PayeeInfo]]:
    """Return (owner_by_policy, insured_by_policy) keyed by MPOLICY."""
    client_ids: dict[str, dict[str, str]] = defaultdict(dict)
    with open(clid_path, encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            mp = norm(row.get("MPOLICY", ""))
            rel = norm(row.get("MRELATION", "")).upper()
            cid = norm(row.get("MCLIENTID", ""))
            if not mp or not cid:
                continue
            if rel in ("OWNR", "INSD") and rel not in client_ids[mp]:
                client_ids[mp][rel] = cid

    clients: dict[str, dict] = {}
    with open(clnt_path, encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            cid = norm(row.get("MCLIENTID", ""))
            if cid:
                clients[cid] = row

    def build_payee(cid: str, source: str) -> PayeeInfo | None:
        c = clients.get(cid)
        if not c:
            return None
        fname = norm(c.get("MFNAME", ""))
        lname = norm(c.get("MLNAME", ""))
        name = " ".join(p for p in (fname, lname) if p).upper()
        if not name:
            return None
        zip_full = norm(c.get("MZIP", ""))
        zip2 = norm(c.get("MZIP2", ""))
        zip5 = zip_full[:5] if zip_full else ""
        tin = norm(c.get("MTAXID", ""))
        if tin == "000000000":
            tin = ""
        return PayeeInfo(
            client_id=cid,
            source=source,
            payname=name,
            addr1=norm(c.get("MADDR1", "")),
            addr2=norm(c.get("MADDR2", "")),
            city=norm(c.get("MCITY", "")),
            state=norm(c.get("MSTATE", "")),
            zip5=zip5,
            zip2=zip2,
            tin=tin,
        )

    owner_by_policy: dict[str, PayeeInfo] = {}
    insured_by_policy: dict[str, PayeeInfo] = {}
    for mp, rels in client_ids.items():
        if "OWNR" in rels:
            p = build_payee(rels["OWNR"], "OWNR")
            if p:
                owner_by_policy[mp] = p
        if "INSD" in rels:
            p = build_payee(rels["INSD"], "INSD")
            if p:
                insured_by_policy[mp] = p

    return owner_by_policy, insured_by_policy


def resolve_payee(
    mpolicy: str,
    owner_by_policy: dict[str, PayeeInfo],
    insured_by_policy: dict[str, PayeeInfo],
) -> tuple[PayeeInfo | None, str]:
    if mpolicy in owner_by_policy:
        return owner_by_policy[mpolicy], "OWNR"
    if mpolicy in insured_by_policy:
        return insured_by_policy[mpolicy], "INSD"
    return None, "NONE"


def existing_phase0_max_mseq(clms_path: Path) -> dict[str, int]:
    max_seq: dict[str, int] = defaultdict(int)
    if not clms_path.is_file():
        return max_seq
    with open(clms_path, encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            if norm(row.get("MPHASE", "")) != MPHASE_PARTIAL:
                continue
            mp = norm(row.get("MPOLICY", ""))
            try:
                seq = int(norm(row.get("MSEQ", "")) or "0")
            except ValueError:
                seq = 0
            if mp and seq > max_seq[mp]:
                max_seq[mp] = seq
    return max_seq


def assign_sequences(events: list[PartialSurrenderEvent], existing_max: dict[str, int]) -> None:
    by_policy: dict[str, list[PartialSurrenderEvent]] = defaultdict(list)
    for ev in events:
        by_policy[ev.mpolicy].append(ev)

    for mp, group in by_policy.items():
        group.sort(key=lambda e: (e.effective_date, e.date_added, e.record_sequence, e.policy_number))
        start = existing_max.get(mp, 0)
        for i, ev in enumerate(group, start=start + 1):
            ev.mseq = i


def build_claimnum(mpolicy: str, mseq: int) -> str:
    digits = mpolicy.replace("C", "")
    return f"PS-{digits}-{mseq:03d}"


def build_rows_for_event(ev: PartialSurrenderEvent, payee: PayeeInfo) -> tuple[dict, dict, dict, dict]:
    amt = fmt_amount(ev.trans_amount)
    claimnum = build_claimnum(ev.mpolicy, ev.mseq)
    memotext = (
        f"{claimnum}|PARTIAL_SURRENDER|ISWL|MPHASE=0|MSEQ={ev.mseq}|"
        f"EFF={ev.effective_date}|ADDED={ev.date_added}"
    )

    clms = _blank_clms_row()
    clms.update({
        "MPOLICY": ev.mpolicy,
        "MPHASE": MPHASE_PARTIAL,
        "CLAIMNUM": claimnum,
        "CLAIMSTAT": CLAIMSTAT_SURRENDER,
        "DTOFDEATH": ev.effective_date,
        "RPTDATE": ev.effective_date,
        "PDDATE": ev.date_added,
        "MPAID": amt,
        "MFACE": amt,
        "CAUSE": CAUSE_PARTIAL,
        "MEMOTEXT": memotext,
        "ORIGSTTUS": ORIGSTATUS_FIXED,
        "ACCPTDATE": ev.date_added,
        "MSEQ": str(ev.mseq),
        "MSURRCHG": "F",
        "MCONTEST": "F",
        "MFACPMT": "F",
    })

    clmp = _blank_clmp_row()
    clmp.update({
        "MPOLICY": ev.mpolicy,
        "MPHASE": MPHASE_PARTIAL,
        "MCHECKNO": "0",
        "MAMOUNT": amt,
        "MPAYNAME": payee.payname,
        "MPAYADDR1": payee.addr1,
        "MPAYADDR2": payee.addr2,
        "MPAYCITY": payee.city,
        "MPAYST": payee.state,
        "MPAYZIP": payee.zip5,
        "MPAYZIP2": payee.zip2,
        "MTIN": payee.tin,
        "MHDPMT": "C",
        "MPMTDATE": ev.date_added,
        "MSEQ": str(ev.mseq),
        "MHOLDINT": "0.00",
        "MFEDTAX": "0.00",
        "MSTTAX": "0.00",
        "MGROSS": amt,
    })

    benh = {
        "MPOLICY": ev.mpolicy,
        "MBENTYP": BENH_TYPE_PARTIAL,
        "MDATE": ev.date_added,
        "MBEN": amt,
    }

    isrr = {
        "MPOLICY": ev.mpolicy,
        "MSURRDATE": ev.effective_date,
        "MSURRAMT": amt,
    }

    return clms, clmp, benh, isrr


def build_emit(
    repo_root: Path,
    *,
    pactg_path: Path | None = None,
    clid_path: Path | None = None,
    clnt_path: Path | None = None,
    existing_clms_path: Path | None = None,
) -> EmitResult:
    root = Path(repo_root)
    pactg = pactg_path or root / "QLA_Migration" / "Source" / "PACTG_Accounting_Extract20260530.csv"
    clid = clid_path or root / "QLA_Migration" / "Output" / "quikclid.csv"
    clnt = clnt_path or root / "QLA_Migration" / "Output" / "quikclnt.csv"
    clms_existing = existing_clms_path or root / "QLA_Migration" / "Output" / "quikclms.csv"

    result = EmitResult()
    candidates, hold_rows, reversal_excluded, fallbacks = load_pactg_events(pactg)
    result.candidates = candidates
    result.hold_rows = hold_rows
    result.reversal_excluded = reversal_excluded
    result.product_id_fallbacks = fallbacks

    owner_map, insured_map = load_payee_index(clid, clnt)
    existing_max = existing_phase0_max_mseq(clms_existing)
    assign_sequences(candidates, existing_max)

    for ev in candidates:
        payee, payee_src = resolve_payee(ev.mpolicy, owner_map, insured_map)
        if payee is None:
            result.payee_exceptions.append({
                "policy_number": ev.policy_number,
                "mpolicy": ev.mpolicy,
                "mplan": ev.mplan,
                "effective_date": ev.effective_date,
                "date_added": ev.date_added,
                "trans_amount": fmt_amount(ev.trans_amount),
                "mseq": ev.mseq,
                "reason": "NO_OWNR_OR_INSD",
            })
            continue

        clms, clmp, benh, isrr = build_rows_for_event(ev, payee)
        result.clms_rows.append(clms)
        result.clmp_rows.append(clmp)
        result.benh_rows.append(benh)
        result.isrr_rows.append(isrr)
        result.emitted_events.append(ev)
        result.sequence_audit.append({
            "mpolicy": ev.mpolicy,
            "mseq": ev.mseq,
            "effective_date": ev.effective_date,
            "date_added": ev.date_added,
            "record_sequence": ev.record_sequence,
            "claimnum": clms["CLAIMNUM"],
            "payee_source": payee_src,
        })

    return result


def read_csv_rows(path: Path) -> tuple[list[str], list[dict]]:
    with open(path, encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        fields = list(reader.fieldnames or [])
        rows = [dict(r) for r in reader]
    return fields, rows


def write_csv_rows(path: Path, fields: list[str], rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with open(tmp, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, "") for k in fields})
    tmp.replace(path)
