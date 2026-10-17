# Changelog

## 26.9

- Add `App(html_path, callbacks=...)` and automatic callback registration for
  Fluorine pages, exposing only the registered functions through pywebview.
- Support callable objects, partials, aliases, arguments, dynamically added
  callbacks, and legacy Fluorine underscore-prefixed callbacks.
- Buffer `App.run()` and page DOM updates until the document is loaded, and
  reconnect the bridge after reloads.
- Add configurable window options, an explicit GUI backend option, and `close()`.
- Keep generated temporary HTML for the lifetime of the window, then remove it
  and detach the page, including when startup fails.
- Preserve JavaScript errors in logs; import Tkinter only for dialog calls.
- Raise useful exceptions for missing HTML, failed builds, or missing pywebview
  instead of terminating the importing process.
- Add regression tests, a real Qt webview integration test, and clean
  Nitrogen-compatible release archives without Python bytecode caches.

Fluorine 26.7 is recommended. Older Fluorine pages remain supported. Applications
that relied on arbitrary page methods being exposed implicitly must supply those
functions through `callbacks` instead.
