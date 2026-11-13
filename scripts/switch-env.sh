# Source this file in the shell used for Switch builds:
#   source scripts/switch-env.sh
export DEVKITPRO=/opt/devkitpro
export DEVKITA64="$DEVKITPRO/devkitA64"
export PATH="$DEVKITA64/bin:$DEVKITPRO/tools/bin:$DEVKITPRO/portlibs/switch/bin:$PATH"
