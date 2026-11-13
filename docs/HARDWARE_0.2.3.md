# Physical Switch: Mario 0.2.3 and Adventure Island 0.1.1

Both SD logs and their build manifests were archived unchanged before any new
build, with verified executable hashes and parsed per-window summaries:

- `build/games/smb1/hardware-v0.2.3/`
- `build/games/adventure-island/hardware-v0.1.1/`

| Measurement | Mario 0.2.3 | Adventure Island 0.1.1 |
| --- | --- | --- |
| Region / target FPS | NTSC / 60.099 | PAL / 50.007 |
| Profiling | Sampled | OFF |
| Frames / elapsed seconds | 7,889 / 169.862 | 2,006 / 106.924 |
| Overall FPS | 46.44 | 18.76 |
| Frame-weighted emulation time | 19.984 ms | 51.795 ms |
| Frame-weighted presentation time | 1.381 ms | 1.358 ms |
| Queued-audio processing | 0.024 ms | 0.026 ms |
| Native CPU cycles | 234,936,019 | 66,656,142 |
| Interpreted ROM cycles | 0 | 30,773 (about 0.046% of total CPU cycles) |
| Interpreted RAM cycles | 0 | 0 |
| Dropped audio chunks / saves | 0 / 0 | 0 / 0 |
| Exit | Normal, code 0 | Normal, code 0 |

These are instrumented runtime observations, not a visual/audio qualification.
The user was asked separately about Adventure Island's picture, sound and controls.
Zero dropped audio chunks does not establish original-speed music: emulation
remains slow, and neither game spends time waiting for its frame deadline.

## Mario's sampled paths

Frame-weighted estimates across the complete run:

| Sampled path | Estimated ms per frame |
| --- | --- |
| PPU dot | 9.158 |
| PPU half-dot | 3.770 |
| PPU CPU-tail | 0.848 |
| PPU native interval | 3.804 |
| PPU total | 17.580 |
| APU cycle | 1.489 |
| APU native interval | 0.576 |
| APU total | 2.065 |
| Residual | 0.338 |

The ranking consistently points to PPU work. Sampling/calibration uncertainty
means this is not an exact percentage split. In particular, the small residual
cannot be read as a precise CPU-only cost. Whole-frame timings include profiling
overhead; compare production builds separately.

## Performance implications

The software presentation path accounts for about 1.4 ms per frame in both games.
Adventure Island's very small interpreter share makes additional code seeds a
lower priority than its shared PAL/PPU execution path. PAL currently refuses
NTSC native intervals, and that safety boundary must remain until separately
validated PAL batching exists.

A candidate for the shared PAL scheduler specializes the ordinary cycle tail
for its five divider phases, preserving all original device edges and falling
back for register-split cycles. It is tested against the original universal
clock executor, with original fixtures and the existing game captures. This
does not change region, CPU frequency, guest cycle count, state layout or
enable NTSC batching for PAL. Benchmark evidence and the outcome follow below.

## PAL candidate validation

The balanced desktop benchmark with audio enabled measured **23.92% median
process-CPU reduction**, with two ABBA blocks at 22.82% and 25.02%. A/A
controls varied by 0.49% and 0.47%. All benchmark WAV digests match. The logs,
executable digests, commands and per-run timings are under
`build/performance-v4/pal-bench/`. Desktop CPU results do not predict an exact
Switch speedup.

CTest `cyc_pal_clock` compares the candidate and universal-loop reference with
identical PPU/APU implementations. It passes four NTSC and five PAL alignments,
delayed register traffic, DMA, Zapper input, full-state checkpoints, mid-span
snapshot replay, pictures and PCM. `cyc_region_test` also passes the clock,
frame length, audio and state-layout contracts.

Adventure Island's complete 1,800-frame route retains native/interpreter and
599-frame save-continuation parity in both renderer variants. Raw frame,
WAV and PNG hashes match the original scheduler. Its updated native trace
also matches a rerun of the preserved pre-change executable. The change lives
in the shared scheduler, not the game recipe. The next SD version is **0.1.2**;
its hardware throughput is still unmeasured.

Mario's balanced NTSC control measured a 0.06% CPU increase, inside its A/A
variation (−0.24% to +0.80%). Its retained 1,800 untraced frame records, WAV
and PNG remain identical. **0.2.4** disables diagnostic profiling for ordinary
play; no Mario speed improvement is claimed from the PAL-specific scheduler.
Both games continue to use stock region clocks with saving disabled.
