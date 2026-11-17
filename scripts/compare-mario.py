#!/usr/bin/env python3
"""Compare upstream Mario with the workspace on one desktop, without a GUI.

Builds the actual upstream application with its pinned engine and our engine,
then checks the same route and measures serial, order-balanced CPU time.
This does not benchmark Switch presentation or predict Switch FPS.
"""
import argparse
import hashlib
import json
from pathlib import Path
import platform
import subprocess
import sys
import wave

ROOT = Path(__file__).resolve().parents[1]
ENGINE = ROOT / '.local/src/nesrecomp'
MARIO = ROOT / '.local/src/SuperMarioBrosNESRecomp'


def git(directory, *args):
    return subprocess.check_output(['git', '-C', str(directory), *args], text=True).strip()


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(command, cwd, log):
    with log.open('w') as stream:
        subprocess.run(list(map(str, command)), cwd=cwd, stdout=stream,
                       stderr=subprocess.STDOUT, check=True, timeout=600)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--rom', type=Path, required=True)
    ap.add_argument('--out', type=Path, default=ROOT / 'build/upstream-comparison')
    ap.add_argument('--skip-build', action='store_true', help='Use the three existing builds')
    ap.add_argument('--blocks', type=int, default=2, help='ABBA blocks per comparison')
    args = ap.parse_args()
    if args.blocks < 2:
        ap.error('Use at least two order-balanced blocks')
    rom = args.rom.expanduser().resolve()
    out = args.out.expanduser().resolve()
    if not rom.is_file():
        ap.error('ROM must exist')
    out.mkdir(parents=True, exist_ok=True)
    # Fetch only the exact engine revision recorded by the Mario checkout.
    pin = git(MARIO, 'ls-tree', 'HEAD', 'nesrecomp').split()[2]
    reference = ROOT / '.local/src/nesrecomp-mario-reference'
    if not reference.exists():
        run(['git', '-C', ENGINE, 'fetch', '--no-tags', '--depth=1', 'origin', pin],
            ROOT, out / 'fetch.log')
        run(['git', '-C', ENGINE, 'worktree', 'add', '--detach', reference, pin],
            ROOT, out / 'reference-checkout.log')
    if git(reference, 'rev-parse', 'HEAD') != pin or git(reference, 'status', '--porcelain'):
        ap.error('Reference engine must be clean and match Mario\'s pinned revision')
    builds = {name: out / name for name in ('upstream-original', 'upstream-shared')}
    if not args.skip_build:
        for name, engine in [('upstream-original', reference), ('upstream-shared', ENGINE)]:
            run(['cmake', '-S', MARIO, '-B', builds[name], '-G', 'Ninja',
                 '-DCMAKE_BUILD_TYPE=Release', f'-DNESRECOMP_ROOT={engine}',
                 f'-DNESRECOMP_ROM={rom}', '-DNESRECOMP_HEADLESS=ON',
                 '-DNESRECOMP_RECOMP_UI=OFF', '-DNESRECOMP_PPU_IMPL=HLE',
                 '-DSMB_ENABLE_NETPLAY=OFF', '-DCMAKE_INTERPROCEDURAL_OPTIMIZATION=ON',
                 '-DCMAKE_EXPORT_COMPILE_COMMANDS=ON'], ROOT, out / f'{name}-configure.log')
            run(['cmake', '--build', builds[name], '--target', 'SuperMarioBrosRecomp',
                 '--parallel', '4'], ROOT, out / f'{name}-build.log')
        run([sys.executable, ROOT / 'scripts/build-game.py', 'smb1', '--rom', rom,
             '--host-only', '--variant', 'optimized'], ROOT, out / 'workspace-build.log')
        # Mario's host extras choose 44.1 kHz, while our unmodified host uses
        # 48 kHz. Supply only that policy through the existing extras API in a
        # separate comparison target; leave production sources/settings alone.
        source = out / 'matched-source'
        source.mkdir(exist_ok=True)
        (source / 'audio_rate.c').write_text(
            '#include "cyc_host_extras.h"\n'
            'const CycHostExtras *cyc_host_extras(void) {\n'
            '    static const CycHostExtras extras = {.audio_rate = 44100};\n'
            '    return &extras;\n}\n')
        (source / 'CMakeLists.txt').write_text(
            'cmake_minimum_required(VERSION 3.20)\nproject(MatchedMario C)\n'
            f'add_subdirectory("{ROOT / "games"}" workspace)\n'
            'get_target_property(defines nes_game COMPILE_DEFINITIONS)\n'
            'list(REMOVE_ITEM defines CYC_HOST_EXTRAS_STRONG=1)\n'
            'set_property(TARGET nes_game PROPERTY COMPILE_DEFINITIONS ${defines})\n'
            'target_sources(nes_game PRIVATE "${CMAKE_CURRENT_SOURCE_DIR}/audio_rate.c")\n')
        run(['cmake', '-S', source, '-B', out / 'workspace-matched', '-G', 'Ninja',
             '-DCMAKE_BUILD_TYPE=Release', '-DGAME_ID=smb1', '-DGAME_VARIANT=optimized',
             f'-DNESRECOMP_ROOT={ENGINE}', f'-DNESRECOMP_ROM={rom}',
             f'-DNESRECOMP_HOST_COMPILER={ROOT / "build/recompiler/NESRecomp"}',
             '-DCMAKE_EXPORT_COMPILE_COMMANDS=ON'], ROOT, out / 'matched-configure.log')
        run(['cmake', '--build', out / 'workspace-matched', '--parallel', '4'],
            ROOT, out / 'matched-build.log')
    programs = {name: folder / 'SuperMarioBrosRecomp' for name, folder in builds.items()}
    programs['workspace'] = ROOT / 'build/games/smb1/host-optimized/nes_game'
    programs['workspace-matched'] = out / 'workspace-matched/workspace/nes_game'
    # A new results directory prevents mixing evidence from different runs.
    results = out / 'results'
    results.mkdir(exist_ok=False)
    empty_mods = results / 'empty-mods'
    empty_mods.mkdir()
    route = ROOT / 'games/smb1/tests/gameplay.txt'
    manifest = dict(platform=platform.platform(), machine=platform.machine(),
                    mario_revision=git(MARIO, 'rev-parse', 'HEAD'),
                    mario_engine_pin=pin, workspace_engine=git(ENGINE, 'rev-parse', 'HEAD'),
                    engine_tracked_changes=git(ENGINE, 'diff', 'HEAD', '--stat'),
                    rom_sha256=digest(rom), route_sha256=digest(route),
                    settings='Release, HLE, IPO, headless, 1800 frames; benchmarks normalized to 44100 Hz; no selected mods',
                    compiler=subprocess.check_output(['cc', '--version'], text=True).splitlines()[0],
                    captures={}, benchmarks={})
    # Separate correctness from timing: frame hashes are expensive diagnostics.
    frame_rows = {}
    for name, exe in programs.items():
        folder = results / name
        folder.mkdir()
        run([exe, rom, '--headless', '--frames', '1800', '--input', route,
             '--no-save', '--mods-root', empty_mods, '--hash-out', folder / 'frames.txt',
             '--wav-out', folder / 'audio.wav', '--screenshot', folder / 'final.png'],
            folder, folder / 'run.log')
        frame_rows[name] = (folder / 'frames.txt').read_text().splitlines()
        manifest['captures'][name] = dict(executable_sha256=digest(exe),
                                          frames=len(frame_rows[name]),
                                          wav_sha256=digest(folder / 'audio.wav'),
                                          png_sha256=digest(folder / 'final.png'))
        with wave.open(str(folder / 'audio.wav')) as audio:
            manifest['captures'][name]['sample_rate'] = audio.getframerate()
    def normalized(rows):
        return [' '.join(f for f in row.split() if not f.startswith('hw=')) for row in rows]
    baseline = normalized(frame_rows['workspace'])
    for name, capture in manifest['captures'].items():
        capture['execution_pixels_match_workspace'] = len(baseline) == 1800 and normalized(frame_rows[name]) == baseline
        capture['all_fields_match_workspace'] = frame_rows[name] == frame_rows['workspace']
    manifest['correctness_passed'] = (
        all(c['execution_pixels_match_workspace'] for c in manifest['captures'].values())
        and all(c['sample_rate'] == (48000 if n == 'workspace' else 44100)
                for n, c in manifest['captures'].items())
        and len({c['wav_sha256'] for n, c in manifest['captures'].items() if n != 'workspace'}) == 1
        and len({c['png_sha256'] for c in manifest['captures'].values()}) == 1)
    report = results / 'summary.json'
    report.write_text(json.dumps(manifest, indent=2) + '\n')
    if not manifest['correctness_passed']:
        raise RuntimeError(f'Correctness comparison failed; inspect {report}')
    # Same arguments, same machine, no build or parallel benchmark jobs here.
    for name in builds:
        folder = results / f'bench-{name}'
        run([sys.executable, ENGINE / 'tools/cyc/bench_host_work.py',
             '--baseline', programs[name], '--candidate', programs['workspace-matched'],
             '--rom', rom, '--input', route, '--frames', '1800', '--blocks', args.blocks,
             '--out', folder, '--lock', ROOT / 'build/desktop-benchmark.lock',
             '--extra', '--mods-root', empty_mods], results, results / f'{name}-benchmark.log')
        manifest['benchmarks'][name] = json.loads((folder / 'summary.json').read_text())
        report.write_text(json.dumps(manifest, indent=2) + '\n')
        print(name, json.dumps(manifest['benchmarks'][name]), flush=True)
    print(f'Report: {report}')


if __name__ == '__main__':
    main()
