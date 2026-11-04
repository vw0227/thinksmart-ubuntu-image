"""Native, always-visible navigation; remote pages get no local control bridge."""
import time


class HomeReturn:
    """Try the local homepage first; exit only when its renderer doesn't become ready."""
    def __init__(self, view, glib, webkit, url, restart):
        self.view, self.glib, self.webkit = view, glib, webkit
        self.url, self.restart, self.timer = url, restart, 0
        view.connect('load-changed', self._loaded)
        view.connect('script-dialog', self._dialog)

    def __call__(self):
        if self.timer:
            return
        self.started = time.monotonic()
        self.timer = self.glib.timeout_add(4000, self._fallback)
        self.view.stop_loading()
        self.view.load_uri(self.url)

    def cancel(self):
        if self.timer:
            self.glib.source_remove(self.timer)
            self.timer = 0

    def _loaded(self, view, event):
        if (self.timer and event == self.webkit.LoadEvent.FINISHED
                and view.get_uri() == self.url):
            # Require actual assistant UI, not a completed browser error document.
            script = "document.readyState !== 'loading' && !!document.getElementById('btnMic') && !!document.getElementById('orb')"
            view.evaluate_javascript(script, -1, None, None, None, self._ready, self.timer)

    def _ready(self, view, result, token):
        if token != self.timer or not self.timer or view.get_uri() != self.url:
            return
        try:
            ready = view.evaluate_javascript_finish(result).to_boolean()
        except Exception:
            return  # Keep the deadline if the web process is broken.
        if ready:
            self.cancel()
            print(f'home-return: direct-ready {time.monotonic() - self.started:.3f}s', flush=True)

    def _fallback(self):
        if self.timer:
            self.timer = 0
            print('home-return: timeout, reopening browser', flush=True)
            self.restart()
        return False

    def _dialog(self, _view, dialog):
        if self.timer and dialog.get_dialog_type() == self.webkit.ScriptDialogType.BEFORE_UNLOAD_CONFIRM:
            dialog.confirm_set_confirmed(True)
            return True
        return False


def wrap_view(Gtk, WebKit2, view, go_home, cancel_home=None, open_wifi=None,
              home_url='http://127.0.0.1:8090/', launch_app=None, available_apps=None):
    box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
    bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
    box.get_style_context().add_class('thinksmart-shell')
    bar.get_style_context().add_class('thinksmart-navigation')
    bar.set_margin_start(36)
    bar.set_margin_end(36)
    bar.set_margin_top(10)
    bar.set_margin_bottom(14)
    css = Gtk.CssProvider()
    css.load_from_data(b'''
        @define-color nav_bg #050813;
        @define-color nav_surface #10172c;
        @define-color nav_ink #f2f5ff;
        @define-color nav_text #b6c0e2;
        @define-color nav_accent #6c8cff;
        @define-color nav_cyan #5ee0ff;
        .thinksmart-shell, .thinksmart-navigation { background-color: @nav_bg; }
        .thinksmart-navigation button {
            font-family: "Noto Sans CJK SC"; font-size: 22px; font-weight: 600;
            background-image: none; background-color: @nav_surface; color: @nav_text;
            border: 1px solid alpha(@nav_ink, 0.09); border-radius: 16px;
            padding: 6px 18px; box-shadow: none; text-shadow: none; transition: none;
        }
        .thinksmart-navigation button.utility {
            background-color: transparent; border-color: transparent; font-weight: 500;
        }
        .thinksmart-navigation button:hover { background-color: #1b2442; color: @nav_ink; }
        .thinksmart-navigation button.current {
            background-color: #1b2b55; border-color: alpha(@nav_accent, 0.55); color: @nav_ink;
        }
        .thinksmart-navigation button:active { background-color: #293e70; color: @nav_cyan; }
        .thinksmart-navigation button:focus { outline: 2px solid @nav_cyan; outline-offset: -3px; }
        .thinksmart-navigation button:disabled { color: #7883ab; background-color: transparent; }
        .thinksmart-navigation image { margin-right: 6px; }
    ''')
    def navigate(action):
        def run():
            if cancel_home:
                cancel_home()
            action()
        return run

    actions = [
        ('语音助手', 'audio-input-microphone-symbolic', go_home),
    ]
    if launch_app:
        for name, label, icon in (
                ('bilibili', '哔哩哔哩', 'media-playback-start-symbolic'),
                ('lx-music', '洛雪音乐', 'audio-x-generic-symbolic')):
            if available_apps is None or name in available_apps:
                actions.append((label, icon, navigate(lambda app=name: launch_app(app))))
    primary_count = len(actions)
    actions.extend([
        ('后退', 'go-previous-symbolic', navigate(view.go_back)),
        ('刷新', 'view-refresh-symbolic', navigate(view.reload)),
    ])
    if open_wifi:
        actions.append(('Wi-Fi 设置', 'network-wireless-signal-excellent-symbolic', navigate(open_wifi)))
    buttons = {}
    for i, (label, icon_name, action) in enumerate(actions):
        if i == primary_count:
            bar.pack_start(Gtk.Box(), True, True, 0)
        button = Gtk.Button(label=label)
        button.set_size_request(-1, 58)
        icon = Gtk.Image.new_from_icon_name(icon_name, Gtk.IconSize.LARGE_TOOLBAR)
        icon.set_pixel_size(22)
        icon.get_style_context().add_provider(css, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        button.set_image(icon)
        button.set_always_show_image(True)
        button.set_image_position(Gtk.PositionType.LEFT)
        button.connect('clicked', lambda _button, fn=action: fn())
        if i >= primary_count:
            button.get_style_context().add_class('utility')
        button.get_style_context().add_provider(css, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        buttons[label] = button
        bar.pack_start(button, False, False, 0)
    box.get_style_context().add_provider(css, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
    bar.get_style_context().add_provider(css, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

    def update_current(*_args):
        uri = view.get_uri() or ''
        current = ('Wi-Fi 设置' if uri.startswith('file:///usr/local/share/thinksmart-kiosk/welcome.html')
                   else '语音助手' if uri.startswith(home_url) else '')
        for label, button in buttons.items():
            context = button.get_style_context()
            context.remove_class('current')
            if label == current:
                context.add_class('current')
        buttons['后退'].set_sensitive(view.can_go_back())

    view.connect('notify::uri', update_current)
    view.connect('load-changed', update_current)
    update_current()

    def new_window(_view, decision, kind):
        if kind != WebKit2.PolicyDecisionType.NEW_WINDOW_ACTION:
            return False
        uri = decision.get_request().get_uri()
        decision.ignore()
        if uri.startswith(('https://', 'http://')):
            view.load_uri(uri)
        return True

    view.connect('decide-policy', new_window)
    # The outer window is already fullscreen. Don't let a site hide the return bar.
    view.connect('enter-fullscreen', lambda *_args: True)
    view.connect('leave-fullscreen', lambda *_args: True)
    box.pack_start(view, True, True, 0)
    box.pack_end(bar, False, False, 0)
    return box
