"""MCP/HTTP JSON server exposing PAN-OS agent skills as tool endpoints.

Provides two server modes:
  - HTTP (default): ``python -m pa_agent.server_mcp [port]``
  - MCP stdio:      ``python -m pa_agent.server_mcp --stdio``
"""
from __future__ import annotations

import asyncio
import json
import time
import uuid
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Any, Callable

from pa_agent.config import get_settings
from pa_agent.errors import PAAgentError
from pa_agent.log import get_logger
from pa_agent.models import PolicyFilter, SecurityRule, ToolResponse
from pa_agent.panos_api import PanosAPI
from pa_agent.skills import anomaly, policy, system
from pa_agent.skills.backup_restore import backup, get_storage, list_backups, restore

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Tool metadata (shared by HTTP and MCP servers)
# ---------------------------------------------------------------------------

TOOL_REGISTRY: list[dict[str, Any]] = [
    {
        "name": "anomaly.detect",
        "description": "Detect anomalous network activity on the firewall",
        "path": "/tools/anomaly.detect",
        "parameters": {
            "window": {"type": "string", "description": "Detection window (e.g. '1h')", "default": "1h"},
            "baseline": {"type": "string", "description": "Baseline period (e.g. '24h')", "default": "24h"},
            "thresholds": {"type": "object", "description": "Optional threshold overrides", "default": None},
        },
    },
    {
        "name": "policy.list",
        "description": "List security policy rules with optional filters",
        "path": "/tools/policy.list",
        "parameters": {
            "name_contains": {"type": "string", "description": "Filter rules by name substring"},
            "tag": {"type": "string", "description": "Filter by tag"},
            "from_zone": {"type": "string", "description": "Filter by source zone"},
            "to_zone": {"type": "string", "description": "Filter by destination zone"},
            "action": {"type": "string", "description": "Filter by action (allow/deny/drop)"},
        },
    },
    {
        "name": "policy.add",
        "description": "Add a new security policy rule",
        "path": "/tools/policy.add",
        "parameters": {
            "rule": {"type": "object", "description": "SecurityRule fields", "required": True},
            "dry_run": {"type": "boolean", "default": True},
            "confirm": {"type": "boolean", "default": False},
            "validate": {"type": "boolean", "default": False},
            "commit": {"type": "boolean", "default": False},
            "commit_comment": {"type": "string", "default": None},
        },
    },
    {
        "name": "policy.update",
        "description": "Update an existing security policy rule",
        "path": "/tools/policy.update",
        "parameters": {
            "name": {"type": "string", "description": "Rule name to update", "required": True},
            "patches": {"type": "object", "description": "Fields to update", "required": True},
            "dry_run": {"type": "boolean", "default": True},
            "confirm": {"type": "boolean", "default": False},
            "validate": {"type": "boolean", "default": False},
            "commit": {"type": "boolean", "default": False},
            "commit_comment": {"type": "string", "default": None},
        },
    },
    {
        "name": "policy.delete",
        "description": "Delete a security policy rule",
        "path": "/tools/policy.delete",
        "parameters": {
            "name": {"type": "string", "description": "Rule name to delete", "required": True},
            "dry_run": {"type": "boolean", "default": True},
            "confirm": {"type": "boolean", "default": False},
            "commit": {"type": "boolean", "default": False},
            "commit_comment": {"type": "string", "default": None},
        },
    },
    {
        "name": "config.backup",
        "description": "Backup the running PAN-OS configuration",
        "path": "/tools/config.backup",
        "parameters": {
            "backend": {"type": "string", "description": "Storage backend: 'local' or 's3'", "default": "local"},
        },
    },
    {
        "name": "config.list_backups",
        "description": "List available configuration backups",
        "path": "/tools/config.list_backups",
        "parameters": {
            "backend": {"type": "string", "description": "Storage backend: 'local' or 's3'", "default": "local"},
        },
    },
    {
        "name": "config.restore",
        "description": "Restore a PAN-OS configuration from backup",
        "path": "/tools/config.restore",
        "parameters": {
            "key": {"type": "string", "description": "Backup key to restore", "required": True},
            "backend": {"type": "string", "description": "Storage backend: 'local' or 's3'", "default": "local"},
            "dry_run": {"type": "boolean", "default": True},
            "confirm": {"type": "boolean", "default": False},
            "commit": {"type": "boolean", "default": False},
            "commit_comment": {"type": "string", "default": None},
        },
    },
    {
        "name": "system.usage",
        "description": "Get firewall system resource usage",
        "path": "/tools/system.usage",
        "parameters": {},
    },
]

_TOOL_BY_NAME: dict[str, dict[str, Any]] = {t["name"]: t for t in TOOL_REGISTRY}
_TOOL_BY_PATH: dict[str, dict[str, Any]] = {t["path"]: t for t in TOOL_REGISTRY}

# ---------------------------------------------------------------------------
# Async skill dispatch helpers
# ---------------------------------------------------------------------------


def _run_skill(coro_factory: Callable[..., Any]) -> ToolResponse:
    """Run an async skill coroutine synchronously."""
    return asyncio.run(coro_factory())


def _dispatch_tool(name: str, args: dict[str, Any]) -> ToolResponse:
    """Dispatch a tool call by name to the appropriate skill function."""
    settings = get_settings()

    if name == "anomaly.detect":

        async def _run() -> ToolResponse:
            async with PanosAPI(settings) as api:
                return await anomaly.detect(
                    api,
                    window=args.get("window", "1h"),
                    baseline=args.get("baseline", "24h"),
                    thresholds=args.get("thresholds"),
                )

        return _run_skill(_run)

    if name == "policy.list":

        async def _run() -> ToolResponse:
            async with PanosAPI(settings) as api:
                filters = PolicyFilter(**args) if args else None
                return await policy.list_rules(api, filters)

        return _run_skill(_run)

    if name == "policy.add":

        async def _run() -> ToolResponse:
            async with PanosAPI(settings) as api:
                rule = SecurityRule(**args.pop("rule", args))
                return await policy.add_rule(
                    api,
                    rule,
                    dry_run=args.get("dry_run", True),
                    confirm=args.get("confirm", False),
                    validate=args.get("validate", False),
                    commit=args.get("commit", False),
                    commit_comment=args.get("commit_comment"),
                )

        return _run_skill(_run)

    if name == "policy.update":

        async def _run() -> ToolResponse:
            async with PanosAPI(settings) as api:
                return await policy.update_rule(
                    api,
                    name=args["name"],
                    patches=args["patches"],
                    dry_run=args.get("dry_run", True),
                    confirm=args.get("confirm", False),
                    validate=args.get("validate", False),
                    commit=args.get("commit", False),
                    commit_comment=args.get("commit_comment"),
                )

        return _run_skill(_run)

    if name == "policy.delete":

        async def _run() -> ToolResponse:
            async with PanosAPI(settings) as api:
                return await policy.delete_rule(
                    api,
                    name=args["name"],
                    dry_run=args.get("dry_run", True),
                    confirm=args.get("confirm", False),
                    commit=args.get("commit", False),
                    commit_comment=args.get("commit_comment"),
                )

        return _run_skill(_run)

    if name == "config.backup":

        async def _run() -> ToolResponse:
            storage = get_storage(args.get("backend", "local"), settings)
            async with PanosAPI(settings) as api:
                return await backup(api, storage)

        return _run_skill(_run)

    if name == "config.list_backups":

        async def _run() -> ToolResponse:
            storage = get_storage(args.get("backend", "local"), settings)
            return await list_backups(storage)

        return _run_skill(_run)

    if name == "config.restore":

        async def _run() -> ToolResponse:
            storage = get_storage(args.get("backend", "local"), settings)
            async with PanosAPI(settings) as api:
                return await restore(
                    api,
                    storage,
                    key=args["key"],
                    dry_run=args.get("dry_run", True),
                    confirm=args.get("confirm", False),
                    commit=args.get("commit", False),
                    commit_comment=args.get("commit_comment"),
                )

        return _run_skill(_run)

    if name == "system.usage":

        async def _run() -> ToolResponse:
            async with PanosAPI(settings) as api:
                return await system.get_usage(api)

        return _run_skill(_run)

    return ToolResponse(
        ok=False,
        error={
            "error_code": "UNKNOWN_TOOL",
            "message": f"Unknown tool: {name}",
            "remediation": "Use tools/list to see available tools.",
        },
    )


# ---------------------------------------------------------------------------
# HTTP Server
# ---------------------------------------------------------------------------

# Map URL paths to tool names for the HTTP handler.
_PATH_TO_NAME: dict[str, str] = {t["path"]: t["name"] for t in TOOL_REGISTRY}


class ToolHandler(BaseHTTPRequestHandler):
    """HTTP request handler for MCP tool endpoints."""

    def log_message(self, format: str, *args: Any) -> None:  # noqa: A002
        # Suppress default stderr logging; we use structlog instead.
        pass

    # ---- GET ---------------------------------------------------------------

    def do_GET(self) -> None:
        """GET /tools — list available tools."""
        path = self.path.rstrip("/")
        if path == "/tools":
            tools = [
                {"name": t["name"], "description": t["description"], "method": "POST", "path": t["path"]}
                for t in TOOL_REGISTRY
            ]
            self._send_json(200, {"tools": tools})
        elif path == "/health":
            self._send_json(200, {"status": "ok"})
        else:
            self._send_json(404, {"error": "Not found"})

    # ---- POST --------------------------------------------------------------

    def do_POST(self) -> None:
        request_id = str(uuid.uuid4())[:8]
        start = time.time()

        content_length = int(self.headers.get("Content-Length", 0))
        body: dict[str, Any] = json.loads(self.rfile.read(content_length)) if content_length else {}

        path = self.path.rstrip("/")
        tool_name = _PATH_TO_NAME.get(path)

        if tool_name is None:
            self._send_json(
                404,
                ToolResponse(
                    ok=False,
                    error={
                        "error_code": "NOT_FOUND",
                        "message": f"Unknown tool: {path}",
                        "remediation": "GET /tools for available endpoints.",
                    },
                ).model_dump(),
            )
            return

        try:
            settings = get_settings()
            result = _dispatch_tool(tool_name, body)
            duration = time.time() - start
            logger.info(
                "tool_call",
                request_id=request_id,
                tool=tool_name,
                host=settings.PANOS_HOST,
                duration=f"{duration:.3f}s",
                ok=result.ok,
            )
            self._send_json(200, result.model_dump())
        except PAAgentError as exc:
            duration = time.time() - start
            logger.warning(
                "tool_error",
                request_id=request_id,
                tool=tool_name,
                duration=f"{duration:.3f}s",
                error_code=exc.error_code,
            )
            self._send_json(
                200,
                ToolResponse(ok=False, error=exc.to_dict()).model_dump(),
            )
        except Exception as exc:
            duration = time.time() - start
            logger.exception(
                "tool_unhandled_error",
                request_id=request_id,
                tool=tool_name,
                duration=f"{duration:.3f}s",
            )
            self._send_json(
                500,
                ToolResponse(
                    ok=False,
                    error={
                        "error_code": "INTERNAL",
                        "message": str(exc),
                        "remediation": "Check server logs for details.",
                    },
                ).model_dump(),
            )

    # ---- helpers -----------------------------------------------------------

    def _send_json(self, status: int, data: dict[str, Any]) -> None:
        payload = json.dumps(data, default=str).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)


# ---------------------------------------------------------------------------
# MCP Stdio Server (JSON-RPC over stdin/stdout)
# ---------------------------------------------------------------------------


class MCPStdioServer:
    """Minimal MCP stdio server.

    Reads newline-delimited JSON-RPC messages from stdin, dispatches to
    the same skill functions, and writes JSON-RPC responses to stdout.
    """

    async def handle_message(self, message: dict[str, Any]) -> dict[str, Any]:
        """Handle a single MCP JSON-RPC message."""
        method = message.get("method", "")
        params: dict[str, Any] = message.get("params", {})
        msg_id = message.get("id")

        if method == "initialize":
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "serverInfo": {"name": "pa-ngfw-agent", "version": "0.1.0"},
                    "capabilities": {"tools": {}},
                },
            }

        if method == "tools/list":
            tools = [
                {
                    "name": t["name"],
                    "description": t["description"],
                    "inputSchema": {
                        "type": "object",
                        "properties": t["parameters"],
                    },
                }
                for t in TOOL_REGISTRY
            ]
            return {"jsonrpc": "2.0", "id": msg_id, "result": {"tools": tools}}

        if method == "tools/call":
            tool_name = params.get("name", "")
            arguments: dict[str, Any] = params.get("arguments", {})

            if tool_name not in _TOOL_BY_NAME:
                return {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "error": {"code": -32601, "message": f"Unknown tool: {tool_name}"},
                }

            try:
                result = _dispatch_tool(tool_name, arguments)
                return {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "result": {
                        "content": [{"type": "text", "text": json.dumps(result.model_dump(), default=str)}],
                        "isError": not result.ok,
                    },
                }
            except PAAgentError as exc:
                err_resp = ToolResponse(ok=False, error=exc.to_dict())
                return {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "result": {
                        "content": [{"type": "text", "text": json.dumps(err_resp.model_dump(), default=str)}],
                        "isError": True,
                    },
                }
            except Exception as exc:
                return {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "error": {"code": -32603, "message": str(exc)},
                }

        # Unknown method
        return {
            "jsonrpc": "2.0",
            "id": msg_id,
            "error": {"code": -32601, "message": f"Method not found: {method}"},
        }

    async def run(self) -> None:
        """Read JSON-RPC messages from stdin, dispatch, write responses to stdout."""
        import sys

        logger.info("mcp_stdio_start")
        for line in sys.stdin:
            line = line.strip()
            if not line:
                continue
            try:
                message = json.loads(line)
            except json.JSONDecodeError:
                sys.stdout.write(
                    json.dumps({"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": "Parse error"}})
                    + "\n"
                )
                sys.stdout.flush()
                continue

            response = await self.handle_message(message)

            # Notifications (no id) don't get responses
            if message.get("id") is not None:
                sys.stdout.write(json.dumps(response, default=str) + "\n")
                sys.stdout.flush()


# ---------------------------------------------------------------------------
# Entry points
# ---------------------------------------------------------------------------


def run_http_server(host: str = "0.0.0.0", port: int = 8080) -> None:
    """Start the HTTP tool server."""
    server = HTTPServer((host, port), ToolHandler)
    logger.info("server_start", host=host, port=port, tools=len(TOOL_REGISTRY))
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("server_stop")
        server.server_close()


def run_mcp_stdio() -> None:
    """Start the MCP stdio server."""
    server = MCPStdioServer()
    asyncio.run(server.run())


if __name__ == "__main__":
    import sys

    if "--stdio" in sys.argv:
        run_mcp_stdio()
    else:
        port = int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1].isdigit() else 8080
        run_http_server(port=port)
