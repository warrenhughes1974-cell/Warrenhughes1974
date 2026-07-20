"""
QUIKConvert branding taglines and rotation helpers (UI presentation only).

No conversion / validation / DBF logic lives here.
"""
from __future__ import annotations

import random
from typing import Sequence

# Primary product tagline (also appears in QUIKCONVERT_TAGLINES[0]).
APP_PRIMARY_TAGLINE = "Convert with confidence."

QUIKCONVERT_TAGLINES: tuple[str, ...] = (
    "Convert with confidence.",
    "QUIK in name. Thorough by design.",
    "Turning QUIK tables into quality data.",
    "Built on QUIK. Powered by validation.",
    "Trust, but validate.",
    "Every policy matters.",
    "Because “close enough” isn’t.",
    "Making bad data uncomfortable.",
    "Friends don’t let friends edit DBFs by hand.",
    "Backups first. Regrets never.",
    "From QUIKMSTR to success.",
    "One QUIK table at a time.",
    "Precision in every policy.",
    "Converting data. Building confidence.",
    "It’s not magic. It’s validation.",
    "Making legacy data behave.",
    "Good conversions are invisible.",
    "Measure twice. Convert once.",
    "Every record tells a story.",
    "Built for accuracy. Designed for trust.",
)

TAGLINE_ROTATION_INTERVAL_MS = 8000

# Optional long-running status copy (use only when accurate for the process).
QUIKCONVERT_STATUS_MESSAGES: tuple[str, ...] = (
    "Backing up the table...",
    "Validating policy numbers...",
    "Looking for duplicate records...",
    "Checking QUIKMSTR...",
    "Consulting QUIKPLAN...",
    "Verifying field definitions...",
    "Preparing the conversion...",
    "Comparing record counts...",
    "Reviewing validation results...",
    "Making sure every record arrives safely...",
)


def pick_initial_tagline(taglines: Sequence[str] | None = None) -> str:
    """Return a random tagline for application start."""
    pool = list(taglines or QUIKCONVERT_TAGLINES)
    if not pool:
        return APP_PRIMARY_TAGLINE
    return random.choice(pool)


def pick_next_tagline(current: str, taglines: Sequence[str] | None = None) -> str:
    """Return a random tagline that is not the same as ``current`` when possible."""
    pool = list(taglines or QUIKCONVERT_TAGLINES)
    if not pool:
        return APP_PRIMARY_TAGLINE
    if len(pool) == 1:
        return pool[0]
    choices = [t for t in pool if t != current]
    if not choices:
        return pool[0]
    return random.choice(choices)


def prefer_reduced_motion() -> bool:
    """Best-effort OS reduced-motion check (Windows / optional env override)."""
    import os

    env = os.environ.get("QUIKCONVERT_REDUCED_MOTION", "").strip().lower()
    if env in ("1", "true", "yes", "on"):
        return True
    if env in ("0", "false", "no", "off"):
        return False
    try:
        import ctypes

        SPI_GETCLIENTAREAANIMATION = 0x1042
        enabled = ctypes.c_int()
        ok = ctypes.windll.user32.SystemParametersInfoW(  # type: ignore[attr-defined]
            SPI_GETCLIENTAREAANIMATION, 0, ctypes.byref(enabled), 0
        )
        if ok and int(enabled.value) == 0:
            return True
    except Exception:
        pass
    return False


class TaglineRotator:
    """
    Tkinter-friendly rotating tagline controller.

    - One timer only (``after`` id)
    - Pause when window inactive; resume on focus
    - Subtle fg fade unless reduced-motion
    - Fixed-height label (caller should set wraplength / height)
    """

    def __init__(
        self,
        root,
        label,
        *,
        taglines: Sequence[str] | None = None,
        interval_ms: int = TAGLINE_ROTATION_INTERVAL_MS,
        fg_active: str = "#FFFFFF",
        fg_muted: str = "#FECACA",
        bg: str = "#B91C1C",
    ):
        self.root = root
        self.label = label
        self.taglines = tuple(taglines or QUIKCONVERT_TAGLINES)
        self.interval_ms = int(interval_ms)
        self.fg_active = fg_active
        self.fg_muted = fg_muted
        self.bg = bg
        self._after_id = None
        self._paused = False
        self._closed = False
        self._fading = False
        self.current = pick_initial_tagline(self.taglines)
        self.label.configure(text=self.current, fg=self.fg_active, bg=self.bg)
        self._bind_lifecycle()
        self._schedule()

    def _bind_lifecycle(self) -> None:
        try:
            self.root.bind("<FocusIn>", self._on_focus_in, add="+")
            self.root.bind("<FocusOut>", self._on_focus_out, add="+")
            self.root.bind("<Destroy>", self._on_destroy, add="+")
        except Exception:
            pass

    def _on_focus_in(self, _event=None) -> None:
        if self._closed:
            return
        self._paused = False
        self._schedule()

    def _on_focus_out(self, _event=None) -> None:
        # Only pause when the whole app loses focus (not child widgets).
        try:
            if self.root.focus_displayof() is not None:
                return
        except Exception:
            pass
        self._paused = True
        self._cancel()

    def _on_destroy(self, _event=None) -> None:
        self.close()

    def _cancel(self) -> None:
        if self._after_id is not None:
            try:
                self.root.after_cancel(self._after_id)
            except Exception:
                pass
            self._after_id = None

    def _schedule(self) -> None:
        if self._closed or self._paused:
            return
        self._cancel()
        self._after_id = self.root.after(self.interval_ms, self._tick)

    def _tick(self) -> None:
        self._after_id = None
        if self._closed or self._paused:
            return
        nxt = pick_next_tagline(self.current, self.taglines)
        if prefer_reduced_motion():
            self.current = nxt
            self.label.configure(text=self.current, fg=self.fg_active)
            self._schedule()
            return
        self._fade_to(nxt)

    def _fade_to(self, new_text: str) -> None:
        if self._fading:
            return
        self._fading = True
        steps = (
            self.fg_active,
            self.fg_muted,
            self.bg,
            self.fg_muted,
            self.fg_active,
        )

        def step(i: int = 0) -> None:
            if self._closed:
                self._fading = False
                return
            if i == 2:
                self.current = new_text
                self.label.configure(text=self.current)
            if i < len(steps):
                self.label.configure(fg=steps[i])
                self.root.after(70, lambda: step(i + 1))
                return
            self.label.configure(fg=self.fg_active)
            self._fading = False
            self._schedule()

        step(0)

    def close(self) -> None:
        self._closed = True
        self._paused = True
        self._cancel()
