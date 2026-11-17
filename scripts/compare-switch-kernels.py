#!/usr/bin/env python3
"""Summarize ordered portable/NEON console benchmark logs with evidence checks."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import statistics


def fields(line):
    return dict(re.findall(r'(\w+)=([^\s]+)', line))


def read_run(path):
    text = path.read_text()
    header = fields(text.splitlines()[0])
    manifest = json.loads((path.parent / 'build.json').read_text())
    if header.get('sha256') != manifest['sha256']:
        raise ValueError(f'Log/package hash mismatch: {path}')
    artifact = path.parent / manifest['artifact']
    if hashlib.sha256(artifact.read_bytes()).hexdigest() != manifest['sha256']:
        raise ValueError(f'Package changed since its recorded build: {path}')
    lines = text.splitlines()
    summaries = [fields(line) for line in lines if line.startswith('benchmark ')]
    states = [fields(line) for line in lines if line.startswith('benchmark_state ')]
    platforms = [fields(line) for line in lines if line.startswith('platform ')]
    if len(summaries) != 1 or len(states) != 1 or not platforms:
        raise ValueError(f'Missing/duplicate benchmark or state/platform evidence: {path}')
    summary = summaries[0]
    if (summary.get('complete') != '1' or summary.get('interruptions') != '0'
            or summary.get('frames') != '600' or summary.get('total_frames') != '900'
            or summary.get('warmup_frames') != '300'):
        raise ValueError(f'Incomplete or interrupted 900-frame benchmark: {path}')
    expected = 'portable' if manifest['sprite_kernel'] == 'portable' else 'neon'
    if summary['kernel'] != expected:
        raise ValueError(f'Runtime kernel does not match package: {path}')
    if 'saves=disabled' not in text or 'core_profiler=off' not in text or 'PPU=HLE' not in text:
        raise ValueError(f'Save/profiler/PPU policy differs: {path}')
    region = [line for line in lines if line.startswith('Region=')]
    audio = [line for line in lines if line.startswith('Audio ')]
    if len(region) != 1 or len(audio) != 1:
        raise ValueError(f'Missing audio/region configuration: {path}')
    modes = {(p['applet_type'], p['operation_mode'], p['performance_mode'],
              p['cpu_hz'], p['clock_result']) for p in platforms}
    if len(modes) != 1 or next(iter(modes))[0] != '0' or next(iter(modes))[4] != '0x00000000':
        raise ValueError(f'Unstable clocks/mode, applet launch or failed clock query: {path}')
    if int(next(iter(modes))[3]) <= 0:
        raise ValueError(f'Missing CPU frequency: {path}')
    return dict(log=str(path), game=manifest['game'], version=manifest['version'],
                sha256=manifest['sha256'], engine_patch_sha256=manifest['engine_patch_sha256'],
                rom_sha256=manifest['rom_sha256'], state=states[0], platform=sorted(modes)[0],
                region=region[0], audio_device=audio[0],
                kernel=summary['kernel'], fps=float(summary['fps']),
                emulation_ms=float(summary['emulation_ms']),
                audio_ms=float(summary['audio_ms']), present_ms=float(summary['present_ms']),
                audio_supply=float(summary['audio_supply']))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('logs', nargs='+', type=Path, help='Console logs in measurement order')
    ap.add_argument('--out', type=Path, required=True)
    args = ap.parse_args()
    try:
        rows = [read_run(path.resolve()) for path in args.logs]
    except (OSError, ValueError, KeyError) as error:
        ap.error(str(error))
    for key in ('game', 'version', 'engine_patch_sha256', 'rom_sha256', 'state', 'platform', 'region', 'audio_device'):
        if any(row[key] != rows[0][key] for row in rows):
            ap.error(f'Runs differ in {key}; this is not a matched comparison')
    groups = {name: [row for row in rows if row['kernel'] == name] for name in ('portable', 'neon')}
    if not all(groups.values()):
        ap.error('Provide at least one run for each kernel')
    means = {name: {field: statistics.mean(row[field] for row in group)
                    for field in ('emulation_ms', 'audio_ms', 'present_ms', 'fps', 'audio_supply')}
             for name, group in groups.items()}
    order = [row['kernel'] for row in rows]
    balanced = order in (['portable', 'neon', 'neon', 'portable'], ['neon', 'portable', 'portable', 'neon'])
    variation = {name: (max(row['emulation_ms'] for row in group) - min(row['emulation_ms'] for row in group))
                       / means[name]['emulation_ms'] * 100 for name, group in groups.items()}
    report = dict(game=rows[0]['game'], order=order, balanced_abba=balanced,
                  means=means, rows=rows, within_kernel_range_percent=variation,
                  neon_emulation_reduction_percent=(1 - means['neon']['emulation_ms']
                                                    / means['portable']['emulation_ms']) * 100,
                  limitation='One neutral-input demo route; desktop correctness is separate. '
                             + ('Four ordered runs, not a statistical confidence interval.' if balanced else
                                'Preliminary comparison: complete ABBA before selecting a default.'))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
