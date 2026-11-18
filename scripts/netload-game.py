#!/usr/bin/env python3
"""Send an existing verified NRO to hbmenu over the local network.

Uses native nxlink when available, otherwise the existing pinned SDK image.
The ROM must already be in the game's SD directory. No version is incremented.
"""
import argparse
import hashlib
import ipaddress
import json
import os
from pathlib import Path
import shlex
import shutil
import socket
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
IMAGE = 'devkitpro/devkita64@sha256:1fc388c3a0d34bd2045a6dadcb1020e069d5f876a187fd705de14b4440c00282'


def wait_for_netloader(address, seconds):
    """Use hbmenu's discovery ping, without opening/consuming its TCP receiver."""
    print(f'Waiting up to {seconds:g}s for NetLoader; open hbmenu and press Y.', flush=True)
    deadline = time.monotonic() + seconds
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as probe:
        probe.bind(('', 28771))
        warned = False
        while time.monotonic() < deadline:
            try:
                probe.sendto(b'nxboot', (address, 28280))
                probe.settimeout(min(1, max(0.001, deadline - time.monotonic())))
                data, peer = probe.recvfrom(64)
                if peer[0] == address and data == b'bootnx':
                    print('NetLoader discovery confirmed; uploading now.', flush=True)
                    return
            except socket.timeout:
                pass
            except OSError as error:
                if not warned:
                    print(f'Console not reachable yet ({error}); waiting for NetLoader.', flush=True)
                    warned = True
                time.sleep(min(1, max(0, deadline - time.monotonic())))
    raise SystemExit('NetLoader did not respond; no upload was started. Open it and retry.')


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('game', choices=sorted(p.name for p in (ROOT / 'games').iterdir() if (p / 'game.cmake').is_file()))
    ap.add_argument('--ip', default=os.environ.get('NESRECOMP_SWITCH_IP'))
    ap.add_argument('--backend', choices=['auto', 'native', 'docker'], default='auto')
    ap.add_argument('--dry-run', action='store_true', help='Check the package and print the command without sending')
    ap.add_argument('--console', action='store_true', help='Collect live runner/audio diagnostics in a local log')
    ap.add_argument('--frames', type=int, help='Exit automatically after this many emulated frames (console mode)')
    ap.add_argument('--package-dir', type=Path, help='Send an isolated experiment package instead of the normal build')
    ap.add_argument('--benchmark', action='store_true', help='Ignore gameplay buttons and measure after 300 warm-up frames')
    ap.add_argument('--warmup', type=int, default=300, help='Number of emulated benchmark warm-up frames')
    ap.add_argument('--gameplay', action='store_true', help='Replay the benchmark input bundled in this NRO')
    ap.add_argument('--game-args', default='', help='Extra NRO arguments, e.g. "--widescreen 21:9"')
    ap.add_argument('--wait-netloader', type=float, default=0,
                    help='Wait this many seconds for a safe UDP discovery reply before uploading')
    args = ap.parse_args()
    if args.wait_netloader < 0:
        ap.error('--wait-netloader cannot be negative')
    if args.frames is not None and (not args.console or args.frames <= 0):
        ap.error('--frames requires --console and a positive frame count')
    if args.benchmark and (not args.console or args.frames is None or args.warmup < 1 or args.frames <= args.warmup):
        ap.error('--benchmark requires --console, a positive --warmup and --frames greater than warm-up')
    if args.gameplay and not args.benchmark:
        ap.error('--gameplay requires --benchmark')
    try:
        address = str(ipaddress.IPv4Address(args.ip))
    except ipaddress.AddressValueError:
        ap.error('Set NESRECOMP_SWITCH_IP or pass --ip with the Switch local IPv4 address')
    folder = args.package_dir.expanduser().resolve() if args.package_dir else ROOT / 'build/recipes' / args.game
    try:
        manifest = json.loads((folder / 'build.json').read_text())
        name = manifest['artifact']
        if manifest['game'] != args.game or Path(name).name != name or not name.endswith('.nro'):
            raise ValueError('Package identity is invalid')
        artifact = folder / name
        actual = hashlib.sha256(artifact.read_bytes()).hexdigest()
        if actual != manifest['sha256']:
            raise ValueError('NRO does not match build.json; rebuild before sending')
        if args.gameplay and (not manifest.get('benchmark_input_sha256') or
                              manifest.get('benchmark_input_asset') != 'romfs:/benchmark-input.txt'):
            raise ValueError('This NRO does not bundle a benchmark route')
        subprocess.run([sys.executable, str(ROOT / 'scripts/inspect-nro.py'), str(artifact),
                        '--expect-version', manifest['version']], check=True)
    except (OSError, ValueError, KeyError) as error:
        ap.error(f'{error}. Build this game first with scripts/build-game.py')
    nxlink = shutil.which('nxlink')
    sdk_tool = Path(os.environ.get('DEVKITPRO', '/opt/devkitpro')) / 'tools/bin/nxlink'
    if not nxlink and sdk_tool.is_file():
        nxlink = str(sdk_tool)
    backend = ('native' if nxlink else 'docker') if args.backend == 'auto' else args.backend
    # hbmenu prepends sdmc:/switch/ to the sanitized upload path.
    remote = f'nesrecomp/{manifest.get("sd_dir", args.game)}/{artifact.stem}-dev.nro'
    if backend == 'native':
        if not nxlink:
            ap.error('Native nxlink is unavailable; use --backend docker')
        command = [nxlink, '-a', address, '-p', remote, str(artifact)]
    else:
        if not shutil.which('docker'):
            ap.error('Install nxlink or start the existing Docker SDK environment')
        command = ['docker', 'run', '--rm']
        if args.console:
            command += ['-p', '28771:28771/tcp']
        command += ['-v', f'{folder}:/package:ro', IMAGE,
                   *(['stdbuf', '-oL', '-eL'] if args.console else []),
                   '/opt/devkitpro/tools/bin/nxlink', '-a', address, '-p', remote,
                   f'/package/{name}']
    if args.game_args and not args.console:
        command[-1:-1] = ['--args', args.game_args]
    if args.console:
        runtime_args = '--nxlink-log'
        if args.frames:
            runtime_args += f' --exit-after {args.frames}'
        if args.benchmark:
            runtime_args += ' --benchmark --uncapped'
            runtime_args += f' --benchmark-warmup {args.warmup}'
            if args.gameplay:
                runtime_args += ' --window-input romfs:/benchmark-input.txt'
        if args.game_args:
            runtime_args += ' ' + args.game_args
        # Insert options before the NRO so GNU getopt also handles them on macOS.
        command[-1:-1] = ['-s', '--args', runtime_args]
    print(f'{"Would send" if args.dry_run else "Sending"} {args.game} {manifest["version"]}, SHA-256 {actual}', flush=True)
    print('The ROM must already be on SD. Open hbmenu and press Y for NetLoader.', flush=True)
    print(shlex.join(command), flush=True)
    if not args.dry_run:
        if args.wait_netloader:
            wait_for_netloader(address, args.wait_netloader)
        if args.console:
            log_path = folder / f'netload-{manifest["version"]}-{actual[:12]}.log'
            if log_path.exists():
                from datetime import datetime
                log_path = log_path.with_stem(log_path.stem + '-' + datetime.now().strftime('%Y%m%d-%H%M%S-%f'))
            print(f'Collecting live diagnostics in {log_path}', flush=True)
            with log_path.open('x') as log:
                log.write(f'game={args.game} version={manifest["version"]} sha256={actual} '
                          f'ppu={manifest.get("ppu", "unknown")} engine={manifest.get("engine_revision", "unknown")} '
                          f'benchmark={args.benchmark} requested_frames={args.frames} warmup={args.warmup} '
                          f'gameplay={args.gameplay} '
                          f'route_sha256={manifest.get("benchmark_input_sha256") if args.gameplay else "none"}\n')
                log.flush()
                with subprocess.Popen(command, cwd=ROOT, stdout=subprocess.PIPE,
                                      stderr=subprocess.STDOUT, text=True, bufsize=1) as process:
                    for line in process.stdout:
                        print(line, end='', flush=True)
                        log.write(line)
                        log.flush()
                    if process.wait():
                        raise subprocess.CalledProcessError(process.returncode, command)
        else:
            subprocess.run(command, cwd=ROOT, check=True, timeout=180)
        receipt = dict(game=args.game, version=manifest['version'], sha256=actual,
                       ppu=manifest.get('ppu'), benchmark=args.benchmark,
                       requested_frames=args.frames,
                       gameplay=args.gameplay, warmup=args.warmup,
                       address=address, remote_path=f'sdmc:/switch/{remote}',
                       verification='Local NRO hash/version checked; nxlink accepted upload; no remote readback')
        (folder / 'netload.json').write_text(json.dumps(receipt, indent=2) + '\n')


if __name__ == '__main__':
    try:
        main()
    except subprocess.CalledProcessError as error:
        sys.exit(error.returncode)
