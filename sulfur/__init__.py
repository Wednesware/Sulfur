import tempfile, sys, logging, tkinter.messagebox as msgbox
try:
    from nitrogen import require
except ImportError as e:
    print(f"sulfur: Nitrogen is not installed. Please install it using 'pip install wwn'.")
    exit(1)
Color = require("magnesium.color").Color
FilePath = require("magnesium.filepath").FilePath
try:
    import webview
except ImportError:
    print(f"{Color.yellow}sulfur: {Color.reset}Webview is not installed. Please install it and its dependencies using 'pip install pywebview PySide6 qtpy'.")
    exit(1)

_IGNORED_MESSAGES = (
    "Error while processing script: unsupported callable",
    "Cannot read properties of null (reading 'appendChild')",
    "Cannot read properties of undefined (reading '_createApi')",
    "QWebChannel is not defined",
    "Registered new object after initialization, existing clients won't be notified!",
    "QtWaylandClient::QWaylandTextInputv3::disableSurface",
)

class _SulfurLogFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        message = record.getMessage()
        return not (message.startswith("js:") or any(ignored in message for ignored in _IGNORED_MESSAGES))

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
        if message.startswith("js:") or any(ignored in message for ignored in _IGNORED_MESSAGES):
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
        quiet = self.silent or "--silent" in sys.argv
        if not quiet:
            print(f"{Color.yellow}sulfur: {Color.reset}Launching app...")
        # Filter only known Qt/pywebview noise; never redirect process stdout/stderr.
        if not dev:
            _install_qt_silencing()
        # On Linux, prefer Qt to avoid GTK probing when Qt is installed.
        # Windows and macOS use pywebview's native default backend.
        gui = "qt" if sys.platform.startswith("linux") else None
        webview.start(gui=gui, debug=dev)
        if not quiet:
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

def yesnocancel(message: str) -> bool:
    return msgbox.askyesnocancel("Confirm", message)