#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."
bash scripts/prepare-sources.sh
engine="$PWD/.local/src/nesrecomp"
cmake -S "$engine/recompiler" -B "$engine/build/recompiler" -G Ninja -DCMAKE_BUILD_TYPE=Release
cmake --build "$engine/build/recompiler" --parallel 4
python3 "$engine/tools/cyc/test_switch_host.py" --out "$engine/build/switch-host-contract" \
  --recompiler "$engine/build/recompiler/NESRecomp"
image=devkitpro/devkita64@sha256:1fc388c3a0d34bd2045a6dadcb1020e069d5f876a187fd705de14b4440c00282
docker run --rm -v "$PWD:$PWD" -w "$engine" "$image" bash -c '
  set -euo pipefail
  cmake -S build/switch-host-contract/project -B build/switch-cross-fixture -G Ninja \
    -DCMAKE_TOOLCHAIN_FILE=/opt/devkitpro/cmake/Switch.cmake -DCMAKE_BUILD_TYPE=Release
  cmake --build build/switch-cross-fixture --parallel 4
'
python3 scripts/inspect-nro.py "$engine/build/switch-cross-fixture/switch_fixture.nro"
artifact=build/switch-fixture/switch/nesrecomp/fixture
mkdir -p "$artifact"
cp "$engine/build/switch-cross-fixture/switch_fixture.nro" "$artifact/fixture.nro"
cp "$engine/build/switch-host-contract/data/rom.nes" "$artifact/rom.nes"
printf 'Test program ready to copy from %s/build/switch-fixture/ to an SD card.\n' "$PWD"
