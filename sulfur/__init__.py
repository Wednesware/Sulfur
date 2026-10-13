import tempfile, sys, logging, tkinter.messagebox as msgbox, contextlib, io
from nitrogen import require
Color = require("magnesium.color").Color
FilePath = require("magnesium.filepath").FilePath
try:
    with contextlib.redirect_stderr(io.StringIO()):
        import webview
except ImportError:
    print(f"{Color.yellow}sulfur: {Color.reset}Webview is not installed. Please install it and its dependencies using 'pip install pywebview qtpy PySide6'.")
    exit(1)

class _SulfurLogFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        return False
    
_qt_message_handler = None
_qt_previous_handler = None

def _install_qt_silencing():
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
    def __init__(self, page: "Page | str | FilePath", silent: bool = False, name: str | None = None) -> None: # type: ignore
        self.silent: bool = silent
        self.name: str = name or f"{getattr(page, 'name', str(page))} - Sulfur"
        pywebview_logger = logging.getLogger("pywebview")
        if not any(isinstance(f, _SulfurLogFilter) for f in pywebview_logger.filters):
            pywebview_logger.addFilter(_SulfurLogFilter())

        if hasattr(page, "build"):
            build: FilePath | None = page.build(to=tempfile.NamedTemporaryFile(suffix=".html").name) # type: ignore
            if build is None:
                print(f"{Color.yellow}sulfur: {Color.reset}No build was generated.")
                return
            self.window: webview.Window = webview.create_window(
                self.name,
                str(build),
                width=1000,
                height=700,
                js_api=page,
            )
            if hasattr(page, "_attach_window"):
                page._attach_window(self.window)
            if not self.silent and "--silent" not in sys.argv:
                print(f"{Color.yellow}sulfur: {Color.reset}Initialized new app for page:", page.name)
        elif isinstance(page, str) and "://" in page:
            self.window: webview.Window = webview.create_window(
                self.name,
                page,
                width=1000,
                height=700,
            )
            if not self.silent and "--silent" not in sys.argv:
                print(f"{Color.yellow}sulfur: {Color.reset}Initialized new app for page:", page)
        else:
            path: FilePath = FilePath(page) # type: ignore
            self.window: webview.Window = webview.create_window(
                self.name,
                str(path),
                width=1000,
                height=700,
            )
            if not self.silent and "--silent" not in sys.argv:
                print(f"{Color.yellow}sulfur: {Color.reset}Initialized new app for page:", path.name)

    def open(self, dev: bool = False) -> None:
        if self.window is None:
            return
        if not self.silent and "--silent" not in sys.argv:
            print(f"{Color.yellow}sulfur: {Color.reset}Launching app...")
        if not dev:
            _install_qt_silencing()
        webview.start(debug=dev)
        if not self.silent and "--silent" not in sys.argv:
            print(f"{Color.yellow}sulfur: {Color.reset}App session terminated.")

def info(message: str) -> None:
    msgbox.showinfo("Info", message)
    
def warning(message: str) -> None:
    msgbox.showwarning("Warning", message)
    
def error(message: str) -> None:
    msgbox.showerror("Error", message)

def yesno(message: str) -> bool:
    return msgbox.askyesno("Confirm", message)

def okcancel(message: str) -> bool:
    return msgbox.askokcancel("Confirm", message)

def retrycancel(message: str) -> bool:
    return msgbox.askretrycancel("Confirm", message)

def yesnocancel(message: str) -> bool | None:
    return msgbox.askyesnocancel("Confirm", message)