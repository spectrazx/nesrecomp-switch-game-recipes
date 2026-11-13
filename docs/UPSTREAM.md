# Notes for future NESRecomp contributions

No PR has been opened. Keep contributions local until console behavior and
performance are satisfactory, then review and rebase against upstream.

## Patch ownership and proposed PR boundaries

The pinned NESRecomp base is `ab3579725ae129b0e04fa2095d7e7dd38ac096b7`.
The local branch `codex/switch-runner` has the original port commit
`4eed78d9d6abf60c651942bc3e60f1762370133d` and performance follow-up
`a4e9f74109067dc5105c1059322efc264d436b75`. The modular architecture is
committed locally as `d248afef21bc80631f53a44c9ebb6efcb2147dd2`, exported
with the patches below.

The subsequent platform fix `8eeb9523344254d66a5ed5ff88661d9d9736bf3b`
makes the runtime banner use the same version as the NACP. Its original-fixture
host test checks that a caller-supplied version reaches the startup log. Per-game
`VERSION` files, automatic patch increments, build manifests and SD deployment
remain workspace policy, outside the engine. `mise run copy` exercised this
workflow and deployed/verified version `0.2.1`; six synthetic unit tests cover
incrementing, invalid versions, stale manifests and build/copy/mount failures.

- **Generic profiles and static build extensions:** `runner/cyc/profile.cmake`,
  `cyc_profile.h`, additive arguments on `nesrecomp_add_cycle_game`, standalone
  cache options, an early startup contract check, original-fixture tests and
  `docs/CYCLE_PROFILES.md`. This API has no Switch dependency or game names.
- **Switch platform port:** `runner/switch/`, narrow platform selections in
  the cycle host/build, diagnostics and platform tests. Saving remains disabled
  by default pending the observed SD-write failure; full speed and suspend
  qualification remain open.
- **Performance fixes:** keep subsequent algorithm changes separate, each with
  before/after measurements and timing, pixel, audio and state comparisons.
  Shared PPU improvements belong upstream even if first measured with Mario.
- **Game recipes:** this workspace's `games/`, generic build launcher and private
  ROM verifier stay outside the engine. Propose a title-repository contribution
  only if appropriate after the upstream API settles. The Mario checkout is
  currently unchanged.

`patches/nesrecomp-switch.patch` is the complete reproducible delta against the
pinned base. `patches/nesrecomp-profiles.patch` isolates the generic architecture
delta against the local 0.2 commit. It also applies cleanly to the pinned
upstream base, where its synthetic test passes without the Switch port.
It is a review aid, not a second patch to apply after the complete patch.
These exports contain no ROM, extracted assets,
generated game C or compiled artifacts. Retain upstream licensing for engine
changes; title module work must not redistribute commercial game content.

## API review points

The default profile is `generic`; existing callers and desktop defaults retain
their behavior. The initial `nrom-ntsc` profile publishes checked constraints,
without adding execution shortcuts or removing runtime correctness checks.
The same recompiler cartridge decoder used for generation qualifies the board.
Configure rejects incompatible board/timing selections; startup also checks
the loaded cartridge and effective region before saves or gameplay begin.

Static modules are opt-in trusted CMake code, with target-scoped sources and
definitions. There is no new runtime plugin system, hot-loop dispatch or
routine-replacement ABI. Tests exercise two targets in one build so flags and
module lists cannot silently leak into an unrelated game. A future runtime
extension needs a concrete use case and explicit bus-cycle/state guarantees.

The Switch frontend's existing restrictions remain. This change does not route
title optimizations through `HOST_EXTRAS` or enable gameplay mods on Switch.

## Reproduce the architecture checks

From the workspace root, after preparing the sources:

```sh
python3 scripts/build-game.py smb1 --rom .local/roms/SMB.nes
python3 games/smb1/tests/verify.py --rom .local/roms/SMB.nes
python3 scripts/build-game.py smb1 --rom .local/roms/SMB.nes --host-only --variant optimized
python3 games/smb1/tests/verify.py --rom .local/roms/SMB.nes --variant optimized
python3 .local/src/nesrecomp/tools/cyc/test_cyc_profiles.py \
  --recompiler build/recompiler/NESRecomp --out build/refactor/profiles --generator Ninja
python3 .local/src/nesrecomp/tools/cyc/test_cyc_project.py \
  --out build/refactor/existing-project --generator Ninja
python3 scripts/inspect-nro.py build/games/smb1/SuperMarioBrosRecomp.nro
```

The new synthetic profile test is also registered as CTest `cyc_profiles` in
the engine's standalone cycle test project and supports its existing nested
toolchain harness. It requires no commercial ROM or SDL window. It compares
generic/qualified frame hashes, checks per-target build flags and rejects
unknown profiles, missing modules, wrong boards, PAL selections, unsupported
console metadata and a changed program image. The existing project test covers
ROM/config/seed regeneration, wrong-ROM rejection and source-tree isolation.

Mario's route checks all 1,800 frame hashes against interpreter execution,
1,199 resumed frames and final pixels. The available TriCNES oracle separately
checks CPU trace, registers, memory and raw pixel indices. Its internal hardware
hash and RGB palette differ, as recorded before this refactor; do not claim
those outputs are identical. Untraced optimized-path frame logs, PCM and PNG
are compared separately with the retained 0.2 artifacts.

Detailed local evidence is under ignored `build/refactor/` and
`build/games/smb1/`; historical physical-console results remain under
`build/smb1/hardware-v2/`. Do not infer console performance from desktop speed.

Recorded refactor results (2026-11-13):

| Check | Result |
| --- | --- |
| Existing project regeneration/default behavior test | Passed |
| New synthetic profile/module test, direct and CTest | Passed |
| Generic contribution alone on pristine pinned upstream | Patch applied; synthetic test passed |
| Mario baseline and optimized routes | Both passed native/interpreter, oracle CPU/memory/raw-pixel and state-continuation checks |
| Baseline versus retained pre-refactor frame hashes | All 1,800 records identical |
| Generated game C versus retained pre-refactor output | All nine units identical |
| Optimized untraced frame records, WAV and PNG versus 0.2 | Byte-for-byte identical |
| Switch Docker cross-build and NRO/NACP inspection | Passed; HLE, LTO, `-O3`, saves OFF |
| Generic ROM verifier and unknown title | Correct fixture accepted; wrong CRC/mapper and unknown title rejected |
| Original ROM and upstream Mario checkout | Unchanged |

The native Mac devkitPro path is retained but not exercised: this machine uses
the pinned Docker SDK. No new SD deployment or physical-console playtest was
performed for this structural change.

## Export updates

New source files must be visible to `git diff` before export (`git add -N` is
sufficient). The cumulative patch is required by `scripts/prepare-sources.sh`:

```sh
git -C .local/src/nesrecomp diff --binary \
  ab3579725ae129b0e04fa2095d7e7dd38ac096b7 > patches/nesrecomp-switch.patch
```

Before a future PR, refresh the pinned upstream checkout deliberately, rebase
the relevant changes, rerun the applicable checks and state the hardware limits
in the PR description. Do not include build outputs or private ROM-derived
files as evidence in a public PR.
