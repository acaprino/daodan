# /// script
# requires-python = ">=3.11"
# dependencies = ["mcp>=2.0.0,<3"]
# ///
"""Local stdio access to the project-bound Codebase Map service.

The host owns LLM workers and continuation. This transport exposes deterministic
operations, persisted run events and request-scoped progress, without a scheduler.
"""

from __future__ import annotations

import argparse
from functools import partial
import json
from pathlib import Path
from typing import Literal

import anyio
from mcp.server import MCPServer
from mcp.server.mcpserver import Context
from mcp.server.mcpserver.exceptions import ToolError
from mcp.types import ToolAnnotations

from mcp_service import MapService


async def _invoke(ctx: Context, operation, *args, **kwargs) -> dict:
    """Report operation milestones; let an in-flight atomic mutation finish."""
    await ctx.report_progress(0, message=f"Starting {operation.__name__}")
    try:
        result = await anyio.to_thread.run_sync(partial(operation, *args, **kwargs))
    except (ValueError, OSError, TypeError, KeyError) as error:
        raise ToolError(str(error)) from error
    except Exception as error:
        # Any other failure is still a tool result the client can read, never
        # a protocol fault that ends the session.
        raise ToolError(f"internal error in {operation.__name__}: {type(error).__name__}: {error}") from error
    await ctx.report_progress(1, message=f"Finished {operation.__name__}")
    return result


def create_server(project: str | Path, store: str | None = None) -> MCPServer:
    service = MapService(project, store)
    server = MCPServer("codebase-map")
    read_only = ToolAnnotations(read_only_hint=True, open_world_hint=False)
    writes = ToolAnnotations(read_only_hint=False, open_world_hint=False)

    def publish(run_id: str) -> dict:
        result = service.publish(run_id)
        if not result.get("published"):
            raise ValueError("Publication refused: " + json.dumps(result, sort_keys=True))
        return result

    @server.tool(annotations=read_only)
    async def codebase_map_scope(ctx: Context, target: str = ".") -> dict:
        """Count the target inventory and exclusions without starting an analysis."""
        return await _invoke(ctx, service.scope, target)

    @server.tool(annotations=writes)
    async def codebase_map_create_run(
        ctx: Context, target: str, run_id: str,
        depth: Literal["full", "lite"] = "full", critical: bool = False,
        comments: bool = False, docs_only: bool = False,
        phase: int | None = None, stop_after: int | None = None,
        format: Literal["sqlite", "json"] = "sqlite",
    ) -> dict:
        """Prepare a classic run and snapshot. The host must dispatch its analysis workers."""
        return await _invoke(ctx, service.create_run, target, run_id, depth=depth,
                             critical=critical, comments=comments, docs_only=docs_only,
                             phase=phase, stop_after=stop_after, format=format)

    @server.tool(annotations=read_only)
    async def codebase_map_runs(ctx: Context) -> dict:
        """List this project's canonical analysis runs and active registry."""
        return await _invoke(ctx, service.runs)

    @server.tool(annotations=read_only)
    async def codebase_map_status(ctx: Context, run_id: str) -> dict:
        """Read canonical state and actual delivery gaps, including direct worker changes."""
        return await _invoke(ctx, service.status, run_id)

    @server.tool(annotations=read_only)
    async def codebase_map_outline(
        ctx: Context, run_id: str, path: str | None = None,
        pattern: str | None = None, limit: int = 100,
    ) -> dict:
        """Navigate the bound snapshot's symbol metadata; this is not a source read."""
        return await _invoke(ctx, service.outline, run_id, path=path, pattern=pattern, limit=limit)

    @server.tool(annotations=read_only)
    async def codebase_map_graph(
        ctx: Context, run_id: str, paths: list[str] | None = None,
        hops: int = 2, limit: int = 100,
    ) -> dict:
        """Query verified static links and diagnostics for a run's source manifest."""
        return await _invoke(ctx, service.graph, run_id, paths=paths, hops=hops, limit=limit)

    @server.tool(annotations=read_only)
    async def codebase_map_read(ctx: Context, run_id: str, requests: list[dict]) -> dict:
        """Read hash-verified source blocks using path, symbols, ranges or full_file requests."""
        return await _invoke(ctx, service.read, run_id, requests)

    @server.tool(annotations=read_only)
    async def codebase_map_edit_impact(
        ctx: Context, run_id: str, targets: list[str], neighbors: int = 20,
        history: int = 5, include_source: bool = True,
    ) -> dict:
        """Before editing symbols: digests, cards, one-hop callers and callees, unresolved references and verified source."""
        return await _invoke(ctx, service.edit_impact, run_id, targets, neighbors=neighbors,
                             history=history, include_source=include_source)

    @server.tool(annotations=read_only)
    async def codebase_map_meta_query(
        ctx: Context, run_id: str, paths: list[str] | None = None, symbol: str | None = None,
        freshness: str | None = None, include_history: bool = True, limit: int = 100,
    ) -> dict:
        """Query Meta-Code symbols, their card freshness and the bounded changeset history."""
        return await _invoke(ctx, service.meta_query, run_id, paths=paths, symbol=symbol,
                             freshness=freshness, include_history=include_history, limit=limit)

    @server.tool(annotations=read_only)
    async def codebase_map_diff(ctx: Context, run_id: str) -> dict:
        """Compare the bound snapshot to current source without changing the run."""
        return await _invoke(ctx, service.diff, run_id)

    @server.tool(annotations=read_only)
    async def codebase_map_artifact(ctx: Context, run_id: str, name: str) -> dict:
        """Read one declared analysis artifact with its digest from the exact run."""
        return await _invoke(ctx, service.artifact, run_id, name)

    @server.tool(annotations=writes)
    async def codebase_map_checkpoint(
        ctx: Context, run_id: str, phase: int,
        event: Literal["phase_started", "phase_completed", "blocked"], message: str = "",
    ) -> dict:
        """Record a host phase hook. Completion requires the phase's actual declared outputs."""
        return await _invoke(ctx, service.checkpoint, run_id, phase, event, message=message)

    @server.tool(annotations=read_only)
    async def codebase_map_events(
        ctx: Context, run_id: str, after: int = 0, limit: int = 100,
    ) -> dict:
        """Replay persistent service events after a cursor; canonical status owns completeness."""
        return await _invoke(ctx, service.events, run_id, after=after, limit=limit)

    @server.tool(annotations=writes)
    async def codebase_map_resume(ctx: Context, run_id: str, phase: int | None = None) -> dict:
        """Prepare the exact unchanged run for host continuation; start no workers."""
        return await _invoke(ctx, service.resume, run_id, phase=phase)

    @server.tool(annotations=writes)
    async def codebase_map_stop(ctx: Context, run_id: str, reason: str) -> dict:
        """Record a partial run after the host has stopped its workers; does not terminate agents."""
        return await _invoke(ctx, service.stop, run_id, reason)

    @server.tool(annotations=writes)
    async def codebase_map_publish(ctx: Context, run_id: str) -> dict:
        """Publish through canonical freshness/delivery gates after the host verifies requested views."""
        return await _invoke(ctx, publish, run_id)

    return server


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", type=Path, default=Path.cwd(),
                        help="project binding, fixed for the lifetime of this server")
    parser.add_argument("--store", default=None,
                        help="project-relative analysis store beginning with a dot directory; "
                             "default .codebase-map, fixed for the lifetime of this server")
    args = parser.parse_args(argv)
    try:
        server = create_server(args.project, args.store)
    except ValueError as exc:
        parser.error(str(exc))
    server.run(transport="stdio")


if __name__ == "__main__":
    main()
