# Roadmap

Where Konnect is going, in the order the work actually depends on itself.
No dates — items ship when they survive verification. Opening an issue is the
best way to influence priority; several of the largest items below exist
because a contributor measured something we had not.

This roadmap reflects `upstream/main` after v0.11.0. Release notes describe
what shipped in a particular version; this file describes the remaining user
outcomes, their dependencies, and the evidence required to call them complete.
The priorities are informed by
[@neusse's improvement backlog](https://github.com/mixelpixx/Konnect/discussions/165)
and benchmark reports
([#239](https://github.com/mixelpixx/Konnect/discussions/239),
[#295](https://github.com/mixelpixx/Konnect/discussions/295), and
[#224](https://github.com/mixelpixx/Konnect/discussions/224)).

## 1. Truth and write-safety (the standing doctrine)

Every response field derives from the **result**, never from the request. A
verdict without evidence is `INCOMPLETE`, never approval. Fixtures come from
real KiCad output. New guards must be neutralized once to prove their regression
tests fail, and an unavailable check is `BLOCKED`, never a silent pass.

Current Priority 0 work:
- **Exact live-board identity**
  ([#384](https://github.com/mixelpixx/Konnect/issues/384),
  [#390](https://github.com/mixelpixx/Konnect/pull/390)) — bind each generic
  IPC operation to the exact typed document selected for the request. This is
  the foundation for later editor navigation.
- **Fail-closed open-board classification**
  ([#426](https://github.com/mixelpixx/Konnect/issues/426)) — if any open PCB
  document path cannot be resolved, refuse direct-file mutation instead of
  treating the requested board as safely closed. Rebuild PR #407 on current
  `main` with negative and live-KiCad evidence.
- **Cold-start stale-board evidence**
  ([#385](https://github.com/mixelpixx/Konnect/issues/385),
  [#391](https://github.com/mixelpixx/Konnect/pull/391)) — after exact board
  binding lands, use only the requested board's KiCad lock as a conservative
  write veto. Lock absence is never positive proof that a file fallback is safe.
- **Committed schematic readback**
  ([#387](https://github.com/mixelpixx/Konnect/issues/387),
  [#394](https://github.com/mixelpixx/Konnect/pull/394)) — rebuild the final
  stacked change on current `main` so mutation responses report committed state.
- **Authoritative DRC sequencing**
  ([#408](https://github.com/mixelpixx/Konnect/issues/408)) — refill zones and
  establish save/read ordering before reporting DRC evidence.
- **Physical clearance truth**
  ([#410](https://github.com/mixelpixx/Konnect/issues/410)) — report copper and
  pad clearance rather than footprint-origin distance.
- **Type-safe PCB deletion**
  ([#412](https://github.com/mixelpixx/Konnect/issues/412)) — a trace operation
  must not delete a via or zone merely because its UUID exists.

Completed foundations include structured required-argument validation,
lossless zone and footprint parsing, proven project ownership (#189),
process-lifetime stale-board refusal (#240), non-mutating startup (#242),
verified fresh export artifacts (#252), and structural replacement of the
remaining indentation-sensitive schematic scans (#84).

## 2. Schematic correctness and editability

- **Bus-aware connectivity**
  ([#328](https://github.com/mixelpixx/Konnect/issues/328)) — extend the shared
  connectivity model through buses and bus entries without treating visual
  contact as electrical proof.
- **Move the connected region**
  ([#315](https://github.com/mixelpixx/Konnect/issues/315)) — move symbols,
  wires, labels, and junctions as one verified closure instead of leaving wires
  behind or reporting an unobserved success.
- **Editable component metadata**
  ([#258](https://github.com/mixelpixx/Konnect/issues/258),
  [#360](https://github.com/mixelpixx/Konnect/issues/360), and
  [#415](https://github.com/mixelpixx/Konnect/issues/415)) — support custom
  fields, carry useful catalog metadata into placed symbols, and expose DNP
  state through a result-verified contract.
- **Diff-preserving writes**
  ([#210](https://github.com/mixelpixx/Konnect/issues/210)) — avoid rewriting
  an entire sheet's formatting for a local edit.

Multi-unit read behavior (#182), junction maintenance on move/delete (#120),
hierarchical ownership, sheet-instance placement, and connectivity-preserving
component deletion are complete on `main`.

## 3. PCB analysis, placement, and imported designs

- **Pad geometry in inspection results**
  ([#409](https://github.com/mixelpixx/Konnect/issues/409)) — expose observed
  pad size, shape, and rotation so placement and clearance reasoning does not
  have to guess.
- **Placement intent without false positives**
  ([#411](https://github.com/mixelpixx/Konnect/issues/411)) — distinguish a
  connector/interface filter capacitor from misplaced IC decoupling using
  narrow, testable evidence.
- **Footprint-owned mechanical geometry**
  ([#351](https://github.com/mixelpixx/Konnect/issues/351) and
  [#413](https://github.com/mixelpixx/Konnect/issues/413)) — recognize valid
  footprint-owned outlines and cutouts during analysis and DRC classification.
  Automatic destructive promotion remains deferred to a coherent import-
  normalization workflow.
- **Placed-footprint 3D models**
  ([#305](https://github.com/mixelpixx/Konnect/issues/305)) — add a safe model
  editing contract after the current footprint-library refresh work is stable.
- **Exact graphic selection**
  ([#225](https://github.com/mixelpixx/Konnect/issues/225)) — address one
  footprint graphic without using its layer as an ambiguous selector.

## 4. Autorouting: complete the supported workflow

The native Freerouting bridge is now implemented. The supported sequence is:

1. `check_freerouting`
2. `export_specctra_dsn`
3. `route_specctra_dsn`
4. `plan_specctra_ses_import`
5. `apply_specctra_ses`

Konnect exports a revision-bound DSN and manifest, drives the discovered local
Freerouting JAR through its headless MCP server, validates the returned SES,
and applies it through KiCad IPC with committed readback and DRC evidence. The
former `autoroute` contract and the implementation gap tracked by #253/#337 are
closed.

Remaining work is operational evidence rather than another routing API:
exercise this sequence in the real-KiCad release benchmark, retain the known
geometry limitations in release notes, and expand the KiCad-authored fixture
corpus when a real board exposes an unsupported construct.

## 5. IPC context and semantic editor navigation

- **Socket discovery and provenance**
  ([#382](https://github.com/mixelpixx/Konnect/pull/382) and
  [#419](https://github.com/mixelpixx/Konnect/issues/419)) — settle startup
  discovery first, then report which configuration and IPC source actually
  controlled the running process.
- **Open a requested editor context**
  ([#256](https://github.com/mixelpixx/Konnect/issues/256)) — launch a specific
  board and return the exact observed IPC endpoint instead of assuming one.
- **Semantic Navigation MVP**
  ([#395](https://github.com/mixelpixx/Konnect/issues/395)) — after #390,
  introduce the approved five-operation sequence for state, selection,
  resolution, verified selection mutation, and read-only cross-probe resolution.
  Activation/reveal is deferred until a supported KiCad API can execute and
  verify it; raw actions and UI automation are not the product contract.

## 6. Client, workflow, and guidance compatibility

The compact client surface and eager-toolset documentation closed the immediate
VS Code and Linux client reports (#325 and #233). Keep testing clients that do
not refresh `tools/list`, and preserve independent Claude and Codex guidance
review paths.

The bundled skills and agents must teach the same evidence hierarchy as the
tools: KiCad ERC/DRC outrank summaries, one owner controls a live board,
Freerouting follows the supported five-step sequence, and custom parts require
a physical pin map. Advanced library-generation controls
([#296](https://github.com/mixelpixx/Konnect/issues/296)) should extend that
workflow without making prompts a substitute for validation.

## 7. Platform and KiCad-forward

- **Server lifecycle ownership**
  ([#103](https://github.com/mixelpixx/Konnect/issues/103)) — track and reap
  only servers whose owning launcher is gone; do not kill another live session
  or an independently managed MCP server.
- **KiCad 11 readiness**
  ([#257](https://github.com/mixelpixx/Konnect/issues/257)) — replace every
  remaining SWIG-dependent ActionPlugin responsibility before the bindings are
  removed, with tested IPC or executable-plugin equivalents.
- **KiCad compatibility regressions**
  ([#406](https://github.com/mixelpixx/Konnect/issues/406)) — reproduce the
  reported interactive-router layer behavior with a controlled plugin/no-plugin
  matrix before changing code.
- **macOS distribution**
  ([#131](https://github.com/mixelpixx/Konnect/issues/131), then
  [#154](https://github.com/mixelpixx/Konnect/issues/154)) — establish signed,
  stable artifacts before adding a Homebrew tap.

Per-user Windows discovery (#254) is complete. Official KiCad PCM publication
remains a distribution objective after release identity and lifecycle behavior
are stable.

## 8. The quality flywheel

- Repair the live-test contract
  ([#221](https://github.com/mixelpixx/Konnect/issues/221)): documentation must
  name a real job, and the KiCad-authored fixture must pass the test it claims.
- Run the full local gate after every merge, then the real-KiCad E2E, live IPC
  tests, and end-to-end benchmark before a release.
- Grow a real-KiCad fixture corpus for every parser and transform boundary.
- Keep issue-to-PR closure accounting explicit: partial PRs use `Part of #N`;
  exactly one terminal PR uses `Closes #N` after satisfying all acceptance.
- Keep generated tool counts authoritative through `cargo xtask fix-doc-counts`.

## Done (eras, not items)

- ~~v0.1-v0.3~~ — broad schematic, PCB, library, export, transport, and
  cross-platform packaging foundations.
- ~~v0.4-v0.7~~ — atomic PCB transfer, footprint graphics, client-scoped
  installs, and the first truth-and-safety enforcement arc.
- ~~v0.8-v0.11~~ — structured installation provenance, project ownership,
  hierarchical schematic correctness, executable guidance evidence, the native
  Specctra/Freerouting bridge, and safer stale-file fallback behavior.
