#!/usr/bin/env python3
"""Build the next patch version, verify it, and deploy it to a mounted SD."""
import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

from game_version import next_patch

ROOT = Path(__file__).resolve().parents[1]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require_mount(sd):
    if not os.path.ismount(sd):
        raise ValueError(f'SD card is not mounted at {sd}')


def stage(source, destination, expected):
    """Copy content only, flush it and verify before replacing a live file."""
    pending = destination.with_name('.' + destination.name + '.tmp')
    try:
        with source.open('rb') as src, pending.open('wb') as dst:
            shutil.copyfileobj(src, dst)
            dst.flush()
            os.fsync(dst.fileno())
        if digest(pending) != expected:
            raise ValueError(f'Copy verification failed: {destination}')
        return pending
    except BaseException:
        pending.unlink(missing_ok=True)
        raise


def deploy(game, rom, sd, backend):
    require_mount(sd)
    version_file = ROOT / 'games' / game / 'VERSION'
    version = next_patch(version_file.read_text())
    print(f'Building and copying {game} {version}', flush=True)
    command = [sys.executable, str(ROOT / 'scripts/build-game.py'), game,
               '--rom', str(rom), '--version', version, '--backend', backend]
    subprocess.run(command, cwd=ROOT, check=True)
    output = ROOT / 'build/recipes' / game
    manifest_path = output / 'build.json'
    manifest = json.loads(manifest_path.read_text())
    if manifest['game'] != game or manifest['version'] != version:
        raise ValueError('Build manifest does not match the requested game/version')
    name = manifest['artifact']
    if Path(name).name != name or not name.endswith('.nro'):
        raise ValueError('Invalid artifact name in build manifest')
    artifact = output / name
    if digest(artifact) != manifest['sha256'] or digest(rom) != manifest['rom_sha256']:
        raise ValueError('Build artifacts or ROM changed after verification')
    subprocess.run([sys.executable, str(ROOT / 'scripts/inspect-nro.py'), str(artifact),
                    '--expect-version', version], check=True)
    require_mount(sd)  # The card may have been removed during compilation.
    destination = sd / 'switch/nesrecomp' / game
    destination.mkdir(parents=True, exist_ok=True)
    pending = []
    try:
        for source, target, expected in (
            (artifact, destination / name, manifest['sha256']),
            (rom, destination / 'rom.nes', manifest['rom_sha256']),
            (manifest_path, destination / 'build.json', digest(manifest_path)),
        ):
            pending.append((stage(source, target, expected), target, expected))
        for temporary, target, expected in pending:
            temporary.replace(target)
            if digest(target) != expected:
                raise ValueError(f'Final verification failed: {target}')
        os.sync()
        # Only a successfully verified deployment advances the source version.
        temporary_version = version_file.with_suffix('.tmp')
        temporary_version.write_text(version + '\n')
        temporary_version.replace(version_file)
    finally:
        for temporary, _, _ in pending:
            temporary.unlink(missing_ok=True)
    print(f'Deployed {game} {version} to {destination}; hashes verified and writes synced.', flush=True)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('game')
    ap.add_argument('--rom', required=True, type=Path)
    ap.add_argument('--sd-root', type=Path, default=Path('/Volumes/Untitled'))
    ap.add_argument('--backend', choices=['auto', 'native', 'docker'], default='auto')
    args = ap.parse_args()
    if not re.fullmatch(r'[a-z0-9_-]+', args.game) or not (ROOT / 'games' / args.game / 'game.cmake').is_file():
        ap.error(f'Unknown game recipe: {args.game}')
    rom = args.rom.expanduser().resolve()
    if not rom.is_file():
        ap.error('ROM must be an existing file')
    lock_dir = ROOT / '.local'
    lock_dir.mkdir(exist_ok=True)
    with (lock_dir / f'deploy-{args.game}.lock').open('a') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            ap.error(f'A deployment of {args.game} is already running')
        deploy(args.game, rom, args.sd_root.expanduser().resolve(), args.backend)


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        print(f'Deployment failed: {error}', file=sys.stderr)
        sys.exit(1)
