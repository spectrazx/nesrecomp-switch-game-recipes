#!/usr/bin/env python3
"""Compare both PAL renderer builds on the supplied original cartridge."""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import subprocess
import wave


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--rom', type=Path, required=True)
    args = ap.parse_args()
    root = Path(__file__).resolve().parents[3]
    rom = args.rom.resolve()
    base = root / 'build/recipes/adventure-island'
    route = Path(__file__).with_name('gameplay.txt')
    summaries = {}
    captures = {}
    hashes = {}
    for variant, directory in [('baseline', 'host'), ('optimized', 'host-optimized')]:
        exe = base / directory / 'nes_game'
        if not exe.is_file():
            ap.error(f'Build the {variant} variant first')
        out = base / ('tests-' + variant)
        out.mkdir(parents=True, exist_ok=True)
        state = out / 'frame1200.cycstate'

        def run(name, *extra, traced=True):
            command = [str(exe), str(rom), '--frames', '1800', '--input', str(route), '--no-save']
            if traced:
                command += ['--hash-out', str(out / (name + '-hashes.txt'))]
            command += list(map(str, extra))
            with (out / (name + '.log')).open('w') as log:
                subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, check=True, timeout=240)
            return (out / (name + '-hashes.txt')).read_text().splitlines() if traced else None

        native = run('native', '--save-state', f'1200:{state}', '--screenshot', out / 'native.png')
        interp = run('interpreter', '--interp-only', '--screenshot', out / 'interpreter.png')
        resumed = run('resumed', '--load-state', state, '--screenshot', out / 'resumed.png')
        assert len(native) == 1800 and native == interp, f'{variant}: native/interpreter mismatch'
        assert len(resumed) == 599 and resumed == native[1201:], f'{variant}: state continuation mismatch'
        assert (out / 'native.png').read_bytes() == (out / 'interpreter.png').read_bytes() == (out / 'resumed.png').read_bytes()
        assert 'interpreted: ROM 0 ' in (out / 'native.log').read_text(), 'Route needs additional cycle seeds'
        # --hash-out disables native intervals; compare untraced output too.
        run('active', '--frame-log', out / 'active.bin', '--wav-out', out / 'active.wav',
            '--screenshot', out / 'active.png', traced=False)
        with wave.open(str(out / 'active.wav')) as wav:
            pcm = wav.readframes(wav.getnframes())
            peak = max(abs(n[0]) for n in struct.iter_unpack('<h', pcm))
            duration = wav.getnframes() / wav.getframerate()
            assert wav.getframerate() == 48000 and wav.getnchannels() == 1 and peak > 0
            assert 35.94 < duration < 36.05, f'Unexpected PAL audio duration: {duration}'
        captures[variant] = {suffix: hashlib.sha256((out / ('active.' + suffix)).read_bytes()).hexdigest()
                             for suffix in ('bin', 'wav', 'png')}
        hashes[variant] = native
        summaries[variant] = dict(frames=1800, resumed_frames=599, native_interpreter_match=True,
                                  state_continuation_match=True, interpreted_rom_cycles=0,
                                  audio_seconds=duration, audio_peak=peak, output_sha256=captures[variant])
    # hw= hashes internal PPU bookkeeping, which differs between PPU implementations.
    def visible(lines):
        return [[field for field in line.split() if not field.startswith('hw=')] for line in lines]
    assert visible(hashes['baseline']) == visible(hashes['optimized']), 'Reference/optimized frame traces differ'
    assert captures['baseline'] == captures['optimized'], 'Reference/optimized raw frames, PCM or PNG differ'
    summary = dict(region='PAL', variants=summaries, reference_optimized_traces_frames_pcm_png_match=True)
    (base / 'test-summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
