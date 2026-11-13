#!/bin/bash
# Compatibility entry point; the title recipe lives in games/smb1/.
set -euo pipefail
cd "$(dirname "$0")/.."
: "${NESRECOMP_SMB_ROM:?Set NESRECOMP_SMB_ROM to your original Mario ROM path}"
args=(smb1 --rom "$NESRECOMP_SMB_ROM" --output-dir "$PWD/build/smb1")
if [[ -n "${NESRECOMP_SWITCH_PPU:-}" ]]; then
  args+=(--ppu "$NESRECOMP_SWITCH_PPU")
fi
exec python3 scripts/build-game.py "${args[@]}" "$@"
