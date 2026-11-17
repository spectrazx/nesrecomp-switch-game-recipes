# Held IRQ batching and automatic comparisons — 2026-11-15

Mario **0.2.9** tests a shared-core optimization for an already asserted APU
frame IRQ while the CPU masks IRQs. It also adds an opt-in Switch comparison
suite that warms both policies and runs ABBA in one launch. The isolated
package is preserved in `build/masked-irq/smb1/switch/` and promoted to the
normal build directory and version counter after console qualification.
Adventure Island remains 0.1.7.

## Core contract

The previous batching path required the IRQ line to be low and the APU to be
in a mode that could not raise it. Mario's demo fails those checks even though
its CPU masks IRQs. The new case requires an already asserted four-step frame
IRQ, no IRQ inhibition, no pending clear/reset and no pending DMA/sample
transfer. MMC3 IRQs remain excluded. Region/mapper, NMI and PPU boundaries keep
their existing qualifications. This does not enable PAL native intervals.

A derived cursor points to the CPU's IRQ-mask byte only during an admitted
held-IRQ interval. Every attempted batched access checks that mask. Clearing it
closes the cursor before the next bus cycle, and ordinary polling takes over
until another compiled dispatch. This preserves CLI/PLP's delayed recognition,
SEI's previously sampled IRQ, and RTI's restored mask before its final poll.
Register accesses flush hardware work before acknowledging IRQ or changing the
APU mode. State load/restore clears the derived pointer; it is not serialized.

`hw_native_set_masked_irq(false)` flushes work and selects the previous
eligibility policy for reference comparisons. Ordinary launches default to
true. No game code, ROM bytes or CPU interrupt state are patched.

## Tests completed

- New `cyc_masked_irq` checks four NTSC alignments, long held-IRQ spans,
  CLI/SEI/PLP/RTI bus-cycle polling, `$4015` acknowledgement, `$4017` reset and
  OAM DMA against the coupled clock, with full machine and picture hashes.
  It asserts that the candidate actually batches cycles.
- Existing native-interval tests and the new IRQ test pass under LLE and HLE.
  Regional timing contracts also pass.
- Mario neutral and gameplay routes each match the immutable pre-change
  executable across 1,800 untraced raw frames, PCM/WAV and final hardware dump.
  Adventure Island also matches its pre-change executable on its complete
  1,800-frame gameplay route for the same outputs.
- The no-save SDL contract passes 1,900 paced frames and a six-leg scripted
  comparison. Every leg matches headless execution, including controller
  state. Restarting replay is tested through input changes before and after
  warm-up. Existing SD save data remains untouched.

Artifacts are under `build/masked-irq/`. ROMs, binaries, generated code and
private captures remain ignored.

## Desktop performance

The unprofiled 1,800-frame neutral run with audio enabled uses **46.94%** and
**46.41%** less process CPU time in two balanced blocks, median **46.68%**.
A/A controls vary by -0.75% and +2.30%; every benchmark WAV is identical.
These compare separate pre-change/candidate executables, not diagnostic
instrumentation. They establish a desktop gain, not Switch throughput.

The full 1,800-frame gameplay route improves **3.50%** and **3.60%**, median
**3.55%**, against A/A variation of about 0.6%. Its WAV output is also identical.
That route includes startup; this result does not establish an equivalent
improvement in the shorter active gameplay window measured on Switch.

After restarting the console, the direct upload at 192.168.1.224 succeeded.
The neutral-input suite completed all six legs at observed 1.02 GHz, handheld,
full application mode, with every final state matching the desktop reference.

| Measured demo legs | IRQ reference policy | Candidate policy |
| --- | ---: | ---: |
| FPS | 27.879 / 27.861 | 48.678 / 48.718 |
| Mean FPS | 27.870 | 48.698 |
| Mean emulation time/frame | 34.306068 ms | 19.029899 ms |
| Mean audio supply/wall time | 0.463730 | 0.810297 |

The selected demo window gains **74.73% throughput** with **44.53% less
emulation time**. Candidate legs batch 11,539,892 CPU cycles over the entire
600-frame leg; reference legs batch zero. Memory/picture `B12EA272492A9C08`
and hardware `A04C1F3C2A6AFF82` match in all six legs. The analyzer verifies
artifact, window, clocks and states in `build/masked-irq/smb1/console-neutral.json`.
This remains below the 60.099 FPS target, and audio supply is still about 19%
short of real time.

The second six-leg suite uses the existing scripted gameplay route and the
same NRO. Its measured reference legs are 47.879 / 47.957 FPS; candidate legs
are 47.900 / 47.960 FPS. Means are **47.918 / 47.930 FPS**, with emulation time
**19.318498 / 19.321774 ms**: no meaningful active-gameplay speed change.
All six legs match desktop memory/picture `C02B6119C242C9BD` and hardware
`4025888F4A4E427F`, with all 600 route frames replayed and stable 1.02 GHz.
The analyzed report is `build/masked-irq/smb1/console-gameplay.json`.

Both suites finish without focus interruptions, interpreted ROM cycles or
saves. This qualifies the demo gain and the automatic test runner, without
claiming full-speed gameplay or fixed music. The normal local package and
version counter are now **0.2.9**. The same NRO is uploaded to
`sdmc:/switch/nesrecomp/smb1/SuperMarioBrosRecomp-dev.nro`; a normal menu launch
uses controller input and normal pacing. Suite flags apply only to those
network test launches. The ordinary on-card NRO remains separately managed.

## One-upload suite

Build and launch with the existing private ROM and route:

```sh
python3 scripts/build-game.py smb1 --rom SMB.nes --variant optimized \
  --version 0.2.9 --benchmark-input games/smb1/tests/gameplay.txt \
  --output-dir build/masked-irq/smb1/switch
mise exec -- python3 scripts/netload-game.py smb1 \
  --package-dir build/masked-irq/smb1/switch --console --suite \
  --warmup 300 --frames 600 --wait-netloader 120
```

Add `--gameplay` to use the bundled route. Give a heads-up and reopen hbmenu
NetLoader before an upload. Each suite runs six legs: reference/candidate
warm-up runs followed by four measured runs in reference/candidate/candidate/
reference order. Each leg still includes the requested emulated warm-up,
keeping its measured window comparable with earlier full-boot runs.

An initial full state is serialized in memory after audio initialization.
Restoring it resets guest hardware, pictures, audio-output state and frame
number; the host also rewinds its pad route and clears SDL audio queues and
conversion buffers. No snapshot is written to SD. Cartridge-only, unprofiled
runs are required. Both policies warm their host paths before the measured
ABBA legs. A state mismatch or focus interruption invalidates the suite.

`comparison_result` records policy, frame counts, FPS, component times, audio
supply, batched cycles and final hashes. Batched-cycle counts cover the entire
leg including warm-up; performance numbers cover only the measured window.
Clock/application reports surround each leg. The analyzer additionally checks
package/ROM/route identities, all six states against desktop execution, and
stable 1.02 GHz handheld application mode:

```sh
python3 scripts/analyze-comparison-suite.py \
  --log build/masked-irq/smb1/switch/NETLOAD_LOG_NAME.log \
  --reference build/gameplay/smb1/reference600/summary.json \
  --out build/masked-irq/smb1/console-comparison.json
```

This is a same-binary policy comparison: the reference also contains the new
cursor guard. It isolates policy selection, not compiler/code-layout changes
between releases. Separate desktop executable comparisons and previous Switch
baselines provide additional context. Normal menu launches run one game with
controller input, normal pacing and the new policy; suite behavior requires
explicit command-line flags.

## Contribution boundaries

The exact as-built cumulative source snapshot is
`bb674c54036b5dac4984743b96daf5f39886e401bc19c2f3205563733c298850`.
The NRO SHA-256 is
`2dc827abece1419f49765a8b473a82e8c5dc50439d860d9418f07ef576a40ab7`.
The local package manifest records all identities.

`patches/nesrecomp-masked-irq.patch` contains core eligibility, cursor lifetime,
state invalidation and interrupt tests. It applies after the PAL render-tail
snapshot `b036efb611fe…`. `patches/nesrecomp-switch-comparison-suite.patch`
applies next and contains the shared frontend suite, replay restart and its
contract test. A temporary Git index verifies exact reconstruction. The actual
engine index is unchanged; no PR has been opened. Workspace build metadata,
network sender and analysis remain outside the engine patches.
