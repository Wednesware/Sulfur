import tempfile, sys, logging, tkinter.messagebox as msgbox

try:
    import webview
except ImportError:
    print("sulfur: Webview is not installed. Please install it using 'pip install pywebview'.")
    exit(1)

from ww.mg26_12.filepath import FilePath


class _PyWebviewUnsupportedCallableFilter(logging.Filter):
    _ignored_message = "Error while processing script: unsupported callable"

    def filter(self, record: logging.LogRecord) -> bool:
        return self._ignored_message not in record.getMessage()

class App:
    def __init__(self, page: "Page | str | FilePath") -> None: # type: ignore
        pywebview_logger = logging.getLogger("pywebview")
        if not any(isinstance(f, _PyWebviewUnsupportedCallableFilter) for f in pywebview_logger.filters):
            pywebview_logger.addFilter(_PyWebviewUnsupportedCallableFilter())

        if hasattr(page, "build"):
            build: FilePath | None = page.build(to=tempfile.NamedTemporaryFile(suffix=".html").name)
            if build is None:
                print("sulfur: No build was generated.")
                return
            self.window: webview.Window = webview.create_window(
                f"{page.name} - Sulfur",
                str(build),
                width=1000,
                height=700,
                js_api=page,
            )
            if hasattr(page, "_attach_window"):
                page._attach_window(self.window)
            if "--silent" not in sys.argv:
                print("sulfur: Initialized new app for page:", page.name)
        elif isinstance(page, str) and "://" in page:
            self.window: webview.Window = webview.create_window(
                f"{page} - Sulfur",
                page,
                width=1000,
                height=700,
            )
            if "--silent" not in sys.argv:
                print("sulfur: Initialized new app for page:", page)
        else:
            path: FilePath = FilePath(page)
            self.window: webview.Window = webview.create_window(
                f"{path.name} - Sulfur",
                str(path),
                width=1000,
                height=700,
            )
            if "--silent" not in sys.argv:
                print("sulfur: Initialized new app for page:", path.name)

    def open(self, dev: bool = False) -> None:
        if self.window is None:
            return
        print("sulfur: Launching app...")
        webview.start(debug=dev)
        print("sulfur: App session terminated.")

def info(message: str) -> None:
    msgbox.showinfo("Info", message)
    
async def ainfo(message: str) -> None:
    info(message)
    
def warning(message: str) -> None:
    msgbox.showwarning("Warning", message)
    
async def awarning(message: str) -> None:
    warning(message)
    
def error(message: str) -> None:
    msgbox.showerror("Error", message)

async def aerror(message: str) -> None:
    error(message)

def yesno(message: str) -> bool:
    return msgbox.askyesno("Confirm", message)

def okcancel(message: str) -> bool:
    return msgbox.askokcancel("Confirm", message)

def retrycancel(message: str) -> bool:
    return msgbox.askretrycancel("Confirm", message)

def yesnocancel(message: str) -> bool:
    return msgbox.askyesnocancel("Confirm", message)