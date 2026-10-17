"""Run with both repositories on PYTHONPATH under a display or xvfb-run."""
import threading
import sys
import tempfile
from pathlib import Path

from fluorine import Element, Page
from sulfur import App

page = Page('bridge-smoke')
status = Element('p', 'Waiting', id='status')
move = Element('button', 'Move', id='move')
restart = Element('button', 'Restart', id='restart')


def move_hero():
    status.text = 'Moved'


def restart_game():
    status.text = 'Restarted'


move.bind('click', move_hero)
restart.bind('click', restart_game)
page.body(status, move, restart)
page.script("document.getElementById('move').click();")
page.run("document.getElementById('status').setAttribute('data-ready', 'yes');")
temporary = tempfile.TemporaryDirectory()
file_mode = '--file' in sys.argv
if file_mode:
    path = Path(temporary.name) / 'index.html'
    page.build(path)
    app = App(path, callbacks=page.callbacks, silent=True, hidden=True)
    page.attach_runtime(app.runtime)
else:
    app = App(page, silent=True, hidden=True)
result = []


def verify():
    try:
        assert app.window.evaluate_js("document.getElementById('status').getAttribute('data-ready')") == 'yes'
        app.window.evaluate_js("document.getElementById('move').click()")
        # Promise resolution and bridge dispatch happen asynchronously.
        for expected, click in [('Moved', None), ('Restarted', 'restart')]:
            if click:
                app.window.evaluate_js(f"document.getElementById('{click}').click()")
            for _ in range(100):
                if app.window.evaluate_js("document.getElementById('status').textContent") == expected:
                    break
                threading.Event().wait(0.05)
            else:
                raise AssertionError(f'Expected status {expected!r}')
        if not file_mode:
            # Rebind a button after the document is loaded.
            move.bind('click', lambda: setattr(status, 'text', 'Rebound'))
            app.window.evaluate_js("document.getElementById('move').click()")
            for _ in range(100):
                if app.window.evaluate_js("document.getElementById('status').textContent") == 'Rebound':
                    break
                threading.Event().wait(0.05)
            else:
                raise AssertionError('Dynamic callback was not exposed')
        result.append('passed')
    except Exception as exc:
        print('Desktop check failed:', repr(exc), flush=True)
        print('Document:', app.window.evaluate_js('document.body.innerText.slice(0, 1000)'), flush=True)
        print('URL:', app.window.evaluate_js('window.location.href'), flush=True)
        result.append(exc)
    finally:
        app.close()


# App registers its own loaded handler first; wait for its readiness flag.
def after_loaded():
    for _ in range(100):
        if app.runtime._ready:
            verify()
            return
        threading.Event().wait(0.05)
    result.append(AssertionError('Runtime did not become ready'))
    app.close()


app.window.events.loaded += after_loaded
watchdog = threading.Timer(20, app.close)
watchdog.daemon = True
watchdog.start()
try:
    app.open(gui='qt')
finally:
    watchdog.cancel()
    temporary.cleanup()
assert result == ['passed'], result
print('Desktop callback, DOM update, restart, and rebinding checks passed.')
