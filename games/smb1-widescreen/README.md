# Super Mario Bros. (World): widescreen (experimental)

The same cartridge as [smb1](../smb1/README.md), built with the experimental
widescreen renderer from the upstream
[SuperMarioBrosNESRecomp](https://github.com/mstan/SuperMarioBrosNESRecomp)
project (`docs/WIDESCREEN.md` there). It draws 426x240 with square pixels,
which fills a 16:9 screen; the status bar sits at the screen edges, terrain,
ordinary enemies and moving platforms extend into the wider view, and enemies
start moving when they enter it. The ROM is unchanged.

| | |
| --- | --- |
| ROM | payload CRC32 `D445F698`, mapper 0 (NROM), NTSC |
| PPU | FRAME on Switch (custom compositor on top of the native picture) |
| Config / seeds | upstream `game-cycle.toml` (adds the mod hook sites) and `cyc_seeds.txt` |
| SD folder | `sdmc:/switch/nesrecomp/smb1/` (shares `rom.nes` with smb1) |
| Launcher entry | **Super Mario Bros. Widescreen Recomp** (`SuperMarioBrosWidescreenRecomp.nro`) |

## How it's built

This is the first recipe that compiles game-specific code into the NRO, using
the optional recipe fields in `games/CMakeLists.txt`:

- `GAME_CONFIG_FILE`: the enhanced project's config, whose function-entry
  hooks the renderer needs.
- `GAME_MODS_ID`: compiles the engine's mod runtime (hooks and plugins). No
  mod package catalog is read; the renderer is switched on directly.
- `GAME_HOST_EXTRAS`, `GAME_INCLUDE_DIRS`, `GAME_DEFINITIONS`: the upstream
  widescreen sources plus [host/widescreen_host.c](host/widescreen_host.c), a
  trimmed copy of upstream's `cycle_bridge.c`/`cycle_extras.c` without co-op,
  voxel and player-character mods.
- `GAME_DESKTOP_SDL`: the desktop reference is the windowed host, because these
  sources include SDL headers. On macOS the build uses Homebrew's SDL2.
- `GAME_SD_DIR`: shares the smb1 SD folder.

The Switch runner needs `feat/switch-host-extras` on the engine fork (see
[docs/ENGINE.md](../../docs/ENGINE.md)), which lets it accept MODS and
HOST_EXTRAS and present a picture wider than 256 pixels.

The renderer is on by default (`GAME_WIDESCREEN_DEFAULT="16:9"`). Runtime
options from upstream also work as NRO arguments, e.g. over NetLoader:
`--widescreen 21:9|32:9|off`, `--widescreen-enemies classic` (original 4:3
activation timing), `--widescreen-hud center`, `--widescreen-camera centered`.

## License

Upstream SuperMarioBrosNESRecomp, including the widescreen sources and the
derived `host/widescreen_host.c`, is under the
[PolyForm Noncommercial License 1.0.0](https://polyformproject.org/licenses/noncommercial/1.0.0):
personal, noncommercial use only. Keep its license notice with any copy.

## Status and limits

Switch, handheld, stock clock, uncapped scripted route (`--widescreen-enemies
classic` so the stock route stays in gameplay), ms per frame:

| Build | FPS | Emulation | Present (compose) | Audio supply |
| --- | --- | --- | --- | --- |
| stock smb1 | 70.2 | 12.80 | 1.37 | 1.17 |
| first widescreen build | 57.5 | 14.09 | 3.15 | 0.96 |
| + glue: CHR copied once, no picture copy | 59.0 | 13.95 | 2.89 (1.42) | 0.98 |
| + compositor draws only the margins | 59.9 | 14.05 | 2.57 (1.10) | 1.00 |
| + background capture per tile | **60.9** | 13.85 | 2.50 (1.01) | 1.01 |

Full speed (16.64 ms budget) with about 0.3 ms to spare. Every step is
pixel-identical on the desktop (93 presented frames at 16:9, 21:9, 32:9).


Upstream calls it experimental: bosses, linked balance platforms, frenzy
spawners, power-ups and projectiles keep native 4:3 loading, and it has not
been validated through every world. Enemies moving earlier changes gameplay,
so the stock smb1 route in `tests/gameplay.txt` dies in 1-1 here; it is only
used as a benchmark load.

```sh
mise run build-widescreen
mise run netload-widescreen     # needs rom.nes in sdmc:/switch/nesrecomp/smb1/
python3 scripts/build-game.py smb1-widescreen --rom SMB.nes --host-only --variant optimized
build/recipes/smb1-widescreen/host-optimized/nes_game SMB.nes --frames 900 \
  --input games/smb1-widescreen/tests/gameplay.txt --no-save --present-out shot.png --present-every 300
```
