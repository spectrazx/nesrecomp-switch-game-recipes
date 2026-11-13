# Vanilla Mario test — 2026-11-13

This records the original **0.1** build. The user subsequently confirmed boot,
demo playback, game start, controls and music on Switch, but reported slow
execution and a save error. The current **0.2** build disables saving and
targets performance; see [the new test record](PERFORMANCE_V2.md).

The user's `SMB.nes` was copied to ignored `.local/roms/SMB.nes`. Both files
retain SHA-256 `f61548fdf1670cffefcc4f0b7bdcdd9eaba0c226e3b74f8666071496988248de`.
The supplied ROM passes the upstream audited mapper-0 profile, payload CRC
`D445F698`. No ROM or generated game C is included in the tracked contribution.

## Produced artifact

The archived `build/smb1/hardware-v1/SuperMarioBrosRecomp.nro` is 10,242,245 bytes. NRO0 sections,
asset section, NACP size and title (`Super Mario Bros. Recomp`) passed checks.
An identical copy is staged under:

```text
build/smb1/sd-card/switch/nesrecomp/smb1/SuperMarioBrosRecomp.nro
```

The Mac compiler generated the vanilla host code. The official ARM64 devkitPro
Docker image built a Linux host compiler and cross-compiled the Switch target.
The nine generated C units match byte for byte across Mac/Linux. The final
target uses LLE PPU, the existing core and the new Switch host. Inspection of
its build graph found no mod plugins, mod runtime C++, HD packs, recomp-ui,
netplay, desktop TCP or chat frontend. Generic inactive C hook registries
remain part of the shared core as intended.

## Results

| Check | Result |
| --- | --- |
| Vanilla host title boot | Passed, 600 frames; screenshot inspected |
| Scripted route | World 1-1, movement and jumping, 1800 frames |
| Recompiled CPU coverage | No interpreted ROM cycles in the tested route |
| Native vs interpreter | All 1800 complete frame-hash lines identical; final PNG identical |
| Save/reload at frame 600 | Resumes at frame 601; all remaining 1199 frame hashes and final PNG identical |
| Audio generation | 48 kHz mono, 29.949 seconds, nonzero samples; peak 8001 |
| Actual Switch SDL host on the Mac | Dummy-video/audio boot and automatic resume passed, frames 600 then 1200 |
| Paced dummy-driver loop | 600 frames in 9.977 seconds; 14 audio chunks dropped |
| Switch cross-build and NRO packaging | Passed |
| Physical Switch boot, input, graphics, audio and suspend | Not tested; no console connected |

The independent TriCNES reference matched CPU/bus trace hashes, register state,
cycle counts and memory hashes (including raw 9-bit pixel output) for every
scripted frame. Its internal hardware hash and RGB palette conversion differ
from NESRecomp's; full oracle parity is therefore not claimed. The title and
gameplay screenshots were inspected. No core palette or hardware implementation
was changed for this test.

The reference initially failed Apple Clang's C++ narrowing check. A separate
oracle build with `-DCMAKE_CXX_FLAGS=-Wno-c++11-narrowing` succeeded; this flag
was confined to the reference build, with no source changes.

Dummy-driver audio is an automated pipeline check. The observed dropped chunks
mean stable console audio must still be established on hardware. Uncapped
dummy-driver runs intentionally generate audio faster than real time and also
drop chunks at the bounded queue; they are not playback-quality measurements.

## Original 0.1 SD layout and controls

The current README has the 0.2 copy commands and controls. The save controls
below apply only to the original 0.1 build.

Copy the contents of `build/smb1/sd-card/` to the SD root, then copy your original
`SMB.nes` into the same game folder under the name `rom.nes`:

```text
sdmc:/switch/nesrecomp/smb1/
  SuperMarioBrosRecomp.nro
  rom.nes
```

Launch the NRO from the homebrew menu. This is a prototype for a physical
playtest; the HOME-menu forwarder remains a separate step. First verify that
the title appears and World 1-1 is playable with sound, then test:

- D-pad / left stick: move; Nintendo A/B: NES A/B; Plus/Minus: Start/Select.
- ZL: quick save; ZR: load that slot after it has been saved.
- L + R + Plus: save and exit.
- Relaunch: automatic resume. Hold Nintendo X at startup to start fresh.
- HOME, sleep/wake and close/relaunch: check that progress and audio resume.

`runtime.log` and `saves/` are created in the same SD directory. Back up saves
before replacing a build; state compatibility between executables is limited.

## Reproduce

From this workspace:

```sh
NESRECOMP_SMB_ROM="$PWD/.local/roms/SMB.nes" bash scripts/build-smb.sh
python3 scripts/test-smb.py --rom "$PWD/.local/roms/SMB.nes"
python3 scripts/inspect-nro.py build/smb1/SuperMarioBrosRecomp.nro
```

These compatibility commands now delegate to [the game module](../games/smb1/README.md).
New host/test output uses `build/games/smb1/`; the wrapper retains the NRO path
above. The following are archived 0.1 evidence paths.

Build log: `build/smb1/build.log`. Native test route, screenshots, hashes,
state and WAV: `build/smb1/tests/`. Machine-readable results:
`build/smb1/tests/summary.json`. The script uses the already-built oracle if
`.local/src/nesrecomp/build/smb-oracle/cyc_oracle` exists; otherwise the
native/interpreter/save checks still run and oracle results are omitted.

The additional native Switch-host harness is under
`build/smb1/switch-host-runtime/`, with separate boot, resume and paced logs.
It reuses the actual Mario generated-source manifest with `runner/switch/host.c`
and dummy SDL drivers. It does not run the Switch executable itself.
