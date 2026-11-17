# Notes for future NESRecomp contributions

The [2026-11-17 PR plan and file inventory](NESRECOMP_PR_PLAN.md) counts the
complete contribution against our pinned base, proposes a focused platform PR
and separate core changes, and records compatibility with newer upstream.

[Grouped sprite fetches](SPRITE_FETCH_JOBS.md) follow the 0.2.10 sprite-fetch
specialization. The core/test and frontend comparison patches are
`nesrecomp-sprite-fetch-jobs.patch` and
`nesrecomp-switch-sprite-fetch-jobs-comparison.patch`. They apply after
`bf70e97b7c6a…`, preserving all three reference paths across 4,096 HLE/LLE cases.
Desktop process CPU falls another 8.13%; a direct comparison with rebuilt
0.2.9 source measures 26.13% less CPU for the combined changes. Both games'
captured output and Mario's demo remain exact. The six-leg Switch comparison
now passes: 62.72 → 66.62 FPS uncapped, 6.89% less emulation time, all states
matching desktop at 1.02 GHz. Normal paced play and listening remain pending.

[NTSC sprite-fetch specialization](MARIO_SPRITE_FETCH.md) is isolated in
`patches/nesrecomp-sprite-fetch.patch`, followed by the Switch policy comparison
in `patches/nesrecomp-switch-sprite-fetch-comparison.patch`. They apply after
`fe8c472c5982…`. New HLE/LLE sprite-fetch contracts and both games' exact
1,800-frame output comparisons pass. Desktop process CPU falls 18.93%; console
performance and listening verification are pending for Mario 0.2.10. No PR is
opened, and no game-specific code is added to the core.

[PAL eight-pixel rendering](PAL_RASTER_BATCHING.md) is isolated in
`patches/nesrecomp-pal-raster.patch`, followed by
`patches/nesrecomp-switch-pal-raster-comparison.patch`. They apply after the
0.1.8 source snapshot `f98804015bcc…`. The expanded PAL contract caught and now
covers the regional red/green emphasis swap, including background capture.
All 2,560 PAL and 4,096 existing NTSC raster cases pass, as do both games'
1,800-frame output comparisons and 903 Mesen pictures. The final build saves
22.58% desktop CPU; its six-leg Switch suite gains 29.29% throughput with all
states matching desktop at 1.02 GHz. Adventure Island 0.1.9 is promoted locally
and uploaded to its development entry. No PR has been opened.

[PAL native intervals](PAL_NATIVE_INTERVALS.md) are isolated in
`patches/nesrecomp-pal-intervals.patch`, followed by the regional comparison
runner in `patches/nesrecomp-switch-pal-comparison.patch`. They apply after the
held-IRQ/comparison snapshot `bb674c54036b…`. All five PAL phases on NROM/CNROM,
HLE/LLE timing tests, 1,800 untraced Adventure Island frame/audio records and
903 independent Mesen pictures pass. Desktop CPU falls 13.28%; a six-leg
Switch gameplay comparison gains 13.43% throughput with 12.21% less emulation
time and all states matching desktop at 1.02 GHz. Adventure Island 0.1.8 is
promoted locally and uploaded to the development entry. No game-specific code
is added to the core.

[Held IRQ batching](MASKED_IRQ_BATCHING.md) is isolated in
`nesrecomp-masked-irq.patch` after the PAL render-tail source snapshot. It
qualifies only settled masked APU frame IRQs and observes the CPU mask on each
cursor access; interrupt-boundary tests and LLE/HLE native-interval tests pass.
Mario's 1,800-frame neutral and gameplay outputs remain exact. Desktop CPU
reduction is 46.68% on the neutral route and 3.55% on the gameplay route;
two console suites verify a 74.73% demo throughput gain and unchanged active
gameplay throughput, with all 12 final states matching desktop at 1.02 GHz.
Mario 0.2.9 is promoted locally and uploaded to the development entry. The subsequent
`nesrecomp-switch-comparison-suite.patch` adds a six-leg automatic comparison,
in-memory state restoration and pad-route restart. The no-save SDL fixture
matches headless state in every leg. Core and frontend patches reconstruct the
exact as-built source through a temporary index; the real index is untouched.

The [stable PAL render-tail candidate](PAL_PPU_TAIL.md) is isolated in
`nesrecomp-pal-ppu-tail.patch` after the gameplay/replay snapshot. It removes
repeated PPU dispatch while preserving every device edge and sample position.
Its independent reference switch and differential CTest belong to the core.
Regional contracts, both 1,800-frame game comparisons, save continuation and
903 independent PAL reference pictures pass. Four BAAB console runs at observed
1.02 GHz show 2.69% less emulation time and 2.56% more throughput in the selected
gameplay window. Adventure Island 0.1.7 is promoted locally and uploaded to the
development entry. This is a separate shared performance contribution with no
title or Switch frontend dependency.

[Scripted gameplay profiling](GAMEPLAY_PROFILING.md) is isolated in
`nesrecomp-switch-gameplay-replay.patch` after the preceding sprite-benchmark
state. It connects Switch to the existing replay API, adds optional caller-owned
RomFS assets and configurable warm-up, and streams sampled reports without
altering guest state. Regular/profiled native controller fixtures match
headless execution; six console runs match their desktop final states. The
profiled FPS is explicitly separate from baseline performance. All engine
changes are also in the cumulative patch; source snapshots identify the
as-built experiments. Title input routes and asset staging stay in the workspace.

The opt-in [portable/NEON console experiment](SPRITE_AB.md) adds a neutral-input
benchmark mode to the shared Switch frontend. It discards a fixed 300-frame
warm-up, measures 600 frames, reports focus interruptions and computes final
state hashes outside measured time. Two native SDL fixture runs reach identical
states; both title routes match all 1,800 frame records and PCM/PNG output
between portable and automatic kernels. Four isolated Switch packages build.
Eight physical console runs complete the ABBA comparisons at observed 1.02 GHz,
with identical states within each title. Explicit NEON reduces emulation time
by 9.80% for Mario and 8.46% for Adventure Island on these demos; the existing
automatic selection is retained. This qualifies the earlier kernel change
without claiming a new speed fix. `nesrecomp-switch-sprite-benchmark.patch`
applies after the preceding isolated audio-diagnostics patch; applying both to
`56b9265` reconstructs the archived sprite-benchmark source snapshot. The cumulative patch
also includes both. Build flags, sender and comparison orchestration stay in
this workspace.

The uncommitted [Switch audio diagnostic follow-up](AUDIO_DIAGNOSTICS.md) is
isolated in `patches/nesrecomp-switch-audio-diagnostics.patch` against
`56b926508dea5d86fd4f58801afb2dfe30560be5`, and included in the cumulative patch.
It adds opt-in nxlink stdout logging while retaining the SD log, produced-audio
duration/queue observations, and read-only platform/CPU-clock reporting. It
changes no guest timing, renderer or playback policy. The native 1,900-frame
no-save contract passes, and both game packages cross-build. Mario 0.2.6 has
a successful live-console run showing audio starvation; Adventure Island
0.1.4 also has a successful run at 24.86 FPS, with stable 1.02 GHz CPU and full
application mode. Read-only clock reporting works on hardware. No speed fix or
audio-quality fix is claimed from the instrumentation.

The shared ARM sprite-kernel work (`8d2a8696ea31146fa4a3fced93795e36b36bb21a`) is isolated in
`patches/nesrecomp-arm-sprite-kernels.patch` against
`ccc34150f58f4e75f24cee03eb49fa187b27b29e`. It adds AArch64 NEON to the
existing HLE mask/shift interface, retains scalar/SSE2 implementations and
adds exhaustive lane-mask checks plus a forced-scalar full-machine reference.
All game/state/pixel/audio comparisons pass. Actual devkitA64-generated pure
kernel instructions are exercised in ARM64 Linux via the workspace test shim.
The Mac PAL route improves 4.80%; Mario's result is within measurement noise.
No physical speed claim or visual-glitch fix is made.

Separate reference-tool work (`56b926508dea5d86fd4f58801afb2dfe30560be5`) is
exported against the ARM commit in `patches/nesrecomp-mesen-pal.patch`:
explicit PAL/NTSC selection, optional read-only memory captures, and native
macOS building with an external MesenCE libretro checkout. The existing NTSC
default/Windows build remain. Test dependencies and private captures are not
included in either patch or game binaries. The workspace owns the calibrated
title route in `games/adventure-island/tests/reference.py` and documents the
reference revision, reproduction and uninstall in [REFERENCE_TOOLS.md](REFERENCE_TOOLS.md).
The new independent check matches all 903 requested PAL gameplay frames after
pre-input zero-page alignment. The user's visual report remains unresolved
outside that coverage; it is not dismissed as normal sprite flicker.

The PAL scheduler follow-up (`ccc34150f58f4e75f24cee03eb49fa187b27b29e`)
is isolated in `patches/nesrecomp-pal-clock.patch`,
against `20d35364da66dc9eaeb2252e45c25c1ce7df32d5`. It removes ordinary
master-tick dispatch using five constant divider-phase schedules, retaining
all device events and the original loop for partial cycles/reference builds.
It introduces no title-specific optimization or NTSC batching on PAL.
`cyc_pal_clock` compares both schedulers under identical PPU/APU implementations
at all nine NTSC/PAL alignments; region contracts and complete game outputs
also match. [Hardware and balanced desktop measurements](HARDWARE_0.2.3.md)
record the evidence and the pending console speed check. This is a separate
performance contribution from the earlier hardware-profile and profiler APIs.

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

Contribution `20d35364da66dc9eaeb2252e45c25c1ce7df32d5` adds optional shared device-clock sampling, default OFF,
with a host-injected monotonic timer and original-fixture tests. It is separate
from hardware contracts and per-title recipes. The Switch consumer reports
path estimates/raw means and effective region. Empty-scope calibration and a
median of nine sample-group means limit timer and scheduler-pause bias;
diagnostic overhead and statistical error remain explicit. No guest clock,
bus timing, renderer algorithm or state layout is changed.

`patches/nesrecomp-core-profiler.patch` isolates this follow-up against
`8eeb9523344254d66a5ed5ff88661d9d9736bf3b`; the complete patch still restores
the entire workspace contribution against the pinned upstream base. The new
Adventure Island module, PAL recipe, 892 entry-point seed addresses and its
tests stay in this workspace, with no title-specific code added to the engine.

Follow-up validation: CTest `cyc_profiler_test` checks calibration, randomized
sample counts, a deliberately huge scheduler outlier, reporting/reset and a
missing clock. The sampled Switch frontend passes 1,900 paced dummy-driver
frames without saves and emits real profile records. A sampled Mario optimized
run preserves all 1,800 retained untraced frame records, WAV and PNG. Both PAL
Adventure Island variants match native/interpreter execution, 599 resumed
frames, and each other's untraced raw frames/PCM/PNG. Existing project and
deployment tests pass. The NTSC-only local TriCNES adapter is not claimed as
a PAL oracle. Switch package versions/flags and copied SHA-256 hashes are
verified; new physical-console speed results are not yet available.

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
