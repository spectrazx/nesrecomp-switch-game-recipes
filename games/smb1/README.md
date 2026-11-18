# Super Mario Bros. (World)

| | |
| --- | --- |
| ROM | payload CRC32 `D445F698`, mapper 0 (NROM) |
| Region | NTSC (60.1 FPS) |
| PPU | FRAME on Switch; LLE for the desktop reference |
| Seeds | `external/SuperMarioBrosNESRecomp/cyc_seeds.txt` (upstream Mario project) |
| SD folder | `sdmc:/switch/nesrecomp/smb1/` |
| Launcher entry | **Super Mario Bros. Recomp** (`SuperMarioBrosRecomp.nro`) |

Builds the original game with the shared cycle runtime, not upstream's
enhanced Mario host. No title-specific code.

```sh
python3 scripts/build-game.py smb1 --rom SMB.nes
python3 games/smb1/tests/verify.py --rom SMB.nes
```

`tests/gameplay.txt` is an 1,800-frame route into World 1-1. The verifier checks
native vs interpreter execution, save-state continuation from frame 600,
pictures and audio, and compares with the TriCNES oracle if one is built at
`external/nesrecomp/build/smb-oracle/cyc_oracle`.

On a Switch in handheld mode at the stock clock, the route runs at 72 FPS
uncapped (12.5 ms emulation per frame; target 16.6 ms).
