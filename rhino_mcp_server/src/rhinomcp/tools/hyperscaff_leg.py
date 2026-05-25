"""
HyperScaff leg automation: catalog, plan, build, batch, auto-place.

Pattern: catalog → plan → build for single leg; catalog → auto-place for
batched bay-leg generation. All build/auto-place methods MODIFY THE DOCUMENT
and run inside an undo record by default.
"""
from __future__ import annotations

from typing import Any, Dict, Optional

from mcp.server.fastmcp import Context
from mcp.types import ToolAnnotations

from rhinomcp import mcp
from rhinomcp.tools._hyperscaff_bridge import invoke_result_json


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
def hyperscaff_leg_catalog(ctx: Context, system_code: str = "LAR") -> str:
    """
    Return available leg configurations, landings, standard sizing, jack rules,
    and resolved role components for a scaffold system.

    Use this to discover valid (config_id, landing_id) pairs before planning.
    """
    return invoke_result_json("leg.catalog", {"system_code": system_code})


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
def hyperscaff_leg_plan(ctx: Context, request: Dict[str, Any]) -> str:
    """
    Plan a single leg WITHOUT modifying the document.

    request : dict — LegBuildRequest shape. Required: system_code, config_id,
    landing_id, and either a placement_point {x,y,z} or use_set_height + set_height_mm.
    Optional: ledger_x_axis_x / ledger_x_axis_y for non-world-aligned bays,
    override_little_endian, use_base_collar + base_collar_*.

    Returns a LegAutomationOperationResult with the resolved stack (sole, plate,
    jack, standards, top components) and any validation errors. Always present
    this to the user before calling hyperscaff_leg_build with the same request.
    """
    return invoke_result_json("leg.plan", request)


@mcp.tool(annotations=ToolAnnotations(destructiveHint=True, openWorldHint=True))
def hyperscaff_leg_build(ctx: Context, request: Dict[str, Any]) -> str:
    """
    Build a single leg. MODIFIES THE DOCUMENT.

    Same request shape as hyperscaff_leg_plan. Wraps the placement in an undo
    record (unless request.skip_undo_record is true) so a single Ctrl+Z reverts
    the whole stack.
    """
    return invoke_result_json("leg.build", request)


@mcp.tool(annotations=ToolAnnotations(destructiveHint=True, openWorldHint=True))
def hyperscaff_leg_build_batch(ctx: Context, request: Dict[str, Any]) -> str:
    """
    Build multiple legs from a list of seed points. MODIFIES THE DOCUMENT.

    request : dict — LegBatchRequest shape. Required: system_code, config_id,
    landing_id, seed_points (list of {x,y,z}). Set
    resolve_placement_point_automatically / resolve_ground_automatically true
    (default) to let HyperScaff snap each point onto valid geometry; set false
    when you've already computed exact placement.
    """
    return invoke_result_json("leg.build_batch", request)


@mcp.tool(annotations=ToolAnnotations(destructiveHint=True, openWorldHint=True))
def hyperscaff_leg_auto_place_selected(ctx: Context, request: Dict[str, Any]) -> str:
    """
    Auto-place legs at every support column of the currently selected bay
    objects. MODIFIES THE DOCUMENT.

    request : dict — LegAutoPlaceRequest shape. system_code, config_id,
    landing_id required. Use candidate_object_ids to constrain to a subset of
    selection; omit to take everything currently selected.

    REJECT if the returned result has unresolved_support_column_count > 0 —
    that indicates HyperScaff couldn't find geometry to land on for some legs.
    """
    return invoke_result_json("leg.auto_place_selected", request)


@mcp.tool(annotations=ToolAnnotations(destructiveHint=True, openWorldHint=True))
def hyperscaff_leg_auto_place_all(ctx: Context, request: Dict[str, Any]) -> str:
    """
    Auto-place legs at every support column of every bay in the document.
    MODIFIES THE DOCUMENT.

    Same request shape as hyperscaff_leg_auto_place_selected but ignores the
    candidate_object_ids field. Heavy operation — confirm with the user before
    invoking.
    """
    return invoke_result_json("leg.auto_place_all", request)
