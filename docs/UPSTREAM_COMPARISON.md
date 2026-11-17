# Mario application and engine comparison — 2026-11-14

On the same ARM Mac, the simpler workspace application uses about 13–14% less
process CPU than the full upstream Mario application on the tested route.
Compiling that full application is therefore not an evidenced speed fix for
Switch. These are desktop headless measurements, not console FPS measurements.

## Sources and matched settings

The remote Mario `master` was checked and still matched our checkout:

| Source | Revision |
| --- | --- |
| SuperMarioBrosNESRecomp | `de443b01e2707c768be1729970f99d2f9da6bec3` |
| Engine pinned by that Mario project | `5c749a2ec3d3ff32a9f8ea0225db2a9ede5c8387` |
| Workspace's upstream engine base | `ab3579725ae129b0e04fa2095d7e7dd38ac096b7` |
| Workspace engine including our contributions | `56b926508dea5d86fd4f58801afb2dfe30560be5` |

The full Mario application was built twice: first against its recorded engine
pin, then against our engine. Neither source checkout was edited. A detached
reference engine worktree lives at `.local/src/nesrecomp-mario-reference/`.

All measured targets use Apple Clang 17, Release optimization, HLE graphics and
link-time optimization. The actual Mario CMake project supplies its complete
game additions, mod hooks and HD-pack integration; no mods are selected, the
mods directory is empty, and the desktop launcher/netplay are excluded. This
does not benchmark its shipped Windows GUI or enhanced rendering modes.

An important setting difference was found: Mario's `cycle_extras.c` selects
**44,100 Hz** audio, while our ordinary runner uses **48,000 Hz**. For timing
and PCM comparison only, a fourth target builds our existing game recipe with
an extras callback selecting 44,100 Hz. This generated adapter lives under
`build/upstream-comparison/matched-source/`; production sources and audio
settings are unchanged. Headless timing includes PCM synthesis and WAV output.

## Correctness

All four targets execute the existing 1,800-frame World 1-1 route. All 1,800
frame records match, including CPU, bus trace, memory, raw pixels and internal
hardware hashes. Final PNGs are identical. The three 44,100 Hz WAVs are
byte-identical. The normal workspace WAV has its expected different sample
rate; it is not treated as a failed audio comparison.

The older engine interprets 4,534 ROM cycles in this route; our engine
interprets zero in both applications. This is approximately 0.0085% of the
route's 53.6 million CPU cycles, not evidence of a large missing game routine.

## CPU measurements

Each comparison warms both executables, takes four A/A control samples, then
runs ABBA and BAAB blocks serially. Correctness hashing is disabled for timing.
The timer measures child process user plus system CPU, including startup and
WAV writes. No compilation runs during these legs.

| Comparison | Upstream CPU ms/frame | Matched workspace CPU ms/frame | Workspace CPU reduction by block |
| --- | --- | --- | --- |
| Mario with its pinned engine | 2.223 | 1.933 | 11.35%, 14.84% |
| Mario with our engine | 2.174 | 1.872 | 13.38%, 14.36% |

The median reductions are **13.10%** and **13.87%** respectively. A/A variation
was 0.46% / −5.84% in the first comparison and 0.62% / −0.36% in the second.
The second comparison provides stronger evidence because both engine and
sample rate match and its controls are quieter. The two workspace times come
from different sequential measurement blocks and should not be compared as an
optimization. Every timing leg produced identical audio.

Both applications already use native intervals, raster tile spans and APU
event spans in untraced runs. Mario's mod hook boundaries change batching
opportunities: the pinned application recorded about 1.77 million native
interval spans, versus about 0.91 million in the simpler target, for roughly
33.2 million batched cycles each. This is a concrete difference, but the test
does not isolate its contribution from other application overhead.

These results do not establish how fast either full application would run on
Switch. They do show that adding all upstream application code does not
automatically reduce core execution cost.

## Implementation audit

Between Mario's engine pin and our upstream engine base, the CPU interpreter,
PPU implementation, sprite kernels, mapper and cycle scheduler sources are
identical. The newer base contains code-generation coverage changes and audio
features; the added band-limited synthesizer is not the default in our build.
Our subsequent contribution adds the ARM sprite kernels and PAL scheduling
changes already documented in [the hardware follow-up](HARDWARE_0.2.4.md).

The upstream Mario project's current cycle build generates its game code from
the ROM using `game-cycle.toml` and `cyc_seeds.txt`. Its extra C/C++ supplies
mod integration, widescreen, co-op and character replacements. Our recipe uses
that same seed file with a minimal configuration and no gameplay replacements.
HLE graphics, native execution and core batching are already shared; no missing
Mario-specific stock-game speed layer was identified.

Sources: [Mario's build](https://github.com/mstan/SuperMarioBrosNESRecomp/blob/de443b01e2707c768be1729970f99d2f9da6bec3/CMakeLists.txt),
[game configuration](https://github.com/mstan/SuperMarioBrosNESRecomp/blob/de443b01e2707c768be1729970f99d2f9da6bec3/game-cycle.toml).

## Reproduce and remove

From the repository root, use a fresh output directory for each experiment:

```sh
python3 scripts/compare-mario.py --rom SMB.nes --out build/upstream-comparison
```

The script fetches Mario's exact engine pin if it needs the reference worktree,
builds the real upstream applications and our targets, then runs correctness
and timing checks. Existing results are preserved by refusing to reuse the
`results/` directory. `--skip-build` uses an existing set of four executables.

Evidence from this run is in `build/upstream-comparison/results/summary.json`,
with per-frame records, WAVs, logs, executable hashes and individual timing
samples beside it. No ROM content, generated code or binaries enter Git.

No new system package was installed. To remove the reference checkout:

```sh
git -C .local/src/nesrecomp worktree remove ../nesrecomp-mario-reference
```

The generated `build/upstream-comparison/` directory can then be deleted.

The next independent engine reference is [pNES / Nestopia](PNES_REFERENCE.md).
For faster console iteration, see [network and USB transfer](ITERATION.md).
