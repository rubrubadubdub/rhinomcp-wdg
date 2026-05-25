"""
HyperScaff bay automation: catalog discovery, planning, and document-changing
BayAutomation operations exposed through HS_McpInvoke.
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
    origin: Dict[str, float],
    system_code: str = "LAR",
    profile_id: Optional[str] = None,
    front_direction: Optional[Dict[str, float]] = None,
) -> str:
    """
    Place a single unbuilt bay through HyperScaff BayAutomation. CHANGES THE DOCUMENT.

    Use this for lightweight bay placeholders. Use hyperscaff_bay_build when
    the policy-driven component assembly should be populated immediately.

    origin and front_direction are {x, y, z} objects in the same coordinate
    convention as the active model.
    """
    request: Dict[str, Any] = {
        "system_code": system_code,
        "length_mm": length_mm,
        "width_mm": width_mm,
        "height_mm": height_mm,
        "origin": origin,
    }
    if profile_id:
        request["profile_id"] = profile_id
    if front_direction:
        request["front_direction"] = front_direction
    return invoke_result_json("bay.place", request)


@mcp.tool(annotations=ToolAnnotations(destructiveHint=True, openWorldHint=True))
def hyperscaff_bay_build(ctx: Context, request: Dict[str, Any]) -> str:
    """
    Place and build one policy-driven bay. CHANGES THE DOCUMENT.

    request is BayBuildRequest:
      system_code, profile_id, origin {x,y,z}, length_mm, width_mm, height_mm,
      front_direction {x,y,z}, direction_source, selected_handrail_type,
      handrail_force_off_faces, handrail_force_on_faces, active_variants,
      skip_if_coincident.
    """
    return invoke_result_json("bay.build", request)


@mcp.tool(annotations=ToolAnnotations(destructiveHint=True, openWorldHint=True))
def hyperscaff_bay_place_relative(ctx: Context, request: Dict[str, Any]) -> str:
    """
    Place and build bays adjacent to existing source bays. CHANGES THE DOCUMENT.

    request is BayPlaceRelativeRequest:
      source_bay_ids, relative_face (front/back/left/right/up/down),
      use_requested_spec, system_code, profile_id, length_mm, width_mm,
      height_mm, selected_handrail_type, handrail_force_off_faces,
      handrail_force_on_faces, active_variants, skip_if_coincident.
    """
    return invoke_result_json("bay.place_relative", request)


@mcp.tool(annotations=ToolAnnotations(destructiveHint=True, openWorldHint=True))
def hyperscaff_bay_place_at_selected(ctx: Context, request: Dict[str, Any]) -> str:
    """
    Replace selected/provided bay placeholders with a requested bay spec.
    CHANGES THE DOCUMENT.
    """
    return invoke_result_json("bay.place_at_selected", request)


@mcp.tool(annotations=ToolAnnotations(destructiveHint=True, openWorldHint=True))
def hyperscaff_bay_replace(ctx: Context, request: Dict[str, Any]) -> str:
    """
    Replace selected/provided built bays with a requested bay spec.
    CHANGES THE DOCUMENT.
    """
    return invoke_result_json("bay.replace", request)


@mcp.tool(annotations=ToolAnnotations(destructiveHint=True, openWorldHint=True))
def hyperscaff_bay_regenerate(ctx: Context, bay_ids: Optional[list[str]] = None) -> str:
    """
    Rebuild selected/provided bays from current policy and metadata.
    CHANGES THE DOCUMENT.
    """
    return invoke_result_json("bay.regenerate", {"bay_ids": bay_ids or []})


@mcp.tool(annotations=ToolAnnotations(destructiveHint=True, openWorldHint=True))
def hyperscaff_bay_fill_down(ctx: Context, request: Dict[str, Any]) -> str:
    """
    Fill downward from selected/provided grounded bay decks. CHANGES THE DOCUMENT.

    request is BayFillDownRequest: bay_ids and target_step_height_mm.
    Run leg planning/auto-placement after this for final support validation.
    """
    return invoke_result_json("bay.fill_down", request)


@mcp.tool(annotations=ToolAnnotations(destructiveHint=True, openWorldHint=True))
def hyperscaff_bay_set_front_direction(ctx: Context, request: Dict[str, Any]) -> str:
    """
    Set bay front direction for selected/provided bays. CHANGES BAY METADATA.

    request is BayDirectionRequest: bay_ids and front_direction {x,y,z}.
    Front must point toward the structure being scaffolded.
    """
    return invoke_result_json("bay.set_front_direction", request)


@mcp.tool(annotations=ToolAnnotations(destructiveHint=True, openWorldHint=True))
def hyperscaff_bay_flip_front(ctx: Context, bay_ids: Optional[list[str]] = None) -> str:
    """
    Flip front direction for selected/provided bays. CHANGES BAY METADATA.
    """
    return invoke_result_json("bay.flip_front", {"bay_ids": bay_ids or []})


@mcp.tool(annotations=ToolAnnotations(destructiveHint=True, openWorldHint=True))
def hyperscaff_bay_set_front_from_active_view(ctx: Context, request: Dict[str, Any]) -> str:
    """
    Resolve bay front direction from the active or named Rhino view.
    CHANGES BAY METADATA.
    """
    return invoke_result_json("bay.set_front_from_active_view", request)


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, openWorldHint=True))
def hyperscaff_bay_refresh_selection(ctx: Context, bay_ids: Optional[list[str]] = None) -> str:
    """
    Return/refresh HyperScaff bay selection summary for selected/provided bays.
    """
    return invoke_result_json("bay.refresh_selection", {"bay_ids": bay_ids or []})


@mcp.tool(annotations=ToolAnnotations(openWorldHint=True))
def hyperscaff_bay_find_duplicates(ctx: Context) -> str:
    """
    Find duplicate/coincident HyperScaff bay groups and select them in Rhino.
    CHANGES SELECTION STATE.
    """
    return invoke_result_json("bay.find_duplicates")


@mcp.tool(annotations=ToolAnnotations(destructiveHint=True, openWorldHint=True))
def hyperscaff_bay_resize_selected(ctx: Context, request: Dict[str, Any]) -> str:
    """
    Resize selected/provided bays along length, width, or height.
    CHANGES THE DOCUMENT.

    request is BayResizeRequest: bay_ids, system_code, axis, increase.
    """
    return invoke_result_json("bay.resize_selected", request)
