"""
Full HyperScaff automation guide. Heavier than `hyperscaff_start_here()` —
use when the start-here payload doesn't have enough context to pick a method.
"""
from __future__ import annotations

from mcp.server.fastmcp import Context
from mcp.types import ToolAnnotations

from rhinomcp import mcp
from rhinomcp.tools._hyperscaff_bridge import invoke_result_json


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
def hyperscaff_guide(ctx: Context) -> str:
    """
    Return the complete HyperScaff automation guide payload.

    The `result` object contains:
      - plugin_access   How host code reaches HyperScaffPlugin.Instance
      - usage_hints     Cross-cutting rules and orientation guidance
      - services        One entry per Automation service (BayAutomation,
                        LegAutomation, AssemblyRulesAutomation,
                        PartAssistantAutomation) with:
                          * purpose
                          * discovery_calls
                          * operation_calls
                          * usage_hints
    """
    return invoke_result_json("guide")
