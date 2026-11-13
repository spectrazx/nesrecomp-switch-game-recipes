# Adventure Island Classic (Europe)

The supplied cartridge is the European PAL CNROM release: payload CRC32
`86867830`, mapper 3, 32 KiB PRG and 32 KiB CHR. Its dump has legacy header
timing left unspecified. `game.cmake` explicitly selects `REGION PAL` using
the matching [NesCartDB cartridge record](https://nescartdb.com/profile/view/1428/adventure-island-classic).
This preserves its original approximately 50.01 FPS target. The ROM is not
rewritten or included in Git; a private copy is under `.local/roms/`.

This module uses the generic hardware profile and shared CNROM implementation.
It does not use Mario's NROM/NTSC contract, and adds no title routine replacements.
The current core deliberately disables native interval batching for PAL and
mapper 3; don't enable NTSC shortcuts to obtain a misleading speed gain.

```sh
mise run build-adventure
mise run copy-adventure
```

The tasks default to `Adventure Island Classic (Europe).nes` in the workspace.
Override `NESRECOMP_ADVENTURE_ISLAND_ROM` or `NESRECOMP_SD_ROOT` as needed.
The copy task follows the same increment/build/verify/deploy policy as Mario.
The first deployed trial is **0.1.1**. The launcher entry is
**Adventure Island Classic Recomp**, with its own data directory:

```text
sdmc:/switch/nesrecomp/adventure-island/
  AdventureIslandRecomp.nro
  rom.nes
  build.json
  runtime.log               (created on launch)
```

Plus starts, A jumps, B uses the game's B action, and D-pad/left stick moves.
L + R + Plus exits. Saving is disabled, including automatic resume.

## Desktop validation

Build the baseline and optimized host variants, then run the title tests:

```sh
python3 scripts/build-game.py adventure-island --rom .local/roms/adventure-island-europe.nes --host-only
python3 scripts/build-game.py adventure-island --rom .local/roms/adventure-island-europe.nes --host-only --variant optimized
python3 games/adventure-island/tests/verify.py --rom .local/roms/adventure-island-europe.nes
```

The 1,800-frame PAL route waits for title initialization, presses Start, enters
the first forest level and exercises movement/jumps. Both LLE and HLE passed:

- All native/interpreter frame hashes match; no interpreted ROM cycles on this route.
- Saving after frame 1200 resumes at 1201; all remaining 599 hashes and final pixels match.
- LLE/HLE hashes, untraced frame records, PCM and PNG match byte for byte.
- Audio is 48 kHz mono, about 35.990 seconds, peak amplitude 10191.
- Title and first-level screenshots were inspected.

The 892 seed addresses were recorded from the title and gameplay routes with
`--miss-log`; they contain addresses only, not extracted game code. Unvisited
code retains interpreter fallback. Coverage is not a full-game or speed guarantee.
The local TriCNES adapter is NTSC-only, so no independent PAL oracle result is
claimed. Results are under `build/games/adventure-island/test-summary.json`.
Physical-console playability, speed and music still need the user's test.
