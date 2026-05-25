"""
Sanity check that the rhinomcp ↔ HyperScaff bridge is wired up.
"""
from __future__ import annotations

from mcp.server.fastmcp import Context
from mcp.types import ToolAnnotations

from rhinomcp import mcp
from rhinomcp.tools._hyperscaff_bridge import invoke_result_json


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
def hyperscaff_ping(ctx: Context) -> str:
    """
    Verify that HyperScaff is loaded and the HS_McpInvoke bridge is reachable.

    Returns a JSON envelope. On success `result` contains:
        { "pong": true, "plugin": "HyperScaff", "build_version": "0.1.0.x",
          "build_commit": "<hash>", "active_doc": true|false }

    Use this as a one-call connectivity check before relying on any HyperScaff
    tool. If `ok` is false the bridge couldn't reach HyperScaff — common causes:
    HyperScaff plugin not loaded, Rhino has no active document, or the request
    file directory is not writable.
    """
    return invoke_result_json("ping")
