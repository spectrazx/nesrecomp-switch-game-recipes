# NESRecomp Switch prototype — 2026-11-13

The subsequent [modular architecture](ARCHITECTURE.md) separates game recipes
under `games/` from the Switch frontend and adds opt-in shared hardware
contracts/static build modules. [Upstream contribution notes](UPSTREAM.md)
record the scope, validation and future PR boundaries. These additional source
changes are committed locally as `d248afef21bc80631f53a44c9ebb6efcb2147dd2`
and included in the cumulative patch below.
Canonical new outputs use `build/games/smb1/`; paths below describe the retained
0.1/0.2 evidence and compatibility commands.

The latest packaging follow-up is **0.2.1**, built and copied through
`mise run copy`. Versions now come from `games/smb1/VERSION` and advance after
a verified deployment; the NACP and runtime banner agree. This is a versioning
change, with no additional speed improvements or new console qualification.

Current follow-up: [0.2 performance build with saving disabled](PERFORMANCE_V2.md).
The original 0.1 contribution, 0.2 follow-up and modular architecture are
committed locally; the exported patch contains all changes against the upstream base.

Implemented in the local NESRecomp checkout at
`.local/src/nesrecomp`, branch `codex/switch-runner`. The reviewable and
reproducible contribution is [patches/nesrecomp-switch.patch](../patches/nesrecomp-switch.patch),
including its upstream `docs/SWITCH.md`. The Mario checkout is unchanged.
The NESRecomp contribution is committed locally as
`8eeb9523344254d66a5ed5ff88661d9d9736bf3b` (`codex/switch-runner`), following
the architecture `d248afef21bc80631f53a44c9ebb6efcb2147dd2`,
0.2 `a4e9f74109067dc5105c1059322efc264d436b75` and original
`4eed78d9d6abf60c651942bc3e60f1762370133d` commits.
The parent workspace records the exported patch, scripts and results in its
own local commit. No PR, remote write or publishing has been performed.

## Revisions

| Source | Base revision |
| --- | --- |
| mstan/nesrecomp | `ab3579725ae129b0e04fa2095d7e7dd38ac096b7` |
| mstan/SuperMarioBrosNESRecomp | `de443b01e2707c768be1729970f99d2f9da6bec3` |

`bash scripts/prepare-sources.sh` restores these checkouts and applies the
patch, or verifies it is already applied. It accepts the pinned base or the
local contribution commit and refuses other revisions. The prompt and parent repository are separate from
the upstream contribution; all cloned sources, SDK build outputs, ROMs and
generated C remain under ignored local directories.

## Implemented

- `runner/switch/switch.cmake`: devkitPro toolchain integration, required SDL,
  per-game SD path and metadata, NACP/NRO packaging using official SDK helpers.
- `runner/switch/host.c`: SDL video/audio/input, automatic resume, quick save/load,
  checkpointing, exit/focus notifications, visible fatal errors on Switch.
- `runner/switch/diagnostics.c`: a small log adapter that avoids desktop process,
  crash-reporting and `/proc` assumptions.
- Narrow changes in the cycle host/build files select this platform, retain the
  existing single `main`, keep ROM identity checks, route battery saves to SD,
  and disable replay recording and desktop UI on Switch.
- Save-state writes now check `fclose` as well as `fflush` before replacing the
  previous state, so close errors do not count as a successful write.
- `tools/cyc/test_switch_host.py`: original NROM fixture, native SDL dummy tests
  and a prepared cross-build harness using the Mac-generated C.

## Results

| Check | Result |
| --- | --- |
| Native Mac compiler configure/build | Passed, exit 0 |
| Compiler `--help` | Passed, exit 0 |
| Existing cycle-project generation/rebuild/identity test | Passed, exit 0 |
| Switch SDL host on Mac dummy drivers | Passed: 600 frames, then resume through frame 1200 |
| Fixture coverage | No interpreted ROM cycles in the tested route |
| Missing/wrong ROM | Rejected; previous automatic state preserved |
| Corrupt automatic state | Rejected without replacing it |
| Save write failure / invalid directory | Detected; previous state preserved |
| Mac-generated fixture C → Switch ARM64 → NRO | Passed in official devkitPro Docker image |
| Normal cycle-project Switch integration | Passed with a Linux host compiler inside Docker |
| Mac/Linux fixture code generation | Two generated C units matched byte for byte |
| NRO sections, asset header and NACP metadata | Passed |
| Missing SDL / headless Switch configuration | Both rejected as required |
| Five selected desktop CTests | All passed, including SDL window/input coverage |
| Actual Mario generation/boot/build | Passed with the user-supplied ROM; NRO produced |
| Mario scripted gameplay | 1800 frames in World 1-1; native/interpreter hashes identical |
| Mario save-state continuation | All 1199 remaining frame hashes identical after reload |
| Physical Switch 0.2 user test | 46.36 FPS over 115 seconds; normal exit, saves off; full speed and suspend remain unfinished |

Native tests use actual SDL textures, renderer calls, audio-stream conversion
and queues with dummy drivers. They do not establish working console GPU/audio
output. This remains a prototype until hardware qualification.

The official image is ARM64 and includes devkitA64 r29.2-1 / GCC 15.2.0, libnx
4.12.0-1, switch-tools 1.13.1-1, switch-cmake 1.5.2-1 and switch-sdl2 2.28.5-4.
No native Mac SDK was installed; the administrator step remains pending. Both
the Docker image and existing Mac tools ran without an added Rosetta install.

The compiler emits an existing const-qualification warning in
`function_finder.c`; GCC reports an existing VRC7 vendor-code bounds warning.
The desktop link reports an alignment warning. None prevented these builds.
The desktop test project initially selected a bundled Windows SDL DLL;
reconfiguring with an explicit native `SDL2_DIR` fixed the test environment.

## Reproduce the verified fixture and obtain an NRO

From this repository root, with Docker running:

```sh
bash scripts/test-port.sh
```

This uses the pinned official image
`devkitpro/devkita64@sha256:1fc388c3a0d34bd2045a6dadcb1020e069d5f876a187fd705de14b4440c00282`.
It generates its own test ROM on the Mac; no commercial assets are used.
The cross-build compiles exactly those Mac-generated units.

Copy the contents of `build/switch-fixture/` to the SD root. It contains:

```text
switch/nesrecomp/fixture/fixture.nro
switch/nesrecomp/fixture/rom.nes
```

Launch through the homebrew menu. Expect a solid-color test picture; this is
a platform smoke test, not Mario. It can produce `runtime.log` and `saves/` on
the SD card. Controls and the hardware test checklist are in the patch's
`docs/SWITCH.md` (also readable in `.local/src/nesrecomp/docs/SWITCH.md`).

For the independent normal cycle-project integration, the commands executed
inside the same image, from the NESRecomp checkout, were:

```sh
cmake -S recompiler -B build/recompiler-linux -G Ninja -DCMAKE_BUILD_TYPE=Release
cmake --build build/recompiler-linux --parallel 4
cmake -S runner/cyc/project -B build/switch-project-integration -G Ninja \
  -DCMAKE_TOOLCHAIN_FILE=/opt/devkitpro/cmake/Switch.cmake -DCMAKE_BUILD_TYPE=Release \
  -DNESRECOMP_ROM="$PWD/build/switch-host-contract/data/rom.nes" \
  -DNESRECOMP_GAME_CONFIG="$PWD/build/switch-host-contract/vanilla.toml" \
  -DNESRECOMP_HOST_COMPILER="$PWD/build/recompiler-linux/NESRecomp" \
  -DNESRECOMP_SWITCH_GAME_DIR=sdmc:/switch/nesrecomp/fixture \
  -DNESRECOMP_RECOMP_UI=OFF
cmake --build build/switch-project-integration --parallel 4
```

## Desktop regression commands executed

From the NESRecomp checkout:

```sh
python3 tools/cyc/test_cyc_project.py --out build/switch-project-baseline --generator Ninja
cmake -S runner/cyc -B build/cycle-checks -G Ninja -DCMAKE_BUILD_TYPE=Release \
  -DSDL2_DIR=/opt/homebrew/opt/sdl2-compat/lib/cmake/SDL2
cmake --build build/cycle-checks --parallel 4 --target cyc_helper_test cyc_mapper_test \
  cyc_frame_pacing_test cyc_input_test cyc_window cyc_window_dev cyc_interp
ctest --test-dir build/cycle-checks --output-on-failure \
  -R '^(cyc_helper_test|cyc_mapper_test|cyc_frame_pacing_test|cyc_input_test|cyc_window_run)$'
```

Logs live under `.local/src/nesrecomp/build/`: `switch-host-contract.log`,
`switch-cross-fixture.log`, `switch-project-integration.log`,
`switch-final-build.log`, `cycle-checks-results.log` and their test directories.
The final root reproduction run is recorded in `build/test-port.log`.

## Build and test Mario

```sh
NESRECOMP_SMB_ROM='/absolute/path/to/your/Super Mario Bros.nes' bash scripts/build-smb.sh
```

The script verifies the original audited mapper-0 payload (CRC D445F698), builds
the Mac compiler and no-mod 600-frame baseline, and attempts Switch packaging.
It uses the native SDK if installed; otherwise it uses the pinned Docker SDK
and a separate Linux host compiler. This wrapper now passes the complete build
with the supplied `SMB.nes`, copied to ignored `.local/roms/SMB.nes`. It never
downloads or bundles a commercial ROM. Run the reproducible gameplay checks:

```sh
python3 scripts/test-smb.py --rom "$PWD/.local/roms/SMB.nes"
```

Produced artifact (10,242,245 bytes; NRO sections and metadata verified):
`build/smb1/SuperMarioBrosRecomp.nro`. On the SD card, put that NRO and your
matching ROM renamed `rom.nes` in `switch/nesrecomp/smb1/`.
See [the detailed Mario results and remaining limitations](MARIO_TEST.md).

## Remaining work

Run the Mario NRO on real Switch hardware and measure long-session audio and frame times at
stock clocks. Confirm the physical SDL button mapping and suspend/close hooks.
Then refine the save UI and add a HOME-menu forwarder for the intended daily
experience. The current NRO launches through homebrew.

After Mario is qualified, Adventure Island is the next target. Zelda/Metroid
and other cartridge games need their own matching-ROM configurations,
coverage measurements and gameplay validation. This patch has not been
submitted upstream or described as ready to merge.
