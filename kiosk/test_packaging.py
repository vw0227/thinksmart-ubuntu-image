from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class PackagingTest(unittest.TestCase):
    def test_installs_navigation_module_with_kiosk(self):
        setup = (ROOT / 'image/device-setup.sh').read_text(encoding='utf-8')
        self.assertIn('kiosk/thinksmart_browser_navigation.py', setup)

    def test_optional_media_launchers_keep_shared_lock_and_no_debug_port(self):
        for name in ('thinksmart-bilibili', 'thinksmart-lx-music'):
            text = (ROOT / 'media' / name).read_text(encoding='utf-8')
            text = '\n'.join(line for line in text.splitlines() if not line.startswith('#'))
            self.assertIn('thinksmart-native-media.lock', text)
            self.assertIn('--nonblock', text)
            self.assertNotIn('--remote-debugging-port', text)
            self.assertNotIn(' --no-sandbox', text)
            self.assertIn('PULSE_SERVER=', text)


if __name__ == '__main__':
    unittest.main()
