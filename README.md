> ### Note
> This Document2.0 formatted README.md file was provided by dannywoof, the maintainer of this library. If you have any questions or feedback, feel free to reach out via [bluesky](https://bsky.app/profile/danny.wednesware.org) or [email](mailto:danny@wednesware.org).

[![Wednesware](wednesware.png)](https://wednesware.org)

# Sulfur

Library for desktop app development.

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

### `sulfur:App(page: Page | str | FilePath, silent: bool = False)`

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
