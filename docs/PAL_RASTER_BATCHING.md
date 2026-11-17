# PAL eight-pixel rendering — 2026-11-16

Adventure Island **0.1.9** adds grouped PAL background rendering to the shared
core. The package is preserved in `build/pal-raster/adventure-island/switch/`.
The six-leg console comparison passes: **27.85 → 36.01 FPS**, a **29.29%**
throughput gain in the measured gameplay window. The measured 0.1.9 package is
now the normal local package/version and uploaded Switch development entry.

## Core change

Version 0.1.8 enabled PAL native intervals and sprite-row predecoding, but still
executed each background pixel/fetch/shift separately. The new path reuses the
existing eight-dot raster job, including its sprite composition, OAM evaluation,
sprite-zero pipeline, background capture and bus-decay handling.

Admission requires a tile boundary after the preceding half-dot, settled OAM
and fetch state, and enough interval credit for all eight dot/half-dot pairs.
PAL consumes 40 master ticks for that group. Leading/trailing partial groups
retain the scalar path, preserving all five CPU/PPU divider phases. Only the
already-qualified PAL NROM/CNROM boards without PPU address observers, pending
pattern changes or CHR/CIRAM aliasing enter the grouped path. HD-pack recording
retains the earlier fallback.

The shared raster output also applies PAL's red/green emphasis-bit swap to both
screen pixels and background capture, just like the ordinary output function.
The expanded synthetic test caught this difference even though the available
Adventure Island route does not expose it. No game code or ROM data is patched.

`hw_native_set_pal_raster(false)` flushes pending work and selects the 0.1.8
per-pixel renderer while keeping PAL native intervals enabled. The Switch suite
now compares this policy in PAL; NTSC still compares the held-IRQ policy.
Normal launches enable both PAL optimizations. Build manifests record region
and the compared policy, and the analyzer retains support for older packages.

## Correctness evidence

- The expanded raster contract checks **2,560 PAL cases** across NROM/CNROM,
  CHR ROM/RAM and all five phases: mirroring/four-screen, scrolling/fine X,
  palette/emphasis/greyscale, OAM/overflow/sprite-zero, Zapper, decay deadlines,
  background records, serialized-state replay and PCM. Coupled-clock,
  interval-only and grouped-raster paths agree. Existing **4,096 NTSC cases**
  also pass. LLE PAL checks pass and do not select the HLE raster shortcut.
- The PAL CPU-access probe additionally compares the three paths through
  register traffic, CHR banking, OAM/DMC DMA and snapshot continuation. Distinct
  CHR-bank patterns, palette colors and OAM DMA data strengthen the stimulus;
  candidate cases must actually execute raster jobs.
- Adventure Island's 1,800 untraced gameplay frame records, complete WAV and
  final hardware dump match 0.1.8. The route executes **11,888,595 raster jobs**.
  All **903 independently aligned Mesen pictures** also match.
- Mario's 1,800 untraced gameplay frame records, complete WAV and final hardware
  dump are unchanged. The existing six-leg PAL SDL contract passes with replay
  reset and preservation of save data, including 1,900 paced frames without
  saving. Console packages keep saving and profiling OFF.

Local evidence lives under ignored `build/pal-raster/`, including
`correctness.json`, `core/pal_raster_interval_results/results.json`,
`core/raster_interval_results/results.json`, `mario-gameplay/comparison.json`
and `mesen/summary.json`. No public artifact contains ROM-derived data.

## Desktop performance

The final corrected build reduces process CPU by **22.28% / 22.88%** in two
balanced gameplay blocks, median **22.58%**, against the retained 0.1.8 native
executable. A/A controls vary by -0.80% / -2.30%; every WAV matches. The earlier
23.48% exploratory result predates the PAL emphasis correction and is superseded
by this final-build measurement in `bench-final/summary.json`.

Mario's corresponding blocks show +2.41% / -0.17% CPU reduction, with identical
WAVs and A/A variation of +0.17% / +0.05%. This detects no material NTSC slowdown;
it does not establish a Mario speed improvement. Its report is
`bench-mario/summary.json`. All desktop runs are serial and unprofiled; console
throughput is measured separately.

## Reproduction

```sh
python3 scripts/build-game.py adventure-island \
  --rom 'Adventure Island Classic (Europe).nes' --variant optimized \
  --version 0.1.9 --benchmark-input games/adventure-island/tests/gameplay.txt \
  --output-dir build/pal-raster/adventure-island/switch
mise exec -- python3 scripts/netload-game.py adventure-island \
  --package-dir build/pal-raster/adventure-island/switch \
  --console --suite --gameplay --warmup 900 --frames 1200 --wait-netloader 120
python3 scripts/analyze-comparison-suite.py \
  --log build/pal-raster/adventure-island/switch/NETLOAD_LOG_NAME.log \
  --reference build/gameplay/adventure-island/reference1200/summary.json \
  --out build/pal-raster/adventure-island/console-gameplay.json
```

Open hbmenu NetLoader after the upload heads-up. Warm both policies, then
measure four legs in reference/candidate/candidate/reference order. Each leg
restores the initial in-memory snapshot and replays 1,200 frames, measuring the
last 300 after a 900-frame warm-up. Normal menu launches use live controls.
The comparison isolates the raster policy inside one binary; both paths contain
the new code and generated helpers. It does not compare separate release files.

## Console results

All six legs completed at observed 1.02 GHz in handheld, full application mode.
The four measured legs give:

| Gameplay window | Per-pixel reference | Grouped PAL raster |
| --- | ---: | ---: |
| FPS | 27.864 / 27.841 | 36.022 / 36.001 |
| Mean FPS | 27.8525 | 36.0115 |
| Mean emulation time/frame | 34.340220 ms | 26.248098 ms |
| Mean audio supply/wall time | 0.556967 | 0.720125 |

Throughput rises **29.29%**, with **23.56% less emulation time**. Every final
state matches desktop memory/picture `3FBE7362BB5379D4` and hardware
`C180E015501018B8`, including all 1,200 input frames. Both policies batch
20,835,260 CPU cycles over each full leg: the difference is rendering work
inside those intervals. There are no focus interruptions, interpreted ROM
cycles, dropped audio chunks or saves. The analyzer checks package, ROM and
route identity, measured window, all states, and consistent clock/mode.

The reference is the 0.1.8 rendering policy inside the new binary, not a separate
0.1.8 release-file rerun. The earlier 0.1.8 suite measured 28.21 FPS. This remains
below the **50.007 FPS** target; audio supply is about **72%** of real time.
The reported sprite flicker is not claimed fixed.

The normal local package/version is now **0.1.9**, with 0.1.8 preserved in
`build/pal-raster/adventure-island/previous-package/`. The uploaded file is
`sdmc:/switch/nesrecomp/adventure-island/AdventureIslandRecomp-dev.nro`.
A normal hbmenu launch uses controller input and normal pacing, with saves OFF;
benchmark/replay flags applied only to the network launch. The ordinary
on-card NRO is separately managed and was not overwritten.

Evidence: `build/pal-raster/adventure-island/console-gameplay.json`, the raw log
`build/pal-raster/adventure-island/switch/netload-0.1.9-0acb5d38a53f.log`, and the
combined `build/pal-raster/validation.json`.

## Future upstream contribution

`patches/nesrecomp-pal-raster.patch` contains only shared-core raster execution,
PAL emphasis correction and expanded tests. It applies after the 0.1.8 source
snapshot `f98804015bcce0c6a94a82950a134fcd75f99d7902c4e2bce4a58883528b25c7`.
`patches/nesrecomp-switch-pal-raster-comparison.patch` then selects the raster
policy in the Switch runner and its synthetic test. Temporary-index validation
checks exact reconstruction; the actual engine index is unchanged. Workspace
packaging and analysis metadata remain outside these upstream patches.

Cumulative source SHA-256:
`fe8c472c5982f6992343a27892d91dd3d0f2bf03daacbacbc0837fe950266d22`.
NRO SHA-256:
`0acb5d38a53fb80449250545b4566cbef7cb74f37a811265078dc16e6c0119bf`.
No PR has been opened. Broader mapper qualification and PAL OAM-refresh accuracy
remain separate work; this does not claim a fix for the reported sprite flicker.
