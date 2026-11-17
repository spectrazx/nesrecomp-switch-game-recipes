# Mario sprite-fetch optimization — 2026-11-16

This records the 0.2.10 experiment. The subsequent
[grouped-fetch round](SPRITE_FETCH_JOBS.md) adds another measured desktop gain
and prepares 0.2.11 as the current local candidate.

Mario **0.2.10** tests a shared-core optimization for the settled sprite-fetch
period between visible scanlines. The supplied Mario ROM is NTSC: its original
target is **60.099 FPS**, not PAL's roughly 50 FPS. At the previously measured
47.93 FPS, audio production supplies only about 80% of real-time playback;
continuous playback requires closing that sustained deficit. This change
preserves generated PCM; it does not resample audio to conceal a slowdown.

The candidate package is in `build/mario-realtime/smb1/switch/`. Desktop
measurements show **18.93% less process CPU time**. Console performance and
listening verification are pending; no full-speed or audio-quality fix is
claimed yet. NetLoader discovery at `192.168.1.224` timed out after 120
seconds with no transfer started; the installed Mario development entry and
canonical 0.2.9 package remain unchanged.

## Shared-core change

The general PPU executor still handled the entire sprite-fetch period on every
scanline. A new cached classification covers NTSC visible lines after dot 260
through dot 320. The final screen pixel and horizontal scroll copy have already
completed; background prefetch has not started. The specialized executor keeps
the existing sprite fetches, OAM progression, background commit, status latches,
mapper notifications, output pipelines, Zapper elapsed dots and bus decay.
It omits general-path checks for events excluded by that classification.

Delayed register writes, rendering changes, data-port transactions, corruption
state, pre-render vertical copies and PAL timing retain the existing executor.
CPU register accesses, power-on, state restore and policy changes invalidate
the cached classification. Native CPU intervals can also cover this region,
ending no later than dot 320, but only when the existing machine/DMA/interrupt
proofs hold and no cartridge PPU-address observer or pattern change is pending.
Observed mapper edges remain on the coupled clock.

`hw_native_set_sprite_fetch(false)` flushes pending work and restores the old
path. The NTSC Switch comparison now toggles this policy; held-IRQ batching
stays enabled in both legs. PAL comparisons still toggle PAL raster grouping.
Normal launches enable the optimizations and leave saving disabled.

## Validation

- **4,096 new sprite-fetch cases**, in both HLE and LLE, compare the candidate
  against the original coupled path. Coverage includes four CPU/PPU alignments,
  NROM/MMC1/MMC3/GxROM, CHR ROM/RAM, 8x8/8x16 sprites, flips, changing palette
  and scroll, OAM contents, Zapper, decay, background capture, register-write
  invalidation, current-build state restoration and full PCM. The test asserts
  that native sprite-fetch intervals actually execute.
- Existing **4,096 NTSC raster cases**, **2,560 PAL raster cases**, native
  CPU intervals and PAL interval contracts pass.
- Both games' **1,800 raw frames, full WAV and final hardware dump** remain
  byte-identical to the previous accepted source snapshot. These runs do not
  enable tracing, which would disable native batching. Mario's separate
  1,800-frame neutral/title/demo capture also matches its 0.2.9 reference.
- The no-save SDL contract passes 1,900 paced frames and its automatic six-leg
  comparison, including replay restoration and preservation of existing saves.

Evidence lives under ignored `build/mario-realtime/`. The first test-launch logs
include a Python syntax error in the extended test driver; this was corrected
before the final successful `raster-tests.log` and `lle-tests-final.log` runs.
No test failures are waived.

The serial desktop benchmark uses identical routes and audio output, two
order-balanced blocks and A/A controls. CPU reductions are **18.27% / 19.59%**;
A/A variation is **+1.58% / −2.43%**. Every output WAV matches. These measurements
use Apple Silicon and do not predict an exact Switch FPS.

## Reproduction and contribution boundary

```sh
python3 scripts/build-game.py smb1 --rom SMB.nes --version 0.2.10 \
  --variant optimized --benchmark-input games/smb1/tests/gameplay.txt \
  --output-dir build/mario-realtime/smb1/switch
mise exec -- python3 scripts/netload-game.py smb1 \
  --package-dir build/mario-realtime/smb1/switch \
  --console --suite --gameplay --warmup 300 --frames 600 --wait-netloader 120
```

Open hbmenu NetLoader after the upload heads-up. The suite warms both policies
and runs ABBA measurements from the same in-memory starting state in one launch.
It exits to hbmenu. A normal launch of the development entry uses controller
input and normal pacing. Benchmark arguments do not persist.

`patches/nesrecomp-sprite-fetch.patch` contains the core and differential tests.
`patches/nesrecomp-switch-sprite-fetch-comparison.patch` adds frontend policy
selection and its SDL expectation. Apply them in that order after cumulative
snapshot `fe8c472c5982f6992343a27892d91dd3d0f2bf03daacbacbc0837fe950266d22`.
They reconstruct cumulative source
`bf70e97b7c6a2265d67ed69c1c0c4f1fd9cc9d0178ce92e91dd7c107fdae3a8d`;
patch reconstruction and reverse application were checked using a temporary
Git index. Game identity, versioning and deployment metadata remain in this
workspace. No game-specific replacement routine or ROM patch was added.
No upstream PR has been opened.

No global tool was installed. Disposable evidence lives in
`build/mario-realtime/`, and the experimental worktree is
`.local/src/nesrecomp-mario-realtime`. Preserve desired results before deleting
those directories; the main engine and cumulative patch contain the changes.
Adventure Island's reported moving scan lines remain an open visual issue.
