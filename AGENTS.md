# Agent instructions

Read README.md and AGENT_PROMPT.md before setup or design work.
Run Python 3.10+ scripts from repository directory. Host needs no CAD installation.
Use `python3 scripts/setup.py` to build, select host port, start, and validate.
Keep host binding at 127.0.0.1. Host port defaults to 48322; container port remains 8080.
Preserve .env values, existing MCP entries, unrelated Docker services, and persistent volumes.
Use reported MCP URL. For terminal fallback, use scripts/mcp.py; inspect live tool schemas.
Never treat successful setup as successful design validation.
Create a new project under /workspace/<project>; preserve led-demo and other projects. Confirm circuit requirements, supply voltage, components, board size, connectors, and manufacturing rules. Use list_toolboxes and load_toolset to discover tools. Open target PCB in PCB Editor before live IPC changes. Close Schematic Editor before file-based schematic changes, then reopen. Complete schematic, footprints, placement, and routing. Run full ERC and DRC, including schematic parity and excluded findings. Resolve findings or list each remaining finding. Export native project, schematic PDF, board previews, Gerbers, and drill files to my computer. Do not claim manufacturing readiness from ERC/DRC alone.
Document tested platforms honestly. Do not add machine-specific paths or private network dependencies.
Keep vendored licenses and source attribution intact.
