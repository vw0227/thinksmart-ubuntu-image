import ast
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import MagicMock, Mock
import thinksmart_browser_navigation as nav


class LxEntryTest(unittest.TestCase):
    def test_optional_apps_are_hidden_when_not_installed(self):
        for apps, expected in [((), set()), (('lx-music',), {'洛雪音乐'})]:
            with self.subTest(apps=apps):
                gtk = MagicMock()
                labels = []
                gtk.Button.side_effect = lambda label: labels.append(label) or MagicMock()
                view = MagicMock()
                view.get_uri.return_value = 'http://127.0.0.1:8090/'
                nav.wrap_view(gtk, SimpleNamespace(), view, Mock(), open_wifi=Mock(),
                              launch_app=Mock(), available_apps=apps)
                self.assertEqual(set(labels), expected | {'语音助手', '后退', '刷新', 'Wi-Fi 设置'})

    def test_buttons_and_music_dispatch(self):
        gtk = MagicMock()
        buttons = {}
        def create(label):
            buttons[label] = MagicMock()
            return buttons[label]
        gtk.Button.side_effect = create
        view = MagicMock()
        view.get_uri.return_value = 'http://127.0.0.1:8090/'
        launch = Mock()
        nav.wrap_view(gtk, SimpleNamespace(), view, Mock(), open_wifi=Mock(), launch_app=launch)
        self.assertEqual(set(buttons), {'语音助手', '哔哩哔哩', '洛雪音乐', '后退', '刷新', 'Wi-Fi 设置'})
        buttons['洛雪音乐'].connect.call_args.args[1](buttons['洛雪音乐'])
        launch.assert_called_once_with('lx-music')
        for button in buttons.values():
            self.assertGreaterEqual(button.set_size_request.call_args.args[1], 58)

    def test_allowlist_and_duplicate_guard(self):
        source = ast.parse(Path('thinksmart-kiosk.py').read_text(encoding='utf-8'))
        node = next(x for x in ast.walk(source) if isinstance(x, ast.FunctionDef) and x.name == 'launch_native')
        node.body = [ast.copy_location(ast.Global(names=x.names), x) if isinstance(x, ast.Nonlocal)
                     else x for x in node.body]
        process = Mock()
        process.Popen.return_value.poll.return_value = None
        scope = {'native_process': None, 'subprocess': process}
        exec(compile(ast.Module(body=[node], type_ignores=[]), '<actual native launcher>', 'exec'), scope)
        launch = scope['launch_native']
        for name in ['douyin', '/bin/sh', 'lx-music;id']:
            launch(name)
        process.Popen.assert_not_called()
        launch('lx-music')
        self.assertEqual(process.Popen.call_args.args[0], ['/usr/local/bin/thinksmart-lx-music'])
        launch('lx-music')
        launch('bilibili')
        self.assertEqual(process.Popen.call_count, 1)
        process.Popen.return_value.poll.return_value = 0
        launch('bilibili')
        self.assertEqual(process.Popen.call_args.args[0], ['/usr/local/bin/thinksmart-bilibili'])


if __name__ == '__main__':
    unittest.main()
