# Mario 0.2.1 hardware result and 0.2.2 diagnostic build

The user's short physical-console run is archived, unchanged, under
`build/smb1/hardware-v0.2.1/` with its build manifest and machine-readable summary.
It is sufficient to confirm the version and basic runtime behavior, but is a
short performance sample.

| 0.2.1 result | Value |
| --- | --- |
| Frames / elapsed time | 825 / 18.613 seconds |
| Overall throughput | 44.32 FPS |
| Five-second windows | 34.90, 49.95, 46.53, 46.66 FPS (last window partial) |
| Frame-weighted emulation / presentation time | 21.093 / 1.354 ms |
| Last two windows' emulation time | About 19.95 ms |
| Interpreted ROM/RAM cycles, dropped audio chunks, saves | All zero |
| Exit | Normal, code 0 |

The final windows are consistent with the previous longer 0.2 run near 46 FPS.
Most frame time remains in emulation. Neither renderer presentation nor the
queued-audio copy accounts for the missing approximately 14 FPS.

## The diagnostic build

`mise run copy-profile` deploys the next Mario patch with
`--profile-core`; the first such build is **0.2.2**. This enables the optional
shared core's sampled host-time profiler. It reports PPU dot, half-dot,
CPU-tail and native-interval paths, plus APU cycle/native-interval paths, in
`runtime.log` every five seconds. Sampling gaps vary to avoid locking onto
scanline or audio periods. Empty scopes calibrate the host timer overhead.
The follow-up **0.2.3** uses the median of nine sample-group means to reduce
isolated scheduler-pause bias and also logs the raw mean. It supersedes the
initial 0.2.2 diagnostic deployment; inspect both estimates because rare real
work can also be downweighted by the robust estimator.

These are estimated clock-path costs, not an exact CPU/PPU partition. PPU
paths include their mapper/interrupt work; register accesses and other bus
work are outside those scopes. `residual_ms` is the difference from the whole
emulation measurement, including remaining work and profiler overhead. It is
not pure CPU time; small or negative values can reflect sampling/calibration
error. Use repeated windows to rank paths, rather than interpreting exact
percentages. Per-path sample counts are recorded.

The profiler changes host workload. A lower FPS in a diagnostic build does not establish a
gameplay regression or a speed improvement. `mise run copy` produces a normal
build with profiling explicitly OFF, including in a reused CMake cache. The
build manifest records whether the profiler was enabled. Saves remain disabled.

## Validation and next hardware check

- The original-fixture test checks sample selection, timer calibration,
  estimates, reporting/reset and a missing host clock.
- The sampled Switch frontend runs 1,900 paced frames on Mac SDL dummy drivers
  with broken old saves and logs its profile records without a save write.
- Mario's profiled optimized desktop run matches the retained pre-refactor
  1,800 untraced frame records, WAV and final screenshot byte for byte.
- Existing project/default behavior and deployment/version unit checks pass.
- The Switch NRO is built with the profiler flag and its embedded version checked.

Play Mario for about 1–2 minutes, including title/demo and first-level movement,
then exit with L + R + Plus. Test Adventure Island separately; it uses PAL
timing and has no profiler enabled in its initial build. Return the SD with
both `runtime.log` files intact. The next optimization should follow those
measurements and retain the established pixel/audio/state comparisons.
