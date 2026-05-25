"""
HyperScaff bay automation: catalog discovery and straight-run planning.

These are READ-only / planning operations. Actual placement of bays today is
driven via the HS_PlaceBay command (use `run_command` for that) or via the
Designer WPF window. The planning surface here is what an agent uses to figure
out *what* to place before invoking either flow.
"""
from __future__ import annotations

from typing import Any, Dict, Optional

from mcp.server.fastmcp import Context
from mcp.types import ToolAnnotations

from rhinomcp import mcp
from rhinomcp.tools._hyperscaff_bridge import invoke_result_json


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
def hyperscaff_bay_catalog(
    ctx: Context,
    system_code: str = "LAR",
) -> str:
    """
    List bay profiles and standard sizes available for a scaffold system.

    Parameters
    ----------
    system_code : str
        Scaffold system code (default "LAR" — Layher Allround).

    Returns
    -------
    JSON envelope. `result` contains:
      - default_profile_id, default_bay_length_mm/width_mm/height_mm
      - standard_bay_lengths_mm, standard_bay_widths_mm, standard_lift_heights_mm
      - profiles[]: per-profile required/optional roles, width options, handrail/hopup options
      - usage_hints, messages, errors
    """
    return invoke_result_json("bay.catalog", {"system_code": system_code})


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
def hyperscaff_bay_plan_straight_run(
    ctx: Context,
    request: Dict[str, Any],
) -> str:
    """
    Plan a straight-run bay sequence for a given length and height target.

    Parameters
    ----------
    request : dict
        BayStraightRunRequest shape. Keys (camelCase or snake_case both work
        via the DataMember names — use snake_case for clarity):
          system_code            (str)   default "LAR"
          profile_id             (str)
          target_run_length_mm   (float) required
          target_height_mm       (float) required
          preferred_bay_width_mm (float)
          selected_handrail_type (str)
          active_variants        (list[str])
          leg_config_id          (str)
          leg_landing_id         (str)
          require_exact_coverage (bool)
          allow_length_overrun   (bool)
          allow_height_overrun   (bool)

    Returns
    -------
    JSON envelope. `result` is a BayStraightRunPlan: ordered bay placements,
    leg requirements per support column, coverage diagnostics, and warnings.
    Present this to the user before invoking any HS_PlaceBay calls.
    """
    return invoke_result_json("bay.plan_straight_run", request)


@mcp.tool(annotations=ToolAnnotations(destructiveHint=True, openWorldHint=True))
def hyperscaff_bay_place(
    ctx: Context,
    length_mm: float,
    width_mm: float,
    height_mm: float,
    system_code: Optional[str] = None,
    profile_id: Optional[str] = None,
) -> str:
    """
    Place a single bay interactively via HS_PlaceBay. CHANGES THE DOCUMENT.

    HS_PlaceBay is normally driven via the WPF Designer or interactive command
    line, so the script-mode surface only covers the common case (length, width,
    height, optional system + profile). For richer parameter shapes use the
    Designer WPF window instead.

    The tool returns the captured Rhino command-line output; downstream callers
    should treat anything other than "Placed bay" / explicit success as failure.
    """
    from rhinomcp import get_rhino_connection, logger

    parts = [
        "_-HS_PlaceBay",
        "Length", str(length_mm),
        "Width", str(width_mm),
        "Height", str(height_mm),
    ]
    if system_code:
        parts.extend(["System", system_code])
    if profile_id:
        parts.extend(["Profile", profile_id])
    command = " ".join(parts)
    try:
        rhino = get_rhino_connection()
        result = rhino.send_command("run_command", {"command": command, "echo": False})
        return (result or {}).get("output", "") or "Done."
    except Exception as exc:
        logger.error(f"hyperscaff_bay_place: {exc}")
        return f"Command failed: {exc}"
