"""
List every method the HS_McpInvoke dispatcher routes.
"""
from __future__ import annotations

from mcp.server.fastmcp import Context
from mcp.types import ToolAnnotations

from rhinomcp import mcp
from rhinomcp.tools._hyperscaff_bridge import invoke_result_json


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
def hyperscaff_list_methods(ctx: Context) -> str:
    """
    Return the catalog of HyperScaff bridge methods.

    Each entry is a method name like "bay.catalog", "leg.plan", or "docs.get"
    that can be passed to `hyperscaff_invoke(method=..., params=...)`. Use
    `hyperscaff_start_here()` for the recommended call order, and the typed
    wrappers (hyperscaff_bay_catalog, hyperscaff_leg_catalog, ...) when
    available — they document the param shape inline.
    """
    return invoke_result_json("list_methods")
