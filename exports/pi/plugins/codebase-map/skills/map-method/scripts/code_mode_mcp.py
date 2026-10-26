"""Opt-in MCP Code Mode over the native server's validated tool registry."""

from __future__ import annotations

import json

from mcp.server import MCPServer
from mcp.server.mcpserver import Context
from mcp.server.mcpserver.exceptions import ToolError
from mcp.types import CallToolResult, ToolAnnotations

from code_mode import CodeModeError, DenoExecutor


class _NestedContext(Context):
    async def report_progress(self, progress, total=None, message=None) -> None:
        # Native operations report 0 then 1. Replaying those milestones inside
        # one composed request would reset its progress after each operation.
        pass


async def create_code_mode_server(
    native: MCPServer, executor: DenoExecutor, allow_writes: tuple[str, ...] = (),
) -> MCPServer:
    """Build a two-tool facade; startup grants come only from trusted config."""
    registered = {tool.name: tool for tool in await native.list_tools()}
    reads = {name for name, tool in registered.items()
             if tool.annotations is not None and tool.annotations.read_only_hint is True}
    grants = set(allow_writes)
    invalid = grants - (registered.keys() - reads)
    if invalid:
        raise ValueError("--code-mode-allow-write requires exact native mutation names: "
                         + ", ".join(sorted(invalid)))
    permitted = reads | grants
    catalog = [tool.model_dump(mode="json", by_alias=True, exclude_none=True)
               for name, tool in registered.items() if name in permitted]
    server = MCPServer("codebase-map")

    @server.tool(annotations=ToolAnnotations(read_only_hint=True, open_world_hint=False))
    async def search(ctx: Context, code: str) -> dict:
        """Discover permitted operations by running an async JavaScript function.

        The function reads `catalog`, an array of native MCP tool descriptors
        with name, description, inputSchema and annotations. Return only the
        matching names or schemas. No operations or direct I/O are available.
        Example: async () => catalog.filter(t => t.name.includes('outline'))
        """
        await ctx.report_progress(0, total=1, message="Searching operation catalog")
        try:
            result = await executor.run(code, catalog=catalog, call_tool=None,
                                        allowed_tools=set())
        except CodeModeError as error:
            raise ToolError(str(error)) from error
        await ctx.report_progress(1, total=1, message="Catalog search complete")
        return result

    @server.tool(annotations=ToolAnnotations(read_only_hint=not grants, open_world_hint=False))
    async def execute(ctx: Context, code: str, tools: list[str]) -> dict:
        """Compose permitted operations and return a compact selection.

        Supply exact operation names in `tools`. The async JavaScript function
        calls `await tools.operation_name({arguments})`; each call uses native
        schema validation and project boundaries. Await every call and return
        JSON. Intermediate results stay in the runtime. Receipts expose every
        admitted call, including caught errors. Writes require startup grants;
        this request cannot grant permissions. No direct I/O is available.
        """
        selected = set(tools)
        denied = selected - permitted
        if denied:
            raise ToolError("Operations are not permitted: " + ", ".join(sorted(denied)))
        nested = _NestedContext(request_context=ctx.request_context, mcp_server=native)

        async def invoke(name: str, arguments: dict):
            result = await native.call_tool(name, arguments, context=nested)
            if not isinstance(result, CallToolResult):
                raise ToolError("Interactive tool results are unavailable inside Code Mode")
            if result.is_error:
                detail = "\n".join(block.text for block in result.content
                                   if getattr(block, "type", None) == "text")
                raise ToolError(detail or "Native operation failed")
            if result.structured_content is not None:
                return result.structured_content
            # The SDK also serializes dict-returning native operations as one
            # JSON text block when they do not declare an output schema.
            if len(result.content) == 1 and result.content[0].type == "text":
                return json.loads(result.content[0].text)
            return [block.model_dump(mode="json", by_alias=True, exclude_none=True)
                    for block in result.content]

        await ctx.report_progress(0, total=1, message="Executing composed operations")
        try:
            result = await executor.run(
                code, catalog=[item for item in catalog if item["name"] in selected],
                call_tool=invoke, allowed_tools=selected)
        except CodeModeError as error:
            raise ToolError(str(error)) from error
        await ctx.report_progress(1, total=1, message="Composed operations complete")
        return result

    return server
