# Runtime and game modules

The Switch frontend, shared NES implementation and title recipes have separate
owners. Game selection happens at build time; each output is still one NRO.
There is no module loader or new callback in the CPU/PPU hot paths.

```text
scripts/build-game.py <game> --rom <private ROM>
               |
games/<game>/game.cmake + game.toml + tests/ + optimizations/
               | selects a validated build
NESRecomp runner/cyc/project.cmake
               |-- profile.cmake / cyc_profile.h: checked hardware contracts
               |-- cyc CPU / PPU / APU / mapper implementation
               `-- runner/switch/: SDL, controls, audio queue, lifecycle, NRO
```

| Responsibility | Location | Example |
| --- | --- | --- |
| Platform behavior shared by all titles | NESRecomp `runner/switch/` | Controller mapping, presentation, save policy |
| Reusable emulation algorithms | NESRecomp `runner/cyc/` | Existing HLE PPU, sprite evaluation, scheduler |
| Checked cartridge-family assumptions | NESRecomp `runner/cyc/profile.cmake`, `cyc_profile.h` | `nrom-ntsc` board and timing contract |
| ROM revision, seeds, metadata, validated settings | `games/<id>/game.cmake` | Mario CRC, upstream seeds, HLE selection |
| Title-specific additions | `games/<id>/optimizations/` | Future static CMake modules and C sources |
| Gameplay routes and expected behavior | `games/<id>/tests/` | Mario's 1,800-frame route |
| Toolchain and build orchestration | `scripts/build-game.py`, `games/CMakeLists.txt` | Native generator, Docker SDK, packaging |

The Mario checkout supplies only its existing seed file. It is unchanged.
No Mario name, ROM address or routine selection is added to the Switch host.
The old `build-smb.sh` and `test-smb.py` commands delegate to the module layout.
`examples/smb-vanilla.toml` remains a compatibility example; the build reads
`games/smb1/game.toml`.

## Hardware contracts and static extensions

`nesrecomp_add_cycle_game` accepts optional `HARDWARE_PROFILE` and
`OPTIMIZATION_MODULES` arguments. Omitting them preserves the generic target.
The initial `nrom-ntsc` profile checks decoded mapper/submapper, console and
timing at configure time and checks the loaded cartridge/effective region at
startup. Existing ROM identity checks remain. This profile establishes checked
facts; it does not itself specialize the CPU or renderer.

A static module receives a target name and hardware profile and uses ordinary
`target_sources`, `target_include_directories` and `target_compile_definitions`.
It is trusted build code, included once for each requested target. It must use
target-scoped settings and paths relative to `CMAKE_CURRENT_LIST_DIR`; avoid
directory-wide flags and global include guards that would skip a second target.

The first interface does not automatically replace generated routines or
register runtime hooks. Such an extension will need an explicit timing and state
contract when a real optimization requires it. Existing gameplay mod hooks can
skip guest bus cycles, so they are not assumed suitable for transparent speedups.
Switch's existing `HOST_EXTRAS`/`MODS` exclusions remain in place.

There are currently **no Mario-specific execution shortcuts**. HLE PPU belongs
to the shared core; Mario's module selects it after validation. Future work
should put a generally useful algorithm in the core, qualify family-specific
assumptions through a hardware contract, and keep ROM-address assumptions in
the title module.

## Adding a title

1. Add `games/<id>/game.cmake`, `game.toml` and a `VERSION` file. Declare title, artifact name,
   payload CRC, mapper, seeds, hardware profile, baseline/optimized PPU choices
   and any explicit static modules. Use `generic` unless a checked contract fits.
2. Add an input route and title tests. Keep ROMs and generated code under ignored
   local/build directories. Verify the original ROM before code generation.
3. Build both variants, compare execution/raw pixels/PCM/state continuation,
   then measure frame time and audio on physical hardware before selecting a
   faster default. Native coverage alone does not establish full speed.

The framework's synthetic two-target profile test checks extension isolation.
The second module, [Adventure Island Classic](../games/adventure-island/README.md),
uses generic CNROM hardware with explicit PAL timing and its own seeds/tests.
Both renderer variants pass the desktop route; physical-console qualification
remains separate. Optional sampled core-clock diagnostics live in NESRecomp;
the workspace chooses which builds enable them.

## Refactor validation

Reproduction and contribution notes are in [UPSTREAM.md](UPSTREAM.md).
The baseline Mario route matches the pre-refactor 1,800 frame-hash records.
These checks validate this refactor, not every possible title or route. The
latest physical-console measurement remains the pre-refactor 0.2 result of
46.36 FPS; this change is preparation for subsequent performance work.
