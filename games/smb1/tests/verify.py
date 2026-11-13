#!/usr/bin/env python3
"""Exercise an already built vanilla Mario host with the user's private ROM."""
import argparse
import json
from pathlib import Path
import struct
import subprocess
import wave
import shutil


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--rom', required=True, type=Path)
    ap.add_argument('--variant', choices=['baseline', 'optimized'], default='baseline')
    args = ap.parse_args()
    root = Path(__file__).resolve().parents[3]
    rom = args.rom.resolve()
    out = root / 'build/games/smb1' / ('tests' if args.variant == 'baseline' else 'tests-optimized')
    out.mkdir(parents=True, exist_ok=True)
    exe = root / 'build/games/smb1' / ('host' if args.variant == 'baseline' else 'host-optimized') / 'nes_game'
    if not exe.is_file():
        ap.error('Build this variant with scripts/build-game.py first')
    route = out / 'gameplay.txt'
    shutil.copyfile(Path(__file__).with_name('gameplay.txt'), route)
    state = out / 'frame600.cycstate'

    def run(program, name, *extra):
        command = [str(program), str(rom), '--frames', '1800', '--input', str(route),
                   '--hash-out', str(out / f'{name}-hashes.txt'), *map(str, extra)]
        with (out / f'{name}.log').open('w') as log:
            result = subprocess.run(command, cwd=root, stdout=log, stderr=subprocess.STDOUT, timeout=180)
        assert result.returncode == 0, f'{name} failed: see {out / (name + ".log")}'
        return (out / f'{name}-hashes.txt').read_text().splitlines()

    native = run(exe, 'native', '--save-state', f'600:{state}', '--screenshot', out / 'gameplay.png',
                 '--shot-every', '300', '--wav-out', out / 'gameplay.wav')
    interp = run(exe, 'interpreter', '--interp-only', '--screenshot', out / 'interpreter.png')
    resumed = run(exe, 'resumed', '--load-state', state, '--screenshot', out / 'resumed.png')
    assert len(native) == 1800 and native == interp, 'Native/interpreter comparison failed'
    # The CLI's FRAME argument is zero-based: saving after frame 600 resumes at 601.
    assert len(resumed) == 1199 and resumed == native[601:], 'State continuation comparison failed'
    assert (out / 'gameplay.png').read_bytes() == (out / 'interpreter.png').read_bytes()
    assert (out / 'gameplay.png').read_bytes() == (out / 'resumed.png').read_bytes()
    assert 'interpreted: ROM 0 ' in (out / 'native.log').read_text()
    with wave.open(str(out / 'gameplay.wav')) as wav:
        pcm = wav.readframes(wav.getnframes())
        peak = max(abs(value[0]) for value in struct.iter_unpack('<h', pcm))
        audio = dict(rate=wav.getframerate(), channels=wav.getnchannels(),
                     duration_seconds=wav.getnframes() / wav.getframerate(), peak=peak)
        assert audio['rate'] == 48000 and audio['channels'] == 1 and peak > 0
    summary = dict(frames=1800, native_interpreter_match=True, resumed_frames=1199,
                   state_continuation_match=True, interpreted_rom_cycles=0, audio=audio)
    oracle = root / '.local/src/nesrecomp/build/smb-oracle/cyc_oracle'
    if oracle.is_file():
        reference = run(oracle, 'oracle', '--screenshot', out / 'oracle.png')
        def without_internal_hash(line):
            return [field for field in line.split() if not field.startswith('hw=')]
        summary['oracle_cpu_trace_memory_raw_pixels_match'] = (
            len(reference) == len(native) and
            all(without_internal_hash(a) == without_internal_hash(b) for a, b in zip(native, reference)))
        summary['oracle_internal_hardware_hash_match'] = reference == native
        summary['oracle_rgb_png_match'] = (out / 'oracle.png').read_bytes() == (out / 'gameplay.png').read_bytes()
        assert summary['oracle_cpu_trace_memory_raw_pixels_match'], 'Reference execution comparison failed'
    (out / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
