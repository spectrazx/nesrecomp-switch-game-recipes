# Faster development and console testing

## Send builds over Wi-Fi

hbmenu's NetLoader receives and launches NROs with `nxlink`. The scripts below
use native nxlink if present, otherwise the **existing pinned devkitPro Docker
image**. No new system tool is required. The Docker route uses an explicit IP
instead of relying on broadcast discovery across Docker Desktop's network.

1. Keep the Switch and Mac on the same reachable local network. Start Docker
   if using the existing container SDK.
2. Keep the existing per-game folders and `rom.nes` on the SD. The first
   `mise run copy` / `copy-adventure` deployment supplies those files.
3. Exit the game, open hbmenu in the same application mode used for ordinary
   tests, and press **Y** to enter NetLoader. Use the local IPv4 address shown
   there.
4. Send the existing package from the repository root:

```sh
NESRECOMP_SWITCH_IP=192.168.1.123 mise run netload
NESRECOMP_SWITCH_IP=192.168.1.123 mise run netload-adventure
```

Replace the example IP with the Switch's address. For a new local build, run
`mise run build` or `mise run build-adventure` first. These development commands
retain the current version. The regular SD copy tasks still advance versions
after successful verified deployment.

The current console address is **192.168.1.224** (2026-11-15). This workspace
stores it in ignored `mise.local.toml`, so `mise run netload` and
`mise run netload-adventure` work without an explicit IP. Update the local
override when DHCP changes it:

```sh
mise set --file mise.local.toml NESRECOMP_SWITCH_IP=192.168.1.224
mise exec -- python3 scripts/netload-game.py adventure-island --dry-run
```

The sender checks the local executable's manifest SHA-256 and embedded version
before sending it. It uploads a **separate `*-dev.nro`** beside the normal NRO,
so the ordinary executable and its on-card `build.json` remain paired. The
development build uses the same per-game ROM/log directory. A successful send
records its local hash/version in `build/games/<id>/netload.json`. nxlink's
acknowledgement is not an independent remote SHA-256 readback.

Paths passed to nxlink are relative to hbmenu's `sdmc:/switch/` root. For Mario,
the upload argument is `nesrecomp/smb1/SuperMarioBrosRecomp-dev.nro`.

To validate locally and print the command without contacting the console:

```sh
python3 scripts/netload-game.py smb1 --ip 192.168.1.123 --dry-run
```

Mario **0.2.5** was successfully uploaded and launched on the user's console.
Mario **0.2.6** also passed the live-console upload/test below. These commands
send the NRO only, not the ROM or a new SD manifest. Ordinary sends retain
SD-only logging and do not initialize the runner's networking support.

### Live frame/audio diagnostics

New builds accept opt-in `--nxlink-log`. To send one, collect its diagnostics
on the Mac and exit after a fixed number of emulated frames:

```sh
mise exec -- python3 scripts/netload-game.py smb1 --console --frames 1800
mise exec -- python3 scripts/netload-game.py adventure-island --console --frames 900
```

These commands use the local IP override described above; it can change.
**Give the user a heads-up and wait for NetLoader to be open before sending
each test.** Finishing a game returns to hbmenu, not automatically NetLoader.
The receiver's upload port is TCP 28280. Console output returns to TCP 28771;
the container task publishes this port and line-buffers nxlink output.

New manifests identify logging-capable builds, and the sender rejects console
mode for older packages. Output is saved in a uniquely named
`build/games/<id>/netload-<version>-<hash>.log`. The runner mirrors platform
timing/audio reports to stdout over nxlink and keeps `runtime.log` on SD.
Other core stdout messages also reach the console. This is a diagnostic mode;
ordinary launches make no network connection.

`--wait-netloader 120` waits up to two minutes for hbmenu's safe UDP discovery
reply before starting the upload. Give a heads-up first; the user can then
press Y without typing a separate readiness message. Direct sending remains
available if a local firewall blocks discovery.

Reports include FPS, emulation/presentation time, source PCM duration per wall
second, queued output and pre-enqueue queue observations. A sustained supply
ratio below 1 means real-time audio production is insufficient. An empty SDL
queue observation is **not** an exact hardware underrun counter: SDL may have
already passed audio to its backend. The existing `dropped_audio_chunks`
counter describes excess output discarded at the upper queue limit, not
shortage. Later diagnostic builds also read application/operation/performance
mode and CPU clock without changing clocks; failed clock reads are reported.

Mario 0.2.6 and Adventure Island 0.1.4 successfully streamed these reports on
the physical console; Adventure Island also verified the clock queries.
[Results and remaining uncertainty](AUDIO_DIAGNOSTICS.md).

Sources: [nxlink options](https://github.com/switchbrew/switch-tools/blob/master/src/nxlink.c),
[hbmenu receive/path handling](https://github.com/switchbrew/nx-hbmenu/blob/master/common/netloader.c).

## USB and log retrieval

If Hekate is already available, its **Tools → USB Tools → SD Card** mass-storage
mode exposes the Switch SD over a USB cable. macOS can mount it normally, so
our existing copy commands work using the actual mounted volume path. Safely
eject it before leaving USB storage and returning to the console firmware.
This avoids physical card removal but still requires leaving the game and
booting back after transfer. It does not require changing our game code.
[Hekate USB mass storage](https://github.com/CTCaer/hekate#features)

Another option is an FTP homebrew server to transfer packages and retrieve
`/switch/nesrecomp/<id>/runtime.log` after play. The pNES discovery does not
require installing one, and this task has not installed or configured one.
[ftpsrv](https://github.com/ITotalJustice/ftpsrv) is one implementation.
USB MTP is a further option, but it requires a compatible Mac client and a
Switch MTP application; it is not the same mounted-volume workflow as Hekate.

Live nxlink logs and fixed-frame exit are now available. A deterministic input
route through the Switch frontend remains a useful next extension: a fixed
frame count by itself does not make manually played scenes comparable.

## Use the Mac to screen optimizations

Mac tests are useful for correctness and reducing the number of console tests:

1. Run the same deterministic input route through baseline and candidate.
   Compare CPU/memory traces, pixels, audio and save continuation separately
   from the speed measurements.
2. Measure **process CPU time**, with audio enabled, the profiler disabled and
   no per-frame hash/screenshot capture. Warm both binaries, use A/A controls
   and alternate ABBA/BAAB order. Do not compile or run other benchmarks in
   parallel. Existing tooling is `tools/cyc/bench_host_work.py` in NESRecomp;
   [the Mario comparison](UPSTREAM_COMPARISON.md) provides a complete example.
3. Send only promising candidates to the console and measure emulation time
   and presentation separately. Compare the same scene, region, application
   mode and power state.

Both machines execute ARM64 instructions, but Apple's CPU and the Switch's
Cortex-A57 differ substantially in cache, branches, instruction throughput and
clock. We also use Apple Clang on Mac and devkitA64 GCC for Switch. A desktop
gain is a candidate, **not a predicted percentage or guaranteed console gain**;
even the ordering of two implementations can reverse.

Our evidence illustrates the limits: the PAL scheduler reduced desktop CPU by
23.92% and later raised console throughput by 22.48% (equivalent to about
18.35% less overall time per frame). ARM sprite kernels showed a modest Mac
Adventure Island gain but no demonstrated Mario gain on the desktop routes.
The later [controlled console demo tests](SPRITE_AB.md) establish 9.80% less
emulation time for Mario and 8.46% less for Adventure Island with NEON. These
are different routes and machines, illustrating why desktop percentages do
not predict console gains. An FPS increase and CPU-time reduction also use
different denominators, so their percentages should not be equated.

## Remove development transfer support

No tool was installed for network sending. Remove any `*-dev.nro` test entries
from the per-game SD folders when no longer wanted. The ordinary game package,
ROM, saves and settings do not need to change. The optional reference checkouts
and benchmark outputs have removal notes in [the comparison](UPSTREAM_COMPARISON.md)
and [pNES reference](PNES_REFERENCE.md).
