#!/bin/bash
# Execute SDK-generated pure AArch64 kernels in ARM64 Linux, without libnx.
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p build/switch-kernels
cat > build/switch-kernels/newlib-assert.c <<'EOF'
#include <stdio.h>
#include <stdlib.h>
void __assert_func(const char *file, int line, const char *function, const char *expression)
{
    fprintf(stderr, "%s:%d: %s: %s\n", file, line, function, expression);
    abort();
}
EOF
image=devkitpro/devkita64@sha256:1fc388c3a0d34bd2045a6dadcb1020e069d5f876a187fd705de14b4440c00282
docker run --rm -v "$PWD:$PWD" -w "$PWD" "$image" bash -c '
  set -euo pipefail
  sdk_cc=/opt/devkitpro/devkitA64/bin/aarch64-none-elf-gcc
  for kind in selftest portable; do
    "$sdk_cc" -O3 -std=c11 -march=armv8-a+crc+crypto -mtune=cortex-a57 \
      -I .local/src/nesrecomp/runner/cyc \
      -c ".local/src/nesrecomp/runner/cyc/tests/ppu_kernel_${kind}.c" \
      -o "build/switch-kernels/${kind}.o"
  done
  gcc build/switch-kernels/selftest.o build/switch-kernels/portable.o \
    build/switch-kernels/newlib-assert.c -o build/switch-kernels/kernel-test
  build/switch-kernels/kernel-test
'
