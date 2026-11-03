# Validation

## Native builds — 2026-11-03

[Linux amd64 workflow](https://github.com/RexSpex/agent-tool-kicad/actions/runs/41694761878) validates native amd64 packaging on Ubuntu 24.04.
Docker Desktop 4.91.0 (Docker Engine 29.8.0) on macOS Apple Silicon validates native Linux arm64 packaging.
KiCad 10.0.8, Konnect 0.13.0, FreeRouting 2.3.0, and Java 25 run in both builds.
ARM64 compiles unchanged Konnect source with pinned Rust 1.96.0; amd64 verifies release archive checksum.

Checks cover build, healthy startup, desktop redirect, VNC handshake, MCP discovery,
live PCB IPC, foreign-Origin rejection, and FreeRouting native MCP integration.
Fresh sample workflow creates schematic, synchronizes PCB, routes six tracks,
repairs managed demo, exports files, and reads saved board independently.
Board measures 25 × 17 mm with three footprints. Full ERC and DRC report zero
errors, warnings, missing connections, and schematic parity differences.
Ten Gerber/job/drill files plus PCB PDF/SVG and schematic PDF/PNG are produced.
Project and clean checks survive container recreation. Terminal MCP client calls
installation info and FreeRouting checks. Eight Python tests cover setup safeguards,
JSON/SSE negotiation, sessions, nested errors, image artifacts, and ARM64 disk preflight.

Default host port is 48322. Setup selects another free port when occupied,
saves selected port in .env, and caps CPU limit to available Docker CPUs.
Native ARM64 validation also runs successfully on automatically selected port 48323.
Container port remains 8080. Builds need 12 GiB free host disk for amd64,
or 20 GiB for native ARM64 source compilation. Setup verifies FreeRouting automatically.
Routing HTTP timeout defaults to two hours and remains configurable.

Windows is not tested. Native harness configuration remains client-specific;
terminal MCP client is tested. Software checks do not establish physical circuit performance.

## Earlier validation — 2026-10-15

Linux amd64; Docker Engine and Compose v2.40.3.
KiCad 10.0.7; Konnect 0.13.0, commit
6bbe3e4f890ba1d37c0e5d5f38ccd03d90958c9e.

## Small board

25 × 17 mm board, three footprints, six pads, three nets, six front copper
segments. J1 supplies VIN/GND; R1 is 330 ohms; D1 is an LED.

MCP creates the schematic, places library symbols, assigns footprints, connects
pins to named nets, plans and applies schematic-to-PCB synchronization, places
and rotates footprints, refreshes library content, routes traces, saves, checks,
and exports. Every PCB placement/pad readback reports live IPC.
Native Ctrl-Z restores an MCP placement. No schematic editor writes concurrently.

- Unwired schematic: ERC detects six disconnected pins.
- Connected schematic: ERC reports zero errors and zero warnings.
- Unrouted PCB: DRC detects three missing connections.
- Routed PCB after native repair: zero ERC/DRC errors or warnings, zero missing
  connections, and zero schematic parity differences.
- Exports: ten Gerber/job/drill files, PCB PDF/SVG, schematic PDF/PNG.
- Independent `pcbnew` saved-file readback verifies pad nets, component count,
  board dimensions, track count, reports, and nonempty exports.
- Browser screenshot verifies visible routed board in noVNC.

## Resolved demo warnings

Initial raw MCP workflow leaves three missing PCB Description fields and a
resistor footprint mismatch. Native comparison identifies both R1 pads as
1,024,999 nm wide, while stock library requires 1,025,000 nm. Height is unchanged.

`scripts/clean_demo.py` repairs only these proven demo defects while the desktop
is stopped. It takes the workspace ownership lock, obtains Description fields
from KiCad's schematic netlist, and restores exact library pad widths through
KiCad's native API. It checks a private candidate with full ERC/DRC before atomic
replacement and retains a content-addressed original board backup.

Both checks use `--severity-all --exit-code-violations`; DRC also uses
`--all-track-errors --schematic-parity`. All findings, including excluded items,
are empty. Schematic and project/rule bytes remain unchanged. Placement, routing,
UUIDs, outline and pad nets remain unchanged. MCP checks after reopening also
report zero errors, warnings, unrouted items and parity differences.

This repairs the acceptance board, not Konnect's general synchronization code.
Future Konnect edits may recreate these defects. Do not apply this narrow helper
to arbitrary boards. Electrical rule cleanliness does not prove physical circuit
performance.

KiCad's legacy Python board readback also emits three enum-choice assertion
messages while completing successfully. CLI DRC and live IPC remain separate
acceptance evidence. Native ARM64 and Docker Desktop are untested.

## Desktop and boundary checks

Root redirect, noVNC HTTP, VNC WebSocket upgrade/RFB handshake, MCP initialization,
tool discovery, exact Konnect build, and live board access pass. Foreign MCP
browser Origin is rejected with HTTP 403.

Fresh volumes start without setup dialogs. Bootstrap supplies standard symbol
and footprint tables, an empty design-block table, API enablement, and answered
update/privacy prompts. No client credentials or guidance are installed.

A workspace flock prevents a second managed container from becoming a writer.
Under that lock, startup clears only stale cad-owned locks for the managed demo.
Readiness requires an open PCB answering IPC; a listening socket alone
is insufficient. Tests preserve project bytes across container replacement.

## Reproduce

Start a fresh Compose project with an unused loopback port. Run:

```bash
python3 tests/smoke.py http://localhost:48322
python3 tests/build_demo.py http://localhost:48322
python3 tests/route_demo.py http://localhost:48322
docker compose stop
docker compose run --rm --no-deps -T --entrypoint python3 kicad - < scripts/clean_demo.py
docker compose up -d --wait
python3 tests/verify_clean.py http://localhost:48322
docker compose exec -T kicad python3 - < tests/verify_saved.py
docker compose up -d --force-recreate --wait
python3 tests/smoke.py http://localhost:48322
docker compose exec -T kicad python3 - < tests/verify_saved.py
```

Creation scripts require the untouched demo. Repeated read-only smoke/readback
checks verify persistence without replacing the design.

## Packaging scope

Default Compose uses named volumes, host loopback, and no external network.
Deployment-specific overrides and operational records live outside this package.
Source is available in the repository linked from README. No CI pipeline result
is claimed; validation above records direct container and tool checks.
