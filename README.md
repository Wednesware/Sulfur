> ### Note
> This Document2.0 formatted README.md file was provided by dannywoof, the maintainer of this library. If you have any questions or feedback, feel free to reach out via [bluesky](https://bsky.app/profile/danny.wednesware.org) or [email](mailto:danny@wednesware.org).

[![Wednesware](wednesware.png)](https://wednesware.org)

# Sulfur

Run an HTML file in a desktop application window, with optional Python callbacks. Version 26.9.

## Installation

> `n2 get sulfur`

If you don't have Nitrogen: `pipx install wwn` first.

## Quick start

### Basic app window

```python
from ww.f import Page
from ww.f.structuring import h1, p
from ww.s import App

page = Page("demo")
page.body(
    h1 ("Hello from Sulfur"),
    p ("This page is running in a native desktop window.")
)

App(page).open()
```

### Open a page from a file

```python
from ww.s import App

App("index.html").open()
```

### Open an external URL

```python
from ww.s import App

App("https://example.com").open()
```

## Dependencies

- Python 3.12+
- Nitrogen 26.58+ (`pip install wwn`)
- Webview (`pip install pywebview`)
- PySide6 (`pip install PySide6`)
- qtpy (`pip install qtpy`)

# Definitions

## `sulfur`

From the base library, you can import the app launcher and desktop dialog helpers.

> `from ww.s import App, info, warning, error, yesno, okcancel, retrycancel, yesnocancel`

### `sulfur:App(page, silent=False, name=None, *, callbacks=None, width=1000, height=700, serve_local=False, **window_options)`

The `App` class creates a desktop application window for a Fluorine page, a file path, or a URL. It uses pywebview under the hood and registers the page’s Python API handlers when the page object supports them.

> `app = App(page, silent=False)`

#### `sulfur:App.open(dev: bool = False)`

Starts the app window and blocks until the application exits. `dev=True` enables developer mode with debugging features.

> `app.open(dev=True)`

### `sulfur:info(message: str)`

Displays an informational message box using Tkinter.

> `info("Operation complete.")`

### `sulfur:warning(message: str)`

Displays a warning dialog.

> `warning("The file may be outdated.")`

### `sulfur:error(message: str)`

Displays an error dialog.

> `error("Something went wrong.")`

### `sulfur:yesno(message: str)`

Displays a yes/no confirmation dialog and returns a boolean result.

> `confirmed = yesno("Do you want to continue?")`

### `sulfur:okcancel(message: str)`

Displays an OK/Cancel dialog and returns a boolean result.

> `ok = okcancel("Would you like to proceed?")`

### `sulfur:retrycancel(message: str)`

Displays a Retry/Cancel dialog and returns a boolean result.

> `should_retry = retrycancel("The operation failed.")`

### `sulfur:yesnocancel(message: str)`

Displays a Yes/No/Cancel dialog and returns a boolean result.

> `choice = yesnocancel("Save your changes?")`

## Example app

```python
from ww.f import Page
from ww.f.structuring import h1, p, button
from ww.f.scripting import document, event
from ww.s import App

page = Page("demo")


def on_click():
    document.getElementById("status").innerHTML = "Button clicked!"

page.body(
    h1 ("Hello from Sulfur"),
    p ("Waiting for input", id="status"),
    button ("Click me!") @event(onclick=on_click),
)

App(page).open()
```

This is the typical Sulfur flow: build a Fluorine page, then wrap it in `App(page)` and open it as a desktop application.

## Notes

- Sulfur depends on pywebview to create the desktop window.
- If a Fluorine `Page` instance is supplied, Sulfur will build a temporary HTML file automatically.
- If a local file path or remote URL is supplied directly, Sulfur opens it as-is.
- The dialog helpers are simple wrapper functions around Tkinter message boxes for quick confirmation and notification flows.



## Explicit Python callbacks (26.9)

Sulfur opens HTML; it does not require Fluorine. Pass a mapping of JavaScript API
names to Python functions when hosting an existing file:

```python
from sulfur import App

app = App('index.html', callbacks={'greet': lambda name: f'Hello, {name}!'},
          name='My application', width=640, height=480, resizable=False)
app.open()
```

In the HTML, wait for the bridge before using the API:

```javascript
window.addEventListener('pywebviewready', async () => {
  const greeting = await window.pywebview.api.greet('traveller');
  document.getElementById('status').textContent = greeting;
});
```

See [examples/html_callbacks.py](examples/html_callbacks.py) for a complete example.
Only registered callbacks are exposed; unrelated page methods are not exposed.
Aliases, partials, callable objects, and arguments are supported. Do not attach
privileged callbacks to untrusted HTML or URLs: the loaded document can invoke them.

### With Fluorine 26.7

`App(page)` builds the HTML, reads `page.callbacks`, and attaches a runtime that
buffers DOM updates until the page is loaded. Newly bound callbacks are exposed
before their DOM update, and the bridge reconnects on reload. Legacy Fluorine
registries and callback names remain supported.

You can also build first and host the file:

```python
page.build('index.html')
app = App('index.html', callbacks=page.callbacks)
# Optional: deliver later updates to this same page's element tree.
page.attach_runtime(app.runtime)
app.open()
```

The Python functions must remain available in the launching process. HTML cannot
restore them. When launching a previously generated file in another process, pass
a matching callback mapping explicitly.

### Window lifecycle and JavaScript

- `app.run(script)` queues JavaScript before document readiness and evaluates it
  immediately afterward. A queued call returns `None`; a live call returns the
  pywebview result.
- `app.close()` requests window closure.
- `app.open(dev=True)` enables pywebview debugging. JavaScript errors remain visible
  in normal mode as well.
- `app.open(gui='gtk')` selects a backend; Linux defaults to Qt as before.
- Extra constructor keyword arguments go to `webview.create_window`, such as
  `resizable=False` or `fullscreen=True`.
- Temporary HTML built for a page object is removed after closure or startup
  failure. Explicit input files are never removed.

## Development

```sh
PYTHONPATH=. python3 -m unittest discover -s tests -v
python3 tools/build_release.py
# Real bridge integration with Fluorine checked out alongside this repository:
PYTHONPATH=.:../Fluorine xvfb-run -a python3 tests/desktop_smoke.py
```

The Qt integration test requires `pywebview`, `PySide6`, and `qtpy`, and a desktop
session or Xvfb. Release archives exclude bytecode caches and use Nitrogen's
expected layout. See [CHANGELOG.md](CHANGELOG.md) for compatibility notes.


Local HTML opens through a `file://` URL by default, so a basic desktop application
does not depend on a loopback HTTP server. Relative scripts, styles, and images
resolve alongside the HTML file. If your page needs an HTTP origin (for example,
JavaScript modules or `fetch` subject to file-origin restrictions), pass
`serve_local=True` to use pywebview's local server as in previous versions.
