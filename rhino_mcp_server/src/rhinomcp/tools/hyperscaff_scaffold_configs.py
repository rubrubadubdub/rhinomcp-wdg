"""
HyperScaff scaffold-intent discovery and document fetch.

Scaffold configs are HyperScaff's named intents for a job (straight_run,
full_perimeter, birdcage, etc.). The catalog lists which configs are enabled
for a system; the document call returns the resolved JSON for one config.
"""
from __future__ import annotations

from typing import Optional

from mcp.server.fastmcp import Context
from mcp.types import ToolAnnotations

from rhinomcp import mcp
from rhinomcp.tools._hyperscaff_bridge import invoke_result_json


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
def hyperscaff_scaffold_config_catalog(
    ctx: Context,
    system_code: Optional[str] = None,
) -> str:
    """
    List scaffold-intent configs available for a system.

    Parameters
    ----------
    system_code : str, optional
        Scaffold system code (e.g. "LAR"). Omit to get the policy default.

    Returns
    -------
    JSON envelope. `result` lists configs like "straight_run", "full_perimeter",
    "birdcage" along with whether each is enabled and which profiles it allows.
    Use the chosen config as the `scaffold_config` arg to `hyperscaff_rulebook`.
    """
    params = {}
    if system_code is not None:
        params["system_code"] = system_code
    return invoke_result_json("rules.scaffold_config_catalog", params)


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
def hyperscaff_scaffold_config_document(
    ctx: Context,
    config_code: str,
    system_code: Optional[str] = None,
) -> str:
    """
    Fetch the resolved JSON document for one scaffold-intent config.

    Use this when the agent needs full structured config details — width
    options, handrail requirements, allowed leg landings, perimeter rules,
    etc. — not just the catalog row.

    Parameters
    ----------
    config_code : str
        Required. The config to read, e.g. "full_perimeter".
    system_code : str, optional
        Scaffold system code (omit for default).
    """
    params = {"config_code": config_code}
    if system_code is not None:
        params["system_code"] = system_code
    return invoke_result_json("rules.scaffold_config_document", params)
