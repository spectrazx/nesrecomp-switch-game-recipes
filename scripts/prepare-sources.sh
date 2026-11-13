#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p .local/src
prepare() {
  local name="$1" revision="$2" contribution="${3:-}"
  local dir=".local/src/$name"
  if [[ ! -d "$dir/.git" ]]; then
    git clone "https://github.com/mstan/$name.git" "$dir"
    git -C "$dir" checkout --detach "$revision"
  fi
  local actual
  actual="$(git -C "$dir" rev-parse HEAD)"
  if [[ "$actual" != "$revision" && "$actual" != "$contribution" ]]; then
    printf 'Unexpected revision in %s; preserving checkout. See docs/PORT_STATUS.md.\n' "$dir" >&2
    exit 1
  fi
}
prepare nesrecomp ab3579725ae129b0e04fa2095d7e7dd38ac096b7 4eed78d9d6abf60c651942bc3e60f1762370133d
prepare SuperMarioBrosNESRecomp de443b01e2707c768be1729970f99d2f9da6bec3
patch="$PWD/patches/nesrecomp-switch.patch"
if git -C .local/src/nesrecomp apply --reverse --check "$patch" 2>/dev/null; then
  printf '%s\n' 'Switch patch is already applied.'
else
  git -C .local/src/nesrecomp apply --check "$patch"
  git -C .local/src/nesrecomp apply "$patch"
fi
