import copy
import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

import configure_lx
from configure_lx import fullscreen_config


class FullscreenTest(unittest.TestCase):
    def test_preserves_other_settings_and_does_not_mutate_original(self):
        original = {'version': '2', 'setting': {
            'common.startInFullscreen': False, 'common.apiSource': 'keep',
            'common.isAgreePact': False, 'player.playQuality': '128k'}}
        before = copy.deepcopy(original)
        changed = fullscreen_config(original)
        self.assertEqual(original, before)
        self.assertIs(changed['setting']['common.startInFullscreen'], True)
        changed['setting']['common.startInFullscreen'] = False
        self.assertEqual(changed, before)

    def test_idempotent(self):
        original = {'setting': {'common.startInFullscreen': True}}
        self.assertEqual(fullscreen_config(original), original)

    def test_rejects_unknown_schema(self):
        for value in ({}, {'setting': []}, []):
            with self.subTest(value=value), self.assertRaises(ValueError):
                fullscreen_config(value)

    def test_cli_backs_up_and_preserves_unrelated_settings(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory).resolve()
            config = home / '.config/lx-music-desktop/LxDatas/config_v2.json'
            config.parent.mkdir(parents=True)
            original = {'setting': {'common.apiSource': 'keep', 'common.isAgreePact': False}}
            raw = json.dumps(original).encode('utf-8')
            config.write_bytes(raw)
            with patch.object(configure_lx.os, 'geteuid', return_value=1000, create=True), \
                 patch.object(configure_lx.Path, 'home', return_value=home), \
                 patch.object(configure_lx.Path, 'iterdir', return_value=iter(())), \
                 contextlib.redirect_stdout(io.StringIO()):
                configure_lx.main()
            self.assertEqual(json.loads(config.read_text()), fullscreen_config(original))
            backups = list(config.parent.glob('config-before-fullscreen-*.json'))
            self.assertEqual(len(backups), 1)
            self.assertEqual(backups[0].read_bytes(), raw)

    def test_cli_refuses_to_write_while_lx_is_running(self):
        process = Mock()
        process.name = '42'
        process.__truediv__ = Mock(return_value=Mock())
        process.__truediv__.return_value.read_bytes.return_value = (
            b'/opt/lx-music-desktop/lx-music-desktop\0--ozone-platform=wayland\0')
        with patch.object(configure_lx.os, 'geteuid', return_value=1000, create=True), \
             patch.object(configure_lx.Path, 'iterdir', return_value=iter((process,))), \
             self.assertRaisesRegex(SystemExit, 'Close LX'):
            configure_lx.main()


if __name__ == '__main__':
    unittest.main()
