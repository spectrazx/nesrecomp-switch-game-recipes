# Shared PAL render-tail candidate — 2026-11-14

Adventure Island **0.1.7** contains a shared-core optimization for stable visible
PAL rendering. Its measured package is preserved under
`build/pal-ppu-tail/adventure-island/switch-candidate/` and promoted to the
normal build directory and version counter after the console comparison.
No game-specific optimization or game patch is involved.

The existing PAL master clock selects one of five divider-phase schedules.
The candidate also checks the PPU's cached render classification once at the
start of a complete CPU-cycle tail, then calls its stable render operations
directly. It retains all three dot and three half-dot operations, their exact
master-tick positions, cartridge notifications, NMI/IRQ sampling and the late
cartridge clock. It changes no guest clocks or frame rate target. Register-split
cycles, scanline boundaries, blanking and PAL forced OAM refresh retain the
previous path. PAL native CPU intervals remain disabled.

The change is isolated in `patches/nesrecomp-pal-ppu-tail.patch`, applying after
the gameplay/replay source snapshot `bf29404734a8…` documented in
[GAMEPLAY_PROFILING.md](GAMEPLAY_PROFILING.md). The cumulative Switch patch
also includes it. A separate temporary Git index verifies exact reconstruction;
the real engine index is untouched. No PR has been opened.

## Correctness

- `cyc_pal_ppu_tail` compares against the previous specialized PAL master clock
  with only this render shortcut disabled (`NESRECOMP_PAL_PPU_TAIL_REFERENCE=1`).
- `cyc_pal_clock` retains the original universal master-clock reference.
- `cyc_ppu_spans` retains the general PPU reference, and `cyc_region_test` checks
  regional timing/audio/state contracts. All four pass.
- Both supplied games match their immutable pre-change executables across
  1,800 scripted frames: frame hashes, untraced raw pictures, PCM/WAV and PNG.
  Saving at frame 1,200 and resuming matches all 599 remaining frame records.
  Neither route executes interpreted ROM cycles.
  A separate HLE game build with the core profiler compiled ON also matches
  all 1,800 unprofiled candidate frame records.
- Adventure Island matches the independent pinned MesenCE PAL reference for
  all 903 requested gameplay pictures. Pre-input alignment checks still match.

Artifacts and comparison reports are under `build/pal-ppu-tail/`. Private
ROMs, captures, binaries and generated game code remain ignored by Git.

## Desktop timing

The serial process-CPU comparison with audio enabled measured **1.24%** and
**1.99%** reductions in two balanced blocks (median **1.61%**), versus A/A
variation of -0.25% and +0.34%. All benchmark WAV digests match. A network
upload began near the end of the second block, so the first block is the
cleaner desktop estimate; this small gain needs console qualification.

The candidate source snapshot is `b036efb611fe…`, archived beside the local
experiment reports. Its NRO SHA-256 starts `f9ac36ff47ab…`; the isolated build
manifest records complete identities and route digest.

## Console qualification

Four scripted console runs used **B A A B** order (B = candidate), each with
900 warm-up and 300 measured frames. Both repeated binaries are identical
within their version, verified against the package manifest and log header.

| Version | Two measured FPS results | Mean emulation time/frame | Mean FPS | Audio supply/wall time |
| --- | --- | --- | --- | --- |
| 0.1.6 baseline | 24.712 / 24.696 | 38.923691 ms | 24.704 | 0.4940165 |
| 0.1.7 candidate | 25.328 / 25.344 | 37.875932 ms | 25.336 | 0.5066545 |

The candidate reduces emulation time **2.69%** and increases throughput
**2.56%** in this window. Both candidate runs exceed both baseline runs;
within-version FPS variation is about 0.06%. Presentation cost is comparable.
This is a small shared-core gain, not full-speed playback or a whole-game claim.
The target remains 50.007 FPS and sustained audio supply remains about half of
real time. No music-quality or reported sprite-flicker fix is claimed.

All runs use full application mode, handheld operation, normal performance
mode, successful observed 1.02 GHz CPU-clock reads, HLE and explicit NEON.
All 1,200 input frames replayed, with zero focus interruptions, saves or
interpreted guest cycles. Memory/picture `3FBE7362BB5379D4` and internal state
`C180E015501018B8` match desktop execution exactly in every run. The strict
log/artifact/window/route/state validator used for the gameplay baseline passes;
`build/pal-ppu-tail/adventure-island/console-comparison.json` preserves the rows,
identities and computed means.

The current local Adventure Island package and version counter are **0.1.7**.
The development SD entry `sdmc:/switch/nesrecomp/adventure-island/AdventureIslandRecomp-dev.nro`
contains that measured NRO. Benchmark/replay flags were supplied only for the
network test; launching the entry normally uses controller input and normal
pacing, with profiling and saving disabled. Mario's package remains **0.2.8**;
its NTSC algorithm is unchanged and its desktop regression check passes.

## Reproduction

From the workspace root, with the supplied private ROM present:

```sh
cmake -S .local/src/nesrecomp/runner/cyc -B build/pal-ppu-tail/core -G Ninja -DCMAKE_BUILD_TYPE=Release
cmake --build build/pal-ppu-tail/core --parallel 4 --target cyc_pal_clock_reference cyc_pal_clock_candidate cyc_pal_ppu_tail_reference cyc_ppu_span_reference cyc_ppu_span_candidate cyc_region_test
ctest --test-dir build/pal-ppu-tail/core -R '^(cyc_pal_clock|cyc_pal_ppu_tail|cyc_ppu_spans|cyc_region_test)$' --output-on-failure
python3 games/adventure-island/tests/reference.py --rom 'Adventure Island Classic (Europe).nes' --out build/pal-ppu-tail/mesen-new
```

For desktop timing, preserve the pre-change optimized executable first, then
build the candidate with `--host-only --variant optimized`. Measure serially,
with no concurrent builds/captures, using the engine's `bench_host_work.py`:

```sh
python3 .local/src/nesrecomp/tools/cyc/bench_host_work.py \
  --baseline build/pal-ppu-tail/adventure-island/baseline/nes_game \
  --candidate build/games/adventure-island/host-optimized/nes_game \
  --rom 'Adventure Island Classic (Europe).nes' \
  --input games/adventure-island/tests/gameplay.txt --frames 1800 --blocks 2 \
  --out build/pal-ppu-tail/adventure-island/bench-new --lock build/desktop-benchmark.lock
```

The Switch candidate uses the same frontend settings and bundled route as the
0.1.6 baseline: NEON, HLE, Release/LTO, profiling and saving OFF. Compare 300
measured frames after 900 warm-up frames, with no physical gameplay input:

```sh
python3 scripts/netload-game.py adventure-island --ip 192.168.1.195 \
  --package-dir build/pal-ppu-tail/adventure-island/switch-candidate \
  --console --benchmark --gameplay --warmup 900 --frames 1200 --wait-netloader 120
```

Give a heads-up and reopen hbmenu NetLoader before each upload. Compare with
`build/gameplay/adventure-island/baseline/`, retaining final-state and observed
clock checks. Desktop speed changes do not establish Switch performance.
