# Super Mario Bros NESRecomp for Switch 
<img width="1743" height="1028" alt="Screenshot 2026-11-17 at 19 21 24" src="https://github.com/user-attachments/assets/f37e93b4-0208-414f-a06a-2e47b347738a" />



Workspace for a Nintendo Switch 1 NESRecomp homebrew runner.

- [Implementation brief](CODEX_PROMPT_NESRECOMP_SWITCH.md)
- [Mac toolchain setup, verification, and uninstall](docs/TOOLCHAIN.md)
- [Switch prototype, test results, reproduction, and remaining work](docs/PORT_STATUS.md)
- [Core, Switch frontend and game module architecture](docs/ARCHITECTURE.md)
- [Changes and validation for future upstream PRs](docs/UPSTREAM.md)
- [Upstream Mario comparison and measurements](docs/UPSTREAM_COMPARISON.md)
- [Faster iteration: Wi-Fi transfer, USB and Mac benchmarks](docs/ITERATION.md)
- [pNES / Nestopia architecture reference](docs/PNES_REFERENCE.md)
- [Controlled Switch portable/NEON sprite comparison](docs/SPRITE_AB.md)
- [Repeatable gameplay measurements and PPU profiling](docs/GAMEPLAY_PROFILING.md)
- [Shared PAL rendering optimization and validation](docs/PAL_PPU_TAIL.md)
- [Larger performance opportunities and faster experiments](docs/PERFORMANCE_STRATEGY.md)
- [PAL eight-pixel rendering](docs/PAL_RASTER_BATCHING.md)
- [Mario sprite-fetch optimization and audio target](docs/MARIO_SPRITE_FETCH.md)
- [Grouped sprite fetches: second Mario optimization round](docs/SPRITE_FETCH_JOBS.md)
- [PAL native intervals and console comparison](docs/PAL_NATIVE_INTERVALS.md)
- [Held IRQ batching and automatic Switch comparisons](docs/MASKED_IRQ_BATCHING.md)

ROMs, generated game code, build artifacts, and local installation records are
excluded from Git. The initial Switch runner builds both an original test
program and vanilla Mario. [Mario test results and SD instructions](docs/MARIO_TEST.md)
record the verified host behavior and remaining real-console checks.

The current **0.2 test build disables saving and automatic resume** while
addressing the slowdown found in the first Switch playtest. It uses the faster
PPU path, `-O3`, link-time optimization and requests presentation without VSync.
See [the hardware findings and performance checks](docs/PERFORMANCE_V2.md).
The confirmed 0.2.1 run and the next diagnostic build are documented in
[the 0.2.2 profiling notes](docs/PROFILING_0.2.2.md).
The subsequent longer runs are recorded in
[the Mario/Adventure Island hardware findings](docs/HARDWARE_0.2.3.md).
The next [console measurements and independent pixel investigation](docs/HARDWARE_0.2.4.md)
record the confirmed PAL gain, remaining slowdown and unconfirmed visual issue.

Build and test the Mario module from this repository root, with Docker running
if a native devkitPro SDK is unavailable:

```sh
python3 scripts/build-game.py smb1 --rom .local/roms/SMB.nes
python3 games/smb1/tests/verify.py --rom .local/roms/SMB.nes
```

The generic builder reads [the title recipe](games/smb1/README.md) and writes
`build/games/smb1/SuperMarioBrosRecomp.nro`. Use `--host-only` for a desktop
reference build, or `--host-only --variant optimized` to check HLE with LTO.
The existing `NESRECOMP_SMB_ROM=... bash scripts/build-smb.sh` command delegates
to this builder and preserves its historical `build/smb1/` package location.
The refactor adds no new execution shortcuts; full console speed is still pending.

## Copy Mario to the SD card

With the SD mounted at `/Volumes/Untitled`, run from this repository root:

```sh
mise run copy
```

The task increments the patch version from [games/smb1/VERSION](games/smb1/VERSION)
(`0.2.1` → `0.2.2` → …), rebuilds, checks the version embedded in the NRO,
and copies the executable, ROM and `build.json` to the SD. It stages and verifies
the copies before replacing files, then syncs writes. The version file advances
only after successful deployment; a failed build or copy leaves the counter
unchanged. Commit this file with the progress it identifies.

The homebrew menu and `runtime.log` use the new version. The executable keeps
the name `SuperMarioBrosRecomp.nro` so each deployment replaces the same entry.
The JSON records the version and executable/ROM SHA-256 hashes; it contains no
ROM content. Saves remain disabled. Existing `saves/` files are preserved.

`mise run build` builds the current version without incrementing or copying.
`mise run copy-profile` deploys the next Mario patch with sampled core timing
logs. Profiling adds overhead and is OFF in ordinary builds.
Both tasks default to `SMB.nes`; set `NESRECOMP_SMB_ROM` to use another path.
Set `NESRECOMP_SD_ROOT` if the SD mounts somewhere other than `/Volumes/Untitled`.
The copy task checks that this is a mounted volume before building and copying.

For direct use, run `python3 scripts/deploy-game.py smb1 --rom SMB.nes`.
`scripts/build-game.py` reads the module's version file; `--version 0.3.0`
overrides it for a build without changing the file. To start a new minor or
major release, edit `VERSION` deliberately before building. Versions must be
`MAJOR.MINOR.PATCH` and fit the Switch's 15-byte display field.

Eject the SD through Finder when finished, or run `diskutil eject /Volumes/Untitled`.
On the Switch, launch **Super Mario Bros. Recomp** through the homebrew menu.
Plus starts the game; D-pad / left stick and A/B control it.
L + R + Plus exits. ZL/ZR save/load shortcuts are disabled in this build.

For development, the existing build can also be sent and launched over Wi-Fi:
open hbmenu, press **Y** for NetLoader, then run
`NESRECOMP_SWITCH_IP=192.168.1.123 mise run netload` with the Switch's actual IP.
This checks the local package and sends a separate `*-dev.nro`; its ROM must
already be on SD. Use `netload-adventure` for the other game. These tasks use
the existing SDK container when native nxlink is absent and retain the current
version. Mario upload/launch and opt-in live diagnostic logging are now
confirmed on the physical console. Set `NESRECOMP_SWITCH_IP` to your console's
current address and open NetLoader before sending.
[Full instructions and USB alternatives](docs/ITERATION.md).

## Adventure Island Classic (Europe)

The second module uses the supplied European CNROM ROM with explicit PAL
timing (about 50 FPS at full speed). [Its validation and controls](games/adventure-island/README.md)
describe the current first-level test coverage and remaining console checks.

```sh
mise run build-adventure
mise run copy-adventure
```

These default to `Adventure Island Classic (Europe).nes`; override
`NESRECOMP_ADVENTURE_ISLAND_ROM` if needed. The game gets a separate launcher
entry and SD directory, `switch/nesrecomp/adventure-island/`.
