# Repeatable gameplay and PPU profile — 2026-11-14

Mario **0.2.8** and Adventure Island **0.1.6** add repeatable input replay and
packaged read-only routes. They do not change the renderer algorithm or audio
playback policy. All six console measurements ran handheld, in full application
mode, with successful observed CPU-clock reads at **1.02 GHz**. NEON, HLE,
Release optimization and LTO remain selected; saving is OFF.

## Measurement windows

Each title uses the existing `games/<id>/tests/gameplay.txt` NES-pad route.
The Switch frontend calls the engine's existing `cyc_host_window_replay` API;
game-specific inputs remain outside the engine. Optional RomFS assets bundle
the route in the NRO, so a network upload supplies everything except the ROM
already on SD. No game ROM or derived game asset is bundled in RomFS.

| Title | Excluded warm-up frames | Measured zero-based frame indices | Total frames |
| --- | --- | --- | --- |
| Mario | 300 | 300–599 | 600 |
| Adventure Island | 900 | 900–1199 | 1,200 |

Local screenshots at the selected endpoints show active first-level gameplay.
The longer Mario route reaches a death/respawn screen by frame 900; this is
why its measurement ends at 600. Each window measures 300 frames. Neutral
input gives the matching title/demo comparison. The baseline NRO is identical
between that title's neutral and gameplay runs. The separate profiled NRO
enables host-clock sampling; its FPS is not used as ordinary game speed.

## Console results

| Title | Neutral/demo FPS | Scripted gameplay FPS | Original target | Gameplay audio supply / wall time |
| --- | --- | --- | --- | --- |
| Mario | 28.177 | **48.208** | 60.099 | 0.802150 |
| Adventure Island | 25.032 | **24.709** | 50.007 | 0.494108 |

Mario's same-binary comparison establishes strong scene-dependent cost. Its
gameplay result is consistent with the earlier manually played 46–47 FPS run;
the lower demo result does not establish a global regression. This test has
not isolated exactly which operation makes Mario's demo more expensive.
Adventure Island remains slow in both selected scenes.

The audio producer still falls behind real-time playback, by about 20% for
Mario gameplay and 51% for Adventure Island gameplay. This supports starvation
as a contributor to the reported sound; no audio-quality fix is claimed.

## Profile of the gameplay windows

Sampling counters are reset after warm-up. Reports are weighted by the number
of measured frames in each reporting interval, totaling exactly 300 per game.
The sampler's median-of-group estimates and timer calibration are retained.
Network and SD copies of the profile use a snapshot of diagnostic counters;
no guest state is changed by copying/reporting them.

| Cost per frame | Mario | Adventure Island |
| --- | --- | --- |
| Unprofiled emulation | 19.186 ms | 38.936 ms |
| Unprofiled presentation | 1.439 ms | 1.361 ms |
| Profiled emulation | 19.916 ms | 42.461 ms |
| Estimated PPU processing in profiled build | **16.669 ms** | **35.978 ms** |
| Estimated APU processing in profiled build | 1.765 ms | 3.907 ms |
| Profile residual | 1.481 ms | 2.576 ms |
| Emulation overhead with profiling enabled | 3.80% | 9.05% |

These are approximate path estimates from instrumented builds, not additive
measurements of the uninstrumented baseline. PPU work dominates both profiles.
Mario's largest estimated paths are ordinary dots (8.405 ms), half dots
(3.250 ms) and native PPU intervals (4.391 ms). Adventure Island records
ordinary dots (25.900 ms) and half dots (10.079 ms), with **zero** PPU tail,
PPU native-interval or APU native-interval calls in this profile.

Two existing eligibility rules explain why Adventure Island lacks the native
interval path: `native_interval_board` qualifies mappers 0/1/4/66 but excludes
CNROM mapper 3, and `hw_native_begin`/`hw_native_interval_limit` exclude PAL.
Its generated build defines `NESRECOMP_NATIVE_INTERVALS=0`. Extending these
paths requires preserving PAL divider phases, register timing and mapper
behavior; toggling eligibility flags alone is not a validated optimization.

## Correctness and evidence

All six console runs completed without focus interruptions. Every final
memory/raw-picture and internal-hardware hash matches the corresponding
desktop replay, including profiled builds:

| Case | Memory/picture hash | Hardware hash |
| --- | --- | --- |
| Mario gameplay | `C02B6119C242C9BD` | `4025888F4A4E427F` |
| Mario neutral | `B12EA272492A9C08` | `A04C1F3C2A6AFF82` |
| Adventure Island gameplay | `3FBE7362BB5379D4` | `C180E015501018B8` |
| Adventure Island neutral | `CAAAFE14A250ED65` | `66494DE556B58846` |

The native SDL contract now polls actual controller bits in its original test
program. A scripted SDL run matches its headless execution and differs from
neutral input, so the test detects ignored replay or incorrect frame alignment.
Both regular and profiler configurations pass that test and the existing
1,900-frame no-save contract. RomFS bounds/header and packaged route bytes
were verified for the NROs; the console successfully reads the bundled files.

Full artifacts, transcripts and validated reports live under
`build/gameplay/<id>/`. Desktop references are in `reference600/` for Mario and
`reference1200/` for Adventure Island. Each title's `comparison.json` records
the baseline and profiler hashes, platform settings, per-frame cost estimates
and state checks. The exact as-built engine patch is archived as
`build/gameplay/nesrecomp-switch-bf29404734a8.patch`.

These are short first-level windows with one unprofiled run per scene, not
campaign-wide performance qualification or statistical confidence intervals.

## Reproduce

```sh
python3 scripts/build-game.py smb1 --rom SMB.nes --version 0.2.8 --variant optimized --benchmark-input games/smb1/tests/gameplay.txt --output-dir build/gameplay/smb1/baseline
python3 scripts/build-game.py smb1 --rom SMB.nes --version 0.2.8 --variant optimized --benchmark-input games/smb1/tests/gameplay.txt --profile-core --output-dir build/gameplay/smb1/profile
```

After a heads-up and reopening NetLoader for each test:

```sh
python3 scripts/netload-game.py smb1 --package-dir build/gameplay/smb1/baseline --ip 192.168.1.195 --console --benchmark --gameplay --warmup 300 --frames 600
```

Omit `--gameplay` for the neutral comparison; use `profile/` for instrumented
gameplay. Adventure Island uses its European ROM, version 0.1.6, warm-up 900
and total 1,200. `scripts/analyze-gameplay.py --help` describes the report tool;
it checks executable identity, route identity, state references, equal runtime
settings, complete windows and profiler coverage. Profiling remains OFF in
normal builds. `--benchmark-input` is optional, and subsequent ordinary builds
clear the RomFS cache setting when it is omitted.

The isolated engine follow-up is
`patches/nesrecomp-switch-gameplay-replay.patch`, applying after the previous
sprite-benchmark source state. A separate Git index verified it reconstructs
the current engine source exactly. The cumulative patch includes it as well.
No system package was installed; generated assets and reports can be removed
by deleting `build/gameplay/` and per-title `benchmark-assets/` build folders.
