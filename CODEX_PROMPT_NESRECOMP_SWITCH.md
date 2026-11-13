# Codex task: Add a Nintendo Switch 1 homebrew runner to NESRecomp and build vanilla Super Mario Bros.

You are a software engineering agent working on an **upstreamable contribution** to **[mstan/nesrecomp](https://github.com/mstan/nesrecomp)**. Implement a reusable **Nintendo Switch 1 homebrew (libnx/devkitA64)** target for the existing **cycle-accurate NESRecomp backend**, then **attempt a genuine vanilla Super Mario Bros. build**, without any mods. Do not stop at a plan: inspect the current code, implement, run the builds and tests that this machine permits, and report the precise result and blockers.

## Context and outcome

- **Development machine:** macOS on an Apple Silicon M1 MacBook. Run the NESRecomp code generator on macOS; cross-compile its generated C and runtime for the Switch's ARM64 target. Check whether the installed devkitPro toolchain works natively or requires Rosetta; don't assume the toolchain is already installed.
- **Target:** original Nintendo Switch, **homebrew `.nro` via devkitPro/libnx**, *not* Switch 2 and *not* Nintendo's proprietary SDK.
- **Distribution model:** **one separately compiled `.nro` per game**, not an emulator frontend, universal ROM picker, or console-side recompilation service.
- **First game:** original NES **Super Mario Bros. (USA/World, NES NROM/mapper 0)**, **stock single-player NES behavior**, no co-op or enhancements. The existing game project is [mstan/SuperMarioBrosNESRecomp](https://github.com/mstan/SuperMarioBrosNESRecomp); use its ROM validation and cycle seeds where compatible, but do not accidentally pull in its mods.
- **Desired artifact:** e.g. `SuperMarioBrosRecomp.nro` and build instructions, with the user's **matching, legally obtained ROM on the Switch SD card**. Do not commit, bundle, publish, download from unauthorized sites, or print the bytes of a commercial ROM, copyrighted extracted assets, or generated ROM-derived C.
- **Upstream changes:** prioritize changes to `nesrecomp` itself. If a tiny companion change to `SuperMarioBrosNESRecomp` is truly necessary, keep it independent, clearly scoped, and document the two commits/PRs separately.

## Read the actual repositories before editing

Review the following *current* files; follow the checked-out revisions, not assumptions from this prompt:

- `nesrecomp/README.md`, `runner/cyc/PROJECTS.md`, `runner/cyc/README.md` and `runner/cyc/MAPPERS.md`.
- `runner/cyc/project.cmake` and `runner/cyc/project/CMakeLists.txt`: these expose `nesrecomp_add_cycle_game(...)`, `RECOMPILER`/`NESRECOMP_HOST_COMPILER`, ROM/config/seeds inputs, and opt-in `MODS`, `HD_PACKS`, `HEADLESS`, `NO_RECOMP_UI` flags.
- `runner/cyc/cyc.cmake`: C11 core source list, optional SDL2 sources (`cyc_sdl.c`, `cyc_input.c`, `cyc_settings.c`, `cyc_tcp.c`, `cyc_chat.c`) and recomp-ui linkage. Reuse core sources and CMake functions rather than maintaining a duplicate hardware-core source list.
- `runner/cyc/cyc_host.c`: ROM and cartridge identity checks, main entry point, frame/session lifecycle, save logic, SDL host dispatch. **Avoid defining a second conflicting `main()`**.
- `runner/cyc/cyc_sdl.c`: uses SDL2 renderer/texture, `SDL_QueueAudio`, controllers and event loop. Determine whether to reuse it with narrowly scoped Switch changes or implement a *small* Switch SDL host with existing core APIs. The SDL2 video output must be functional, not merely an NRO that links headless.
- `runner/cyc/cyc_settings.c` and `cyc_diagnostics.c`: POSIX paths currently use `readlink("/proc/self/exe", ...)`, which is not an appropriate Switch path-resolution strategy. Audit other filesystem, time, socket, process and locale assumptions.
- `SuperMarioBrosNESRecomp/CMakeLists.txt`: the current cycle build **forces `NESRECOMP_ENABLE_MODS ON`**, passes `MODS HD_PACKS`, compiles many `mods/` files and `HOST_EXTRAS`, and may enable netplay/recomp-ui. **Do not assume `-DMODS=OFF` or `-DNESRECOMP_ENABLE_MODS=OFF` is sufficient**. Also inspect `game-cycle.toml`, which has `[[mod_function_hook]]` entries, and `cyc_seeds.txt`.

Use the existing `runner/cyc/project` standalone integration as the preferred vanilla starting point. A small distinct `game-switch-vanilla.toml` (or generated temporary equivalent) may have only a `[game]` section with a suitable `output_prefix` and `cycle_accurate = true`, *provided the compiled game actually boots*. Reuse compatible cycle seeds for coverage, but verify their behavior. **Do not remove the enhanced Mario project's existing features just to make the Switch port compile.**

## Scope: minimum viable upstream contribution

1. **Build separation.** Keep the NESRecomp recompiler a macOS **host executable** (`build/recompiler/NESRecomp`). The Switch build must receive its path explicitly, not try to execute an ARM64 Switch ELF as the generator. The existing cross-compilation path in `nesrecomp_add_cycle_game` already requires `RECOMPILER` on cross builds.
2. **Switch build integration.** Add a maintainable opt-in path such as `runner/switch/` or an appropriately guarded `cmake/` module. Prefer official devkitPro/libnx CMake facilities if available, otherwise provide a clearly documented toolchain file and NRO post-build packaging (`elf2nro`, `nacptool` or the correct installed equivalent). Create a valid NRO with app name/author/version metadata. Keep Windows/macOS/Linux builds unchanged.
3. **Reuse hardware code.** Compile the generated 6502 C plus existing C11 cycle CPU/PPU/APU/mappers/runtime for `aarch64-none-elf`. No x86 JIT, Nintendo SDK, custom NES hardware rewrite or separate general emulator.
4. **Video.** Display the stock **256×240** NES frame in correct aspect ratio on the Switch screen, with nearest-neighbor filtering and letterboxing as needed. Start with SDL2's standard renderer/texture path; do not make advanced OpenGL/HD packs/voxel rendering a prerequisite. Switch SDL2 video support is a hard requirement; **fail configuration if it is missing**, rather than quietly creating a headless NRO.
5. **Input.** Support at least one Joy-Con pair or Pro Controller; map NES D-pad/left stick, A, B, Start and Select. Respect homebrew exit/lifecycle events. Two controllers and split Joy-Cons are subsequent improvements, not gates for the first playable build.
6. **Audio.** Output stable NES audio via available Switch SDL2 audio APIs. Validate the actual audio format and rates, and avoid unbounded queue growth, large latency or accumulating drift. Resample or adapt channels when necessary; do not claim sound works based on linking alone.
7. **ROM and files.** Support a predictable **runtime** location such as `sdmc:/switch/nesrecomp/smb1/rom.nes`, separate from the **build-time** private path on the Mac. Preserve the existing ROM hash/cartridge/region mismatch rejection. Put configs and saves under a writable SD path such as `sdmc:/switch/nesrecomp/smb1/saves/`; handle missing folders and write errors, never overwrite the ROM. Never depend on `/proc/self/exe` or a desktop executable directory on the Switch. Make the per-game path configurable or data-driven for future NROs.
8. **No mods for the initial game.** **Do not pass** `MODS`, `HD_PACKS`, `GAME_ID` solely for mod packages, mod-related `HOST_EXTRAS`, netplay, external `recomp-ui`, chat streaming, voxel assets or HD packs in the vanilla Switch build. Avoid app-side mod source compilation and package copying. Some generic core hooks are unconditionally compiled by the engine; this is acceptable if they are dependency-free and inactive. The criterion is **no mod runtime and no mod gameplay/content features**, not blindly deleting every file containing the word `mod`.
9. **Regression safety.** Gate Switch-specific behavior narrowly. Keep desktop CMake defaults, existing enhanced Mario builds and cross-platform runtime behavior intact. Avoid large-scale refactors; favor a small, reviewable PR.

## Implementation sequence — execute, don't only describe

### A. Inventory the environment

From macOS Terminal or Codex's local execution environment, record and use what exists:

```sh
uname -m
sw_vers
cmake --version
python3 --version
command -v ninja || true
printf 'DEVKITPRO=%s\nDEVKITA64=%s\n' "$DEVKITPRO" "$DEVKITA64"
command -v dkp-pacman || true
command -v aarch64-none-elf-gcc || true
```

Check for `devkitA64`, `libnx`, Switch SDL2 portlibs, and NRO metadata/packing tools. **If missing**, state exact missing prerequisites and the official macOS installation steps; proceed with host builds, implementation and static checks anyway. Do not claim a Switch build was tested if the toolchain is missing. macOS Apple Silicon may need Rosetta for some precompiled devkitPro components; verify rather than assume. A Docker-based devkitPro toolchain can be an optional fallback if installed.

### B. Build the host recompiler on macOS

In the NESRecomp repository (adjust paths to actual checkouts):

```sh
cmake -S recompiler -B build/recompiler -G Ninja -DCMAKE_BUILD_TYPE=Release
cmake --build build/recompiler --parallel
./build/recompiler/NESRecomp --help || true
```

Inspect the executable and CLI output. Report the exact commands and exit statuses. The CLI `--help` may differ; confirm the supported syntax from the source instead of guessing.

### C. Establish a **no-mod Super Mario Bros. baseline** on the host

Inspect the Mario checkout. Use the original, locally provided ROM only, e.g. environment variable `NESRECOMP_SMB_ROM=/absolute/path/to/your/rom.nes`. Do **not** fabricate or download one. Check its revision against `SuperMarioBrosNESRecomp/tools/verify_usa_rom.py` (the existing Mario project currently checks CRC **D445F698**, mapper 0), without weakening the check.

Use `nesrecomp/runner/cyc/project` with a vanilla config, optionally existing `cyc_seeds.txt`. For example, once `SMB_REPO`, `NESRECOMP_SMB_ROM` and `VANILLA_GAME_TOML` are defined:

```sh
cmake -S runner/cyc/project -B build/smb-vanilla-host -G Ninja \
  -DCMAKE_BUILD_TYPE=Release \
  -DNESRECOMP_ROM="$NESRECOMP_SMB_ROM" \
  -DNESRECOMP_GAME_CONFIG="$VANILLA_GAME_TOML" \
  -DNESRECOMP_CYCLE_SEEDS="$SMB_REPO/cyc_seeds.txt" \
  -DNESRECOMP_HOST_COMPILER="$PWD/build/recompiler/NESRecomp" \
  -DNESRECOMP_HEADLESS=ON \
  -DNESRECOMP_RECOMP_UI=OFF
cmake --build build/smb-vanilla-host --parallel
./build/smb-vanilla-host/nes_game "$NESRECOMP_SMB_ROM" \
  --frames 600 --screenshot build/smb-vanilla-host/smb-boot.png
```

These are **baseline example commands**; adjust them after examining the real checkout. If the matching ROM is unavailable, still build the host compiler, attempt a ROM-independent smoke test if suitable public test assets exist, and document that *Mario generation and playability cannot be verified without the user's matching ROM*. Do not write fake success results.

### D. Add an opt-in Switch runner and produce an NRO

Implement the smallest production-quality target that will play this **same vanilla code**. Existing `NESRECOMP_HEADLESS=ON` builds a headless application: **do not use this as the final playable Switch target**. Disable recomp-ui independently while retaining/implementing video, input and audio.

A **desired interface**, which you may refine to match the real project conventions, is:

```sh
cmake -S runner/cyc/project -B build/smb-switch -G Ninja \
  -DCMAKE_TOOLCHAIN_FILE="$DEVKITPRO/cmake/Switch.cmake" \
  -DCMAKE_BUILD_TYPE=Release \
  -DNESRECOMP_HOST_COMPILER="$PWD/build/recompiler/NESRecomp" \
  -DNESRECOMP_ROM="$NESRECOMP_SMB_ROM" \
  -DNESRECOMP_GAME_CONFIG="$VANILLA_GAME_TOML" \
  -DNESRECOMP_CYCLE_SEEDS="$SMB_REPO/cyc_seeds.txt" \
  -DNESRECOMP_RECOMP_UI=OFF
cmake --build build/smb-switch --parallel
```

**This is a design target, not a claim that current NESRecomp supports Switch, or that a particular devkitPro CMake path exists.** Verify the toolchain file and CMake APIs on the installed environment, provide the *actual working command* in final docs, and never hardcode an unverified helper. Ensure the final output is an `.nro` (not just ELF or static library).

### E. Run verification

At minimum, attempt and report:

- Host `NESRecomp` builds and executes on the Mac.
- Plain vanilla Mario host: configure, compile, boot/title screenshot for hundreds of frames, and — if a suitable input script exists — reach actual gameplay; compare the output to the pre-port behavior.
- Cross-compile the **generated Mario C + cycle runtime** for Switch, with SDL video/audio/input, package an `.nro`, and verify that the NRO exists, is nonempty and has a plausible structure/metadata using available tools.
- Confirm no Mario mod sources, mod plugin libraries, HD packs, recomp-ui or netplay are included/required in the vanilla Switch target. Check the CMake invocation and link targets rather than relying on a label.
- Run applicable existing CTest or project checks. Test wrong-ROM rejection and SD save/error handling where feasible.
- On a real homebrew-capable Switch, test boot, first level, audio, control mapping, quit, save state or battery save if supported, and suspend/resume. If hardware isn't available, **mark these unverified**, don't infer success from an NRO compile.
- Confirm existing desktop builds are unaffected (or explain which regression tests were unavailable).

## Acceptance criteria

A successful implementation provides:

1. Reusable **NESRecomp-owned** Switch platform/CMake integration for individual games, without cloning the hardware core or turning the tool into a generic ROM emulator.
2. A verifiable **vanilla Mario** Switch build path that does not enable the Mario project’s mod/HD/netplay additions, while keeping those additions available for desktop builds.
3. A documented, reproducible **M1 macOS → host recompiler → Switch ARM64 → `.nro`** build with real commands and dependencies.
4. A sensible runtime SD layout, game-ROM identity checking, working display/input/audio and save persistence, with clear disclosure of which aspects have/ haven't been hardware-tested.
5. Clean code, no distributed game ROM or generated copyrighted game content, no destructive modifications to pre-existing user files, and a concise upstream-ready change description.

## Deliverables and reporting format

Create/update, as appropriate:

- `runner/switch/` (or a smaller location justified in the final notes) plus focused changes to `runner/cyc/` only where needed.
- `docs/SWITCH.md` with macOS M1 prerequisites, exact host/cross-build commands, minimum SDK versions actually verified, ROM placement, SD-card layout and test matrix.
- A small vanilla Super Mario Bros. integration example/test fixture, or a precise documented command against `SuperMarioBrosNESRecomp`; if companion project changes are necessary, identify them separately.
- `.gitignore` entries for generated sources, ROMs, build products and private assets as applicable.

When finished, provide:

1. **Implemented changes** (files touched and rationale).
2. **Exact commands executed** and their results; distinguish native host build, cross-compile, NRO packaging and real hardware playtest.
3. **Build artifact path** if an `.nro` was actually produced.
4. **Known blockers / tests not run**, including missing local ROM, toolchain or Switch console.
5. **Minimal follow-up work** needed for a clean upstream PR and later Zelda/Metroid builds.

**Working style:** Take initiative. Make the smallest safe assumptions, inspect before changing, try builds, fix compiler/linker errors, and continue until you have the strongest verifiable result available in the current environment. Do not claim completion from source review alone. Do not ask for approval for ordinary local refactoring/testing; do not modify unrelated repos or access/download commercial ROMs. If a required user-supplied ROM or installed toolchain is missing, say exactly what is missing and finish every independent task you can.

## Useful external references

- NESRecomp: <https://github.com/mstan/nesrecomp>
- Mario cycle project: <https://github.com/mstan/SuperMarioBrosNESRecomp>
- Switchbrew setup: <https://switchbrew.org/wiki/Setting_up_Development_Environment>
- devkitPro: <https://devkitpro.org/wiki/Getting_Started>
- Switch homebrew CMake pattern, for comparison only: <https://github.com/vbe0201/switch-cmake>
- Related but **not drop-in compatible** static recompilation Switch project: <https://github.com/souldbminerr/DKC2Recomp-NX/blob/main/docs/SWITCH.md>
