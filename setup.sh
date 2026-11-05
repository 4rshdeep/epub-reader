#!/bin/sh
# One-time setup on macOS: installs dependencies and builds ~/Applications/Reader.app
set -e
cd "$(dirname "$0")"
DIR="$(pwd)"

command -v brew >/dev/null || { echo "Install Homebrew first: https://brew.sh"; exit 1; }
command -v uv >/dev/null || brew install uv
command -v espeak-ng >/dev/null || brew install espeak-ng   # pronunciation fallback for unusual words

uv venv -q -p 3.12 .venv            # kokoro needs Python < 3.13
uv pip install -q -p .venv -r requirements.txt

APP="$HOME/Applications/Reader.app"
mkdir -p "$APP/Contents/MacOS"
printf '#!/bin/sh\nexec "%s/.venv/bin/python" "%s/server.py"\n' "$DIR" "$DIR" > "$APP/Contents/MacOS/Reader"
chmod +x "$APP/Contents/MacOS/Reader"
cat > "$APP/Contents/Info.plist" <<'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>CFBundleName</key><string>Reader</string>
  <key>CFBundleDisplayName</key><string>Reader</string>
  <key>CFBundleIdentifier</key><string>local.epub-reader</string>
  <key>CFBundleExecutable</key><string>Reader</string>
  <key>CFBundlePackageType</key><string>APPL</string>
  <key>CFBundleVersion</key><string>1</string>
  <key>NSHighResolutionCapable</key><true/>
</dict></plist>
EOF

echo "Done. Open Reader from Spotlight or ~/Applications. The first launch downloads the voice model (~330 MB)."
