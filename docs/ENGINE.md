# Engine pin and divergence from upstream

`external/nesrecomp` points at the `switch-integration` branch of
[spectrazx/nesrecomp](https://github.com/spectrazx/nesrecomp). That branch is
upstream `master` with each open pull request merged on top, in this order.
It has no commits of its own.

| Upstream PR | Branch | What it does | Needed for |
| --- | --- | --- | --- |
| [#111](https://github.com/mstan/nesrecomp/pull/111) | `feat/switch-runner` | Switch runner (libnx/SDL2, NRO packaging, benchmark mode) | Everything |
| [#110](https://github.com/mstan/nesrecomp/pull/110) | `perf/arm-neon-sprite-kernels` | NEON sprite kernels for the HLE PPU | HLE builds only (minor) |
| [#112](https://github.com/mstan/nesrecomp/pull/112) | `perf/masked-irq-intervals` | Native intervals while a masked APU frame IRQ is pending | Adventure Island speed |
| [#113](https://github.com/mstan/nesrecomp/pull/113) | `perf/frame-ppu-pal` (on #112) | FRAME PPU and native intervals on PAL NROM/CNROM | Adventure Island speed |
| [#114](https://github.com/mstan/nesrecomp/pull/114) | `perf/pal-clock` | Specialized PAL clock tail | Adventure Island (+4%) |
| not opened yet | `feat/switch-host-extras` (on #111) | Switch runner accepts MODS/HOST_EXTRAS and presents a wider picture | smb1-widescreen |

Pinned engine commit: see `git submodule status` or `mise run engine-status`
(lists the merges on top of upstream `master`).

## Rebuilding the integration branch

In a clone of the fork with `upstream` = mstan/nesrecomp:

```sh
git fetch upstream
git checkout -B switch-integration upstream/master
for b in feat/switch-runner perf/arm-neon-sprite-kernels perf/frame-ppu-pal perf/pal-clock feat/switch-host-extras; do
  git merge --no-ff --no-edit "$b"
done
git push --force-with-lease origin switch-integration
```

Leave out a branch once its PR is merged upstream. After review changes,
rebase the PR branch on `upstream/master` first, then rebuild.

Then in this repository:

```sh
git -C external/nesrecomp fetch origin
git -C external/nesrecomp checkout origin/switch-integration
# rebuild and test both games, then
git add external/nesrecomp && git commit -m "Update engine to <commit>"
```

When every PR is merged, point the submodule at upstream instead:
`git submodule set-url external/nesrecomp https://github.com/mstan/nesrecomp.git`
and `git submodule set-branch --branch master external/nesrecomp`.

## Other submodule

`external/SuperMarioBrosNESRecomp` (upstream Mario project, pinned at
`de443b0`) provides only `cyc_seeds.txt` for the Mario recipe.

## Measurements

Switch, handheld, stock 1.02 GHz CPU, uncapped, 1,200-frame scripted route,
emulation time over the last 300 frames:

| Game | Upstream `master` | This engine |
| --- | --- | --- |
| Super Mario Bros. (FRAME) | 12.48 ms (FRAME, master + #111) | 12.50 ms |
| Adventure Island (PAL) | 51.76 ms (HLE, 18.7 FPS) | 17.25 ms (FRAME, 53.4 FPS) |

All runs end in the same memory state as upstream. Earlier work (old engine
patches, profiling notes, abandoned experiments) is in this repository's Git
history before the restructure.
