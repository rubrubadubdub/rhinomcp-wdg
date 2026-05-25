"""
HyperScaff documentation access: list, fetch, and digest of the docs/ tree.

HyperScaff's documentation is the source of truth for behavior policies, bay
builder trajectories, role resolution, and operational invariants. Read the
relevant doc BEFORE making non-trivial decisions about how to drive HyperScaff
— the dispatcher methods don't repeat the same context.
"""
from __future__ import annotations

from mcp.server.fastmcp import Context
from mcp.types import ToolAnnotations

from rhinomcp import mcp
from rhinomcp.tools._hyperscaff_bridge import invoke_result_json


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
def hyperscaff_docs_digest(ctx: Context) -> str:
    """
    Return a curated map of HyperScaff's most-important docs with one-line
    summaries each.

    Call this once when starting any non-trivial HyperScaff task so the agent
    knows which docs to read for which problem. Each entry has a `path` you
    can pass to `hyperscaff_docs_get(path=...)` to fetch the full text.
    """
    return invoke_result_json("docs.digest")


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
def hyperscaff_docs_list(ctx: Context) -> str:
    """
    List every Markdown doc under HyperScaff's docs/ tree.

    Each entry: {"path": "<relative-to-docs/>", "title": "<H1 if present>",
                 "size_bytes": <int>}.

    Sorted case-insensitively by path. Pass any `path` to hyperscaff_docs_get.
    """
    return invoke_result_json("docs.list")


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
def hyperscaff_docs_get(ctx: Context, path: str) -> str:
    """
    Fetch the full Markdown content of one doc.

    Parameters
    ----------
    path : str
        Path relative to docs/, e.g. "ARCHITECTURE.md" or
        "assembly/POLICY_AUTHORING_GUIDE.md". Forward slashes only;
        directory escape (..) is rejected.

    Files over 512 KB are truncated with `truncated: true` in the result.
    """
    return invoke_result_json("docs.get", {"path": path})
