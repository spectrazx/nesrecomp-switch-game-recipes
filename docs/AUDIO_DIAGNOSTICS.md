# Live audio and frame diagnostics — 2026-11-14

The user confirmed network loading works. Mario 0.2.5 felt nearly playable but
its music sounded distorted or slow; Adventure Island remained clearly slow.
The user requested a heads-up before uploads and supplied the current Switch
address `192.168.1.195`, with hbmenu NetLoader on TCP 28280.

## First measured live test: Mario 0.2.6

The diagnostic runner mirrors infrequent host reports over nxlink while
retaining the SD log. The source audio generation, sample rate, frame pacing,
graphics and save policy are unchanged. Console profiling is OFF; saving is
OFF. This version adds instrumentation, not a speed or audio playback fix.

The physical console accepted the upload and streamed logs to the Mac:

| Measurement | Result |
| --- | --- |
| Artifact SHA-256 | `165fd8252989e7808bb368c079cd93cc827ec15d5292a695db11cafb9894eaba` |
| Emulated frames / real seconds | 1,800 / 63.037 |
| Overall FPS / target | 28.55 / 60.099 |
| Typical steady emulation / presentation | about 34 ms / 1.4 ms |
| Generated PCM duration / elapsed time | 0.4752 |
| Pre-enqueue empty software-queue polls | 1,760 / 1,800 |
| Device / source audio rate | 48,000 / 48,000 Hz |
| Device channels / format / buffer frames | 2 / signed 16-bit / 1,024 |
| Interpreted ROM/RAM cycles | 0 / 0 |
| Dropped excess chunks / saves | 0 / 0 |

The log establishes a sustained shortage of generated audio relative to wall
time. The speaker consumes audio in real time; the emulator generated only
about 47.5% of the duration needed for continuous playback during this run.
That supports gaps/starvation as a contributor to the reported distortion.
It does not establish that every audible artifact has the same cause.

`dropped_audio_chunks=0` does not rule out starvation: that counter only tracks
output discarded when the queue is too full. Empty software-queue polls are
not hardware underrun counts, because SDL can have submitted another buffer to
the audio backend. The supply ratio is the stronger evidence here.

This run is slower than the earlier Mario 0.2.4 SD test (46.69 FPS). It is not
valid to attribute that difference to an optimization or to networking yet:
the manual scenes/launch conditions were not controlled, the first live build
does not report CPU clocks or application mode, and ARM kernels had not had a
paired console benchmark. Later diagnostic builds add read-only clock and
launch-mode reports to help establish a controlled comparison. No clocks are
changed by these diagnostics.

Evidence, including the actual NRO, local build/send manifests and complete
console transcript, is archived in `build/games/smb1/hardware-v0.2.6/`.
Its `summary.json` records the weighted supply ratio and overall throughput.
The SD is not mounted; the report was collected entirely through the network.

## Adventure Island follow-up

Adventure Island 0.1.4 was built with the same supply diagnostics plus clock
and launch-mode reporting. The first attempt found NetLoader closed; after the
user reopened it, the retry successfully uploaded, launched and streamed the
complete 900-frame test. Both attempt logs are preserved.

| Measurement | Result |
| --- | --- |
| Artifact SHA-256 | `988fc45561518ffc0161f92f19a927ce5688fa3d06e68d12908951db92e766df` |
| Emulated frames / real seconds | 900 / 36.203 |
| Overall FPS / PAL target | 24.86 / 50.007 |
| Weighted emulation / presentation | 38.597 ms / 1.364 ms |
| Generated PCM duration / elapsed time | 0.4973 |
| Pre-enqueue empty software-queue polls | 900 / 900 |
| CPU clock, every read successful | 1,020,000,000 Hz throughout |
| Launch / operation / performance mode | Application / handheld / normal |
| Interpreted ROM/RAM cycles | 0 / 0 |
| Dropped excess chunks / saves | 0 / 0 |

The application is not running in library-applet mode. Device-clock reads are
successful and stable; the diagnostics do not alter clocks. Audio supply is
again insufficient for continuous playback. About 38.6 ms per frame is spent
in emulation, against a roughly 20 ms PAL frame budget; presentation takes only
about 1.36 ms. This points to emulation work as the main cost in this run.

The earlier 0.1.2 measurement was 22.98 FPS, but these short manually played
scenes are not a paired benchmark and do not establish a speed gain. Mario's
separate 0.2.6 run still lacks clock readings, so Adventure Island's clock
cannot retrospectively explain Mario's slower result.

Evidence is archived in `build/games/adventure-island/hardware-v0.1.4/`, with
the exact executable, manifests, successful console transcript and summary.
The workspace's Adventure Island version advances to 0.1.4 after this verified
local-package upload/test. Ordinary on-card NRO/manifests are preserved because
network testing uses the separate `*-dev.nro` entry.

## Validation and upstream boundary

The native SDL dummy-driver contract passed its 1,900-frame paced no-save run.
It checks positive produced/wall durations, near-real-time supply at full
speed, preservation of existing save files, and native fallback when the
network option is requested outside Switch. Both real game packages cross-build
against the existing pinned devkitPro SDK, and embedded versions are checked.
Both diagnostic packages have successful console runs. Read-only clock and
launch-mode reporting is physically verified by the Adventure Island test.

The isolated engine delta is
`patches/nesrecomp-switch-audio-diagnostics.patch` against local commit
`56b926508dea5d86fd4f58801afb2dfe30560be5`. It is also included in the cumulative
Switch patch. It remains an uncommitted local contribution pending review;
no upstream PR is opened. Network-send orchestration and manifests belong to
this workspace; generic runner metrics and opt-in logging belong to the engine.

Before claiming an audio fix, measure production at the original game rate
and audition the result on hardware. Increasing buffering alone cannot fix a
sustained supply ratio below 1. A mature emulator backend remains a separate
candidate for evaluation, as described in [the pNES notes](PNES_REFERENCE.md).
