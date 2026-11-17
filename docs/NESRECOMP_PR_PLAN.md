# NESRecomp contribution plan — 2026-11-17

Start with a focused experimental Nintendo Switch platform PR, followed by
independently reviewable shared-core improvements. The cumulative development
patch contains several contributions and should not become one undifferentiated
PR. This document plans the extraction; no PR or rebase has been performed.

## Counted scope

Counts below are the exact contents of `patches/nesrecomp-switch.patch`, SHA-256
`d6fffebd8599fd2770f1b1df36f29c0d67b359c0cd458b3a94ecb15390181b2f`,
against pinned upstream `ab3579725ae129b0e04fa2095d7e7dd38ac096b7`.
They include committed and uncommitted engine work, but exclude this workspace's
game recipes, deployment tools and research notes. Each path appears once.

| Area | New files | Modified files | Lines added | Lines removed |
| --- | ---: | ---: | ---: | ---: |
| Switch implementation | 3 | 0 | 744 | 0 |
| Switch guide and test | 2 | 0 | 488 | 0 |
| Shared runtime/core | 3 | 11 | 658 | 32 |
| Shared build and code generation | 1 | 5 | 172 | 4 |
| Shared tests | 6 | 4 | 474 | 20 |
| Other documentation, reference tools and repo config | 6 | 3 | 291 | 3 |
| **Total** | **21** | **23** | **2,827** | **59** |

Thus the Switch-specific contribution is **five new files**, of which three
are implementation files. It also needs narrow modifications to existing
platform-selection and host files. Those modifications are classified in the
shared rows above; the port is not completely additive.

The eleven modified runtime/core files are not all hardware algorithms. Six
are hardware-execution files or headers: `hw.h`, `hw_internal.h`,
`hw_machine.c`, `hw_ppu.c`, `hw_apu.c`, `ppu_hle_kernel.h` (**465 additions,
28 removals**). The other five concern the host, replay and state/file handling.
Line counts do not measure semantic risk: relatively small IRQ or PPU changes
still need detailed correctness review.

### New Switch files

- `runner/switch/host.c`: SDL display, controller input, audio, pacing,
  lifecycle, optional diagnostics and comparison harness; 661 lines.
- `runner/switch/switch.cmake`: devkitPro/SDL2 target setup, NACP/NRO/RomFS
  packaging and build settings; 62 lines.
- `runner/switch/diagnostics.c`: platform diagnostics adapter; 21 lines.
- `docs/SWITCH.md`: 281 lines.
- `tools/cyc/test_switch_host.py`: original synthetic cartridge / SDL contract;
  207 lines.

### Shared runtime/core

New: `cyc_profile.h`, `cyc_profiler.c`, `cyc_profiler.h` under `runner/cyc/`.

Modified under `runner/cyc/`: `cyc_fds_save.inc`, `cyc_host.c`, `cyc_host.h`,
`cyc_replay.c`, `cyc_state.c`, `hw.h`, `hw_apu.c`, `hw_internal.h`,
`hw_machine.c`, `hw_ppu.c`, `ppu_hle_kernel.h`.

### Shared build and generation

New: `runner/cyc/profile.cmake`.

Modified: `runner/cyc/CMakeLists.txt`, `runner/cyc/cyc.cmake`,
`runner/cyc/project.cmake`, `runner/cyc/project/CMakeLists.txt`,
`tools/cyc/prepare_project.py`.

### Shared tests

New: `runner/cyc/tests/masked_irq_probe.c`, `pal_interval_probe.c`,
`profiler_selftest.c`; `tools/cyc/test_cyc_profiles.py`, `test_masked_irq.py`,
`test_pal_intervals.py`.

Modified: `runner/cyc/tests/native_interval_probe.c`, `ppu_kernel_selftest.c`,
`raster_interval_probe.c`; `tools/cyc/test_raster_intervals.py`.

### Other documentation and reference tooling

New: `docs/ARM_SPRITE_KERNELS.md`, `CORE_PROFILER.md`, `CYCLE_PROFILES.md`,
`PAL_CLOCK.md`; `tools/cyc/mesen_shot/README.md`, `build.sh`.

Modified: `.gitignore`, `runner/cyc/PROJECTS.md`,
`tools/cyc/mesen_shot/mesen_shot.cpp`.

## Recommended PR boundaries

### 1. Experimental Nintendo Switch cartridge runner

Proposed title: **Add an experimental Nintendo Switch SDL runner for cycle games**.

Deliver direct per-game NRO launch, controls, original-rate pacing, audio,
private SD paths, SDK packaging and basic diagnostics. Keep saves disabled by
default, as in the tested package. Document the current vanilla-cartridge
scope and its limitations. Include the original synthetic host test and
reproducible SDK build instructions.

Extract the five new Switch-specific files and the necessary platform glue:
`.gitignore`, `cyc.cmake`, `project.cmake`, `cyc_host.c`, `cyc_replay.c` and
`cyc_fds_save.inc`. Register the test in `runner/cyc/CMakeLists.txt` if that
fits upstream's preferred test organization. This is an estimated **11–12
files: five new, six or seven modified**, before review/rebase changes.

Do not copy the current 661-line host verbatim into this first PR: its
comparison-policy setters depend on our unmerged core optimizations, and it
includes the new profiler API. Extract the functional runner and basic metrics;
move the optional profiler and policy-comparison integration into their
respective follow-ups. The older port commits are extraction aids, not
ready-to-submit patches: they predate the save-disable fix and later validation.

This platform PR need not modify the PPU/APU hardware algorithms. Consequently,
its performance on current upstream must be measured independently; the local
0.2.11 result belongs to the combined optimized source, not to the isolated port.

### 2. Shared performance improvements, in small independent PRs

- **AArch64 NEON sprite kernels:** small architecture-specific implementation
  behind the existing kernel interface; retain portable/SSE2 paths and exact
  differential tests. This benefits supported ARM desktop targets as well.
- **Masked-IRQ native intervals:** preserve CPU IRQ-mask changes, interrupt
  polling, DMA boundaries and restored-state pointer invalidation. Adapt to
  upstream's updated interval/APU design before comparing performance.
- **NTSC sprite-fetch specialization and grouping:** keep the two steps as
  separate reviewable commits, with coupled/interval/grouped comparisons and
  observer fallbacks. Their dependency order is specialization, then grouping.
- **PAL scheduling and batching:** constant-phase scheduling, PAL native
  intervals and grouped raster output in dependency order, with all five PAL
  phases and regional emphasis handling tested. Split further if requested.

Each performance PR carries its own synthetic tests, correctness evidence and
balanced measurements against its actual upstream parent. Existing isolated
patches and archived source identities provide starting points. Keep Switch
benchmark-harness integrations out of platform-independent algorithm commits.

### 3. Optional tooling and API contributions

Submit separately when useful to maintainers: the default-off sampled profiler,
Mac/PAL Mesen reference tools, and checked hardware profiles/static extension
API. The profile API is not necessary to land the basic platform port; defer it
if upstream prefers a smaller API surface. Likewise, isolate the generic
`fclose` error-propagation correction from platform plumbing.

The automatic comparison harness can follow the core policies it actually
uses, or be redesigned around generic policy registration in a separate change.
Avoid introducing that extra abstraction solely to shorten the first PR.

## Current upstream compatibility

A read-only upstream inspection/fetch on 2026-11-17 resolved `origin/master` to
`3f7421c45745f46b6f6d5b2cbd3be7783e26d24e`. It has no `runner/switch/` directory.
The source comparison above is still against our pinned base, not this newer
upstream; final PR diff counts will change during integration.

A temporary Git index loaded the new upstream tree and checked the complete
patch without changing the working tree or real index. The check reports seven
files that no longer apply cleanly: `runner/cyc/CMakeLists.txt`, `cyc_state.c`,
`hw.h`, `hw_apu.c`, `hw_internal.h`, `hw_machine.c`, and `hw_ppu.c`.

Upstream now has event-driven APU work, DMC deadline admission, native-picture
experiments and revised interval/counter ownership. The main hardware/state
files have changed substantially. A patch failure is not proof of a semantic
conflict, but it means the full development patch is not ready to submit as-is.
The shared optimizations require individual comparison, integration and renewed
qualification; some may overlap or interact with upstream's newer work.

## Preparation and acceptance

1. Preserve our working 0.2.11 engine/package and its archived tests.
2. Create fresh contribution branches from an identified current upstream
   revision; extract the platform PR first without altering our working port.
3. Build the platform-only SDK target and run its synthetic no-save SDL test;
   verify ordinary desktop builds remain unchanged.
4. Integrate each shared optimization separately. Re-run its timing/state/PCM
   tests and measure against the new parent before retaining it.
5. Record actual standalone and combined hardware results separately. Current
   evidence is 66.62 FPS uncapped for selected Mario gameplay, with all six
   states matching; it does not qualify every scene, suspend behavior, storage
   writes, widescreen or normal-play audio quality.
6. Prepare titles/descriptions around final scope and evidence. No ROMs,
   generated game code, extracted assets, private replay captures or NROs belong
   in engine PRs. Game modules, version/deploy/mise policy and Wi-Fi sender
   orchestration remain in this workspace.

Widescreen has only been assessed; no widescreen integration is in these counts.

## Reproduce the inventory

```sh
git apply --summary patches/nesrecomp-switch.patch
git apply --numstat patches/nesrecomp-switch.patch
```

These commands only inspect the patch. Ordinary `git diff` from the engine's
current HEAD misses earlier committed port changes and untracked additions,
so it is not the correct source for this cumulative inventory.
