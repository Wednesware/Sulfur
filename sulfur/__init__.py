"""Host HTML files and optional Python callbacks in a desktop window."""
import logging
import sys
import tempfile
from pathlib import Path

from .bridge import PageRuntime

__version__ = '26.9'

try:
    from nitrogen import require
    Color = require('magnesium.color').Color
except ImportError:
    class Color:
        yellow = reset = ''

try:
    import webview
except ImportError as exc:
    raise ImportError(
        'Sulfur requires pywebview. Install pywebview and a supported GUI backend '
        '(on Linux: PySide6 and qtpy).'
    ) from exc

_IGNORED_MESSAGES = (
    'Registered new object after initialization, existing clients won\'t be notified!',
    'QtWaylandClient::QWaylandTextInputv3::disableSurface',
)

class _SulfurLogFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        message = record.getMessage()
        return not any(ignored in message for ignored in _IGNORED_MESSAGES)

# Keep the handler alive: Qt holds a Python callback for native Qt messages.
_qt_message_handler = None
_qt_previous_handler = None

def _install_qt_silencing():
    """Filter known Qt/pywebview startup noise, preserving other Qt messages.

    This only applies when the installed Qt binding matches pywebview's backend.
    """
    global _qt_message_handler, _qt_previous_handler
    if _qt_message_handler is not None:
        return
    try:
        from PySide6.QtCore import qInstallMessageHandler
    except ImportError:
        try:
            from PyQt6.QtCore import qInstallMessageHandler
        except ImportError:
            try:
                from PyQt5.QtCore import qInstallMessageHandler
            except ImportError:
                return

    def handler(mode, context, message):
        if any(ignored in message for ignored in _IGNORED_MESSAGES):
            return
        if _qt_previous_handler is not None:
            _qt_previous_handler(mode, context, message)
        else:
            print(message, file=sys.stderr)

    _qt_message_handler = handler
    _qt_previous_handler = qInstallMessageHandler(handler)

class App:
    def __init__(self, page, silent=False, name=None, *, callbacks=None,
                 width=1000, height=700, serve_local=False, **window_options):
        self.silent = silent
        self.name = name or f"{getattr(page, 'name', str(page))} - Sulfur"
        self.window = None
        self._temporary = None
        self._page = page if callable(getattr(page, 'build', None)) else None
        self._callbacks = dict(callbacks or {})
        logger = logging.getLogger('pywebview')
        if not any(isinstance(f, _SulfurLogFilter) for f in logger.filters):
            logger.addFilter(_SulfurLogFilter())
        try:
            if self._page is not None:
                self._temporary = tempfile.TemporaryDirectory(prefix='sulfur-')
                target = self._page.build(to=Path(self._temporary.name) / 'index.html')
                if target is None:
                    raise ValueError('Page.build() did not produce an HTML file')
                target_path = Path(str(target)).resolve()
                target = str(target_path) if serve_local else target_path.as_uri()
            elif isinstance(page, str) and '://' in page:
                target = page
            else:
                target_path = Path(str(page)).expanduser().resolve()
                if not target_path.is_file():
                    raise FileNotFoundError(f'HTML file does not exist: {target_path}')
                target = str(target_path) if serve_local else target_path.as_uri()
            self.window = webview.create_window(
                self.name, target, width=width, height=height, **window_options
            )
            self.runtime = PageRuntime(self.window, self._registered_callbacks)
            self.window.events.closed += self._cleanup
            if self._page is not None:
                attach = getattr(self._page, 'attach_runtime', None)
                if not callable(attach):
                    attach = getattr(self._page, '_attach_window', None)
                if callable(attach):
                    attach(self.runtime)
        except Exception:
            self._cleanup()
            raise
        if not self.silent and '--silent' not in sys.argv:
            print(f'{Color.yellow}sulfur: {Color.reset}Initialized new app for page:',
                  getattr(page, 'name', str(page)))

    def _registered_callbacks(self):
        # Older Fluorine pages keep their registry private. Explicit exposure
        # also supports their underscore-prefixed callback names.
        registered = dict(getattr(self._page, 'callbacks',
                                  getattr(self._page, '_python_handlers', {})))
        for name, callback in self._callbacks.items():
            if name in registered and registered[name] is not callback:
                raise ValueError(f'Duplicate callback name: {name!r}')
            registered[name] = callback
        return registered

    def run(self, script):
        """Evaluate JavaScript, or queue it until the document is ready."""
        return self.runtime.evaluate_js(str(script))

    def _cleanup(self):
        if self._page is not None:
            detach = getattr(self._page, 'detach_runtime', None)
            if callable(detach):
                detach()
            elif getattr(self._page, '_window', None) is getattr(self, 'runtime', None):
                self._page._window = None
        if self._temporary is not None:
            self._temporary.cleanup()
            self._temporary = None

    def close(self):
        """Request that the window close; temporary HTML is removed on exit."""
        if self.window is not None:
            self.window.destroy()

    def open(self, dev=False, *, gui=None):
        quiet = self.silent or '--silent' in sys.argv
        if not quiet:
            print(f'{Color.yellow}sulfur: {Color.reset}Launching app...')
        if not dev:
            _install_qt_silencing()
        backend = gui if gui is not None else ('qt' if sys.platform.startswith('linux') else None)
        try:
            webview.start(gui=backend, debug=dev)
        finally:
            self._cleanup()
        if not quiet:
            print(f'{Color.yellow}sulfur: {Color.reset}App session terminated.')


def _dialog(method, title, message):
    # Import Tk only when a desktop dialog is actually requested.
    import tkinter.messagebox as msgbox
    return getattr(msgbox, method)(title, message)


def info(message: str) -> None:
    _dialog("showinfo", "Info", message)
    
def warning(message: str) -> None:
    _dialog("showwarning", "Warning", message)
    
def error(message: str) -> None:
    _dialog("showerror", "Error", message)

def yesno(message: str) -> bool:
    return _dialog("askyesno", "Confirm", message)

def okcancel(message: str) -> bool:
    return _dialog("askokcancel", "Confirm", message)

def retrycancel(message: str) -> bool:
    return _dialog("askretrycancel", "Confirm", message)

def yesnocancel(message: str) -> bool:
    return _dialog("askyesnocancel", "Confirm", message)
