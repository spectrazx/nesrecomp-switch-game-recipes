#!/usr/bin/env python3
"""Build one game recipe: a desktop reference check, then the Switch NRO."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

from game_version import validate

ROOT = Path(__file__).resolve().parents[1]
ENGINE = ROOT / 'external/nesrecomp'
BUILD = ROOT / 'build/recipes'
IMAGE = 'devkitpro/devkita64@sha256:1fc388c3a0d34bd2045a6dadcb1020e069d5f876a187fd705de14b4440c00282'


def run(*args, env=None):
    subprocess.run(list(map(str, args)), cwd=ROOT, check=True, env=env)


def ensure_submodules():
    if not (ENGINE / 'runner/cyc/project.cmake').is_file():
        run('git', 'submodule', 'update', '--init', '--recursive')


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('game')
    ap.add_argument('--rom', required=True, type=Path)
    ap.add_argument('--backend', choices=['auto', 'native', 'docker'], default='auto')
    ap.add_argument('--host-only', action='store_true', help='Only build and boot-test the desktop reference')
    ap.add_argument('--variant', choices=['baseline', 'optimized'], default='baseline',
                    help='Desktop variant: baseline (LLE reference PPU) or optimized (the Switch PPU)')
    ap.add_argument('--ppu', choices=['LLE', 'HLE', 'FRAME'], help='Override the Switch PPU for comparisons')
    ap.add_argument('--output-dir', type=Path, help='Override the packaged NRO directory')
    ap.add_argument('--version', help='Override games/<game>/VERSION for this build')
    ap.add_argument('--benchmark-input', type=Path,
                    help='Embed a pad route as romfs:/benchmark-input.txt (default: games/<game>/tests/gameplay.txt)')
    ap.add_argument('--no-benchmark-input', action='store_true', help='Do not embed a benchmark route')
    args = ap.parse_args()
    if not args.game or any(c not in 'abcdefghijklmnopqrstuvwxyz0123456789_-' for c in args.game):
        ap.error('Invalid game recipe name')
    recipe = ROOT / 'games' / args.game
    if not (recipe / 'game.cmake').is_file():
        ap.error(f'Unknown game recipe: {args.game}')
    rom = args.rom.expanduser().resolve()
    if not rom.is_file():
        ap.error('ROM must be an existing file')
    try:
        version = validate(args.version if args.version is not None else (recipe / 'VERSION').read_text())
    except (OSError, ValueError) as error:
        ap.error(str(error))
    print(f'Building {args.game} version {version}', flush=True)
    ensure_submodules()
    build = BUILD / args.game
    output = args.output_dir.expanduser().resolve() if args.output_dir else build
    route = None
    if not args.no_benchmark_input:
        route = (args.benchmark_input or recipe / 'tests/gameplay.txt').expanduser().resolve()
        if not route.is_file():
            if args.benchmark_input:
                ap.error('Benchmark input route must exist')
            route = None
    romfs_root = route_sha256 = None
    if route:
        route_bytes = route.read_bytes()
        route_sha256 = hashlib.sha256(route_bytes).hexdigest()
        romfs_root = build / 'romfs'
        romfs_root.mkdir(parents=True, exist_ok=True)
        staged = romfs_root / 'benchmark-input.txt'
        if not staged.is_file() or staged.read_bytes() != route_bytes:
            staged.write_bytes(route_bytes)

    def configure(binary, compiler_path, rom_path, variant):
        return ['cmake', '-S', str(ROOT / 'games'), '-B', str(binary), '-G', 'Ninja',
                '-DCMAKE_BUILD_TYPE=Release', f'-DGAME_ID={args.game}', f'-DGAME_VARIANT={variant}',
                f'-DNESRECOMP_ROOT={ENGINE}', f'-DNESRECOMP_ROM={rom_path}',
                f'-DNESRECOMP_HOST_COMPILER={compiler_path}', f'-DGAME_OUTPUT_DIR={output}',
                f'-DNESRECOMP_GAME_VERSION={version}']

    compiler = BUILD / 'recompiler-host/NESRecomp'
    run('cmake', '-S', ENGINE / 'recompiler', '-B', compiler.parent, '-G', 'Ninja', '-DCMAKE_BUILD_TYPE=Release')
    run('cmake', '--build', compiler.parent, '--parallel', '4')
    host = build / ('host' if args.variant == 'baseline' else 'host-optimized')
    desktop_sdl = []
    for candidate in ('/opt/homebrew/opt/sdl2-compat/lib/cmake/SDL2', '/opt/homebrew/opt/sdl2/lib/cmake/SDL2',
                      '/usr/local/opt/sdl2/lib/cmake/SDL2'):
        if sys.platform == 'darwin' and Path(candidate).is_dir():
            # Prefer the system SDL2 over the engine's vendored Windows copy.
            desktop_sdl = [f'-DSDL2_DIR={candidate}']
            break
    run(*configure(host, compiler, rom, args.variant), '-DGAME_PPU_OVERRIDE=', *desktop_sdl)
    run('cmake', '--build', host, '--parallel', '4')
    with (host / 'boot.log').open('w') as log:
        subprocess.run([str(host / 'nes_game'), str(rom), '--frames', '600', '--no-save',
                        '--screenshot', str(host / 'boot.png')], check=True, cwd=ROOT,
                       stdout=log, stderr=subprocess.STDOUT)
    print(f'Desktop {args.variant} boot test passed: {host / "boot.png"}', flush=True)
    if args.host_only:
        return

    sdk = Path(os.environ.get('DEVKITPRO', '/opt/devkitpro')).expanduser().resolve()
    devkita64 = Path(os.environ.get('DEVKITA64', str(sdk / 'devkitA64'))).expanduser().resolve()
    native = (devkita64 / 'bin/aarch64-none-elf-gcc').is_file()
    backend = ('native' if native else 'docker') if args.backend == 'auto' else args.backend
    extras = ['-DNESRECOMP_SWITCH_SAVES=OFF', '-DNESRECOMP_SWITCH_LTO=ON',
              f'-DNESRECOMP_SWITCH_VERSION={version}',
              f'-DNESRECOMP_SWITCH_ROMFS_ROOT={romfs_root or ""}',
              f'-DGAME_PPU_OVERRIDE={args.ppu or ""}']
    binary = build / ('switch' if backend == 'native' else 'switch-docker')
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
        # The code generator runs inside the Linux container, so build a Linux copy there.
        run('docker', 'info', '--format', '{{.Architecture}} {{.ServerVersion}}')
        prefix = ['docker', 'run', '--rm', '-v', f'{ROOT}:{ROOT}', '-v', f'{rom}:/private/game.nes:ro',
                  '-w', str(ROOT), IMAGE]
        linux_compiler = BUILD / 'recompiler-linux/NESRecomp'
        run(*prefix, 'cmake', '-S', ENGINE / 'recompiler', '-B', linux_compiler.parent,
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
    cache = (binary / 'CMakeCache.txt').read_text()
    ppu = next((line.split('=', 1)[1] for line in cache.splitlines()
                if line.startswith('NESRECOMP_PPU_IMPL:')), 'unknown')
    sd_dir = (binary / 'game-sd-dir.txt').read_text().strip()
    if not sd_dir or any(c not in 'abcdefghijklmnopqrstuvwxyz0123456789_-' for c in sd_dir):
        raise ValueError('Invalid SD directory from CMake')
    manifest = dict(game=args.game, version=version, artifact=artifact_name, region=region, ppu=ppu, sd_dir=sd_dir,
                    benchmark_input_sha256=route_sha256,
                    benchmark_input_asset='romfs:/benchmark-input.txt' if route else None,
                    engine_revision=subprocess.check_output(
                        ['git', '-C', str(ENGINE), 'rev-parse', 'HEAD'], text=True).strip(),
                    engine_dirty=bool(subprocess.check_output(
                        ['git', '-C', str(ENGINE), 'status', '--porcelain'], text=True).strip()),
                    sha256=hashlib.sha256(artifact.read_bytes()).hexdigest(),
                    rom_sha256=hashlib.sha256(rom.read_bytes()).hexdigest())
    manifest_path = output / 'build.json'
    pending = manifest_path.with_suffix('.json.tmp')
    pending.write_text(json.dumps(manifest, indent=2) + '\n')
    pending.replace(manifest_path)
    print(f'Packaged {args.game} {version} ({region}, PPU {ppu}): {artifact}', flush=True)


if __name__ == '__main__':
    try:
        main()
    except subprocess.CalledProcessError as error:
        sys.exit(error.returncode)
