# Larger performance opportunities — 2026-11-15

Adventure Island's latest measured throughput is 25.34 FPS against its PAL
target of 50.007. Closing that gap needs nearly twice the throughput. The
latest PAL render-tail gain (2.56%) is useful but too small to establish a
practical route to full speed. The next experiments should target eligibility
for whole blocks of efficient hardware execution, then the renderer's amount
of work, and reduce manual console interaction.

## New finding: Mario's batching cliff

The same 600-frame desktop execution was run with audio at 48 kHz and no trace,
first with neutral input, then with the existing gameplay route. Neither run
uses interpreted ROM cycles. Instrumentation was built in the separate
`.local/src/nesrecomp-strategy` worktree, based on the current cumulative source
snapshot `b036efb611fe…`; the normal engine and packages were not edited.

| Counter over 600 frames | Neutral/title/demo | Gameplay route |
| --- | ---: | ---: |
| Batched CPU cycles | 0 | 9,330,364 |
| Batched raster tiles | 0 | 2,875,047 |
| Batching eligibility queries | 17,268,236 | 8,219,785 |
| Queries with IRQ line asserted | 17,242,673 | 3,452,507 |
| Of those, CPU IRQ mask set | 17,242,673 | 3,452,507 |
| Queries with APU readiness rejected | 17,268,236 | 3,479,922 |

These rejection counts overlap; they are not separate percentages to add.
The neutral run has IRQ asserted in **99.85%** of eligibility queries. At
frame 599 its APU is in four-step mode, IRQ inhibition is off and the frame
IRQ output is asserted. Gameplay has five-step mode, IRQ inhibition on and
IRQ output clear. `hw_native_interval_limit` rejects any asserted IRQ line;
`apu_native_interval_ready` additionally requires a conservative no-IRQ mode.
The CPU interrupt mask does not currently relax either requirement.

Separate uninstrumented 300- and 600-frame runs show that **6,074,263 of
8,934,151 cycles (about 68%)** are batched in gameplay frames 300–599, versus
zero in the neutral case. This matches the measurement window where Switch
gameplay reaches 48.21 FPS and neutral input reaches 28.18 FPS. It establishes
a major execution-path difference and a concrete optimization hypothesis;
only a controlled implementation change can establish its speed contribution.

Both diagnostic runs produce byte-identical WAV output and complete final
hardware dumps to the uninstrumented executions. Instrumented runtimes are
not performance measurements. Logs, patch, identities and validated counters
are preserved under `build/strategy-investigation/`.

## Priority experiments

1. **Make batching respect interrupt deadlines instead of rejecting broad
   audio modes.** Start with the Mario finding. A stable raised IRQ while the
   CPU masks IRQs can potentially permit useful work. Preserve the IRQ line,
   CPU polling, CLI/SEI/PLP/RTI behavior, NMI edges and DMA deadlines; removing
   the guards without replacing their safety contracts is incorrect. Keep
   full-state and PCM differential tests, including interrupt-boundary
   fixtures. This is a shared-core fix, not a Mario ROM patch.
2. **Extend proven batching to PAL/CNROM.** Adventure Island is excluded by
   both region and mapper eligibility, before its scene can benefit. Support
   the actual PAL divider phase (16 master clocks per CPU cycle, five per PPU
   dot), exact interrupt samples and DMA behavior, and flush pending work on
   CHR-bank writes. The existing NTSC executors assume three dots per cycle
   and cannot simply be enabled for PAL. Test scheduler and renderer portions
   separately. The expected gain is unmeasured.
3. **Make efficient sprite/raster work less dependent on CPU batching.**
   The current fast sprite/raster products are reached through qualified
   native intervals. A reusable decoded sprite-row/output cache could avoid
   checking and shifting all sprite units at every pixel even when CPU
   batching is unavailable. Preserve sprite-zero-hit timing and invalidate
   correctly at observable register/mapper boundaries. The pinned Nestopia
   source provides a useful design reference: `LoadSprite` decodes row pixels
   once, and `RenderPixel` reads them by horizontal position. NESRecomp already
   does related work inside its native spans; broaden reuse before inventing
   another representation.

Accept candidates on deterministic correctness first, then measured work
reduction. Test the same selected scene on Switch before claiming its speed
gain. The current general executor remains the reference and fallback.

## Faster experiments

The next console benchmark harness should run an entire comparison after one
NetLoader upload. For algorithms that can coexist in one executable, select
reference/candidate at runtime, restore the same in-memory starting snapshot,
replay the same input, clear audio queues/counters between legs, and execute
an order-balanced comparison automatically. Report per-leg hashes, observed
clock/mode and timings. Warm both paths before measuring. Compiler/build-flag
comparisons still require separate executables and are a different problem.

Use saved snapshots at the measurement start to avoid repeating 900 frames of
warm-up for every new idea, while keeping a separate full-boot correctness run
and a short host-cache warm-up. First establish that snapshot continuation has
the same measured final state and behavior as the current full replay.

Add low-overhead counters for why batching is refused and how many cycles,
pixels and tiles use each fast path. This gives more actionable information
than repeatedly measuring only aggregate PPU time. Detailed instruction
profiling can follow if the path counters do not explain the cost.

## Other options and their limits

- A per-game launcher around a mature emulator core is a practical alternate
  route to the original easy-launch experience. Compare it on the same console
  before assuming full speed. ROM patches and frontend enhancements can still
  work; existing NESRecomp native hooks would need separate integration.
- Replacing only SDL presentation or skipping display updates has limited
  potential here: presentation is about 1.4 ms of roughly 39.5 ms per Adventure
  Island frame. Most cost remains inside emulated hardware work. A more
  aggressive render-skip mode must still preserve CPU-visible PPU behavior.
- A GPU renderer could eventually consume recorded draw events, but sending
  individual hardware ticks to the GPU would not address the coordination
  problem. Batching and a suitable rendering representation come first.
- More threads require explicit synchronization around the tightly coupled
  CPU/PPU/APU. Parallelizing them naively is not an established shortcut.
- The actual Switch build already uses `-O3`, LTO, Cortex-A57 tuning and NEON.
  There is no missing basic optimization flag identified in this audit.

## Local setup

The current console IP is **192.168.1.224**, stored in ignored
`mise.local.toml` as `NESRECOMP_SWITCH_IP`. `mise run netload` and
`mise run netload-adventure` inherit it. A dry run verified the new target.
Historical transcripts retain the old address. Update or remove this local
override with:

```sh
mise set --file mise.local.toml NESRECOMP_SWITCH_IP=192.168.1.224
```

To remove the disposable diagnostic checkout after preserving any desired
results:

```sh
git -C .local/src/nesrecomp worktree remove --force ../nesrecomp-strategy
```

The force option is needed because this explicitly disposable worktree contains
the applied cumulative patch and diagnostic edits. The experiment artifacts
are contained in `build/strategy-investigation/`; no global tools were installed.
