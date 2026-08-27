try:
    import webview
except ImportError:
    print("sulfur.bue: Webview is not installed. Please install it using 'pip install pywebview'.")
    exit(1)

import tempfile, asyncio, sys
from ww.mg26_12.filepath import FilePath

class Bue:
    def __init__(self, page: "Page | str | FilePath") -> None: # type: ignore
        if hasattr(page, "build"):
            self.window: webview.Window = webview.create_window(
                f"{page.name} - Bue",
                str(page.build(to=tempfile.NamedTemporaryFile(suffix=".html").name)),
                width=1000,
                height=700,
            )
            if "--buesilent" not in sys.argv:
                print("sulfur.bue: Initialized new Bue window for page:", page.name)
        else:
            path: FilePath = FilePath(page)
            self.window: webview.Window = webview.create_window(
                f"{path.name} - Bue",
                str(path),
                width=1000,
                height=700,
            )
            if "--buesilent" not in sys.argv:
                print("sulfur.bue: Initialized new Bue window for page:", path.name)
    def open(self, dev: bool = False) -> None:
        print("sulfur.bue: Launching Bue...")
        webview.start(debug=dev)
        print("sulfur.bue: Bue session terminated.")
        