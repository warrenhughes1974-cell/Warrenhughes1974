"""Load approved policy/client/relationship codes for Policy Data Governance."""

from __future__ import annotations

import csv
import os
from functools import lru_cache


_CONFIG_PATH = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "policy_code_authorities.csv")
)


@lru_cache(maxsize=1)
def load_policy_code_authorities() -> dict[str, frozenset[str]]:
    path = _CONFIG_PATH
    out: dict[str, set[str]] = {}
    if not os.path.isfile(path):
        return {}
    with open(path, newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            auth = (row.get("AUTHORITY") or "").strip().upper()
            code = (row.get("CODE") or "").strip()
            if not auth or code == "":
                continue
            out.setdefault(auth, set()).add(code)
            # Also store uppercase form for character codes
            out[auth].add(code.upper())
    return {k: frozenset(v) for k, v in out.items()}


def codes_for(authority: str) -> frozenset[str]:
    return load_policy_code_authorities().get(authority.upper(), frozenset())


def is_approved(authority: str, value: str, *, casefold: bool = False) -> bool:
    codes = codes_for(authority)
    if not codes:
        return False
    if casefold:
        return value.casefold() in {c.casefold() for c in codes}
    return value in codes or value.upper() in codes


def reset_policy_code_authorities_for_tests() -> None:
    load_policy_code_authorities.cache_clear()
