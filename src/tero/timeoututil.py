"""Wall-clock deadlines for Bedrock agent calls (Unix SIGALRM)."""

from __future__ import annotations

import signal
from collections.abc import Callable
from typing import TypeVar

from tero.errors import TeroError

T = TypeVar("T")


class TurnTimeoutError(TeroError):
    def __init__(self, seconds: float) -> None:
        super().__init__(
            (
                f"Tiempo de turno agotado ({seconds:.0f}s). "
                "Bedrock no respondió a tiempo — pulsa r o sube TERO_TURN_TIMEOUT."
            ),
            code="turn_timeout",
        )
        self.seconds = seconds


def call_with_timeout(seconds: float, fn: Callable[..., T], *args, **kwargs) -> T:
    """Run ``fn`` and raise ``TurnTimeoutError`` if it exceeds ``seconds``.

    Uses SIGALRM / setitimer (main thread, Unix). ``seconds <= 0`` disables the limit.
    """
    if seconds <= 0:
        return fn(*args, **kwargs)

    def _handler(_signum, _frame) -> None:  # noqa: ANN001
        raise TurnTimeoutError(seconds)

    previous = signal.signal(signal.SIGALRM, _handler)
    # nested deadlines: preserve any outer timer remaining
    old_timer = signal.setitimer(signal.ITIMER_REAL, 0.0)
    try:
        signal.setitimer(signal.ITIMER_REAL, seconds)
        return fn(*args, **kwargs)
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0.0)
        signal.signal(signal.SIGALRM, previous)
        # restore outer timer if it had remaining time
        if old_timer[0] > 0:
            signal.setitimer(signal.ITIMER_REAL, old_timer[0], old_timer[1])
