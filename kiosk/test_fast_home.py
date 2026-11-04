import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, Mock

import thinksmart_browser_navigation as nav


class FastHomeTest(unittest.TestCase):
    def setUp(self):
        self.view, self.glib, self.restart = MagicMock(), MagicMock(), Mock()
        self.glib.timeout_add.return_value = 42
        self.webkit = SimpleNamespace(LoadEvent=SimpleNamespace(FINISHED=3),
            ScriptDialogType=SimpleNamespace(BEFORE_UNLOAD_CONFIRM=4))
        self.url = 'http://127.0.0.1:8090/'
        self.home = nav.HomeReturn(self.view, self.glib, self.webkit, self.url, self.restart)

    def finish(self, ready=True, token=None):
        self.view.get_uri.return_value = self.url
        self.home._loaded(self.view, 3)
        args = self.view.evaluate_javascript.call_args.args
        self.view.evaluate_javascript_finish.return_value.to_boolean.return_value = ready
        args[5](self.view, Mock(), args[6] if token is None else token)

    def test_navigate_first_without_restarting(self):
        self.home()
        self.view.stop_loading.assert_called_once_with()
        self.view.load_uri.assert_called_once_with(self.url)
        self.restart.assert_not_called()
        self.assertEqual(self.glib.timeout_add.call_args.args[0], 4000)

    def test_ready_home_cancels_fallback(self):
        self.home()
        self.finish()
        self.glib.source_remove.assert_called_once_with(42)
        self.home._fallback()
        self.restart.assert_not_called()

    def test_wrong_page_does_not_count_as_home(self):
        self.home()
        self.view.get_uri.return_value = 'https://www.iqiyi.com/'
        self.home._loaded(self.view, 3)
        self.view.evaluate_javascript.assert_not_called()
        self.home._fallback()
        self.restart.assert_called_once_with()

    def test_error_or_incomplete_page_keeps_fallback(self):
        self.home()
        self.finish(ready=False)
        self.glib.source_remove.assert_not_called()
        self.home._fallback()
        self.home._fallback()
        self.restart.assert_called_once_with()

    def test_javascript_error_keeps_fallback(self):
        self.home()
        self.view.get_uri.return_value = self.url
        self.home._loaded(self.view, 3)
        args = self.view.evaluate_javascript.call_args.args
        self.view.evaluate_javascript_finish.side_effect = RuntimeError('test')
        args[5](self.view, Mock(), args[6])
        self.home._fallback()
        self.restart.assert_called_once_with()

    def test_repeat_press_does_not_extend_deadline(self):
        self.home()
        self.home()
        self.glib.timeout_add.assert_called_once()
        self.view.load_uri.assert_called_once()

    def test_cancel_prevents_late_restart(self):
        self.home()
        self.home.cancel()
        self.home._fallback()
        self.restart.assert_not_called()

    def test_stale_javascript_cannot_cancel_new_attempt(self):
        self.home()
        self.home.cancel()
        self.glib.timeout_add.return_value = 43
        self.home()
        self.finish(token=42)
        self.home._fallback()
        self.restart.assert_called_once_with()

    def test_leave_confirmation_only_during_explicit_return(self):
        dialog = MagicMock()
        dialog.get_dialog_type.return_value = 4
        self.assertFalse(self.home._dialog(self.view, dialog))
        self.home()
        self.assertTrue(self.home._dialog(self.view, dialog))
        dialog.confirm_set_confirmed.assert_called_once_with(True)
        dialog.get_dialog_type.return_value = 1
        self.assertFalse(self.home._dialog(self.view, dialog))


if __name__ == '__main__':
    unittest.main()
