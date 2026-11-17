#!/usr/bin/env python3
"""Check portable/automatic host kernels on a title's existing gameplay route."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('game', choices=['smb1', 'adventure-island'])
    ap.add_argument('--rom', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    args = ap.parse_args()
    rom = args.rom.expanduser().resolve()
    route = ROOT / 'games' / args.game / 'tests/gameplay.txt'
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=True)
    captures = {}
    for name, suffix in [('portable', '-portable'), ('auto', '')]:
        exe = ROOT / 'build/games' / args.game / f'host-optimized{suffix}/nes_game'
        folder = out / name
        folder.mkdir(exist_ok=True)
        command = [str(exe), str(rom), '--headless', '--frames', '1800', '--no-save',
                   '--input', str(route), '--hash-out', str(folder / 'frames.txt'),
                   '--wav-out', str(folder / 'audio.wav'), '--screenshot', str(folder / 'final.png')]
        with (folder / 'run.log').open('w') as log:
            subprocess.run(command, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT,
                           check=True, timeout=180)
        captures[name] = dict(executable_sha256=hashlib.sha256(exe.read_bytes()).hexdigest(),
                              frames=(folder / 'frames.txt').read_text().splitlines())
        print(f'{name}: {len(captures[name]["frames"])} frame records', flush=True)
    records_match = (len(captures['auto']['frames']) == 1800
                     and captures['auto']['frames'] == captures['portable']['frames'])
    audio_match = (out / 'auto/audio.wav').read_bytes() == (out / 'portable/audio.wav').read_bytes()
    picture_match = (out / 'auto/final.png').read_bytes() == (out / 'portable/final.png').read_bytes()
    summary = dict(game=args.game, frames=1800, all_frame_records_match=records_match,
                   pcm_wav_match=audio_match, final_png_match=picture_match,
                   rom_sha256=hashlib.sha256(rom.read_bytes()).hexdigest(),
                   route_sha256=hashlib.sha256(route.read_bytes()).hexdigest(),
                   executables={k: v['executable_sha256'] for k, v in captures.items()})
    (out / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps(summary, indent=2))
    if not (records_match and audio_match and picture_match):
        raise SystemExit('Sprite-kernel output comparison failed')


if __name__ == '__main__':
    main()
