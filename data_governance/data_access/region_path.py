"""Validate QLAdmin data-region paths for governance runs."""

from __future__ import annotations

import os


class DataRegionPathError(Exception):
    """Raised when a data-region path cannot be used for governance."""


def validate_data_region_path(path: str | None, *, require_explicit: bool = False) -> str:
    """Validate and normalize a QLAdmin data-region path.

    Checks:
    - path is provided (when require_explicit)
    - path exists
    - path is a directory
    - process can list/read the directory
    """
    if path is None or not str(path).strip():
        if require_explicit:
            raise DataRegionPathError(
                "A data-region input path is required. "
                "Provide --input with the folder that contains the QLAdmin DBF files."
            )
        raise DataRegionPathError("Data-region path is blank.")

    normalized = os.path.normpath(str(path).strip())

    if not os.path.exists(normalized):
        raise DataRegionPathError(
            f"Data-region path does not exist: {normalized}"
        )
    if not os.path.isdir(normalized):
        raise DataRegionPathError(
            f"Data-region path is not a folder: {normalized}"
        )

    # Read permission / accessibility
    if not os.access(normalized, os.R_OK):
        raise DataRegionPathError(
            f"No read permission for data-region path: {normalized}"
        )
    try:
        os.listdir(normalized)
    except PermissionError as exc:
        raise DataRegionPathError(
            f"No read permission for data-region path: {normalized}"
        ) from exc
    except OSError as exc:
        raise DataRegionPathError(
            f"Cannot read data-region path '{normalized}': {exc}"
        ) from exc

    return normalized


def validate_output_base_path(path: str | None) -> str:
    """Normalize the user-selected output base folder (created later per run)."""
    if path is None or not str(path).strip():
        raise DataRegionPathError(
            "An output path is required. "
            "Provide --output with a folder for governance reports "
            "(outside the source data region unless you intentionally choose that folder)."
        )
    return os.path.normpath(str(path).strip())
