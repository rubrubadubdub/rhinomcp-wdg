"""
HyperScaff first-touch bootstrap. ALWAYS call this before any other HyperScaff
tool — it tells you which call order HyperScaff expects, which critical rules
apply, and where each service surface lives.
"""
from __future__ import annotations

from mcp.server.fastmcp import Context
from mcp.types import ToolAnnotations

from rhinomcp import mcp
from rhinomcp.tools._hyperscaff_bridge import invoke_result_json


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
def hyperscaff_start_here(ctx: Context) -> str:
    """
    Return HyperScaff's automation start-here payload.

    The `result` object contains:
      - plugin_access      Snippet showing how host code reaches HyperScaffPlugin.Instance
      - first_touch_call   The very first call you should make from any agent
      - why_first          One-line justification
      - required_call_order  Ordered list of calls (start_here → rulebook → catalog → plan → build)
      - critical_rules     Hard rules HyperScaff enforces (front-face orientation, GROUND-layer skip, etc.)
      - service_entrypoints  For each service (Bay, Leg, PartAssistant): rulebook call, catalog call, plan call

    Recommended workflow for any HyperScaff job:
      1. hyperscaff_start_here()         (this tool)
      2. hyperscaff_docs_digest()        (skim the documentation map)
      3. hyperscaff_rulebook(...)        (the rulebook for your target service + scaffold config)
      4. hyperscaff_<service>_catalog(...) (discover available profiles/configs/components)
      5. plan call (hyperscaff_bay_plan_straight_run, hyperscaff_leg_plan, etc.)
      6. build call (only after presenting the plan to the user)
    """
    return invoke_result_json("start_here")
