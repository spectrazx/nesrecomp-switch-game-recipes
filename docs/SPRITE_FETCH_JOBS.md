# Grouped sprite fetches — 2026-11-16

Mario **0.2.11** groups a complete eight-dot sprite fetch into one shared-core
operation. Against the 0.2.10 desktop executable, it reduces process CPU by
**8.13%** in the selected 1,800-frame gameplay route. Pictures, PCM and final
hardware state remain exact. The six-leg Switch comparison now passes at **66.62 FPS uncapped** in the
selected gameplay window, exceeding the original 60.099 FPS rate. Normal paced
play and audio listening remain to be checked; this is not campaign-wide
performance qualification.

The verified SDK package is now the local `build/games/smb1/` package and
`games/smb1/VERSION` is **0.2.11**, so ordinary build/netload tasks select this
candidate and the next incrementing deployment advances to 0.2.12. The previous
0.2.9 NRO and manifests are preserved in
`build/sprite-fetch-jobs/smb1/previous-package/`. The package was subsequently uploaded to
`sdmc:/switch/nesrecomp/smb1/SuperMarioBrosRecomp-dev.nro`; all six console
passes completed successfully. The NRO SHA-256 is
`004267a9a59e0a8583cc3ba036544ad7091bafe55a3178e0dba709c491f36b3e`.

## Finding and change

A new sampled Mac profile of 0.2.10 still shows work in sprite-fetch dispatch,
VRAM reads and sprite loading. Sampling was used to choose an experiment,
not as the performance comparison. Version 0.2.10 already skips general PPU
checks in the settled sprite-fetch region; it still executes each dot and
half-dot of a complete fetch separately.

The new job consumes eight dots only inside that qualified native interval,
at a sprite boundary, with enough credit remaining and no pending commit.
Partial groups retain 0.2.10's dot executor. The job reads secondary OAM with
its existing increment/wrap/full semantics, fetches the sprite's two pattern
bytes, applies flips and row bounds, and materializes the exact resulting
register, bus, pipeline, status and decay state. Out-of-range sprites still
perform their pattern reads. No visible screen pixels are skipped.

The enclosing interval excludes CPU register access, DMA and interrupt
boundaries. Address-observing cartridges and pending pattern changes cannot
enter it. Grouping additionally excludes CHR/CIRAM aliasing and active HD-pack
recording. Currently NROM and GxROM use the grouped fetches; MMC1 and MMC3 keep
the observer fallback. PAL retains its previous implementation.

`hw_native_set_sprite_fetch_jobs(false)` flushes pending work and selects the
0.2.10 executor. The NTSC Switch suite compares these two policies; both keep
0.2.10's sprite-fetch classification and held-IRQ batching enabled. The PAL
suite remains unchanged. Saving remains OFF.

## Correctness

The expanded sprite-fetch contract compares **three paths**: original coupled
clocks, 0.2.10's interval executor, and grouped jobs. All **4,096 cases** pass
in HLE and LLE. The fixture covers four alignments, NROM/MMC1/MMC3/GxROM, CHR
ROM/RAM, 8x8/8x16 sprites, flips, secondary-OAM address wrapping/full state,
scroll and palette variation, Zapper, decay, background capture and state
restoration. Writes to $2005/$2006/$2007/$2001 and reads of $2002 exercise
invalidation. It asserts that eligible boards actually execute jobs and
address observers execute none.

An initial stronger coverage assertion incorrectly expected MMC1 to execute
jobs. The check caught that MMC1 is also an address observer; the final check
uses the cartridge's observer flag and verifies its fallback instead. The
output comparisons passed before and after that fixture correction. No failed
hardware-state comparison was waived.

Existing **4,096 NTSC raster cases**, **2,560 PAL raster cases**, native CPU
interval and PAL interval contracts pass. Mario gameplay, Mario neutral/demo,
and Adventure Island each preserve **1,800 raw frames, complete WAV output and
final hardware dump**. Captures run without tracing, so native batching stays
enabled. The SDL contract passes its 1,900 paced no-save frames and automatic
six-leg comparison, including restored input replay and existing save data.

## Desktop measurements

The incremental benchmark uses preserved 0.2.10 and candidate executables,
identical ROM/route/audio settings, serial runs and two balanced blocks.
CPU reductions are **7.38% / 8.89%**, median **8.13%**. A/A control variation
is **0.93% / 0.66%**. Every WAV matches. This is CPU time saved, not an equal
percentage increase in FPS, and not a measured Switch gain.

A separate direct comparison rebuilt the exact archived **0.2.9 engine source**
(`bb674c54036b…`), the version last measured on Switch, with the same current Mac
toolchain and game recipe. Against that baseline, the new candidate saves
**24.84% / 27.41% CPU**, median **26.13%**. A/A variation is **−0.91% / +0.11%**;
all WAVs match. This measures the combined change directly instead of adding
percentages from separate experiments. The report is
`bench-combined/summary.json`. Both measurements include the full 1,800-frame
route; they are not timings of only the Switch's frames 300–599 window.

Evidence is under ignored `build/sprite-fetch-jobs/`: `sample.txt`,
`bench/summary.json`, `core/sprite_fetch_interval_results/results.json`,
`core-lle/sprite_fetch_interval_results/results.json`, the three gameplay
capture directories, and `sdl.log`. Final fixture results are in
`fetch-tests-final.log` and `lle-tests-final.log`; the other four contracts
pass in `core-final-tests.log`.

## Build and future upstream contribution

```sh
python3 scripts/build-game.py smb1 --rom SMB.nes --version 0.2.11 \
  --variant optimized --benchmark-input games/smb1/tests/gameplay.txt \
  --output-dir build/sprite-fetch-jobs/smb1/switch
```

For a future console comparison, after the NetLoader heads-up:

```sh
mise exec -- python3 scripts/netload-game.py smb1 \
  --console --suite --gameplay --warmup 300 --frames 600 --wait-netloader 120
```

The suite measures 0.2.10's scalar sprite-fetch policy against 0.2.11's grouped
policy, with both restored to the same starting state. The completed suite establishes
console throughput for both policies in this selected gameplay window.

The isolated core/test delta is `patches/nesrecomp-sprite-fetch-jobs.patch`.
The subsequent `patches/nesrecomp-switch-sprite-fetch-jobs-comparison.patch`
selects the new comparison in the Switch frontend and SDL contract.
They apply after 0.2.10's cumulative source
`bf70e97b7c6a2265d67ed69c1c0c4f1fd9cc9d0178ce92e91dd7c107fdae3a8d`,
reconstructing
`d6fffebd8599fd2770f1b1df36f29c0d67b359c0cd458b3a94ecb15390181b2f`.
A temporary Git index verifies reconstruction; reverse application to the main
engine succeeds. Game identity, version and package metadata stay in this
workspace. No Mario-specific routine or ROM patch was added, and no PR opened.

No tools were installed. The experiment and historical-baseline worktrees are
`.local/src/nesrecomp-sprite-fetch-jobs` and
`.local/src/nesrecomp-sprite-fetch-baseline`; they can be removed after preserving
the desired ignored evidence. The main engine and cumulative patch contain the
accepted local change. Adventure Island's reported moving scan lines remain
an open issue.

## Physical Switch result

The uploaded 0.2.11 executable warms both policies and measures ABBA on the
same 600-frame replay, excluding the first 300 frames. All six final
memory/picture hashes (`C02B6119C242C9BD`) and hardware hashes
(`4025888F4A4E427F`) match the desktop reference. The console stays in full
application mode, handheld, at an observed 1.02 GHz, with no interruptions,
interpreted ROM/RAM cycles or saves.

| Measurement | 0.2.10 policy | Grouped 0.2.11 policy |
| --- | ---: | ---: |
| Measured FPS, two passes | 62.654 / 62.790 | 66.515 / 66.733 |
| Mean uncapped FPS | 62.722 | **66.624** |
| Emulation ms/frame | 14.408120 | **13.415329** |
| Presentation ms/frame | 1.458222 | 1.504193 |
| Generated audio / wall duration | 1.043650 | **1.108577** |

Grouping gains **6.22% throughput** and saves **6.89% emulation time** in this
same-binary comparison. Both policies exceed 60.099 FPS. The older 0.2.9
measurement was 47.93 FPS in the same selected route; that is historical
context, not a third policy measured in this upload.

The uncapped suite intentionally produces audio faster than playback. Its
40 discarded excess chunks reflect the 100 ms queue ceiling; they do not
indicate an audio shortage. This benchmark establishes sufficient average
production in the selected window, not clean listening or absence of transient
underruns during normal play. Normal hbmenu launches restore controller input,
original-rate pacing, and all optimizations; benchmark arguments do not persist.

The complete transcript and send manifest are archived beside the exact NRO
in `build/sprite-fetch-jobs/smb1/switch/`; the validated report is
`build/sprite-fetch-jobs/smb1/console-gameplay.json`. The application exits to
hbmenu after the comparison. Launch the development entry normally to audition
music and play. The ordinary non-development SD entry remains separate.
