# Switch 0.2 test: saving disabled and faster execution

The first real Switch test confirmed boot, title/demo playback, Plus to start,
controls and music. The SD log records **842 frames in 30.094 seconds (27.98
FPS)**, no interpreted ROM cycles, and a failed save at the 30-second automatic
checkpoint. Battery percentage is not consulted. The original log and NRO are
archived in ignored `build/smb1/hardware-v1/`. The underlying SD save failure
has not been diagnosed; progress saving is disabled to isolate performance.

## Changes

- `NESRECOMP_SWITCH_SAVES=OFF` is now the Switch default. It disables progress
  save/load, automatic resume/checkpoints, exit/focus saves and battery-file
  persistence. Old saves are ignored, not deleted. ZL/ZR have no save action;
  L + R + Plus exits without saving. Logging remains active.
- The Mario Switch recipe selects the existing **HLE PPU**. Framework and
  desktop defaults remain LLE. The original NES cycle budget is retained.
- Switch Release targets explicitly request **`-O3` and link-time optimization**;
  the SDK supplied `-O2` despite `CMAKE_BUILD_TYPE=Release`.
- SDL requests VSync off to avoid an extra display wait after the guest's
  deadline. The last sub-millisecond wait avoids scheduler yields.
- Every five seconds `runtime.log` reports FPS and average emulation/audio/
  presentation/wait times. Startup records renderer, PPU and save settings.

There is no overclock, extra-scanline enhancement, guest-speed multiplier,
gameplay modification or audio pitch adjustment. The second physical test,
reported below, confirms improvement but still falls short of original speed.

## Checks performed

| Check | Result |
| --- | --- |
| LLE vs HLE traced Mario gameplay | All 1800 frame-hash lines identical |
| LLE vs HLE + LTO with tracing disabled | All 1800 captured memory/raw-pixel records identical |
| Active-path audio and final screenshot | Byte-identical |
| HLE PPU kernel, native-interval and raster-interval CTests | 3/3 passed, including 4096 varied raster cases |
| Optional save-enabled frontend contracts | Passed; retained for later save repair |
| No-save frontend contracts | Ignored old invalid state and invalid save directory; 1900 paced frames crossed 30 seconds with zero saves and normal exit |
| Actual Mario HLE + LTO frontend on Mac dummy drivers | 1900 frames in 31.607 seconds, normal exit, zero saves; existing state hash unchanged |
| Switch packaging | Passed with HLE, saves off, `-O3` and LTO |
| Revised build on physical Switch | User log: 5324 frames in 114.838 seconds, 46.36 FPS overall, normal exit |

Serial, order-balanced process-CPU benchmarks used the same ROM, input route
and audio output, with tracing/captures disabled. Across two ABBA blocks, HLE
alone reduced median CPU time by **22.84%**; HLE plus Clang LTO reduced it by
**25.46%**. A/A controls varied by about 0.5–3%, and all benchmark WAVs matched.
These are Mac results, not a measured Switch speedup. The intended NTSC frame
rate remains about 60.10 FPS. Mac dummy audio still dropped chunks, so that
test does not establish physical-device audio stability.

## Reproduce

```sh
NESRECOMP_SMB_ROM="$PWD/.local/roms/SMB.nes" bash scripts/build-smb.sh
python3 scripts/inspect-nro.py build/smb1/SuperMarioBrosRecomp.nro
```

The build wrapper explicitly selects HLE, disables saves, enables LTO and sets
version 0.2.0, including when reusing an old CMake cache. The README documents
the SD copy command. The exported patch includes the committed 0.2 updates.

After the [module refactor](ARCHITECTURE.md), the wrapper delegates to
`games/smb1/` and retains the package path above. Current baseline/optimized
host builds use `build/games/smb1/host` and `host-optimized`; historical paths
and measurements below are retained. [UPSTREAM.md](UPSTREAM.md) has current
build/test commands and the byte-identical comparison with these 0.2 captures.

From the NESRecomp checkout, the no-save contract command is:

```sh
python3 tools/cyc/test_switch_host.py --out build/switch-host-no-saves \
  --recompiler build/recompiler/NESRecomp --no-saves
```

Separate workspace builds `build/smb1/host-hle` and `host-hle-lto` use the same
ROM/config/seeds as `host`, with `-DNESRECOMP_PPU_IMPL=HLE`; the latter also
sets `-DCMAKE_INTERPROCEDURAL_OPTIMIZATION=ON`.

Active-path captures and comparison logs are in
`build/smb1/performance-v2/active-paths/`. Both executables ran 1800 frames with
`build/smb1/tests/gameplay.txt`, `--no-save`, `--frame-log`, WAV output and a
final screenshot. `cmp` passed for the complete frame captures, WAVs and PNGs.
Using frame captures instead of `--hash-out` leaves optimized intervals active.

The order-balanced benchmark was run from the workspace with:

```sh
python3 .local/src/nesrecomp/tools/cyc/bench_host_work.py \
  --baseline build/smb1/host/nes_game --candidate build/smb1/host-hle-lto/nes_game \
  --rom .local/roms/SMB.nes --input build/smb1/tests/gameplay.txt \
  --out build/smb1/performance-v2/cpu-hle-lto-bench \
  --lock build/smb1/performance-v2/benchmark.lock --frames 1800 --blocks 2
```

The HLE-only run used candidate `host-hle/nes_game` and output
`cpu-hle-bench`. Use a new output directory when repeating; the tool preserves
existing measurements. HLE CTest logs are in
`.local/src/nesrecomp/build/switch-hle-checks-*`.

## Second physical Switch result

The archived log at `build/smb1/hardware-v2/runtime.log` records 5324 frames in
114.838 seconds (**46.36 FPS overall**), mostly 45–49 FPS after startup. The
weighted averages across timing windows are:

| Work | Time per frame |
| --- | --- |
| Emulation | 20.070 ms |
| Presentation | 1.402 ms |
| Audio conversion/queueing | 0.025 ms |
| Deliberate waits | 0 ms |

The renderer is accelerated OpenGL ES2; disabling VSync succeeded. There are
no interpreted ROM cycles, progress saves or dropped audio chunks, and exit
is normal. The user still notices slow music, consistent with executing fewer
NES frames per real second. This is not evidence of a separate audio-decoder
bottleneck.

The 60.10 FPS target permits 16.639 ms per frame. With presentation/audio cost
unchanged, emulation needs to fall to roughly 15.213 ms, a **24.2% reduction**.
The next step is to profile the core and optimize its dominant clock/render
work, preserving existing pixel, input and PCM comparisons. Optimizing audio
queueing alone cannot recover the missing frame budget.

Statistics are also saved in `build/smb1/hardware-v2/summary.json`. The two
hardware runs are different routes and durations; the observed improvement
does not isolate each individual optimization's effect.
