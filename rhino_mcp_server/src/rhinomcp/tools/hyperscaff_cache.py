"""
HyperScaff maintenance tools.
"""
from __future__ import annotations

from typing import Optional

from mcp.server.fastmcp import Context
from mcp.types import ToolAnnotations

from rhinomcp import mcp
from rhinomcp.tools._hyperscaff_bridge import invoke_result_json


@mcp.tool(annotations=ToolAnnotations(openWorldHint=True))
def hyperscaff_cache_clear(
    ctx: Context,
    targets: Optional[list[str]] = None,
    target: Optional[str] = None,
) -> str:
    """
    Clear HyperScaff automation caches after policy/config changes.

    targets accepts any combination of: all, rules, bay, leg.
    target is a single-target convenience alias.
    """
    request = {}
    if targets:
        request["targets"] = targets
    if target:
        request["target"] = target
    return invoke_result_json("cache.clear", request)
