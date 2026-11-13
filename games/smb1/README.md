# Super Mario Bros. module

This recipe builds the original game with NESRecomp's shared cycle runtime.
It does not build the enhanced upstream Mario host. That unchanged checkout
supplies `cyc_seeds.txt` only, at the revision pinned by `prepare-sources.sh`.

The required ROM has payload CRC32 `D445F698` and mapper 0. The original image
is supplied privately through `--rom`; the build does not alter or redistribute it.
The `nrom-ntsc` core profile checks its board and timing contract. Title and
artifact metadata, seed selection and renderer choices live in `game.cmake`.

The baseline desktop variant uses LLE PPU. The optimized variant uses the
existing shared HLE PPU and LTO; the Switch recipe selects this variant.
Neither variant changes NES clock rates. `optimizations/` is reserved for
future explicit static modules; there are no Mario routine replacements today.

```sh
python3 scripts/build-game.py smb1 --rom .local/roms/SMB.nes
python3 games/smb1/tests/verify.py --rom .local/roms/SMB.nes
python3 scripts/build-game.py smb1 --rom .local/roms/SMB.nes --host-only --variant optimized
python3 games/smb1/tests/verify.py --rom .local/roms/SMB.nes --variant optimized
```

Outputs live in `build/games/smb1/`; the packaged NRO is
`SuperMarioBrosRecomp.nro`. The compatibility `build-smb.sh` wrapper instead
copies the package to the historical `build/smb1/` location.

`tests/gameplay.txt` drives 1,800 frames into World 1-1. The verifier compares
native/interpreter execution and save continuation, checks final pictures and
audio, and uses the local TriCNES oracle when available. Desktop save-state
testing does not enable Switch saves. The current Switch save policy remains
OFF; physical-console full speed is still pending (latest 0.2 result: 46.36 FPS).
