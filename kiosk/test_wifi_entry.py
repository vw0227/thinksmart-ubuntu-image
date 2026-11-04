import ast
from pathlib import Path
import unittest
import urllib.parse
from unittest.mock import MagicMock


class WifiEntryTest(unittest.TestCase):
    def setUp(self):
        source = Path(__file__).with_name('thinksmart-kiosk.py').read_text(encoding='utf-8')
        self.tree = ast.parse(source)
        self.state = {'welcome': False, 'busy': False}
        self.view = MagicMock()

    def function(self, name):
        func = next(n for n in ast.walk(self.tree) if isinstance(n, ast.FunctionDef) and n.name == name)
        ns = {'state': self.state, 'view': self.view, 'urllib': urllib,
              'WELCOME': '/usr/local/share/thinksmart-kiosk/welcome.html',
              'page_status': lambda: {'target': 'http://127.0.0.1:8090/'}}
        exec(compile(ast.Module(body=[func], type_ignores=[]), '<actual kiosk function>', 'exec'), ns)
        return ns[name]

    def test_wifi_opens_existing_local_sheet_and_holds_page(self):
        self.function('show_welcome')(wifi=True)
        uri = self.view.load_uri.call_args.args[0]
        self.assertTrue(uri.startswith('file:///usr/local/share/thinksmart-kiosk/welcome.html?'))
        self.assertTrue(uri.endswith('#wifi'))
        self.assertTrue(self.state['welcome'])
        self.assertTrue(self.state['busy'])

    def test_normal_welcome_is_not_pinned_to_wifi(self):
        self.function('show_welcome')()
        self.assertNotIn('#wifi', self.view.load_uri.call_args.args[0])
        self.assertFalse(self.state['busy'])

    def test_leaving_local_page_clears_stale_welcome_state(self):
        self.state.update(welcome=True, busy=True)
        self.view.get_uri.return_value = 'https://www.iqiyi.com/'
        self.function('on_uri_changed')(self.view, None)
        self.assertFalse(self.state['welcome'])
        self.assertFalse(self.state['busy'])

    def test_wifi_page_keeps_local_state(self):
        self.state.update(welcome=True, busy=True)
        self.view.get_uri.return_value = 'file:///usr/local/share/thinksmart-kiosk/welcome.html#wifi'
        self.function('on_uri_changed')(self.view, None)
        self.assertTrue(self.state['welcome'])
        self.assertTrue(self.state['busy'])


if __name__ == '__main__':
    unittest.main()
