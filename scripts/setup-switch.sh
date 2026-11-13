#!/bin/bash
# Run as your normal user; sudo prompts happen only in your Terminal.
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p .local/setup
if [[ ! -x /usr/local/bin/dkp-pacman ]]; then
  printf '%s\n' 'Install the official devkitPro pacman package first; see docs/TOOLCHAIN.md.' >&2
  exit 1
fi
if [[ ! -f .local/setup/devkitpro-before.txt ]]; then
  /usr/local/bin/dkp-pacman -Q > .local/setup/devkitpro-before.txt
fi
# Refresh and upgrade together: devkitPro supports a consistent current SDK.
sudo /usr/local/bin/dkp-pacman -Syu --needed --noconfirm switch-dev switch-sdl2
/usr/local/bin/dkp-pacman -Q > .local/setup/devkitpro-after.txt
bash scripts/verify-tools.sh
