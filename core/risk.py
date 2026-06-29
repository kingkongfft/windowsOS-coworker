from __future__ import annotations

import functools
from enum import Enum
from typing import Any, Callable, TypeVar

F = TypeVar("F", bound=Callable[..., Any])


class Risk(str, Enum):
    """Risk classification for tool/skill functions.

    Levels:
        LOW    — read-only, no side effects, executes immediately.
        MEDIUM — has side effects but is reversible; requires one-click confirmation.
        HIGH   — destructive or irreversible; requires explicit typed/clicked approval
                 and writes to the audit log before and after execution.
    """

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


# Attribute name used to store risk metadata on decorated functions.
_RISK_ATTR = "__risk_level__"


def risk(level: Risk) -> Callable[[F], F]:
    """Decorator that annotates a tool function with a risk level.

    The orchestrator reads ``fn.__risk_level__`` at runtime to decide whether
    to invoke the approval gate before calling the tool.

    This decorator is order-safe: when applied *outside* ``@function_tool``
    (i.e. ``@risk`` is written first in source), it detects that the wrapped
    object is already a ``FunctionTool`` and stamps the attribute directly on
    it without re-wrapping, preserving the SDK-recognised type.

    Usage::

        @risk(Risk.HIGH)
        @function_tool
        def kill_process(pid: int) -> dict[str, str]:
            ...

    Args:
        level: The :class:`Risk` level to assign to the function.

    Returns:
        A decorator that attaches the risk level to the wrapped function.
    """

    def decorator(fn: F) -> F:
        # If fn is already a FunctionTool (or any non-callable object such as
        # an SDK tool wrapper), just stamp the attribute on it and return it
        # as-is so the SDK still recognises it as a valid tool.
        if not callable(fn) or type(fn).__name__ == "FunctionTool":
            setattr(fn, _RISK_ATTR, level)
            return fn

        # Plain function — wrap normally.
        @functools.wraps(fn)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            return fn(*args, **kwargs)

        setattr(wrapper, _RISK_ATTR, level)
        return wrapper  # type: ignore[return-value]

    return decorator


def get_risk(fn: Callable[..., Any]) -> Risk:
    """Return the :class:`Risk` level attached to *fn*, defaulting to HIGH.

    If the function has not been decorated with :func:`risk`, the safest
    default (HIGH) is returned so unknown tools are always gated.

    Args:
        fn: Any callable, typically a ``@function_tool``-decorated function.

    Returns:
        The :class:`Risk` level of the function.
    """
    return getattr(fn, _RISK_ATTR, Risk.HIGH)
