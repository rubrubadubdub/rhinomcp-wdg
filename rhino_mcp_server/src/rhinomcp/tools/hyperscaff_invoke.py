"""
Generic HyperScaff bridge tool — calls any HS_McpInvoke method with a free-form
params dict.

This is the escape hatch when there is no typed wrapper for the method you need.
Prefer the typed tools (`hyperscaff_bay_catalog`, `hyperscaff_leg_plan`, etc.)
when one exists — they validate the param shape and return cleaner errors.

Call `hyperscaff_list_methods()` first to discover what method names are
available, and `hyperscaff_start_here()` to understand the recommended call order.
"""
from __future__ import annotations

from typing import Any, Dict, Optional

from mcp.server.fastmcp import Context
from mcp.types import ToolAnnotations

from rhinomcp import mcp
from rhinomcp.tools._hyperscaff_bridge import invoke_result_json


@mcp.tool(annotations=ToolAnnotations(destructiveHint=True, openWorldHint=True))
def hyperscaff_invoke(
    ctx: Context,
    method: str,
    params: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Invoke any HyperScaff bridge method via HS_McpInvoke.

    Parameters
    ----------
    method : str
        The bridge method name (e.g. "bay.catalog", "leg.plan", "docs.get").
        Call `hyperscaff_list_methods()` to see the full catalog.
    params : dict, optional
        Method-specific parameters. Shape varies per method — read
        `hyperscaff_start_here()` and the dispatcher source for guidance.

    Returns
    -------
    JSON string of the full bridge envelope:
        { "ok": true,  "method": "...", "result": {...} }
        { "ok": false, "method": "...", "error": "..." }

    Safety: some methods (leg.build, leg.auto_place_*, part.place_at_point,
    part.replace_selected, part.cull_duplicates) MODIFY THE ACTIVE DOCUMENT.
    Always call the corresponding plan/catalog method first, present the plan
    to the user, and only invoke the destructive method after they confirm.
    """
    return invoke_result_json(method, params)
