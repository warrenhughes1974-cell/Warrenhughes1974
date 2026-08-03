"""Align QUIKCLMP.MSEQ to QUIKCLMS claim-header MSEQ for QLAdmin payee UI.

QLAdmin relates payees on MPOLICY + MPHASE + MSEQ.

- Death/surrender pattern: one header MSEQ=0; all payees must also be MSEQ=0.
  Payees with MSEQ 1..n under a single MSEQ=0 header are invisible in the UI.
- Partial-settlement pattern: multiple headers with MSEQ 1..n and matching payees
  must keep their own MSEQ (do not collapse).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

GOLDEN_POLICY = "9011156655C"
GOLDEN_PAYEE_COUNT = 4


class ClaimsPayeeMseqAlignError(ValueError):
    """Hard-fail when payee/header MSEQ cannot be aligned safely."""


def _strip(value: Any) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    return str(value).strip()


def _header_indexes(clms: pd.DataFrame) -> tuple[dict[tuple[str, str], list[str]], set[tuple[str, str, str]]]:
    if clms is None or clms.empty:
        raise ClaimsPayeeMseqAlignError("quikclms is empty")
    for col in ("MPOLICY", "MPHASE", "MSEQ"):
        if col not in clms.columns:
            raise ClaimsPayeeMseqAlignError(f"quikclms missing column {col}")

    by_key: dict[tuple[str, str], list[str]] = {}
    triples: set[tuple[str, str, str]] = set()
    for _, row in clms.iterrows():
        pol = _strip(row.get("MPOLICY"))
        phase = _strip(row.get("MPHASE")) or "1"
        if not pol:
            raise ClaimsPayeeMseqAlignError("quikclms has blank MPOLICY")
        mseq = _strip(row.get("MSEQ")) or "0"
        by_key.setdefault((pol, phase), []).append(mseq)
        triples.add((pol, phase, mseq))

    # De-dupe seq lists while preserving discovery order.
    by_key = {k: list(dict.fromkeys(v)) for k, v in by_key.items()}
    return by_key, triples


def _resolve_target_mseq(
    pol: str,
    phase: str,
    current: str,
    by_key: dict[tuple[str, str], list[str]],
    triples: set[tuple[str, str, str]],
) -> str:
    key = (pol, phase)
    if key not in by_key:
        raise ClaimsPayeeMseqAlignError(
            f"payee has no matching claim header: {pol} phase={phase}"
        )
    if (pol, phase, current) in triples:
        return current

    seqs = by_key[key]
    if len(seqs) == 1:
        return seqs[0]
    if "0" in seqs:
        # Orphan payee under a key that includes header MSEQ=0 → join to header 0.
        return "0"
    raise ClaimsPayeeMseqAlignError(
        f"orphan payee MSEQ={current} for {pol} phase={phase} header_mseqs={seqs}"
    )


def align_clmp_mseq_to_claim_header(
    clms: pd.DataFrame,
    clmp: pd.DataFrame,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Align payee MSEQ to a resolvable claim-header MSEQ.

    Idempotent when already joined. Preserves multi-sequence claim payees that
    already match a header triple.
    """
    if clmp is None or clmp.empty:
        return clmp.copy() if clmp is not None else pd.DataFrame(), {
            "ok": True,
            "rows": 0,
            "changed": 0,
            "already_aligned": 0,
        }
    for col in ("MPOLICY", "MPHASE", "MSEQ"):
        if col not in clmp.columns:
            raise ClaimsPayeeMseqAlignError(f"quikclmp missing column {col}")

    by_key, triples = _header_indexes(clms)
    out = clmp.copy()
    changed = 0
    already = 0
    for idx, row in out.iterrows():
        pol = _strip(row.get("MPOLICY"))
        phase = _strip(row.get("MPHASE")) or "1"
        if not pol:
            raise ClaimsPayeeMseqAlignError("quikclmp has blank MPOLICY")
        current = _strip(row.get("MSEQ")) or "0"
        target = _resolve_target_mseq(pol, phase, current, by_key, triples)
        if current == target:
            already += 1
        else:
            out.at[idx, "MSEQ"] = target
            changed += 1

    stats = {
        "ok": True,
        "rows": int(len(out)),
        "changed": int(changed),
        "already_aligned": int(already),
        "header_keys": int(len(by_key)),
        "header_triples": int(len(triples)),
    }
    return out, stats


def validate_payee_mseq_join(
    clms: pd.DataFrame,
    clmp: pd.DataFrame,
    *,
    require_golden: bool = True,
) -> dict[str, Any]:
    """Validate every payee triple matches a claim header; optional golden check."""
    fails: list[str] = []
    try:
        _by_key, triples = _header_indexes(clms)
    except ClaimsPayeeMseqAlignError as exc:
        return {"ok": False, "fails": [str(exc)], "mismatch_n": -1}

    mismatch = 0
    if clmp is not None and not clmp.empty:
        for _, row in clmp.iterrows():
            pol = _strip(row.get("MPOLICY"))
            phase = _strip(row.get("MPHASE")) or "1"
            mseq = _strip(row.get("MSEQ")) or "0"
            if (pol, phase, mseq) not in triples:
                mismatch += 1

    if mismatch:
        fails.append(f"mseq_mismatch_rows={mismatch}")

    golden = {
        "present": False,
        "payee_n": 0,
        "mseqs": [],
        "ok": True,
    }
    pols = set(_strip(v) for v in clms.get("MPOLICY", pd.Series(dtype=str)).tolist())
    if GOLDEN_POLICY in pols:
        golden["present"] = True
        g = clmp[clmp["MPOLICY"].map(_strip) == GOLDEN_POLICY] if clmp is not None else pd.DataFrame()
        golden["payee_n"] = int(len(g))
        golden["mseqs"] = sorted({_strip(v) or "0" for v in g.get("MSEQ", pd.Series(dtype=str)).tolist()})
        hdr = clms[clms["MPOLICY"].map(_strip) == GOLDEN_POLICY].iloc[0]
        hdr_mseq = _strip(hdr.get("MSEQ")) or "0"
        if golden["payee_n"] != GOLDEN_PAYEE_COUNT:
            golden["ok"] = False
            fails.append(f"golden_payee_count={golden['payee_n']} expected={GOLDEN_PAYEE_COUNT}")
        if golden["mseqs"] != [hdr_mseq]:
            golden["ok"] = False
            fails.append(f"golden_mseqs={golden['mseqs']} header={hdr_mseq}")
    elif require_golden:
        fails.append(f"golden_missing:{GOLDEN_POLICY}")

    return {
        "ok": len(fails) == 0,
        "fails": fails,
        "mismatch_n": mismatch,
        "golden": golden,
        "clms_rows": int(len(clms)) if clms is not None else 0,
        "clmp_rows": int(len(clmp)) if clmp is not None else 0,
    }


def align_claims_csv_dir(
    output_dir: str | Path,
    *,
    test_validation_dir: str | Path | None = None,
    require_golden: bool = False,
) -> dict[str, Any]:
    """Align Output quikclmp.csv in place; optionally sync Test_Validation copies."""
    out = Path(output_dir)
    clms_path = out / "quikclms.csv"
    clmp_path = out / "quikclmp.csv"
    if not clms_path.is_file() or not clmp_path.is_file():
        raise ClaimsPayeeMseqAlignError(f"missing claims CSV under {out}")

    clms = pd.read_csv(clms_path, dtype=str).fillna("")
    clmp = pd.read_csv(clmp_path, dtype=str).fillna("")
    aligned, stats = align_clmp_mseq_to_claim_header(clms, clmp)
    gate = validate_payee_mseq_join(clms, aligned, require_golden=require_golden)
    if not gate["ok"]:
        raise ClaimsPayeeMseqAlignError("; ".join(gate["fails"]))

    tmp = clmp_path.with_suffix(".csv.mseq_align_tmp")
    aligned.to_csv(tmp, index=False, encoding="utf-8")
    tmp.replace(clmp_path)

    tv_copied = False
    if test_validation_dir is not None:
        tv = Path(test_validation_dir)
        tv.mkdir(parents=True, exist_ok=True)
        import shutil

        shutil.copy2(clms_path, tv / "quikclms.csv")
        shutil.copy2(clmp_path, tv / "quikclmp.csv")
        tv_copied = True

    return {
        "ok": True,
        "align": stats,
        "gate": gate,
        "clms_path": str(clms_path),
        "clmp_path": str(clmp_path),
        "test_validation_copied": tv_copied,
    }
