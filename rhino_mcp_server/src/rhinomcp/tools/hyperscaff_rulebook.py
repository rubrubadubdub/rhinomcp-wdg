"""
HyperScaff rulebook lookup — the gate for any build/place/replace/leg-generation.

Call before invoking any service operation. The rulebook for the requested
(system_code, target_service, scaffold_config) tuple tells you which profiles,
configs, landings, and roles are valid, plus the call sequence HyperScaff
expects for that combination.
"""
from __future__ import annotations

from typing import Optional

from mcp.server.fastmcp import Context
from mcp.types import ToolAnnotations

from rhinomcp import mcp
from rhinomcp.tools._hyperscaff_bridge import invoke_result_json


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
def hyperscaff_rulebook(
    ctx: Context,
    system_code: str = "LAR",
    target_service: str = "bay_builder",
    intended_operation: Optional[str] = None,
    bay_profile_id: Optional[str] = None,
    leg_config_id: Optional[str] = None,
    leg_landing_id: Optional[str] = None,
    scaffold_config: Optional[str] = None,
) -> str:
    """
    Get the AssemblyRulebook for a specific service+system+scaffold combo.

    Parameters
    ----------
    system_code : str
        Scaffold system code (e.g. "LAR" for Layher Allround). Defaults to "LAR".
    target_service : str
        One of "bay_builder", "leg_builder", "block_assistant" (PartAssistant).
        Defaults to "bay_builder".
    intended_operation : str, optional
        Hint about what the caller wants to do, e.g. "place", "replace", "fill_down".
    bay_profile_id : str, optional
        Bay profile to resolve rules against (omit to use the policy default).
    leg_config_id : str, optional
        Leg configuration (e.g. "deck_2m_handrail").
    leg_landing_id : str, optional
        Leg landing strategy (e.g. "default").
    scaffold_config : str, optional
        Scaffold intent: "straight_run", "full_perimeter", "birdcage", etc.
        Required for perimeter/birdcage work; informs which rules and workflow
        steps apply.

    Returns
    -------
    JSON envelope with `result` containing the AssemblyRulebook:
      - policy_name, policy_hash
      - resolved_* and available_* identifiers
      - required_call_sequence, instructions
      - general_requirements, bay_requirements, leg_requirements, block_requirements,
        scaffold_config_requirements
      - scaffold_generation_workflow
    """
    params = {
        "system_code": system_code,
        "target_service": target_service,
    }
    if intended_operation is not None:
        params["intended_operation"] = intended_operation
    if bay_profile_id is not None:
        params["bay_profile_id"] = bay_profile_id
    if leg_config_id is not None:
        params["leg_config_id"] = leg_config_id
    if leg_landing_id is not None:
        params["leg_landing_id"] = leg_landing_id
    if scaffold_config is not None:
        params["scaffold_config"] = scaffold_config
    return invoke_result_json("rules.rulebook", params)
