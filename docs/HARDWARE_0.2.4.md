# Console follow-up: Mario 0.2.4 / Adventure Island 0.1.2

Both logs and manifests were archived before rebuilding, with executable hashes
checked against the card:

- `build/games/smb1/hardware-v0.2.4/`
- `build/games/adventure-island/hardware-v0.1.2/`

| Measurement | Mario 0.2.4 | Adventure Island 0.1.2 |
| --- | --- | --- |
| Frames / seconds | 5,388 / 115.408 | 2,910 / 126.645 |
| Overall FPS | 46.69 | 22.98 |
| Target FPS | 60.099 | 50.007 |
| Weighted emulation time | 19.956 ms | 42.039 ms |
| Weighted presentation time | 1.370 ms | 1.349 ms |
| Interpreted ROM cycles | 0 | 40,203 |
| Dropped audio chunks / saves | 0 / 0 | 0 / 0 |
| Exit | Normal | Normal |

The shared PAL scheduler improved Adventure Island's throughput by **22.48%**
against 0.1.1 (18.76 FPS), reducing emulation time by **18.84%**. Both remain
below original speed. The user confirms Adventure Island has sound and
responsive buttons, with visible glitches and slower play than Mario. The
specific appearance/location of the glitches was requested separately.

## Independent pixel investigation

A pinned, unmodified MesenCE libretro core was built locally as a reference,
with PAL timing, sprite limit on, no run-ahead or overclocking, and zeroed RAM.
The existing capture driver was extended with explicit region selection and
optional memory snapshots, plus a native macOS build script.

The first unaligned continuous comparison differed in 36 of 903 frames, in
small sprite-sized clusters near the player. Pre-input title captures then
established the boot offset: all 256 zero-page bytes at NESRecomp frames 299
and 599 match Mesen frames 300 and 600, including frame-counter/random bytes.
Applying this fixed offset to input and pictures yields **903/903 exact raw
nine-bit pixel matches**, before and after the NEON candidate. No frame-specific
offset search or palette similarity threshold is used.

The reported glitches have therefore **not been reproduced on this route**.
This does not show that a different user route, Switch presentation, or an
intermittent issue is correct. It also does not justify disabling original
sprite limits to make artifacts disappear. [Reference setup and reproduction](REFERENCE_TOOLS.md)
include uninstall instructions and the exact coverage boundary.

As an additional diagnostic, the European ROM was run in NTSC mode only for
comparison with the NTSC-only TriCNES adapter. All 1,400 CPU/trace/memory/raw-pixel
hash records matched after excluding the adapters' internal hardware hash.
That experiment is not PAL qualification and does not change the shipped region.

An unrelated audit finding remains for separate investigation: the existing PAL
forced-OAM-refresh implementation performs evaluation work where
[documented hardware](https://www.nesdev.org/wiki/PPU_OAM) and MesenCE increment
the OAM address. This was not changed in this iteration, and is not established
as the cause of the user's glitches. PAL register/refresh edge cases beyond the
tested route remain a qualification limit.

## Shared ARM sprite-kernel candidate

The HLE core had explicit SSE2 sprite kernels on x86-64 but used scalar fallback
on ARM. AArch64 now has an equivalent NEON mask/shift implementation. It keeps
counter, priority, skip-dot and rendering-off semantics and changes no guest
cycles, state layout, game logic or timing clocks.

The balanced native Mac benchmark with audio enabled measured:

| Route | ABBA CPU reductions | Median | A/A control variation |
| --- | --- | --- | --- |
| Mario | 0.60%, 1.58% | 1.09% | 2.01%, 1.16% |
| Adventure Island | 4.45%, 5.15% | 4.80% | 0.63%, −0.32% |

Mario's result is within noise and is **not a demonstrated desktop speedup**.
Adventure Island's reduction exceeds its measured control variation. All WAV
digests match. Results and exact executable digests are in
`build/performance-v5/{mario-bench,adventure-bench}/`. Cortex-A57 speed still
needs a fresh physical-console measurement; full-speed play is not claimed.

Validation includes native/scalar kernel comparisons (250,000 random cases,
every planar row, all simultaneous lane masks and byte-valued counters),
complete-machine SIMD/scalar comparisons, native/raster interval tests, both
1,800-frame game routes with save continuation, unchanged untraced PCM/pixels,
and the independent 903-frame PAL reference. Actual devkitA64 GCC-generated
kernel instructions also pass the pure-kernel test under ARM64 Linux.
