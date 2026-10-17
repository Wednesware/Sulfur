"""Host an existing HTML file with an explicit Python callback mapping."""
from pathlib import Path
import tempfile

from sulfur import App

with tempfile.TemporaryDirectory() as directory:
    path = Path(directory) / 'index.html'
    path.write_text('''<!doctype html><html><body>
      <button id="greet" disabled>Greet</button><p id="status">Loading…</p>
      <script>
        window.addEventListener('pywebviewready', () => {
          const button = document.getElementById('greet');
          button.disabled = false;
          document.getElementById('status').textContent = 'Ready';
          button.onclick = async () => {
            try {
              document.getElementById('status').textContent =
                await window.pywebview.api.greet('traveller');
            } catch (error) { console.error(error); }
          };
        });
      </script></body></html>''', encoding='utf-8')
    App(path, callbacks={'greet': lambda name: f'Hello, {name}!'},
        name='HTML callbacks', width=480, height=320).open()
