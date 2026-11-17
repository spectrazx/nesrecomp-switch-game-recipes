# pNES / Nestopia reference — 2026-11-14

[pEMU's pNES target](https://github.com/Cpasjuste/pemu/tree/master/src/cores/pnes)
is a frontend for **Nestopia**, not a separate engine called the pNES core.
Its CMake file compiles Nestopia's C++ CPU, PPU, APU, cartridge and controller
sources and connects them to pEMU/libcross2d for platform input, audio and
display. The target excludes several optional software scaling/NTSC filters.
Our runner already omits those filters, so that setting is not a newly found
optimization for us.

Read-only, nonrecursive research checkouts were created under `.local/src/`:

| Project | Revision |
| --- | --- |
| `pemu-reference` | `eeb5199ee0657b87f65197cbb043e5014befffbd` |
| Its pinned `nestopia-reference` | `3746b104d875670df07e49295d40eba7ad4c8a44` |
| libcross2d recorded by pEMU, not downloaded | `9dfe2fcb4ccb2dd7be04718ee7ddb450abd85de1` |

No pEMU/Nestopia implementation was copied into our runner. Neither reference
has been built or measured on the user's Switch. The frontend sets a target of
50 FPS for PAL and 60 FPS for NTSC; that assignment alone is not a measured
throughput result. The library's Switch compiler and clock policy lives partly
in libcross2d, which this inspection did not qualify.

## Useful implementation differences

Nestopia's CPU executes instructions until the next scheduled clock boundary.
Its clock scheduler considers APU, interrupt and frame deadlines. PPU register
accesses and synchronization hooks bring its PPU up to the corresponding CPU
timestamp; end-of-frame processing finishes pending graphics work.

This reduces repeated coordination between CPU and PPU while retaining detailed
graphics processing. It is not equivalent to drawing an entire frame from its
final register values. Its renderer still handles pixels, sprites, scrolling
and timed events; its internal representations and synchronization strategy
differ from NESRecomp's.

The most relevant sources are
[CPU scheduling](https://github.com/Cpasjuste/nestopia/blob/3746b104d875670df07e49295d40eba7ad4c8a44/source/core/NstCpu.cpp)
(`Clock`, `ExecuteOp`, `Run0`) and
[PPU synchronization/rendering](https://github.com/Cpasjuste/nestopia/blob/3746b104d875670df07e49295d40eba7ad4c8a44/source/core/NstPpu.cpp)
(`Sync`, `Update`, `EndFrame`, `RenderPixel`). These are mechanisms worth
investigating, not proof of which mechanism dominates its Switch performance.
NESRecomp already batches some safe intervals, so comparisons should measure
what additional coordination can actually be removed.

The PPU is not a ready-made standalone graphics library: `Ppu` is constructed
with a Nestopia `Cpu&` and uses its timing, memory callbacks and interrupts.
Keeping our recompiled CPU while importing this PPU would require an adapter
for those contracts, mapper events, state serialization and accuracy checks.
CPU/PPU state from the two engines cannot simply be interchanged.

## Practical choices

1. **Use pNES as a console reference.** Test the same ROM revisions, region,
   scene and original sprite limit. Compare sound, partial sprite flicker and
   frame rate under the same power/application conditions. This separates
   expectations about the game from our current implementation's behavior.
2. **Study Nestopia's scheduling and representation choices.** Prototype one
   measured change in NESRecomp, preserve its existing state/timing contracts,
   and run independent pixel/audio checks. This keeps our native game hooks.
3. **Consider a complete Nestopia backend for simple game launchers.** A small
   per-game frontend could offer launch/input/save behavior without a ROM
   browser. That would be an emulator-backed application, with a different
   path for deep native enhancements. ROM/data patches could still work;
   NESRecomp's C hooks and enhancement modules would need new integration.

The user's original goal—easy individual games—does not require static
recompilation. A mature emulator backend deserves evaluation if time to
full-speed play matters more than retaining this particular recompilation
architecture. This investigation does not switch the project's backend or
promise full speed before testing it. Importing implementation code would
also require reviewing the projects' license terms.

Primary frontend sources:
[build](https://github.com/Cpasjuste/pemu/blob/eeb5199ee0657b87f65197cbb043e5014befffbd/src/cores/pnes/CMakeLists.txt),
[execution and audio adapter](https://github.com/Cpasjuste/pemu/blob/eeb5199ee0657b87f65197cbb043e5014befffbd/src/cores/pnes/sources/pnes_ui_emu.cpp).

## Remove research files

These are ordinary sparse clones, with no globally installed tools or initialized
submodules. Delete `.local/src/pemu-reference/` and
`.local/src/nestopia-reference/` to remove them.
