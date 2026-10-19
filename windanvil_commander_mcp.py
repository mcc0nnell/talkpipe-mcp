"""Fail-closed Commander MCP facade for WindAnvil Blade authority."""
from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations
from blade_local_client import BladeBlocked, health, status, talkpipe_run, host_inspect, process_list

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
        "Allowed operations: system.info, dir.list, file.read, file.find, content.search. Paths are relative "
        "to the administrator-pinned directory, cannot traverse symlinks/hidden "
        "entries. Searches are capped and return locations only, not matching content. No shell fallback."
    ),
    annotations=READ_ONLY,
)
def commander_host_inspect(operation: str, path: str = "", needle: str = "") -> dict:
    try:
        response = host_inspect(operation, path, needle)
        return {"outcome": "PASS", "blade": response, "capability": "host.inspect"}
    except BladeBlocked as exc:
        return {"outcome": "BLOCKED", "reason": str(exc), "capability": "host.inspect"}


@server.tool(
    description=(
        "List bounded PID and process-name metadata for the Blade runtime user "
        "through separately signed process.inspect authority. No command lines, "
        "environment variables, signals, or shell execution."
    ),
    annotations=READ_ONLY,
)
def commander_process_list() -> dict:
    try:
        response = process_list()
        return {"outcome": "PASS", "blade": response, "capability": "process.inspect"}
    except BladeBlocked as exc:
        return {"outcome": "BLOCKED", "reason": str(exc), "capability": "process.inspect"}


if __name__ == "__main__":
    server.run(transport="stdio")
