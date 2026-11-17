# Portable C versus explicit NEON on Switch

This experiment tests the HLE sprite kernels on the actual Cortex-A57. The
portable C implementation remains eligible for compiler auto-vectorization;
it is not a promise of scalar machine code. The other build selects the
explicit AArch64 intrinsics added earlier. Both use HLE, Release `-O3`, LTO,
48 kHz audio, the same region/ROM and saves/profiling OFF.

The first packages are Mario **0.2.7** and Adventure Island **0.1.5**. Each
kernel has an isolated output directory under `build/sprite-ab/<game>/`, with
its NRO and manifest. The ordinary packages under `build/games/` are preserved.
The title version is the same for both kernels; manifests, SHA-256 hashes and
the runtime `Sprite_kernel`/`benchmark kernel` fields identify the variant.

## Build and desktop correctness

```sh
python3 scripts/build-game.py smb1 --rom SMB.nes --version 0.2.7 --variant optimized --sprite-kernel portable --output-dir build/sprite-ab/smb1/portable
python3 scripts/build-game.py smb1 --rom SMB.nes --version 0.2.7 --variant optimized --sprite-kernel auto --output-dir build/sprite-ab/smb1/neon
```

Use `adventure-island`, its supplied European ROM and version `0.1.5` for the
other title. The builder uses separate portable host/SDK build directories and
sets `NESRECOMP_PPU_HLE_FORCE_PORTABLE=1` only on that target. The default is
still `auto`; this experiment does not select a new shipping default.

Both titles' ARM Mac executables match all 1,800 scripted gameplay frame
records, PCM WAV bytes and final PNG bytes. Evidence is under
`build/sprite-ab/<game>/correctness/`. This validates output equivalence on those
routes, not Cortex-A57 throughput. The earlier exhaustive kernel/SDK tests
remain relevant because the kernel implementations themselves are unchanged.

The reusable check, after building both optimized host variants, is:

```sh
python3 scripts/verify-sprite-pair.py adventure-island --rom 'Adventure Island Classic (Europe).nes' --out build/sprite-ab/adventure-island/correctness
```

The frontend's ROM-free SDL dummy-driver contract also passes its 1,900-frame
no-save run, plus two independent 900-frame neutral-input benchmark runs.
Each reports exactly 600 measured frames after 300 warm-up frames, completes
without focus interruptions and ends with identical memory/hardware hashes.

## Controlled console procedure

Give the user a heads-up and wait for hbmenu NetLoader to be open at the
currently confirmed address `192.168.1.195`. Keep the console handheld and do
not change its power/settings during the comparison. Each upload needs a new
NetLoader opening after the previous test returns to hbmenu.

Add `--wait-netloader 120` to wait for readiness. This sends hbmenu's standard
UDP `nxboot` discovery message and waits for its `bootnx` reply from the
specified address. It does not open or consume the TCP upload connection, so
the user can simply press Y after each announced test without typing a reply.
The readiness check runs on the Mac before starting the SDK container; no
extra package is installed. An unanswered discovery request does not prove
the console is offline, since local firewalls can block UDP.

```sh
python3 scripts/netload-game.py smb1 --package-dir build/sprite-ab/smb1/portable --ip 192.168.1.195 --console --benchmark --frames 900
python3 scripts/netload-game.py smb1 --package-dir build/sprite-ab/smb1/neon --ip 192.168.1.195 --console --benchmark --frames 900
```

`--benchmark` leaves the NES controller input neutral, so the original game
runs its built-in demo; **do not play during these tests**. The normal exit
chord remains available. No title addresses or gameplay replacement code are
introduced. Both variants exclude the same first 300 emulated frames, measure
frames 301–900, keep audio/rendering enabled, and run uncapped to measure
available throughput. Normal play retains its original pacing.

Every test reports its measured emulation/audio/presentation time, throughput,
audio production ratio, observed CPU clock and launch modes. It records focus
loss after warm-up as an interruption. Final memory/raw-picture and hardware
hashes are computed once **after** measured time; per-frame tracing is off.
This final-state check complements the separate desktop per-frame comparison.

Prefer portable → NEON → NEON → portable (ABBA) for each title. Two runs give
a preliminary comparison; four allow checking repeatability and order effects.
The comparison tool requires successful full-application clock reads, stable
and matching platform/clock fields, equal ROM/engine patch/version, completed
600-frame measurement windows, zero interruptions and equal final states:

```sh
python3 scripts/compare-switch-kernels.py PATH_TO_A1_LOG PATH_TO_B1_LOG PATH_TO_B2_LOG PATH_TO_A2_LOG --out build/sprite-ab/smb1/comparison.json
```

Logs remain in their corresponding package directories. The tool verifies the
log's executable hash against that directory's manifest and actual NRO. It
reports means, within-kernel spread and NEON's percentage reduction in emulation
time; a negative reduction means the explicit NEON path costs more time.
It labels a two-run comparison preliminary and does not automatically change
defaults or claim statistical confidence from four runs.

## Physical results — Mario

All four Mario runs completed with full application mode, handheld operation,
normal performance mode and observed CPU clock 1.02 GHz. Saves and profiling
were OFF. All memory/raw-picture and internal hardware hashes match:
`E605AC24D4DFC887` / `A5CCB0D7A01E7FCD`.

| Order | Kernel | Measured FPS | Emulation ms/frame |
| --- | --- | --- | --- |
| A1 | Portable C | 25.373 | 37.770949 |
| B1 | Explicit NEON | 28.019 | 34.063076 |
| B2 | Explicit NEON | 28.058 | 34.084044 |
| A2 | Portable C | 25.417 | 37.778545 |

Mean emulation cost falls from **37.774747 ms to 34.073560 ms**, a **9.80%**
reduction with explicit NEON. Within-kernel emulation-time ranges are only
0.020% (portable) and 0.062% (NEON). Mean throughput rises from **25.395 FPS
to 28.0385 FPS**. These four observations support keeping NEON for this demo;
the implementation was already enabled, so this is qualification of an
existing optimization, not a new speed improvement in version 0.2.7.

The test does not reach the 60.099 FPS NTSC target. Its mean audio supply is
about 0.467 of real time with NEON, versus 0.423 with portable C. It also does
not explain the earlier 46.69 FPS manual-play result: those scenes and launch
conditions were not matched to this neutral-input demo. A deterministic
gameplay route is needed before comparing title-demo and in-level performance.

The executable hashes are `fb35f635f967e99dd7f3ac6fd2031d1626873a3fcb1055372d51c1e057afd43a`
(portable) and `b3499abe7ca9be9ffd4a821056ab4255b5314a6f209f6c0684f13378213658d8`
(NEON). Complete validated evidence is in `build/sprite-ab/smb1/comparison.json`.
The exact as-built cumulative engine patch, SHA-256
`6cf9e66eea5dfb4de09621bd23bd3b38f0b1335f5a71a549258f825ada353e42`,
is archived at `build/sprite-ab/nesrecomp-switch-6cf9e66eea5d.patch`.

## Physical results — Adventure Island

The PAL title completed the same four-run design at observed CPU clock
1.02 GHz, full application/handheld/normal mode. No interruptions were
reported. Every run ended with matching memory/raw-picture and hardware
hashes: `304AB0EB19B67AD5` / `8702C21D8D628CEF`.

| Order | Kernel | Measured FPS | Emulation ms/frame |
| --- | --- | --- | --- |
| A1 | Portable C | 23.259 | 41.496942 |
| B1 | Explicit NEON | 25.327 | 38.011077 |
| B2 | Explicit NEON | 25.366 | 37.965944 |
| A2 | Portable C | 23.255 | 41.499980 |

Mean emulation cost falls from **41.498461 ms to 37.988511 ms**, an **8.46%**
reduction with NEON. Within-kernel emulation-time ranges are 0.0073% (portable)
and 0.119% (NEON). Mean throughput rises from **23.257 FPS to 25.3465 FPS**.
Mean audio supply rises from about 0.465 to 0.507 of real time, still below
the amount needed for uninterrupted playback at the original game speed.

The executable hashes are `4da81a3b1b746fc821f02c0631dd874372d39c9efcdea7b2b61a81cec65ea240`
(portable) and `e6dd48a13fba10de483ae07b04c018a44ed000cba7ce4fb7398f4a632bee6818`
(NEON). The validated report is
`build/sprite-ab/adventure-island/comparison.json`. All eight console tests
passed their completion, state, clock, region and audio-setting checks.

## Outcome and normal packages

Keep the existing automatic ARM kernel selection: NEON helps both measured
demos. Versions 0.2.7/0.1.5 add measurement tooling; they do not introduce a
new renderer optimization or audio playback fix. The source version counters
advance to these tested versions. The verified NEON NRO/manifests are prepared
at the normal `build/games/<id>/` paths, and ordinary netload tasks use those
packages. Without benchmark arguments, physical controls and normal pacing
remain active.

Each four-run sequence ends with the portable test entry on SD. After the
measurements, restore NEON through a quick `--console --frames 1` upload for
each title. This checks `Sprite_kernel=neon benchmark=0` and returns immediately
to hbmenu. These command-line flags are per launch; they are not saved in the
NRO. The ordinary on-card NRO and its older manifest are separate from the
temporary `*-dev.nro` entry and are not rewritten by netload.

Both restoration uploads completed successfully: Mario 0.2.7 and Adventure
Island 0.1.5 report `Sprite_kernel=neon benchmark=0` and exit after the one
requested frame. Their receipts and logs are archived under
`build/sprite-ab/restored/<game>/`. Both temporary entries now contain NEON;
opening them normally starts ordinary play without benchmark arguments.
The combined comparison/restoration summary is `build/sprite-ab/summary.json`.

The measured demo routes still miss 60.099 FPS (Mario) and 50.007 FPS
(Adventure Island). The next useful measurement is a deterministic in-level
route and PPU profile under the same console conditions. These data do not
establish why the earlier manually played Mario session averaged 46.69 FPS.

## Contribution boundary

The existing core macro already selects portable kernels. Target selection,
isolated build/package directories and comparison orchestration belong to this
workspace. The shared Switch frontend adds only opt-in measurement behavior:
neutral input, fixed-frame warm-up, aggregate reports and final-state checks.
Its additions are included in the cumulative engine patch. The existing
`nesrecomp-switch-audio-diagnostics.patch` retains the preceding isolated
audio/logging delta against `56b9265`; the newer benchmark addition is not
included in that older isolated patch. The new
`nesrecomp-switch-sprite-benchmark.patch` applies after the audio patch;
applying both to `56b9265` reconstructs the current engine source exactly.
This was verified with a separate Git index without changing the real index.
No PR is opened.

No new system tool is installed. Delete `build/sprite-ab/` and the per-game
`*-dev.nro` test entries to remove experiment artifacts. Regular builds and
ordinary on-card packages are separate from this experiment.
