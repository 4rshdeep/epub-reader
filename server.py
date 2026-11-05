"""Serves the reader + a Kokoro TTS endpoint. Run: .venv/bin/python server.py"""
import base64, io, json, os, re, threading, webbrowser
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

os.environ.setdefault('PYTORCH_ENABLE_MPS_FALLBACK', '1')
import numpy as np, soundfile as sf, torch
from kokoro import KModel, KPipeline

ROOT = Path(__file__).parent
LIB = ROOT / 'library'  # <id>.epub, <id>.json (progress + highlights), <id>.<img> (cover)
LIB.mkdir(exist_ok=True)
NAME = re.compile(r'^[0-9a-f]{24}\.(epub|json|jpg|png|gif|webp)$')  # whitelist: no path traversal, no html/svg
PORT = 8777
REPO = 'hexgrad/Kokoro-82M'
model = KModel(repo_id=REPO).to('mps' if torch.backends.mps.is_available() else 'cpu').eval()  # M-series GPU ~1.4x CPU
pipes = {lang: KPipeline(lang_code=lang, repo_id=REPO, model=model) for lang in 'ab'}  # a = US voices, b = UK voices
lock = threading.Lock()  # ponytail: one generation at a time; prefetch queues behind the current paragraph


def tts(text, voice):
    """-> (wav bytes, [[word_index, start_sec], ...]) where word_index counts space-separated words of text."""
    chunks, words, offset, pos, word = [], [], 0.0, 0, 0
    with lock:
        results = list(pipes[voice[0]](text, voice=voice))
    for r in results:
        for tk in r.tokens or []:
            i = text.find(tk.text, pos)
            if i < 0 or tk.start_ts is None:
                continue  # ponytail: token not found verbatim (rare normalization) -> highlight just waits for the next word
            word += text.count(' ', pos, i)
            pos = i + len(tk.text)
            if not words or words[-1][0] != word:
                words.append([word, round(offset + tk.start_ts, 3)])
        chunks.append(r.audio.numpy())
        offset += len(chunks[-1]) / 24000
    buf = io.BytesIO()
    sf.write(buf, np.concatenate(chunks) if chunks else np.zeros(1, 'float32'), 24000, format='WAV', subtype='PCM_16')
    return buf.getvalue(), words


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *a, **k):
        super().__init__(*a, directory=str(ROOT), **k)

    def send_json(self, obj):
        body = json.dumps(obj).encode()
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == '/api/books':
            books = []
            for f in LIB.glob('*.json'):
                try:
                    books.append(json.loads(f.read_text()))
                except ValueError:
                    pass
            return self.send_json(books)
        super().do_GET()

    def do_PUT(self):  # PUT /library/<id>.<ext>
        name = self.path.removeprefix('/library/')
        if not NAME.match(name):
            return self.send_error(400, 'bad file name')
        tmp = LIB / (name + '.tmp')
        tmp.write_bytes(self.rfile.read(int(self.headers['Content-Length'])))
        tmp.replace(LIB / name)  # atomic: a crash mid-write never corrupts saved progress/notes
        self.send_response(204)
        self.end_headers()

    def do_DELETE(self):  # DELETE /library/<id> removes the book, its cover and its notes
        m = re.fullmatch(r'/library/([0-9a-f]{24})', self.path)
        if not m:
            return self.send_error(400)
        for f in LIB.glob(m[1] + '.*'):
            f.unlink()
        self.send_response(204)
        self.end_headers()

    def do_POST(self):
        if self.path != '/tts':
            return self.send_error(404)
        req = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
        try:
            wav, words = tts(req['text'], req.get('voice', 'af_heart'))
        except Exception as e:
            return self.send_error(500, str(e))
        self.send_json({'audio': base64.b64encode(wav).decode(), 'words': words})

    def log_message(self, *a):
        pass


if __name__ == '__main__':
    import sys
    for port in range(PORT, PORT + 10):  # skip ports other apps already use
        try:
            server = ThreadingHTTPServer(('127.0.0.1', port), Handler)
            break
        except OSError:
            continue
    url = f'http://localhost:{port}/'
    print('Reader at', url)
    if '--browser' in sys.argv:
        webbrowser.open(url)
        server.serve_forever()
    else:  # standalone window (macOS WebKit); closing it quits the app
        import webview
        threading.Thread(target=server.serve_forever, daemon=True).start()
        # text_select: pywebview disables text selection by default, which kills highlighting/notes
        webview.create_window('Reader', url, width=1440, height=920, min_size=(720, 560), background_color='#EFE4D1', text_select=True)
        webview.start(private_mode=False, storage_path=str(ROOT / '.webview'))  # keep prefs (voice, speed, layout)
