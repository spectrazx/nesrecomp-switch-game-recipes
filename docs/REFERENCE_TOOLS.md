# Independent PAL reference on macOS

MesenCE is a test dependency only. It is not linked into the Switch games.
The existing NESRecomp capture helper now accepts `--region ntsc|pal` (default
NTSC) and optional `--memory` snapshots. Its native Mac build uses the supplied
MesenCE libretro checkout with no .NET UI or new system packages.

The tested source is [libretro/MesenCE](https://github.com/libretro/MesenCE),
pinned at `562ee84de49acbd7866d0c079e61f0dc52cc27f4`. Tracked emulator sources
are unmodified. The helper reads raw PPU output and optional RAM/OAM/palette
memory; it does not change the emulator's algorithms. Build logs and all
private captures stay in ignored directories.

## Setup and reproduction

From the workspace root:

```sh
git clone https://github.com/libretro/MesenCE.git .local/src/MesenCE-libretro
git -C .local/src/MesenCE-libretro checkout --detach 562ee84de49acbd7866d0c079e61f0dc52cc27f4
bash .local/src/nesrecomp/tools/cyc/mesen_shot/build.sh \
  .local/src/MesenCE-libretro build/reference-tool
python3 games/adventure-island/tests/reference.py \
  --rom .local/roms/adventure-island-europe.nes \
  --out build/adventure-reference-new
```

Skip cloning when the checkout already exists; the reference test checks its
revision and refuses tracked source edits. Use a new `--out` directory for each
experiment. Apple Clang and Make are from the existing Xcode tools. The driver
uses an explicit library run path; it needs no global loader/environment changes.
The existing Windows `build.ps1` helper remains available separately.

The title-specific test verifies the ROM revision, builds the reference tool,
and compares all 256 zero-page bytes at two title frames before any input.
NESRecomp frame 299 matches Mesen frame 300; frame 599 matches 600. Both the
frame counter and random-state bytes agree. It then applies the same one-frame
offset to input and screenshots. This calibrates boot timing before gameplay;
it does not shift pictures individually to force agreement.

With PAL timing, zeroed RAM and that fixed calibration, **all 903 frames from
899 through 1801 match pixel-for-pixel**, including the NEON candidate. The
comparison uses 256×240 raw nine-bit color indices, bypassing RGB palette
differences. It covers a first-level route, not every level or user input.
It does not prove that reported console glitches are normal or resolved.

The initial unaligned comparison differed in 36 frames around the player.
Those differences disappear with the boot offset independently established
from pre-input RAM. This is why the reference check includes calibration.

## Switch compiler kernel check

```sh
bash scripts/check-switch-kernels.sh
```

This compiles native and portable pure kernels with devkitA64 GCC 15.2 and
Cortex-A57 flags, then links those AArch64 objects into a native Linux test
program. A small assertion shim bridges newlib's assertion symbol to Linux.
It verifies SIMD instructions and byte results without pretending to run a
Switch application. Game lifecycle, display output and actual speed still
require physical hardware.

## Remove the reference tools

No system installation was performed. These commands remove only the added
reference checkout and the example build directories:

```sh
rm -rf .local/src/MesenCE-libretro
rm -rf build/reference-tool build/switch-kernels build/adventure-reference-new
```

The local investigation also uses `build/visual-investigation/`; remove that
directory if its private captures are no longer wanted. Game builds and
archived SD logs under `build/games/` are separate. Reproduction source and
contribution patches remain tracked in this repository.
