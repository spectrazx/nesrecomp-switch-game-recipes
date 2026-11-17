# PAL native intervals — 2026-11-15

Adventure Island **0.1.8** enables a shared-core PAL batching path for NROM and
CNROM. Its six-leg console comparison passes, with **13.43% more throughput**
in the measured gameplay window. The measured package is preserved in
`build/pal-intervals/adventure-island/switch/`, promoted to the normal local
build directory/version counter, and uploaded to the Switch development entry.

## Why this helps

Previously PAL executed every CPU cycle through the coupled CPU/PPU/APU clock.
The new path admits bounded intervals in the stable visible part of a scanline.
Compiled CPU code can accumulate ordinary RAM/ROM accesses while the core
advances graphics and sound together at the next observable boundary. Existing
sprite-row predecoding also becomes available to PAL. This changes the amount
of host coordination, not the emulated frame rate or game logic.

The optimization belongs in the shared NESRecomp core. Adventure Island's game
module still selects its ROM identity, PAL region and CNROM hardware; no game
addresses, instruction patches or title-specific shortcuts enter this change.

## Timing contract and limits

- PAL has 16 master ticks per CPU cycle and five per PPU dot. Each admitted
  interval preserves all five divider phases. For N CPU cycles from phase p,
  the executor emits `floor((p + 16*N)/5)` dots and retains the intervening
  half-dot edges, original `hw.tick` values and resulting divider phase.
- Admission stops before the visible-span boundary. NMI, pending DMA, IRQ
  transitions, delayed PPU effects and CPU-observing/clocked mappers retain the
  existing eligibility guards. The previously qualified held, CPU-masked APU
  IRQ case remains available with its cursor mask check.
- Only PAL mapper 0/3 boards are admitted. CNROM CHR-bank writes flush pending
  work before changing the mapping. The generated project's mapper allowlist
  now includes mapper 3; NTSC mapper 3 still uses the ordinary clock.
- APU advancement retains ordinary per-cycle PAL work. The existing constant
  output optimization has NTSC frame-counter deadlines and is explicitly
  excluded from PAL. No NTSC raster-tile shortcut is reused for PAL.
- HD-pack recording avoids sprite predecoding. PAL idle spans and forced OAM
  refresh are unchanged. This is not a claim to fix the reported sprite flicker.
- `hw_native_set_pal_intervals(false)` flushes pending work and selects the
  reference policy. Normal launches enable the candidate. Save-state formats
  are unchanged; runtime comparison snapshots stay in memory, with SD saves OFF.

## Completed desktop checks

- `cyc_pal_intervals` compares reference/candidate at all five PAL phases on
  mapper 0 and 3. It exercises CHR banking, RAM and PPU traffic, OAM/DMC DMA,
  APU modes, Zapper timing and snapshot continuation, comparing intermediate
  machine/picture hashes and PCM. It requires actual batching in each case.
  The test and existing NTSC native-interval tests pass under HLE and LLE.
- Adventure Island's 1,800-frame gameplay route matches the retained pre-change
  executable byte-for-byte for untraced raw frame records, WAV and final full
  hardware dump. The candidate batches 31,041,784 CPU cycles over that route;
  the reference batches none. Tracing is not used for this comparison because
  tracing itself disables batching.
- Mario also matches the previous core across 1,800 untraced gameplay frame
  records, WAV and final hardware state.
- The no-save SDL contract passes 1,900 paced frames and a six-leg scripted
  comparison in both regions, including exact desktop state, replay restart
  and preservation of existing save files. The PAL fixture uses NES 2.0 timing
  metadata; legacy iNES byte 9 does not select PAL in this core.
- Independently, all **903 raw gameplay pictures** match pinned MesenCE after
  establishing boot alignment before controller input. This checks picture
  output, not complete independent CPU/APU equivalence.
- Balanced, serial desktop benchmark blocks reduce process CPU time by
  **13.50% / 13.06%**, median **13.28%**. A/A controls vary by 0.14% / 0.18%.
  Every benchmark WAV matches. These desktop results do not establish Switch
  speed or real-time audio.

Evidence is preserved under ignored `build/pal-intervals/`: `correctness.json`,
`bench/summary.json`, core test logs and `mesen/summary.json`.

## One-upload console comparison

The existing six-leg suite now selects `pal_intervals` for PAL and `masked_irq`
for NTSC. Logs explicitly record `policy` and `enabled`; the analyzer also
accepts archived IRQ-suite logs. Both policies warm up, then four measurement
legs run in reference/candidate/candidate/reference order. Each leg restores
the initial in-memory snapshot and rewinds the same input route.

```sh
python3 scripts/build-game.py adventure-island \
  --rom 'Adventure Island Classic (Europe).nes' --variant optimized \
  --version 0.1.8 --benchmark-input games/adventure-island/tests/gameplay.txt \
  --output-dir build/pal-intervals/adventure-island/switch
mise exec -- python3 scripts/netload-game.py adventure-island \
  --package-dir build/pal-intervals/adventure-island/switch \
  --console --suite --gameplay --warmup 900 --frames 1200 --wait-netloader 120
python3 scripts/analyze-comparison-suite.py \
  --log build/pal-intervals/adventure-island/switch/NETLOAD_LOG_NAME.log \
  --reference build/gameplay/adventure-island/reference1200/summary.json \
  --out build/pal-intervals/adventure-island/console-gameplay.json
```

Open hbmenu NetLoader after the upload heads-up. Normal menu launches do not
replay input or run comparisons. This is a same-binary policy comparison; both
paths contain the new compiled helpers and eligibility code. Separate desktop
executable comparisons and earlier console results provide additional context.

## Console result

The gameplay suite completed all six legs at observed 1.02 GHz, handheld,
full application mode, with saving and profiling disabled. Each leg ran 1,200
scripted frames, measuring the last 300 after a 900-frame warm-up.

| Measured gameplay legs | Reference policy | PAL batching |
| --- | ---: | ---: |
| FPS | 24.884 / 24.851 | 28.214 / 28.201 |
| Mean FPS | 24.8675 | 28.2075 |
| Mean emulation time/frame | 38.601008 ms | 33.886016 ms |
| Mean audio supply/wall time | 0.497280 | 0.564065 |

Throughput improves **13.43%**, with **12.21% less emulation time**. Every leg
matches desktop memory/picture `3FBE7362BB5379D4` and hardware
`C180E015501018B8`. Candidate legs batch 20,835,260 CPU cycles over the full
1,200-frame route; reference legs batch zero. There are no focus interruptions,
interpreted ROM cycles, dropped audio chunks or saves. The analyzer verifies
artifact/ROM/route identities, warm-up and measured windows, all six states,
and clock/application mode.

This is a comparison of two policies inside the same binary. The reference
also contains the newly generated interval helpers; it is not a rerun of the
separate 0.1.7 executable. The older 0.1.7 console test measured 25.34 FPS on
this window. The current result remains below the **50.007 FPS** target, and
only about **56%** of real-time audio is produced. No flicker fix is claimed.

The upload succeeded at `192.168.1.224:28280` after reopening NetLoader. The
normal local package and version counter are now **0.1.8**; the previous 0.1.7
package is retained under `build/pal-intervals/adventure-island/previous-package/`.
The uploaded entry is
`sdmc:/switch/nesrecomp/adventure-island/AdventureIslandRecomp-dev.nro`.
Launching it normally from hbmenu uses controller input, normal pacing and PAL
batching, with saving OFF. Benchmark flags applied only to the network launch.
The separately managed ordinary on-card NRO is unchanged.

The raw log is
`build/pal-intervals/adventure-island/switch/netload-0.1.8-0b1510a22ca6.log`;
the analyzed report is
`build/pal-intervals/adventure-island/console-gameplay.json`.

The measured NRO SHA-256 is
`0b1510a22ca6fbe1cb91ab59fc2651665fae0fead4f63f3362b25fd58afd3ea1`;
the cumulative source patch is
`f98804015bcce0c6a94a82950a134fcd75f99d7902c4e2bce4a58883528b25c7`.
The combined local evidence is `build/pal-intervals/validation.json`.

## Future upstream contribution

`patches/nesrecomp-pal-intervals.patch` contains core eligibility, PAL execution,
project preparation and timing tests. It applies after cumulative source
`bb674c54036b5dac4984743b96daf5f39886e401bc19c2f3205563733c298850`.
`patches/nesrecomp-switch-pal-comparison.patch` then extends the Switch test
runner and synthetic PAL fixture. A temporary Git index checks exact layered
reconstruction without staging the engine's working changes. Original line
endings are retained to keep the core patch reviewable.

The package manifest records the final cumulative patch and NRO hashes. ROMs,
generated game code, binaries and private captures stay ignored. No PR has been
opened; additional PAL boards require separate qualification.
