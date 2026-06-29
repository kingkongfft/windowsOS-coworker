from __future__ import annotations

import pytest

from core.risk import Risk, get_risk, risk


def test_risk_enum_values() -> None:
    assert Risk.LOW.value == "low"
    assert Risk.MEDIUM.value == "medium"
    assert Risk.HIGH.value == "high"


def test_risk_decorator_attaches_level() -> None:
    @risk(Risk.LOW)
    def my_tool() -> None:
        pass

    assert get_risk(my_tool) == Risk.LOW


def test_risk_decorator_high() -> None:
    @risk(Risk.HIGH)
    def dangerous_tool() -> None:
        pass

    assert get_risk(dangerous_tool) == Risk.HIGH


def test_get_risk_defaults_to_high_when_undecorated() -> None:
    def undecorated() -> None:
        pass

    assert get_risk(undecorated) == Risk.HIGH


def test_risk_decorator_preserves_function_name() -> None:
    @risk(Risk.MEDIUM)
    def my_function() -> None:
        """My docstring."""

    assert my_function.__name__ == "my_function"
    assert my_function.__doc__ == "My docstring."


def test_risk_decorator_preserves_behaviour() -> None:
    @risk(Risk.LOW)
    def add(a: int, b: int) -> int:
        return a + b

    assert add(2, 3) == 5
