"""
Private bridge helper used by the HyperScaff tool wrappers.

Architecture
------------
rhinomcp's C# plugin (.NET 7) and the HyperScaff plugin (.NET Framework 4.8) run
in isolated runtimes inside the same Rhino process. Direct .NET reflection across
that boundary is fragile, so the bridge uses Rhino *commands* (which are
runtime-agnostic) plus a file-based request/response envelope:

    1. Python writes  %TEMP%/hyperscaff_mcp/<uuid>.req.json  with
       { "method": "...", "params": { ... } }
    2. Python calls   run_command("_-HS_McpInvoke <uuid>")
    3. HyperScaff's HS_McpInvoke command reads the request, dispatches to the
       right Automation service or docs lookup, writes
       %TEMP%/hyperscaff_mcp/<uuid>.resp.json, and prints
       "HS_McpInvoke OK <uuid> <path>" or "HS_McpInvoke ERR <uuid> <msg>"
       to the Rhino command line.
    4. Python reads the response file and returns its parsed JSON to the MCP
       client.

Both files live under %TEMP%/hyperscaff_mcp/ on the same machine as Rhino.
rhinomcp's Python server normally runs locally too (RHINO_MCP_HOST defaults to
127.0.0.1) so file paths line up. If anyone ever runs the Python server on a
different host than Rhino, this bridge silently won't work — that's an explicit
non-goal until we add a transport for it.

Module name starts with an underscore so rhinomcp's tool auto-discovery skips it.
"""
from __future__ import annotations

import json
import os
import tempfile
import time
import uuid
from typing import Any, Dict, Optional

from rhinomcp import get_rhino_connection, logger


_BRIDGE_DIR_NAME = "hyperscaff_mcp"
_INVOKE_COMMAND = "_-HS_McpInvoke"
_DEFAULT_POLL_SECONDS = 0.05
_DEFAULT_MAX_WAIT_SECONDS = 30.0


def _bridge_dir() -> str:
    """Return the shared request/response directory, creating it if needed."""
    path = os.path.join(tempfile.gettempdir(), _BRIDGE_DIR_NAME)
    try:
        os.makedirs(path, exist_ok=True)
    except OSError as exc:
        # If we can't create %TEMP%/hyperscaff_mcp/ we can't talk to HyperScaff
        # at all. Surface a clean error.
        raise RuntimeError(f"HyperScaff bridge dir unavailable: {path}: {exc}")
    return path


def _request_paths(token: str) -> tuple[str, str]:
    directory = _bridge_dir()
    return (
        os.path.join(directory, f"{token}.req.json"),
        os.path.join(directory, f"{token}.resp.json"),
    )


def invoke(
    method: str,
    params: Optional[Dict[str, Any]] = None,
    *,
    max_wait_seconds: float = _DEFAULT_MAX_WAIT_SECONDS,
) -> Dict[str, Any]:
    """
    Call a HyperScaff bridge method and return the parsed response envelope.

    The envelope shape is always:
        { "ok": True,  "method": <name>, "result": <structured result> }
        { "ok": False, "method": <name>, "error":  <message> [, "stack": ...] }

    The wrapper preserves that envelope rather than unwrapping `result` so the
    caller can branch on `ok` and inspect `error` without losing context.
    """
    if not method:
        return {"ok": False, "method": "", "error": "method is required"}

    token = uuid.uuid4().hex
    req_path, resp_path = _request_paths(token)
    payload = {"method": method, "params": params or {}}

    # Clean any stale response left behind by a previous interrupted call.
    if os.path.exists(resp_path):
        try:
            os.remove(resp_path)
        except OSError:
            pass

    try:
        with open(req_path, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False)
    except OSError as exc:
        return {"ok": False, "method": method,
                "error": f"failed to write request file {req_path}: {exc}"}

    try:
        command = f"{_INVOKE_COMMAND} {token}"
        try:
            rhino = get_rhino_connection()
            result = rhino.send_command("run_command", {"command": command, "echo": False})
        except Exception as exc:
            logger.error(f"HS_McpInvoke transport failure for {method}: {exc}")
            return {"ok": False, "method": method,
                    "error": f"transport failure: {exc}"}

        captured = (result or {}).get("output", "") or ""
        command_ok = bool((result or {}).get("success", False))

        # Wait briefly for the response file to land. HS_McpInvoke writes
        # synchronously before returning, but file flushing across the
        # Rhino UI thread can lag in pathological cases — poll with a tight
        # cap rather than racing the disk.
        deadline = time.monotonic() + max_wait_seconds
        while not os.path.exists(resp_path):
            if time.monotonic() > deadline:
                return {
                    "ok": False,
                    "method": method,
                    "error": (
                        "response file did not appear within "
                        f"{max_wait_seconds:.1f}s. command_ok={command_ok}. "
                        f"captured_output={captured.strip()[:512]}"
                    ),
                }
            time.sleep(_DEFAULT_POLL_SECONDS)

        try:
            with open(resp_path, "r", encoding="utf-8-sig") as handle:
                parsed = json.load(handle)
        except (OSError, json.JSONDecodeError) as exc:
            return {"ok": False, "method": method,
                    "error": f"failed to read response: {exc}"}

        if not isinstance(parsed, dict):
            return {"ok": False, "method": method,
                    "error": "response was not a JSON object"}

        # Tag transport-level diagnostics so callers debugging via the MCP
        # client can see the underlying run_command outcome too.
        parsed.setdefault("transport", {})
        if isinstance(parsed["transport"], dict):
            parsed["transport"]["command_ok"] = command_ok
            if captured:
                parsed["transport"]["captured_output"] = captured.strip()

        return parsed
    finally:
        # Best-effort cleanup. Leaving temp files behind is noisy but never
        # corrupting; failure here must not mask the real result.
        for path in (req_path, resp_path):
            try:
                if os.path.exists(path):
                    os.remove(path)
            except OSError:
                pass


def invoke_result_json(method: str, params: Optional[Dict[str, Any]] = None) -> str:
    """
    Convenience wrapper that returns the full envelope as an indented JSON
    string. Use this from MCP tool implementations whose return type is `str`
    so clients get pretty-printed output without each tool re-serializing.
    """
    envelope = invoke(method, params)
    return json.dumps(envelope, indent=2, ensure_ascii=False)
