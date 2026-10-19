"""Fail-closed Commander MCP facade for WindAnvil Blade authority."""
from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations
from blade_local_client import BladeBlocked, health, status, talkpipe_run, host_inspect

server = FastMCP(
    name="windanvil-commander",
    instructions=(
        "TalkPipe execution requires an already-admitted signed Blade grant. "
        "This gateway never falls back to direct Python, ChatterLang or shell "
        "execution when Blade is offline or authorization is refused."
    ),
)

READ_ONLY = ToolAnnotations(
    readOnlyHint=True, destructiveHint=False,
    idempotentHint=True, openWorldHint=False,
)


@server.tool(description="Check the local WindAnvil Blade authority socket; blocked unless mode 0600 and owned by this UID.", annotations=READ_ONLY)
def commander_health() -> dict:
    try:
        return {"outcome": "PASS", "blade": health()}
    except BladeBlocked as exc:
        return {"outcome": "BLOCKED", "reason": str(exc)}


@server.tool(description="Retrieve local WindAnvil Blade authority and admitted grant status without mutating state.", annotations=READ_ONLY)
def commander_status() -> dict:
    try:
        return {"outcome": "PASS", "blade": status()}
    except BladeBlocked as exc:
        return {"outcome": "BLOCKED", "reason": str(exc)}


@server.tool(
    description=(
        "Execute an existing approved TalkPipe pipeline only through Blade's "
        "signed capability talkpipe.run. Requires exact SHA-256 of the pipeline "
        "file and an active Blade grant. Never executes arbitrary scripts."
    ),
    annotations=ToolAnnotations(
        readOnlyHint=False, destructiveHint=True,
        idempotentHint=False, openWorldHint=True,
    ),
)
def commander_talkpipe_run(pipeline: str, pipeline_sha256: str) -> dict:
    try:
        response = talkpipe_run(pipeline, pipeline_sha256)
        return {"outcome": "PASS", "blade": response, "capability": "talkpipe.run"}
    except BladeBlocked as exc:
        return {"outcome": "BLOCKED", "reason": str(exc), "capability": "talkpipe.run"}




@server.tool(
    description=(
        "Inspect the pinned host root through Blade's signed host.inspect capability. "
        "Allowed operations: system.info, dir.list, file.read. Paths are relative "
        "to the administrator-pinned directory, cannot traverse symlinks/hidden "
        "entries, and file output is capped at 16 KiB. No shell fallback."
    ),
    annotations=READ_ONLY,
)
def commander_host_inspect(operation: str, path: str = "") -> dict:
    try:
        response = host_inspect(operation, path)
        return {"outcome": "PASS", "blade": response, "capability": "host.inspect"}
    except BladeBlocked as exc:
        return {"outcome": "BLOCKED", "reason": str(exc), "capability": "host.inspect"}


if __name__ == "__main__":
    server.run(transport="stdio")
