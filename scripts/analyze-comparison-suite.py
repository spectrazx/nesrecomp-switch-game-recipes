#!/usr/bin/env python3
"""Validate a one-launch shared-core policy comparison against desktop execution."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import statistics


def fields(line):
    return dict(re.findall(r'(\w+)=([^\s]+)', line))


def require(ok, message):
    if not ok:
        raise ValueError(message)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--log', type=Path, required=True)
    p.add_argument('--reference', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    a = p.parse_args()
    lines = a.log.read_text().splitlines()
    header = fields(lines[0])
    manifest = json.loads((a.log.parent / 'build.json').read_text())
    reference = json.loads(a.reference.read_text())
    mode = 'gameplay' if header['gameplay'] == 'True' else 'neutral'
    expected = reference[mode]
    require(header['suite'] == 'True' and header['profiled'] == 'False', 'Wrong experiment mode')
    require(header['sha256'] == manifest['sha256'] == hashlib.sha256(
        (a.log.parent / manifest['artifact']).read_bytes()).hexdigest(), 'Changed artifact')
    require(not manifest['core_profiler'], 'Profiled build cannot be a baseline')
    require(manifest['rom_sha256'] == reference['_metadata']['rom_sha256'], 'ROM mismatch')
    if mode == 'gameplay':
        require(header['route_sha256'] == manifest['benchmark_input_sha256'] == reference['_metadata']['route_sha256'], 'Route mismatch')
    regions = {fields(line)['Region'] for line in lines if line.startswith('Region=')}
    require(len(regions) == 1 and regions <= {'NTSC', 'PAL'}, 'Missing/changing region')
    region = next(iter(regions))
    policy = manifest.get('switch_comparison_policy', 'pal_intervals' if region == 'PAL' else 'masked_irq')
    require(policy in ({'pal_intervals', 'pal_raster'} if region == 'PAL' else
                       {'masked_irq', 'sprite_fetch', 'sprite_fetch_jobs'}), 'Policy/region mismatch')
    expected_region = manifest.get('region', 'PAL' if manifest['game'] == 'adventure-island' else 'NTSC')
    require(region == expected_region, 'Wrong game region')
    require(any(line.startswith('Sprite_kernel=neon ') for line in lines), 'Wrong kernel')
    require(any('saves=disabled' in line for line in lines), 'Saving enabled')
    rows = [fields(line) for line in lines if line.startswith('comparison_result ')]
    require(len(rows) == 6, 'Missing/duplicate comparison legs')
    for row in rows:
        # Preserve analysis of archived IRQ-suite logs.
        if 'masked_irq' in row:
            row['policy'], row['enabled'] = 'masked_irq', row['masked_irq']
        require(row.get('policy') == policy, 'Wrong comparison policy')
    require([r['enabled'] for r in rows] == ['0', '1', '0', '1', '1', '0'], 'Wrong warmup/ABBA order')
    for i, row in enumerate(rows):
        require(row['index'] == str(i) and row['phase'] == ('warmup' if i < 2 else 'measure'), 'Wrong leg identity')
        require(row['complete'] == row['state_match'] == '1' and row['interruptions'] == '0', 'Interrupted or mismatching leg')
        require(int(row['total_frames']) == expected['frames'] and int(row['warmup']) == expected['warmup'] and
                int(row['frames']) == expected['frames'] - expected['warmup'], 'Wrong measured window')
        require(int(row['replay_frames']) == (expected['frames'] if mode == 'gameplay' else 0), 'Wrong replay count')
        require({k: row[k] for k in ['mem', 'hw']} == expected['state'], 'Desktop/console state mismatch')
    require(lines.count('comparison_complete legs=6 complete=1') == 1, 'Incomplete suite')
    platforms = [fields(line) for line in lines if line.startswith('platform ')]
    require(len(platforms) >= 12, 'Missing leg boundary clock reads')
    states = {(r['applet_type'], r['operation_mode'], r['performance_mode'], r['cpu_hz'], r['clock_result']) for r in platforms}
    require(len(states) == 1, 'Changing clock or application mode')
    platform = next(iter(states))
    require(platform == ('0', '0', '0', '1020000000', '0x00000000'), 'Unexpected handheld launch/clock')
    averages = {name: {key: statistics.mean(float(r[key]) for r in rows[2:] if r['enabled'] == flag)
                       for key in ['fps', 'emulation_ms', 'audio_ms', 'present_ms', 'audio_supply']}
                for name, flag in [('reference', '0'), ('candidate', '1')]}
    old, new = averages['reference'], averages['candidate']
    result = dict(mode=mode, region=region, policy=policy, version=manifest['version'], sha256=manifest['sha256'],
                  engine_patch_sha256=manifest['engine_patch_sha256'], platform=platform,
                  rows=rows, averages=averages, fps_gain_percent=(new['fps']/old['fps']-1)*100,
                  emulation_reduction_percent=(1-new['emulation_ms']/old['emulation_ms'])*100,
                  caveat='Same-binary policy comparison; both variants contain the new core code and generated helpers.')
    a.out.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({key: result[key] for key in ['mode', 'averages', 'fps_gain_percent', 'emulation_reduction_percent']}, indent=2))


if __name__ == '__main__':
    main()
