"""Version/deployment contracts using original fixture data and a fake build."""
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parents[1] / 'scripts'
sys.path.insert(0, str(SCRIPTS))
from game_version import next_patch, validate

spec = importlib.util.spec_from_file_location('deploy_game', SCRIPTS / 'deploy-game.py')
deploy = importlib.util.module_from_spec(spec)
spec.loader.exec_module(deploy)


class DeploymentTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.version = self.root / 'games/fixture/VERSION'
        self.version.parent.mkdir(parents=True)
        self.version.write_text('0.2.0\n')
        (self.root / 'scripts').mkdir()
        shutil.copyfile(SCRIPTS / 'inspect-nro.py', self.root / 'scripts/inspect-nro.py')
        self.rom = self.root / 'original.nes'
        self.rom.write_bytes(b'original test data')
        self.sd = self.root / 'sd'
        self.sd.mkdir()
        self.live = self.sd / 'switch/nesrecomp/fixture'
        self.real_run = subprocess.run
        for context in (patch.object(deploy, 'ROOT', self.root),
                        patch.object(deploy.os.path, 'ismount', return_value=True),
                        patch.object(deploy.os, 'sync')):
            context.start()
            self.addCleanup(context.stop)

    def fake_build(self, command, **kwargs):
        if Path(command[1]).name != 'build-game.py':
            return self.real_run(command, **kwargs, stdout=subprocess.DEVNULL)
        version = command[command.index('--version') + 1]
        output = self.root / 'build/games/fixture'
        output.mkdir(parents=True, exist_ok=True)
        # An original synthetic NRO container: no executable/game content.
        data = bytearray(0x80 + 0x38 + 0x4000)
        data[0x10:0x14] = b'NRO0'
        struct.pack_into('<I', data, 0x18, 0x80)
        data[0x80:0x84] = b'ASET'
        struct.pack_into('<QQ', data, 0x98, 0x38, 0x4000)
        data[0xb8:0xbf] = b'Fixture'
        start = 0xb8 + 0x3060
        data[start:start + len(version)] = version.encode()
        (output / 'Fixture.nro').write_bytes(data)
        manifest = dict(game='fixture', version=version, artifact='Fixture.nro',
                        sha256=hashlib.sha256(data).hexdigest(), rom_sha256=deploy.digest(self.rom))
        (output / 'build.json').write_text(json.dumps(manifest))
        return subprocess.CompletedProcess(command, 0)

    def test_versions_and_switch_field_limit(self):
        self.assertEqual(next_patch('0.2.9\n'), '0.2.10')
        self.assertEqual(next_patch('1.0.99'), '1.0.100')
        for invalid in ('', '0.02.1', '1.2', 'v1.2.3', '1.2.3-beta', '1234567890123.0.0'):
            with self.assertRaises(ValueError):
                validate(invalid)

    def test_successive_deployments_increment_embedded_version(self):
        with patch.object(deploy.subprocess, 'run', side_effect=self.fake_build):
            for expected in ('0.2.1', '0.2.2'):
                deploy.deploy('fixture', self.rom, self.sd, 'auto')
                self.assertEqual(self.version.read_text().strip(), expected)
                metadata = json.loads((self.live / 'build.json').read_text())
                self.assertEqual(metadata['version'], expected)
                self.assertEqual(deploy.digest(self.live / 'Fixture.nro'), metadata['sha256'])
                self.assertEqual((self.live / 'rom.nes').read_bytes(), self.rom.read_bytes())

    def test_build_failure_does_not_advance_or_copy(self):
        with patch.object(deploy.subprocess, 'run', side_effect=subprocess.CalledProcessError(1, 'build')):
            with self.assertRaises(subprocess.CalledProcessError):
                deploy.deploy('fixture', self.rom, self.sd, 'auto')
        self.assertEqual(self.version.read_text(), '0.2.0\n')
        self.assertFalse(self.live.exists())

    def test_copy_failure_preserves_version_and_existing_package(self):
        self.live.mkdir(parents=True)
        (self.live / 'Fixture.nro').write_bytes(b'previous package')
        real_stage = deploy.stage
        def fail_on_rom(source, target, expected):
            if target.name == 'rom.nes':
                raise OSError('SD write failed')
            return real_stage(source, target, expected)
        with patch.object(deploy.subprocess, 'run', side_effect=self.fake_build), \
                patch.object(deploy, 'stage', side_effect=fail_on_rom):
            with self.assertRaises(OSError):
                deploy.deploy('fixture', self.rom, self.sd, 'auto')
        self.assertEqual(self.version.read_text(), '0.2.0\n')
        self.assertEqual((self.live / 'Fixture.nro').read_bytes(), b'previous package')
        self.assertEqual(list(self.live.glob('.*.tmp')), [])

    def test_stale_build_manifest_is_rejected(self):
        def stale_build(command, **kwargs):
            command = list(command)
            command[command.index('--version') + 1] = '0.2.0'
            return self.fake_build(command, **kwargs)
        with patch.object(deploy.subprocess, 'run', side_effect=stale_build):
            with self.assertRaisesRegex(ValueError, 'manifest does not match'):
                deploy.deploy('fixture', self.rom, self.sd, 'auto')
        self.assertEqual(self.version.read_text(), '0.2.0\n')
        self.assertFalse(self.live.exists())

    def test_unmounted_card_fails_before_build(self):
        with patch.object(deploy.os.path, 'ismount', return_value=False), \
                patch.object(deploy.subprocess, 'run') as run:
            with self.assertRaises(ValueError):
                deploy.deploy('fixture', self.rom, self.sd, 'auto')
            run.assert_not_called()
        self.assertEqual(self.version.read_text(), '0.2.0\n')


if __name__ == '__main__':
    unittest.main()
