#!/usr/bin/env python3
"""PAL reference comparison with boot alignment established before any input."""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import subprocess

ROOT = Path(__file__).resolve().parents[3]
MESEN_REVISION = '562ee84de49acbd7866d0c079e61f0dc52cc27f4'


def frames(path):
    with path.open('rb') as file:
        assert file.read(12) == b'CYCFRAME' + struct.pack('<I', 2)
        while header := file.read(36):
            values = struct.unpack('<9I', header)
            sizes = values[3:]
            data = file.read(288 + sum(sizes))
            assert len(data) == 288 + sum(sizes)
            start = 288 + sum(sizes[:4])
            yield values[0], data[288:288 + sizes[0]], data[start:start + sizes[4]]


def sha(path):
    with path.open('rb') as file:
        return hashlib.file_digest(file, 'sha256').hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--rom', required=True, type=Path)
    ap.add_argument('--out', required=True, type=Path, help='New directory for this experiment')
    args = ap.parse_args()
    rom = args.rom.resolve()
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    engine = ROOT / '.local/src/nesrecomp'
    mesen = ROOT / '.local/src/MesenCE-libretro'
    host = ROOT / 'build/games/adventure-island/host-optimized/nes_game'
    oracle = out / 'tool/mesen_shot'
    route = Path(__file__).with_name('gameplay.txt')
    assert subprocess.check_output(['git', '-C', str(mesen), 'rev-parse', 'HEAD'], text=True).strip() == MESEN_REVISION
    subprocess.run(['git', '-C', str(mesen), 'diff', '--quiet'], check=True)
    subprocess.run(['git', '-C', str(mesen), 'diff', '--cached', '--quiet'], check=True)

    def run(name, command):
        with (out / (name + '.log')).open('w') as log:
            subprocess.run(list(map(str, command)), cwd=ROOT, stdout=log, stderr=subprocess.STDOUT,
                           check=True, timeout=900)

    run('verify-rom', ['python3', ROOT / 'scripts/verify-rom.py', '--rom', rom,
                       '--crc', '86867830', '--mapper', '3', '--title', 'Adventure Island Classic'])
    run('build-oracle', ['bash', engine / 'tools/cyc/mesen_shot/build.sh', mesen, out / 'tool'])
    # Align the machines at the same PPU observation point. Compare all 256
    # zero-page bytes on two title frames BEFORE the Start press, not a fitted
    # offset chosen to hide mismatching gameplay pictures.
    run('boot-native', [host, rom, '--region', 'pal', '--ram-init', 'zeros', '--no-save',
                       '--frames', '600', '--frame-log', out / 'boot.bin',
                       '--frame-log-at', 'mesen', '--frame-log-frames', '299:599'])
    run('boot-oracle', [oracle, rom, out / 'boot-oracle', '--region', 'pal', '--memory', '300', '600'])
    calibrated = []
    for frame, ram, _ in frames(out / 'boot.bin'):
        if frame in (299, 599):
            reference = (out / 'boot-oracle' / f'{frame + 1}.ram').read_bytes()
            assert ram[:256] == reference[:256], f'Pre-input boot alignment changed at frame {frame}'
            calibrated.append(frame)
    assert calibrated == [299, 599]
    run('game-native', [host, rom, '--region', 'pal', '--ram-init', 'zeros', '--no-save',
                       '--frames', '1802', '--input', route, '--frame-log', out / 'game.bin',
                       '--frame-log-frames', '899:1801'])
    run('game-oracle', [oracle, rom, out / 'game-oracle', '--region', 'pal', '--frame-offset', '1',
                        '--input', route, *range(900, 1803)])
    compared = 0
    different = []
    for frame, _, picture in frames(out / 'game.bin'):
        compared += 1
        if picture != (out / 'game-oracle' / f'{frame + 1}.idx').read_bytes():
            different.append(frame)
    summary = dict(region='PAL', ram_init='zeros', frame_offset=1, calibration_frames=calibrated,
                   calibration_zero_page_exact=True, frames_compared=compared,
                   exact_raw_pixel_matches=compared - len(different), different_frames=different,
                   mesen_revision=MESEN_REVISION, host_sha256=sha(host), oracle_sha256=sha(oracle),
                   oracle_library_sha256=sha(mesen / 'mesen2_libretro.dylib'), rom_sha256=sha(rom))
    (out / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps(summary, indent=2))
    assert compared == 903 and not different, 'Independent PAL pixel comparison failed'


if __name__ == '__main__':
    main()
