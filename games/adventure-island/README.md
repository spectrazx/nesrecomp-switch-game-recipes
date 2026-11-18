# Adventure Island Classic (Europe)

| | |
| --- | --- |
| ROM | payload CRC32 `86867830`, mapper 3 (CNROM), 32 KiB PRG + 32 KiB CHR |
| Region | PAL (50.0 FPS), set explicitly: the legacy iNES header leaves timing unspecified ([NesCartDB](https://nescartdb.com/profile/view/1428/adventure-island-classic)) |
| PPU | FRAME on Switch; LLE for the desktop reference |
| Seeds | `cyc_seeds.txt`: 892 addresses recorded with `--miss-log` (addresses only) |
| SD folder | `sdmc:/switch/nesrecomp/adventure-island/` |
| Launcher entry | **Adventure Island Classic Recomp** (`AdventureIslandRecomp.nro`) |

Full speed needs FRAME on PAL CNROM and masked-IRQ intervals, which are open
upstream PRs (#112, #113) carried by the engine pin. See
[docs/ENGINE.md](../../docs/ENGINE.md).

```sh
python3 scripts/build-game.py adventure-island --rom "Adventure Island Classic (Europe).nes" --host-only
python3 scripts/build-game.py adventure-island --rom "Adventure Island Classic (Europe).nes" --host-only --variant optimized
python3 games/adventure-island/tests/verify.py --rom "Adventure Island Classic (Europe).nes"
```

`tests/gameplay.txt` is an 1,800-frame route: title, Start, then movement and
jumps through the first forest level. For each build (LLE and FRAME) the
verifier checks native vs interpreter execution, no interpreted ROM cycles,
save-state continuation from frame 1200, and 48 kHz audio of the expected PAL
length. It then requires both builds to produce identical frame traces,
frame logs (RAM, CIRAM, palette, OAM, picture), PCM and screenshots.

On a Switch in handheld mode at the stock clock: 53.4 FPS uncapped (17.25 ms
emulation per frame; target 20.0 ms). Upstream `master` alone: 18.7 FPS.
