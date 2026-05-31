"""Shared LifePRO source path resolution for claims pipeline engines."""

import json
import os

_CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "claims_source_paths.json")


def _repo_root():
    return os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))


def _load_candidates(key, fallback):
    if os.path.isfile(_CONFIG_PATH):
        try:
            with open(_CONFIG_PATH, encoding="utf-8") as fh:
                cfg = json.load(fh)
            values = cfg.get(key, [])
            if values:
                return values
        except (OSError, json.JSONDecodeError):
            pass
    return fallback


def resolve_prelsa_path(explicit=None):
    if explicit and os.path.isfile(explicit):
        return os.path.normpath(explicit)
    env_path = os.environ.get("QLA_CLAIMS_PRELSA_PATH", "").strip()
    if env_path and os.path.isfile(env_path):
        return os.path.normpath(env_path)
    root = _repo_root()
    candidates = [
        os.path.join(root, rel.replace("/", os.sep))
        for rel in _load_candidates(
            "prelsa_candidates",
            [
                "QLA_Migration/Source/RelationshipNameAddress_Extract.csv",
                "docs/claims_conversion_reference/RelationshipNameAddress_Extract.csv",
            ],
        )
    ]
    for path in candidates:
        if os.path.isfile(path):
            return os.path.normpath(path)
    return os.path.normpath(candidates[-1]) if candidates else ""


def resolve_pactg_path(explicit=None):
    if explicit and os.path.isfile(explicit):
        return os.path.normpath(explicit)
    env_path = os.environ.get("QLA_CLAIMS_PACTG_PATH", "").strip()
    if env_path and os.path.isfile(env_path):
        return os.path.normpath(env_path)
    root = _repo_root()
    candidates = [
        os.path.join(root, rel.replace("/", os.sep))
        for rel in _load_candidates(
            "pactg_candidates",
            [
                "QLA_Migration/Source/PACTG_Accounting_Extract20260427.csv",
                "docs/claims_conversion_reference/PACTG_Accounting_Extract20260427.csv",
            ],
        )
    ]
    for path in candidates:
        if os.path.isfile(path):
            return os.path.normpath(path)
    return os.path.normpath(candidates[-1]) if candidates else ""
