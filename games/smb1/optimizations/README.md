# Mario-specific optimizations

There is currently no Mario routine replacement or title-specific runtime
shortcut. HLE PPU and hardware batching live in NESRecomp's shared core;
`game.cmake` selects them for this title after validation.

A future title-specific static module belongs here and is explicitly listed
in `GAME_OPTIMIZATION_MODULES`. Its CMake file receives
`NESRECOMP_OPTIMIZATION_TARGET` and `NESRECOMP_OPTIMIZATION_HARDWARE`; it may
add target sources/includes/definitions using ordinary target-scoped CMake.
Paths inside the module should use `CMAKE_CURRENT_LIST_DIR`.

This is a build extension, not a runtime plugin or callback registry. It does
not automatically register mod hooks or replace generated routines. Any future
execution hook needs a separately reviewed timing/state contract; existing mod
hooks can skip bus cycles and are not an optimization API by default.

Each addition must state its ROM revisions and assumptions, preserve original
CPU/device timing, and compare execution, raw pixels and PCM with the baseline.
Assumptions shared by a cartridge family belong in a core hardware profile;
reusable algorithms belong in the core.
