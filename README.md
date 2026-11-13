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
(
  set -e
  diskutil info /Volumes/Untitled > /dev/null
  sd_game="/Volumes/Untitled/switch/nesrecomp/smb1"
  mkdir -p "$sd_game"
  COPYFILE_DISABLE=1 cp -X build/games/smb1/SuperMarioBrosRecomp.nro "$sd_game/SuperMarioBrosRecomp.nro"
  COPYFILE_DISABLE=1 cp -X SMB.nes "$sd_game/rom.nes"
  cmp build/games/smb1/SuperMarioBrosRecomp.nro "$sd_game/SuperMarioBrosRecomp.nro"
  cmp SMB.nes "$sd_game/rom.nes"
  sync
)
```

The commands copy the executable and your local ROM, then verify both copies.
`cp -X` skips macOS extended attributes and metadata sidecar creation. Existing
`saves/` files are preserved and ignored by the 0.2 build. `runtime.log` is
replaced when the game launches and now includes timing reports every five seconds.

Eject the SD through Finder when finished, or run `diskutil eject /Volumes/Untitled`.
On the Switch, launch **Super Mario Bros. Recomp** through the homebrew menu.
Plus starts the game; D-pad / left stick and A/B control it.
L + R + Plus exits. ZL/ZR save/load shortcuts are disabled in this build.
