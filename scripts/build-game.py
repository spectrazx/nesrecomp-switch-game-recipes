#!/usr/bin/env python3
"""Build one game module using a native host compiler and a Switch SDK."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

from game_version import validate

ROOT = Path(__file__).resolve().parents[1]
IMAGE = 'devkitpro/devkita64@sha256:1fc388c3a0d34bd2045a6dadcb1020e069d5f876a187fd705de14b4440c00282'

def run(*args, env=None):
    subprocess.run(list(map(str, args)), cwd=ROOT, check=True, env=env)

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('game')
    ap.add_argument('--rom', required=True, type=Path)
    ap.add_argument('--backend', choices=['auto', 'native', 'docker'], default='auto')
    ap.add_argument('--host-only', action='store_true')
    ap.add_argument('--variant', choices=['baseline', 'optimized'], default='baseline', help='Native reference variant')
    ap.add_argument('--ppu', choices=['LLE', 'HLE'], help='Explicit Switch PPU override for comparisons')
    ap.add_argument('--output-dir', type=Path, help='Override packaged NRO directory')
    ap.add_argument('--version', help='Override games/<game>/VERSION for this build')
    ap.add_argument('--profile-core', action='store_true', help='Enable sampled Switch core timing diagnostics')
    ap.add_argument('--sprite-kernel', choices=['auto', 'portable'], default='auto',
                    help='Compare explicit architecture kernels with portable C')
    ap.add_argument('--benchmark-input', type=Path, help='Embed an existing NES pad route as a read-only NRO asset')
    args = ap.parse_args()
    if not args.game or any(c not in 'abcdefghijklmnopqrstuvwxyz0123456789_-' for c in args.game):
        ap.error('Invalid game module name')
    if not (ROOT / 'games' / args.game / 'game.cmake').is_file():
        ap.error(f'Unknown game module: {args.game}')
    rom = args.rom.expanduser().resolve()
    if not rom.is_file():
        ap.error('ROM must be an existing file')
    try:
        version = validate(args.version if args.version is not None else
                           (ROOT / 'games' / args.game / 'VERSION').read_text())
    except (OSError, ValueError) as error:
        ap.error(str(error))
    print(f'Building {args.game} version {version}', flush=True)
    run('bash', 'scripts/prepare-sources.sh')
    engine = ROOT / '.local/src/nesrecomp'
    build = ROOT / 'build/games' / args.game
    output = args.output_dir.expanduser().resolve() if args.output_dir else build
    route = args.benchmark_input.expanduser().resolve() if args.benchmark_input else None
    romfs_root = None
    route_sha256 = None
    if route:
        if not route.is_file():
            ap.error('Benchmark input route must exist')
        route_bytes = route.read_bytes()
        route_sha256 = hashlib.sha256(route_bytes).hexdigest()
        romfs_root = build / 'benchmark-assets' / route_sha256
        romfs_root.mkdir(parents=True, exist_ok=True)
        staged_route = romfs_root / 'benchmark-input.txt'
        if not staged_route.is_file() or staged_route.read_bytes() != route_bytes:
            staged_route.write_bytes(route_bytes)
    kernel_suffix = '-portable' if args.sprite_kernel == 'portable' else ''
    host = build / (('host' if args.variant == 'baseline' else 'host-optimized') + kernel_suffix)
    compiler = ROOT / 'build/recompiler/NESRecomp'
    run('cmake', '-S', engine / 'recompiler', '-B', compiler.parent, '-G', 'Ninja', '-DCMAKE_BUILD_TYPE=Release')
    run('cmake', '--build', compiler.parent, '--parallel', '4')

    def configure(binary, compiler_path, rom_path, variant):
        return ['cmake', '-S', str(ROOT / 'games'), '-B', str(binary), '-G', 'Ninja',
                '-DCMAKE_BUILD_TYPE=Release', f'-DGAME_ID={args.game}', f'-DGAME_VARIANT={variant}',
                f'-DNESRECOMP_ROOT={engine}', f'-DNESRECOMP_ROM={rom_path}',
                f'-DNESRECOMP_HOST_COMPILER={compiler_path}', f'-DGAME_OUTPUT_DIR={output}',
                f'-DNESRECOMP_GAME_VERSION={version}',
                f'-DGAME_SPRITE_KERNEL={args.sprite_kernel}',
                '-DNESRECOMP_CORE_PROFILER=OFF',
                '-DGAME_PPU_OVERRIDE=']

    run(*configure(host, compiler, rom, args.variant))
    run('cmake', '--build', host, '--parallel', '4')
    with (host / 'boot.log').open('w') as log:
        subprocess.run([str(host / 'nes_game'), str(rom), '--frames', '600', '--no-save',
                        '--screenshot', str(host / 'boot.png')], check=True, cwd=ROOT,
                       stdout=log, stderr=subprocess.STDOUT)
    if args.host_only:
        return
    sdk = Path(os.environ.get('DEVKITPRO', '/opt/devkitpro')).expanduser().resolve()
    devkita64 = Path(os.environ.get('DEVKITA64', str(sdk / 'devkitA64'))).expanduser().resolve()
    native = (devkita64 / 'bin/aarch64-none-elf-gcc').is_file()
    backend = ('native' if native else 'docker') if args.backend == 'auto' else args.backend
    extras = ['-DNESRECOMP_SWITCH_SAVES=OFF', '-DNESRECOMP_SWITCH_LTO=ON', f'-DNESRECOMP_SWITCH_VERSION={version}',
              f'-DNESRECOMP_CORE_PROFILER={"ON" if args.profile_core else "OFF"}',
              f'-DNESRECOMP_SWITCH_ROMFS_ROOT={romfs_root or ""}',
              f'-DGAME_PPU_OVERRIDE={args.ppu or ""}']
    binary = build / (('switch' if backend == 'native' else 'switch-docker') + kernel_suffix)
    if backend == 'native':
        if not native:
            ap.error('Native devkitA64 is not installed; use --backend docker')
        sdk_env = dict(os.environ, DEVKITPRO=str(sdk), DEVKITA64=str(devkita64))
        sdk_env['PATH'] = os.pathsep.join(map(str, [devkita64 / 'bin', sdk / 'tools/bin',
            sdk / 'portlibs/switch/bin', os.environ.get('PATH', '')]))
        run(*configure(binary, compiler, rom, 'optimized'),
            f'-DCMAKE_TOOLCHAIN_FILE={sdk}/cmake/Switch.cmake', *extras, env=sdk_env)
        run('cmake', '--build', binary, '--parallel', '4', env=sdk_env)
    else:
        run('docker', 'info', '--format', '{{.Architecture}} {{.ServerVersion}}')
        prefix = ['docker', 'run', '--rm', '-v', f'{ROOT}:{ROOT}', '-v', f'{rom}:/private/game.nes:ro',
                  '-w', str(ROOT), IMAGE]
        linux_compiler = ROOT / 'build/recompiler-linux/NESRecomp'
        run(*prefix, 'cmake', '-S', engine / 'recompiler', '-B', linux_compiler.parent,
            '-G', 'Ninja', '-DCMAKE_BUILD_TYPE=Release')
        run(*prefix, 'cmake', '--build', linux_compiler.parent, '--parallel', '4')
        run(*prefix, *configure(binary, linux_compiler, '/private/game.nes', 'optimized'),
            '-DCMAKE_TOOLCHAIN_FILE=/opt/devkitpro/cmake/Switch.cmake', *extras)
        run(*prefix, 'cmake', '--build', binary, '--parallel', '4')
    artifact_name = (binary / 'game-artifact.txt').read_text().strip()
    if Path(artifact_name).name != artifact_name or not artifact_name.endswith('.nro'):
        raise ValueError('Invalid artifact name from CMake')
    artifact = output / artifact_name
    run(sys.executable, ROOT / 'scripts/inspect-nro.py', artifact, '--expect-version', version,
        *(['--expect-romfs'] if route else []))
    region = (binary / 'game-region.txt').read_text().strip()
    if region not in ('PAL', 'NTSC'):
        raise ValueError('Packaged game requires an explicit region for comparison metadata')
    manifest = dict(region=region,
                    switch_comparison_policy='pal_raster' if region == 'PAL' else 'sprite_fetch_jobs',
                    game=args.game, version=version, artifact=artifact_name,
                    core_profiler=args.profile_core,
                    nxlink_log_supported=True,
                    switch_benchmark_supported=True,
                    switch_gameplay_benchmark_supported=True,
                    switch_comparison_suite_supported=True,
                    benchmark_input_sha256=route_sha256,
                    benchmark_input_asset='romfs:/benchmark-input.txt' if route else None,
                    sprite_kernel=args.sprite_kernel,
                    engine_revision=subprocess.check_output(
                        ['git', '-C', str(engine), 'rev-parse', 'HEAD'], text=True).strip(),
                    engine_patch_sha256=hashlib.sha256((ROOT / 'patches/nesrecomp-switch.patch').read_bytes()).hexdigest(),
                    sha256=hashlib.sha256(artifact.read_bytes()).hexdigest(),
                    rom_sha256=hashlib.sha256(rom.read_bytes()).hexdigest())
    manifest_path = output / 'build.json'
    pending = manifest_path.with_suffix('.json.tmp')
    pending.write_text(json.dumps(manifest, indent=2) + '\n')
    pending.replace(manifest_path)
    print(f'Packaged {args.game} {version}: {artifact}', flush=True)

if __name__ == '__main__':
    try:
        main()
    except subprocess.CalledProcessError as error:
        sys.exit(error.returncode)
