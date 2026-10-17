import logging
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.parse import unquote, urlparse


def local_path(url):
    return Path(unquote(urlparse(url).path))

# Unit tests exercise the host contract without a GUI or pywebview dependency.
class Event:
    def __init__(self):
        self.handlers = []

    def __iadd__(self, handler):
        self.handlers.append(handler)
        return self

    def fire(self):
        for handler in self.handlers:
            handler()


class Window:
    def __init__(self, title, target, **options):
        self.title, self.target, self.options = title, target, options
        self.events = types.SimpleNamespace(before_load=Event(), loaded=Event(), closed=Event())
        self.functions = {}
        self.scripts = []

    def expose(self, handler):
        self.functions[handler.__name__] = handler

    def evaluate_js(self, script):
        self.scripts.append(script)
        return 'evaluated'

    def destroy(self):
        self.events.closed.fire()


fake_webview = types.ModuleType('webview')
fake_webview.create_window = Window
fake_webview.start = lambda **kwargs: None
with patch.dict(sys.modules, {'webview': fake_webview}):
    import sulfur
    from sulfur.bridge import PageRuntime


class FakePage:
    name = 'test-page'

    def __init__(self):
        self.callbacks = {}
        self.attached = None

    def build(self, to):
        Path(to).write_text('<html></html>')
        self.callbacks['fl_move_0'] = lambda: 'moved'
        return to

    def attach_runtime(self, runtime):
        self.attached = runtime
        runtime.evaluate_js('queued_by_page()')

    def detach_runtime(self):
        self.attached = None


class AppTests(unittest.TestCase):
    def setUp(self):
        self.patch = patch.object(sulfur, 'webview', fake_webview)
        self.patch.start()
        self.addCleanup(self.patch.stop)

    def test_page_callbacks_are_explicit_and_updates_wait_for_loaded(self):
        page = FakePage()
        app = sulfur.App(page, silent=True)
        self.addCleanup(app._cleanup)
        self.assertNotIn('js_api', app.window.options)
        self.assertEqual(app.window.functions['fl_move_0'](), 'moved')
        self.assertEqual(app.window.scripts, [])
        app.run('queued_by_app()')
        app.window.events.loaded.fire()
        self.assertIn('fluorine.connect', app.window.scripts[0])
        self.assertEqual(app.window.scripts[1:], ['queued_by_page()', 'queued_by_app()'])
        self.assertEqual(app.run('live()'), 'evaluated')

    def test_built_file_callbacks_aliases_and_arguments(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'index.html'
            path.write_text('<html></html>')
            def move(direction):
                return direction
            original = move.__name__
            app = sulfur.App(path, silent=True, callbacks={'left': move, 'right': move},
                             width=640, height=480, resizable=False)
            self.assertEqual(app.window.functions['left']('west'), 'west')
            self.assertEqual(app.window.functions['right']('east'), 'east')
            self.assertEqual(move.__name__, original)
            self.assertEqual(app.window.options['width'], 640)
            self.assertFalse(app.window.options['resizable'])

    def test_private_legacy_callbacks_are_explicitly_exposed(self):
        window = Window('Legacy', 'legacy.html')
        runtime = PageRuntime(window, lambda: {'_fl_move_0': lambda: 12})
        self.assertEqual(window.functions['_fl_move_0'](), 12)
        self.assertFalse(runtime._ready)

    def test_dynamic_callbacks_are_exposed_before_dom_update(self):
        callbacks = {}
        window = Window('Dynamic', 'dynamic.html')
        runtime = PageRuntime(window, lambda: callbacks)
        window.events.loaded.fire()
        callbacks['dynamic'] = lambda: 5
        runtime.evaluate_js('update_button()')
        self.assertEqual(window.functions['dynamic'](), 5)
        self.assertEqual(window.scripts[-1], 'update_button()')

    def test_reload_buffers_updates_again(self):
        window = Window('Reload', 'reload.html')
        runtime = PageRuntime(window)
        window.events.loaded.fire()
        window.events.before_load.fire()
        before = len(window.scripts)
        runtime.evaluate_js('after_reload()')
        self.assertEqual(len(window.scripts), before)
        window.events.loaded.fire()
        self.assertEqual(window.scripts[-1], 'after_reload()')

    def test_failed_queued_script_does_not_block_later_updates(self):
        window = Window('Queue', 'queue.html')
        runtime = PageRuntime(window)
        runtime.evaluate_js('broken()')
        runtime.evaluate_js('valid()')
        evaluate = window.evaluate_js
        def execute(script):
            if script == 'broken()':
                raise RuntimeError('JavaScript error')
            return evaluate(script)
        window.evaluate_js = execute
        with self.assertLogs('sulfur', level='ERROR'):
            window.events.loaded.fire()
        self.assertTrue(runtime._ready)
        self.assertEqual(window.scripts[-1], 'valid()')

    def test_invalid_callbacks_are_rejected(self):
        for callbacks, error in [({'bad-name': lambda: None}, ValueError),
                                 ({'not_callable': 42}, TypeError)]:
            with self.assertRaises(error):
                sulfur.App('https://example.com', callbacks=callbacks, silent=True)

    def test_close_cleans_temporary_html_and_detaches_page(self):
        page = FakePage()
        app = sulfur.App(page, silent=True)
        self.assertTrue(app.window.target.startswith('file://'))
        path = local_path(app.window.target)
        self.assertTrue(path.exists())
        app.close()
        self.assertFalse(path.exists())
        self.assertIsNone(page.attached)
        app._cleanup()  # Cleanup is idempotent.

    def test_missing_file_and_failed_build_have_useful_errors(self):
        with self.assertRaises(FileNotFoundError):
            sulfur.App('/missing/sulfur-file.html', silent=True)
        page = FakePage()
        page.build = lambda to: None
        with self.assertRaisesRegex(ValueError, 'did not produce'):
            sulfur.App(page, silent=True)

    def test_start_failure_cleans_temporary_file(self):
        app = sulfur.App(FakePage(), silent=True)
        path = local_path(app.window.target)
        with patch.object(fake_webview, 'start', side_effect=RuntimeError('backend failed')):
            with self.assertRaisesRegex(RuntimeError, 'backend failed'):
                app.open(dev=True)
        self.assertFalse(path.exists())

    def test_local_server_can_be_requested_explicitly(self):
        app = sulfur.App(FakePage(), silent=True, serve_local=True)
        self.addCleanup(app._cleanup)
        self.assertTrue(Path(app.window.target).is_file())
        self.assertNotIn('serve_local', app.window.options)

    def test_javascript_errors_remain_visible(self):
        record = logging.LogRecord('pywebview', logging.ERROR, '', 0,
                                   'js: Uncaught TypeError: callback is not a function', (), None)
        self.assertTrue(sulfur._SulfurLogFilter().filter(record))


if __name__ == '__main__':
    unittest.main()
