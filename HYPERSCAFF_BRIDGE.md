# HyperScaff Bridge

This rhinomcp-wdg fork includes a bridge layer that lets MCP clients drive
[HyperScaff](https://github.com/rubrubadubdub/hyperscaff_pfr_mvp) — a Rhino
plug-in for scaffold authoring — as a first-class surface, not just via raw
Rhino commands.

## Why a bridge

rhinomcp's C# plugin targets `.NET 7.0`. HyperScaff targets `.NET Framework 4.8`.
Both load into the same Rhino process but in **isolated runtimes**, so neither
plugin can directly reference the other's assemblies, and cross-runtime
reflection is fragile.

What they CAN share is the Rhino command surface — Rhino itself is the
runtime-agnostic bus. So the bridge uses a small file-based RPC envelope on
top of a single HyperScaff command, `HS_McpInvoke`.

## Wire protocol

```
┌────────────────────┐
│  rhinomcp Python   │  (this server)
│  tools/hyperscaff_*│
└────────┬───────────┘
         │ 1. write %TEMP%/hyperscaff_mcp/<uuid>.req.json
         │      { "method": "...", "params": { ... } }
         │ 2. send_command("run_command", "_-HS_McpInvoke <uuid>")
         ▼
┌────────────────────┐
│  rhinomcp C# (.NET 7)
│  RhinoMCPServer    │  ← forwards to Rhino
└────────┬───────────┘
         │
         ▼
┌────────────────────────────────────────┐
│  HyperScaff plugin (.NET Framework 4.8)│
│  Commands/McpInvokeCommand.cs          │
│    └─ Automation/Mcp/McpDispatcher.cs  │
│         └─ HyperScaffPlugin.Instance   │
│            .BayAutomation,             │
│            .LegAutomation, etc.        │
└────────┬───────────────────────────────┘
         │ 3. write %TEMP%/hyperscaff_mcp/<uuid>.resp.json
         │ 4. RhinoApp.WriteLine("HS_McpInvoke OK <uuid> <path>")
         ▼
┌────────────────────┐
│  rhinomcp Python   │  reads response file, parses, returns to MCP client
└────────────────────┘
```

Request envelope (`<uuid>.req.json`):

```json
{
  "method": "bay.catalog",
  "params": { "system_code": "LAR" }
}
```

Success envelope (`<uuid>.resp.json`):

```json
{
  "ok": true,
  "method": "bay.catalog",
  "result": { ... service JSON ... }
}
```

Failure envelope:

```json
{
  "ok": false,
  "method": "bay.catalog",
  "error": "system_code is required",
  "stack": "..."          // present only on unhandled exceptions
}
```

## Tools

All HyperScaff bridge tools live under `rhino_mcp_server/src/rhinomcp/tools/`
and are auto-registered (file names start with `hyperscaff_`). The private
helper that handles the request/response dance is `_hyperscaff_bridge.py`
(leading underscore → skipped by the tool auto-discovery).

Categories:

- **Bootstrap / discovery**
  - `hyperscaff_ping` — connectivity check
  - `hyperscaff_list_methods` — full method catalog
  - `hyperscaff_start_here` — recommended call order
  - `hyperscaff_guide` — full automation guide

- **Rulebook / scaffold configs**
  - `hyperscaff_rulebook` — assembly rulebook for a service+system+config
  - `hyperscaff_scaffold_config_catalog` — list scaffold intents
  - `hyperscaff_scaffold_config_document` — resolved JSON for one config

- **Bay automation**
  - `hyperscaff_bay_catalog`
  - `hyperscaff_bay_plan_straight_run` (READ — plan only)
  - `hyperscaff_bay_place` (DESTRUCTIVE — drives HS_PlaceBay)

- **Leg automation**
  - `hyperscaff_leg_catalog`
  - `hyperscaff_leg_plan` (READ)
  - `hyperscaff_leg_build`, `hyperscaff_leg_build_batch` (DESTRUCTIVE)
  - `hyperscaff_leg_auto_place_selected`, `hyperscaff_leg_auto_place_all` (DESTRUCTIVE)

- **Part assistant (loose components)**
  - `hyperscaff_part_catalog`, `hyperscaff_part_usage_hints`
  - `hyperscaff_part_selected_component_id`, `hyperscaff_part_selected_component_ids`
  - `hyperscaff_part_build_definition` (READ)
  - `hyperscaff_part_place_at_point`, `hyperscaff_part_replace_selected`,
    `hyperscaff_part_resize_selected`, `hyperscaff_part_cycle_variant` (DESTRUCTIVE)
  - `hyperscaff_part_get_variants` (READ)
  - `hyperscaff_part_find_duplicates` (READ),
    `hyperscaff_part_cull_duplicates` (DESTRUCTIVE)

- **Docs**
  - `hyperscaff_docs_digest` — curated map of high-signal docs
  - `hyperscaff_docs_list` — every Markdown file under HyperScaff `docs/`
  - `hyperscaff_docs_get` — full content of one doc

- **Escape hatch**
  - `hyperscaff_invoke` — call any method with a free-form params dict;
    use when no typed wrapper exists

Plus a HyperScaff-specific MCP prompt: `hyperscaff_strategy` (registered in
`prompts/hyperscaff_strategy.py`). Read this prompt before driving HyperScaff
— it lays out the call order, critical rules (orientation, GROUND-layer skip,
scaffold config requirements), and the bridge-vs-generic-tool boundary.

## Requirements

- **HyperScaff plugin loaded in Rhino.** The bridge needs HS_McpInvoke to be
  available; if HyperScaff isn't loaded `hyperscaff_ping` fails with an
  explicit error.
- **Local rhinomcp Python server.** The bridge dir lives under the Python
  server's `%TEMP%`. If the server runs on a different host than Rhino, the
  file-based envelope won't reach HyperScaff — not supported today.
- **Active Rhino document.** Most operations need `RhinoDoc.ActiveDoc` to be
  non-null. The ping result includes an `active_doc` flag you can check first.

## Extending

To expose a new HyperScaff Automation method:

1. In the HyperScaff repo, add a `case "your.method":` arm to
   `Automation/Mcp/McpDispatcher.cs`. Each arm typically deserializes its
   typed request via `Deserialize<T>(@params)`, calls the matching
   `HyperScaffPlugin.Instance.X.YJson(...)` method, and lets the dispatcher
   wrap the JSON result.
2. Add the method name to the `BuildListMethodsResult()` list in the same
   file so `hyperscaff_list_methods()` advertises it.
3. (Optional) add a typed Python wrapper in `rhino_mcp_server/src/rhinomcp/tools/`
   to give MCP clients an ergonomic call. Without it, clients can still reach
   the method via `hyperscaff_invoke(method=..., params=...)`.
