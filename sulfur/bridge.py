"""Explicit callback exposure and page-readiness buffering for pywebview."""
import re
import logging
from threading import RLock


class PageRuntime:
    def __init__(self, window, callbacks=None):
        self.window = window
        self._callbacks = callbacks or (lambda: {})
        self._exposed = {}
        self._pending = []
        self._ready = False
        self._lock = RLock()
        self.sync_callbacks()
        window.events.before_load += self.before_load
        window.events.loaded += self.loaded

    def sync_callbacks(self):
        callbacks = dict(self._callbacks())
        for name, handler in callbacks.items():
            if not isinstance(name, str) or not re.fullmatch(r'[A-Za-z_$][A-Za-z0-9_$]*', name):
                raise ValueError(f'Invalid JavaScript callback name: {name!r}')
            if not callable(handler):
                raise TypeError(f'Callback {name!r} must be callable')
        with self._lock:
            for name, handler in callbacks.items():
                if self._exposed.get(name) is handler:
                    continue
                # Separate wrappers preserve aliases and never mutate user functions.
                def wrap(callback, callback_name):
                    def invoke(*args, **kwargs):
                        return callback(*args, **kwargs)
                    invoke.__name__ = callback_name
                    return invoke
                self.window.expose(wrap(handler, name))
                self._exposed[name] = handler

    def before_load(self):
        with self._lock:
            self._ready = False

    def loaded(self):
        self.sync_callbacks()
        self.window.evaluate_js(
            'if (window.fluorine) window.fluorine.connect(window.pywebview.api);'
        )
        # Preserve FIFO ordering with concurrent Python updates during startup.
        while True:
            with self._lock:
                pending, self._pending = self._pending, []
                if not pending:
                    self._ready = True
                    return
            for script in pending:
                try:
                    self.window.evaluate_js(script)
                except Exception:
                    # One malformed user script must not strand later updates.
                    logging.getLogger('sulfur').exception('Queued JavaScript failed')

    def evaluate_js(self, script):
        self.sync_callbacks()
        with self._lock:
            if not self._ready:
                self._pending.append(script)
                return None
        return self.window.evaluate_js(script)
