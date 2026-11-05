# Reader

A Mac app that reads your EPUB books aloud with a natural open-source voice ([Kokoro](https://huggingface.co/hexgrad/Kokoro-82M)). As it reads, it highlights the current line and word. Everything runs on your Mac: no account, no cloud, and your books never leave your computer.

- **Library**: add EPUBs and see covers and reading progress. It reopens where you left off.
- **Read-aloud**: 11 US and UK voices, with speed from 0.5× to 3× that changes instantly without altering pitch.
- **Follow along**: the line and word being spoken are highlighted. Scroll mode keeps the line centred, and Pages mode turns pages for you.
- **Scroll or Pages**: continuous scrolling, or a two-page spread you turn with ← →, a trackpad swipe or the edge buttons.
- **Highlights & notes**: select text to highlight it in 5 colours, add a note, copy it, or start reading from there.
- **Contents sidebar**: the book's table of contents plus all your notes.
- **Themes**: Original, Quiet, Paper, Bold, Calm (default) and Focus, plus optional automatic dark mode.

Works with DRM-free EPUBs (e.g. [Standard Ebooks](https://standardebooks.org), [Project Gutenberg](https://www.gutenberg.org)). Books bought in Apple Books are DRM-protected and won't open.

## Install (macOS, Apple Silicon recommended)

```sh
git clone https://github.com/<you>/epub-reader.git
cd epub-reader
./setup.sh
```

Then open **Reader** from Spotlight or `~/Applications`. The first launch downloads the voice model (about 330 MB).

Prefer a browser? Run `./start.command --browser`.

## Keyboard shortcuts

| Key | Action |
|---|---|
| Space | Play / pause |
| `]` / `[` | Faster / slower |
| ← / → | Previous / next paragraph (Scroll) or page (Pages) |
| ⌥-click a word | Read from that word |
| Esc | Close menus |

## How it works

- `server.py`: a small local web server with one text-to-speech endpoint. It runs Kokoro on the Apple GPU (MPS) when available and returns WAV audio plus the time each word starts, which drives the word highlight. It also stores your library in `library/` (books, covers, and one JSON file per book with your progress and notes). By default it opens in a native window (pywebview); with `--browser` it opens in your browser instead.
- `index.html`: the whole app in one file, with no build step. JSZip unpacks the EPUB in the browser. Speech is generated a sentence at a time, and the next sentence is prepared while the current one plays.

## License

MIT. The Kokoro model is Apache 2.0.
