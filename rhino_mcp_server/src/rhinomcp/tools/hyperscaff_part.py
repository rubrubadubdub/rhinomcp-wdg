"""
HyperScaff part-assistant automation: discover components, place, replace,
resize, cycle variants, and duplicate housekeeping.

Use for *loose* component work only — when scaffold assembly rules don't apply.
For scaffold-rule-driven placement, prefer the bay/leg automation surface.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from mcp.server.fastmcp import Context
from mcp.types import ToolAnnotations

from rhinomcp import mcp
from rhinomcp.tools._hyperscaff_bridge import invoke_result_json


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
def hyperscaff_part_catalog(
    ctx: Context,
    system_codes: Optional[List[str]] = None,
    search_text: Optional[str] = None,
) -> str:
    """
    List components available for one or more scaffold systems with an optional
    name/role search filter.

    Parameters
    ----------
    system_codes : list[str], optional
        Filter to specific systems (e.g. ["LAR", "RL"]). Omit for all.
    search_text : str, optional
        Case-insensitive substring match against component name, role, or
        part_code (e.g. "ledger", "transom", "LDGR").
    """
    params: Dict[str, Any] = {}
    if system_codes is not None:
        params["system_codes"] = list(system_codes)
    if search_text is not None:
        params["search_text"] = search_text
    return invoke_result_json("part.catalog", params)


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
def hyperscaff_part_usage_hints(ctx: Context) -> str:
    """Return PartAssistant's curated usage-hint list."""
    return invoke_result_json("part.usage_hints")


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
def hyperscaff_part_selected_component_id(ctx: Context) -> str:
    """
    Return the component_id of the currently selected block instance, or empty
    string if nothing eligible is selected. Errors if multiple distinct
    components are selected — use hyperscaff_part_selected_component_ids for
    that case.
    """
    return invoke_result_json("part.selected_component_id")


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
def hyperscaff_part_selected_component_ids(ctx: Context) -> str:
    """
    Return the list of distinct component_ids across the current selection.
    Empty list when nothing eligible is selected.
    """
    return invoke_result_json("part.selected_component_ids")


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
def hyperscaff_part_build_definition(
    ctx: Context,
    comp_id: str,
    enabled_optional_ids: Optional[List[str]] = None,
) -> str:
    """
    Resolve the block definition for a component without inserting an instance.

    Useful for checking that a component is available and its optional
    sub-parts are correctly enumerated before placing.
    """
    params: Dict[str, Any] = {"comp_id": comp_id}
    if enabled_optional_ids is not None:
        params["enabled_optional_ids"] = list(enabled_optional_ids)
    return invoke_result_json("part.build_definition", params)


@mcp.tool(annotations=ToolAnnotations(destructiveHint=True, openWorldHint=True))
def hyperscaff_part_place_at_point(
    ctx: Context,
    comp_id: str,
    placement_point: Dict[str, float],
    rotate_3d: bool = False,
    rotation_point: Optional[Dict[str, float]] = None,
    enabled_optional_ids: Optional[List[str]] = None,
) -> str:
    """
    Place a single component at a 3D point. MODIFIES THE DOCUMENT.

    Parameters
    ----------
    comp_id : str
        Component ID from hyperscaff_part_catalog.
    placement_point : {"x": float, "y": float, "z": float}
        World-space position for the placement.
    rotate_3d : bool
        If True, place the component with a 3D rotation pinned via rotation_point.
    rotation_point : {"x": float, "y": float, "z": float}, optional
        Second point that, together with placement_point, defines the rotation
        axis. Only used when rotate_3d is True.
    enabled_optional_ids : list[str], optional
        Optional sub-part IDs to include in the block definition.
    """
    params: Dict[str, Any] = {
        "comp_id": comp_id,
        "placement_point": placement_point,
        "rotate_3d": rotate_3d,
    }
    if rotation_point is not None:
        params["rotation_point"] = rotation_point
    if enabled_optional_ids is not None:
        params["enabled_optional_ids"] = list(enabled_optional_ids)
    return invoke_result_json("part.place_at_point", params)


@mcp.tool(annotations=ToolAnnotations(destructiveHint=True, openWorldHint=True))
def hyperscaff_part_replace_selected(
    ctx: Context,
    comp_id: str,
    keep_selection: bool = False,
    enabled_optional_ids: Optional[List[str]] = None,
) -> str:
    """
    Replace the currently selected block instance(s) with a different component.
    MODIFIES THE DOCUMENT.
    """
    params: Dict[str, Any] = {
        "comp_id": comp_id,
        "keep_selection": keep_selection,
    }
    if enabled_optional_ids is not None:
        params["enabled_optional_ids"] = list(enabled_optional_ids)
    return invoke_result_json("part.replace_selected", params)


@mcp.tool(annotations=ToolAnnotations(destructiveHint=True, openWorldHint=True))
def hyperscaff_part_resize_selected(
    ctx: Context,
    axis: str,
    increase: bool,
) -> str:
    """
    Step the selected component up or down the standard size ladder on one axis.
    MODIFIES THE DOCUMENT.

    axis : "length" | "width" | "height"
    increase : bool — true to step up, false to step down. Returns an error if
        the size ladder is at the corresponding end.
    """
    return invoke_result_json("part.resize_selected", {"axis": axis, "increase": increase})


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
def hyperscaff_part_get_variants(
    ctx: Context,
    comp_id: str,
    locked_variant_codes: Optional[List[str]] = None,
) -> str:
    """
    Return the variant catalog for a component. Use before cycling a variant
    to see what's available and which combinations are valid.
    """
    params: Dict[str, Any] = {"comp_id": comp_id}
    if locked_variant_codes is not None:
        params["locked_variant_codes"] = list(locked_variant_codes)
    return invoke_result_json("part.get_variants", params)


@mcp.tool(annotations=ToolAnnotations(destructiveHint=True, openWorldHint=True))
def hyperscaff_part_cycle_variant(ctx: Context, request: Dict[str, Any]) -> str:
    """
    Cycle the selected component to the next/previous variant on a given axis.
    MODIFIES THE DOCUMENT.

    request : BlockVariantCycleRequest shape (variant_group, direction, etc.).
    """
    return invoke_result_json("part.cycle_variant", request)


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
def hyperscaff_part_find_duplicates(ctx: Context, tolerance_mm: float = 15.0) -> str:
    """
    Find duplicate block instances (same definition, near-identical transform).
    READ-ONLY.

    Pair with hyperscaff_part_cull_duplicates to actually delete them.
    """
    return invoke_result_json("part.find_duplicates", {"tolerance_mm": tolerance_mm})


@mcp.tool(annotations=ToolAnnotations(destructiveHint=True, openWorldHint=True))
def hyperscaff_part_cull_duplicates(ctx: Context, tolerance_mm: float = 15.0) -> str:
    """
    Delete duplicate block instances within tolerance. MODIFIES THE DOCUMENT.

    ALWAYS call hyperscaff_part_find_duplicates first and confirm the count
    with the user before invoking this.
    """
    return invoke_result_json("part.cull_duplicates", {"tolerance_mm": tolerance_mm})
