#!/usr/bin/env python3
"""Validate matched demo/gameplay/profile console runs against desktop states."""
import argparse
import hashlib
import json
from pathlib import Path
import re


def fields(line):
    return dict(re.findall(r'(\w+)=([^\s]+)', line))


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read_case(path, reference, mode, profiled):
    text = path.read_text()
    lines = text.splitlines()
    header = fields(lines[0])
    manifest = json.loads((path.parent / 'build.json').read_text())
    require(header['sha256'] == manifest['sha256'], f'Log/manifest mismatch: {path}')
    require(hashlib.sha256((path.parent / manifest['artifact']).read_bytes()).hexdigest() == manifest['sha256'],
            f'Executable changed: {path}')
    require(manifest['core_profiler'] == profiled, f'Wrong profiler setting: {path}')
    require(manifest['rom_sha256'] == reference['_metadata']['rom_sha256'], f'Wrong ROM: {path}')
    summaries = [fields(line) for line in lines if line.startswith('benchmark ')]
    states = [fields(line) for line in lines if line.startswith('benchmark_state ')]
    require(len(summaries) == len(states) == 1, f'Missing/duplicate benchmark state: {path}')
    s = summaries[0]
    expected = reference[mode]
    require(s.get('complete') == '1' and s.get('interruptions') == '0', f'Incomplete/interrupted run: {path}')
    require(int(s['total_frames']) == expected['frames'] and int(s['warmup_frames']) == expected['warmup']
            and int(s['frames']) == expected['frames'] - expected['warmup'], f'Wrong measurement window: {path}')
    require(s['input'] == ('scripted' if mode == 'gameplay' else 'neutral')
            and int(s['replay_frames']) == (expected['frames'] if mode == 'gameplay' else 0),
            f'Input replay was not applied correctly: {path}')
    require(int(s['profiled']) == int(profiled) and s['kernel'] == 'neon', f'Kernel/profiler mismatch: {path}')
    require(states[0] == expected['state'], f'Desktop/console final-state mismatch: {path}')
    if mode == 'gameplay':
        require(header['route_sha256'] == manifest['benchmark_input_sha256'] == reference['_metadata']['route_sha256'],
                f'Input route identity mismatch: {path}')
    platforms = [fields(line) for line in lines if line.startswith('platform ')]
    require(bool(platforms), f'Missing platform reports: {path}')
    modes = {(p['applet_type'], p['operation_mode'], p['performance_mode'], p['cpu_hz'], p['clock_result']) for p in platforms}
    require(len(modes) == 1, f'Unstable launch mode/clock: {path}')
    platform = next(iter(modes))
    require(platform[0] == '0' and int(platform[3]) > 0 and platform[4] == '0x00000000', f'Invalid clock/application mode: {path}')
    region = [fields(line) for line in lines if line.startswith('Region=')]
    audio = [line for line in lines if line.startswith('Audio ')]
    renderer = [line for line in lines if line.startswith('Renderer=')]
    require(len(region) == len(audio) == len(renderer) == 1 and 'PPU=HLE' in renderer[0]
            and 'saves=disabled' in text, f'Missing/different runtime settings: {path}')
    profile_frames = 0
    totals = dict(estimated_ppu_ms=0.0, estimated_apu_ms=0.0, residual_ms=0.0)
    frame_count = 0
    paths = {}
    for line in lines:
        if line.startswith('performance '):
            frame_count = int(fields(line)['frames'])
        elif line.startswith('core_profile path='):
            p = fields(line)
            paths[p['path']] = paths.get(p['path'], 0.0) + float(p['estimated_ms']) * frame_count
        elif line.startswith('core_profile estimated_ppu_ms='):
            p = fields(line)
            profile_frames += frame_count
            for key in totals:
                totals[key] += float(p[key]) * frame_count
    if profiled:
        require(profile_frames == int(s['frames']), f'Profiler window does not match benchmark: {path}')
        totals = {key: value / profile_frames for key, value in totals.items()}
        totals['paths_ms'] = {key: value / profile_frames for key, value in paths.items()}
    else:
        require(profile_frames == 0, f'Profiler records in a baseline: {path}')
        totals = None
    return dict(log=str(path), sha256=manifest['sha256'], version=manifest['version'],
                engine_patch_sha256=manifest['engine_patch_sha256'], platform=platform,
                region=region[0]['Region'], target_fps=float(region[0]['target_fps']),
                audio_device=audio[0], renderer=renderer[0], state=states[0],
                measured_frames=int(s['frames']), warmup=int(s['warmup_frames']),
                fps=float(s['fps']), emulation_ms=float(s['emulation_ms']),
                audio_ms=float(s['audio_ms']), present_ms=float(s['present_ms']),
                audio_supply=float(s['audio_supply']), profiled=profiled, core_profile=totals)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    for name in ('reference', 'gameplay', 'neutral', 'profile', 'out'):
        ap.add_argument('--' + name, type=Path, required=True)
    args = ap.parse_args()
    try:
        reference = json.loads(args.reference.read_text())
        rows = {name: read_case(getattr(args, name).resolve(), reference,
                               'neutral' if name == 'neutral' else 'gameplay', name == 'profile')
                for name in ('gameplay', 'neutral', 'profile')}
        require(rows['gameplay']['sha256'] == rows['neutral']['sha256'], 'Demo/gameplay must use the same executable')
        for key in ('version', 'engine_patch_sha256', 'platform', 'region', 'target_fps', 'audio_device', 'renderer'):
            require(all(row[key] == rows['gameplay'][key] for row in rows.values()), f'Runs differ in {key}')
        report = dict(cases=rows, all_console_states_match_desktop=True,
                      profile_overhead_in_emulation_percent=(rows['profile']['emulation_ms'] / rows['gameplay']['emulation_ms'] - 1) * 100,
                      limitation='Short fixed first-level/demo windows, one baseline each; profiler estimates include sampling overhead. '
                                 'Profiled FPS is not the ordinary game speed.')
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(report, indent=2) + '\n')
        print(json.dumps(report, indent=2))
    except (OSError, ValueError, KeyError) as error:
        ap.error(str(error))


if __name__ == '__main__':
    main()
