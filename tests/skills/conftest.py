"""conftest.py — shared helpers for skill unit tests."""

from __future__ import annotations

from agents.tool import FunctionTool


def raw(tool: FunctionTool) -> object:
    """Extract the underlying sync callable from a ``@function_tool`` object.

    The OpenAI Agents SDK wraps decorated functions inside a ``FunctionTool``
    dataclass, making them non-callable via ``tool(...)``.  This helper reaches
    into the closure of the internal ``_invoke_tool_impl`` coroutine to retrieve
    the original Python function so unit tests can call it directly without
    needing a full ``Runner`` context.

    Args:
        tool: A ``FunctionTool`` instance produced by ``@function_tool``.

    Returns:
        The original unwrapped callable.
    """
    # The structure is:
    #   FunctionTool.on_invoke_tool  -> _FailureHandlingFunctionToolInvoker
    #     ._invoke_tool_impl         -> async def (closure)
    #       __closure__[2]           -> the original function
    return tool.on_invoke_tool._invoke_tool_impl.__closure__[2].cell_contents  # type: ignore[attr-defined]
