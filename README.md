# NESRecomp Switch game recipes

<img width="1743" height="1028" alt="Super Mario Bros. Recomp running on a Nintendo Switch" src="https://github.com/user-attachments/assets/f37e93b4-0208-414f-a06a-2e47b347738a" />

Build recipes for running statically recompiled NES games on a Nintendo Switch
(homebrew `.nro`) with [NESRecomp](https://github.com/mstan/nesrecomp).

This repository contains **no engine code and no game data**. Each recipe is
the set of build parameters and test routes for one cartridge. The engine,
including the Switch runner, is the `external/nesrecomp` submodule. You supply
your own ROM.

| Game | Cartridge | Region | PPU | Switch (handheld, stock clock) |
| --- | --- | --- | --- | --- |
| [Super Mario Bros.](games/smb1/README.md) | NROM, CRC32 `D445F698` | NTSC | FRAME | 72 FPS uncapped (target 60.1) |
| [Adventure Island Classic (Europe)](games/adventure-island/README.md) | CNROM, CRC32 `86867830` | PAL | FRAME | 53 FPS uncapped (target 50.0) |

## Engine

`external/nesrecomp` tracks `switch-integration` on
[spectrazx/nesrecomp](https://github.com/spectrazx/nesrecomp): upstream
`master` plus our open upstream pull requests. See [docs/ENGINE.md](docs/ENGINE.md)
for the list, how to update the pin and how to drop PRs once they merge.

## Requirements

- macOS or Linux with Python 3.11+, Git, and [mise](https://mise.jdx.dev)
  (provides CMake and Ninja; or install them yourself).
- Docker (colima works) for the pinned devkitPro image, **or** a native
  devkitPro install with `switch-dev` and `switch-sdl2`.
- A matching ROM for each game. The build checks the CRC32 and mapper.

```sh
git clone --recursive https://github.com/spectrazx/nesrecomp-switch-game-recipes.git
cd nesrecomp-switch-game-recipes
```

`scripts/build-game.py` initializes the submodules if needed.

## Build

```sh
mise run build             # Super Mario Bros. (ROM from NESRECOMP_SMB_ROM, default SMB.nes)
mise run build-adventure   # Adventure Island (NESRECOMP_ADVENTURE_ISLAND_ROM)
```

Or directly: `python3 scripts/build-game.py <game> --rom /path/to/game.nes`.
Each build:

1. builds the code generator and a desktop copy of the game, and boots it for
   600 frames as a quick check;
2. cross-compiles the Switch NRO (native SDK if found, otherwise Docker);
3. embeds the recipe's gameplay route as `romfs:/benchmark-input.txt`;
4. writes `build/recipes/<game>/<Artifact>.nro` and `build.json` (version,
   region, PPU, engine commit, NRO and ROM SHA-256; no ROM content).

Options: `--host-only` (desktop only), `--variant optimized` (desktop build with
the Switch PPU), `--ppu LLE|HLE|FRAME` (override the Switch PPU),
`--version X.Y.Z`, `--no-benchmark-input`.

## Install on the Switch

With the SD card mounted (default `/Volumes/Untitled`, override with
`NESRECOMP_SD_ROOT`):

```sh
mise run copy              # or copy-adventure
```

This bumps the patch version in `games/<game>/VERSION`, rebuilds, verifies the
NRO, and copies it with your ROM (as `rom.nes`) and `build.json` to
`sdmc:/switch/nesrecomp/<game>/`. The version file only advances after a
verified copy.

Launch the game from the homebrew menu. Controls: D-pad or left stick, A/B,
Plus = Start, Minus = Select, L + R + Plus = quit. Saving is off.

## Send over Wi-Fi

Open the homebrew menu, press **Y** (NetLoader), then:

```sh
NESRECOMP_SWITCH_IP=192.168.1.x mise run netload       # or netload-adventure
```

The ROM must already be on the SD (`mise run copy` once). The NRO is sent as
`<Artifact>-dev.nro` and launched. Useful options of `scripts/netload-game.py`:

- `--console`: stream the runner's log to the terminal and save it next to the build.
- `--console --benchmark --gameplay --warmup 900 --frames 1200`: play the
  embedded route uncapped and report FPS and per-stage timings for the last
  300 frames, plus final memory-state hashes.
- `--wait-netloader 600`: wait for NetLoader before uploading.

## Desktop tests

```sh
python3 scripts/build-game.py smb1 --rom SMB.nes --host-only
python3 scripts/build-game.py smb1 --rom SMB.nes --host-only --variant optimized
python3 games/smb1/tests/verify.py --rom SMB.nes [--variant optimized]
python3 games/adventure-island/tests/verify.py --rom "Adventure Island Classic (Europe).nes"
mise run test
```

The game verifiers replay the route and check native vs interpreter execution,
save-state continuation, picture and audio. Adventure Island also checks that
the reference (LLE) and optimized (FRAME) builds produce identical frames,
pixels and PCM.

## Adding a game

Create `games/<id>/` with:

- `game.cmake`: title, artifact name, ROM CRC32 and mapper, region, seed file
  and PPUs (see the existing recipes);
- `game.toml`: NESRecomp game config;
- `cyc_seeds.txt`: code addresses recorded with `--miss-log` (addresses only);
- `VERSION`, `README.md`, and ideally `tests/gameplay.txt` and `tests/verify.py`.

FRAME is the fastest PPU on the Switch but only supports some boards and
regions; others fall back to the slow reference PPU, so use HLE there. See the
engine's `docs/SWITCH.md`.
