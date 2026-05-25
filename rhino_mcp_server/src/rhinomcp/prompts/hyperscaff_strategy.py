"""
HyperScaff-specific strategy prompt.

The general rhinomcp `asset_general_strategy` is for free-form Rhino modeling.
HyperScaff is a domain-specific scaffold authoring system on top of Rhino —
its commands and Automation services have a strict call order, and using
generic Rhino tools to bypass them produces invalid scaffolds.

This prompt teaches the agent the HyperScaff-specific workflow.
"""
from rhinomcp.server import mcp


@mcp.prompt()
def hyperscaff_strategy() -> str:
    """
    Strategy for any HyperScaff (scaffold authoring) task. ALWAYS read this
    before reaching for HyperScaff tools or HS_* commands.
    """
    return """
    ============================================================
    HYPERSCAFF STRATEGY GUIDE
    ============================================================

    HyperScaff is a Rhino plug-in for scaffold authoring (Layher Allround +
    other systems). It owns its own data model (bays, legs, components,
    behavior policies) on top of Rhino's block instances. Generic Rhino tools
    can OBSERVE HyperScaff geometry but should NOT mutate scaffold objects
    directly — use the HyperScaff bridge tools instead.

    STEP 1: VERIFY THE BRIDGE
    -------------------------
    Call hyperscaff_ping(). If `ok` is false, the HyperScaff plugin is not
    loaded or the bridge can't write to %TEMP%. Tell the user and stop —
    do not fall back to manipulating blocks via the generic tools.

    STEP 2: ORIENT
    --------------
    Call hyperscaff_start_here() first, then hyperscaff_docs_digest(). The
    start-here payload tells you the recommended call order; the docs digest
    points you at the specific docs you need for the user's task.

    Read the relevant doc(s) with hyperscaff_docs_get(path=...) BEFORE making
    non-trivial decisions about policies, role resolution, or assembly rules.

    STEP 3: GET THE RULEBOOK
    ------------------------
    Before any build/place/replace/leg operation, call hyperscaff_rulebook()
    with the correct (system_code, target_service, scaffold_config). The
    rulebook returns:
      - Which bay profiles / leg configs / landings are valid
      - Required call sequence for the chosen target_service
      - Critical constraints (orientation, GROUND-layer skip, perimeter
        coverage requirements)
      - Workflow steps when scaffold_config is "full_perimeter" or "birdcage"

    Reject the user's request gracefully if the rulebook returns errors —
    don't try to work around them.

    STEP 4: DISCOVER + PLAN
    -----------------------
    Call the relevant service catalog:
      - hyperscaff_bay_catalog(system_code)
      - hyperscaff_leg_catalog(system_code)
      - hyperscaff_part_catalog(system_codes=..., search_text=...)

    Then call the plan method (READ-only) for the operation you intend:
      - hyperscaff_bay_plan_straight_run(request)
      - hyperscaff_leg_plan(request)

    Present the plan to the user. Do NOT proceed to the build step
    without confirmation, especially for batch operations.

    STEP 5: BUILD (only after confirmation)
    ---------------------------------------
    Use the matching build method, which MODIFIES THE DOCUMENT inside an
    undo record:
      - hyperscaff_leg_build(request) / hyperscaff_leg_build_batch(request)
      - hyperscaff_leg_auto_place_selected(request) /
        hyperscaff_leg_auto_place_all(request)
      - hyperscaff_part_place_at_point(...) for loose components
      - hyperscaff_bay_place(length, width, height, ...) for single bays

    For commands without a typed wrapper, use:
      - hyperscaff_invoke(method=..., params=...)  for any Automation method
      - run_command("_-HS_*")                       for any HS_* Rhino command

    Call get_commands(filter="HS_") to discover the full HS_* command surface.

    CRITICAL HYPERSCAFF RULES (NEVER VIOLATE)
    -----------------------------------------
    1. ORIENTATION: A bay's FRONT face points toward the structure (the
       building or solid object being scaffolded). BACK is the open/worker
       side and is where face bracing lives. Never place bays with front
       facing away from the structure.

       NOTE: There is a UI/code inversion you may notice if you read source —
       the WPF UI label "Front" corresponds to `BayFace.Back` in code, and
       UI "Back" to `BayFace.Front`. The bridge respects the code-side
       semantics; ignore that inversion when reasoning at the API level.

    2. GROUND LAYERS: Layers whose names contain "GROUND" must NOT be
       scaffolded unless the user explicitly requests it. When scanning
       geometry for placement targets, filter these layers out.

    3. SCAFFOLD CONFIGS: For perimeter / birdcage jobs, pass
       scaffold_config="full_perimeter" or "birdcage" to hyperscaff_rulebook
       — the workflow steps and rule set change materially.

    4. LEG AUTO-PLACE VALIDATION: Reject any leg.auto_place_* result with
       unresolved_support_column_count > 0. That means HyperScaff couldn't
       find landing geometry for some legs and the scaffold is not safe.

    5. POLICY IS GROUND TRUTH: Behavior policies (plugin defaults < family
       < system override) define what's valid. Never hardcode values that
       a policy would set. If a policy lookup returns nothing, surface that
       to the user — don't substitute a guess.

    6. ZERO DUPLICATES: HyperScaff's bay management contract requires that
       no duplicate components exist. Use hyperscaff_part_find_duplicates
       (read) before any cleanup; cull only after user confirmation.

    GENERIC RHINO TOOLS — WHEN TO USE
    ---------------------------------
    OK to use:
      - get_document_summary, get_objects, get_object_info — observation
      - capture_viewport — diagnostic screenshots
      - get_commands(filter="HS_") — command discovery
      - undo() — recovery if a HyperScaff operation produced an unexpected result

    AVOID for HyperScaff geometry:
      - create_object / modify_object on bay or scaffold blocks
      - delete_object on bay objects (use HS_DestroyBay via run_command)
      - execute_rhinoscript_python_code that calls rs.Command("_-HS_*") —
        prefer the typed bridge tools so the parameters are validated

    WHEN IN DOUBT
    -------------
    Read the relevant doc with hyperscaff_docs_get(path=...). HyperScaff's
    documentation is exhaustive; the right answer is almost always there.
    """
