"""Focused tests for QUIKConvert tagline selection / rotation helpers."""
from __future__ import annotations

from qla_core.quikconvert_tagline import (
    APP_PRIMARY_TAGLINE,
    QUIKCONVERT_TAGLINES,
    TAGLINE_ROTATION_INTERVAL_MS,
    pick_initial_tagline,
    pick_next_tagline,
)


def test_tagline_collection_has_twenty_messages():
    assert len(QUIKCONVERT_TAGLINES) == 20
    assert QUIKCONVERT_TAGLINES[0] == APP_PRIMARY_TAGLINE


def test_rotation_interval_is_eight_seconds():
    assert TAGLINE_ROTATION_INTERVAL_MS == 8000


def test_pick_initial_tagline_from_pool():
    for _ in range(40):
        assert pick_initial_tagline() in QUIKCONVERT_TAGLINES


def test_pick_next_does_not_immediately_repeat():
    current = QUIKCONVERT_TAGLINES[0]
    for _ in range(100):
        nxt = pick_next_tagline(current)
        assert nxt in QUIKCONVERT_TAGLINES
        assert nxt != current
        current = nxt


def test_pick_next_single_item_pool():
    assert pick_next_tagline("only", ["only"]) == "only"
