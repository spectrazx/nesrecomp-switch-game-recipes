# Switch One

Workspace for a Nintendo Switch 1 NESRecomp homebrew runner.

- [Implementation brief](CODEX_PROMPT_NESRECOMP_SWITCH.md)
- [Mac toolchain setup, verification, and uninstall](docs/TOOLCHAIN.md)
- [Switch prototype, test results, reproduction, and remaining work](docs/PORT_STATUS.md)
- [Core, Switch frontend and game module architecture](docs/ARCHITECTURE.md)
- [Changes and validation for future upstream PRs](docs/UPSTREAM.md)

ROMs, generated game code, build artifacts, and local installation records are
excluded from Git. The initial Switch runner builds both an original test
program and vanilla Mario. [Mario test results and SD instructions](docs/MARIO_TEST.md)
record the verified host behavior and remaining real-console checks.

The current **0.2 test build disables saving and automatic resume** while
addressing the slowdown found in the first Switch playtest. It uses the faster
PPU path, `-O3`, link-time optimization and requests presentation without VSync.
See [the hardware findings and performance checks](docs/PERFORMANCE_V2.md).

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
