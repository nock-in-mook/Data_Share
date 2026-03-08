#!/bin/bash
# 即シェア君 Mac版 インストールスクリプト

set -e

echo "========================================="
echo "  即シェア君 Mac版 セットアップ"
echo "========================================="
echo ""

# Homebrew Python 3.12 を使う
PYTHON="/opt/homebrew/bin/python3.12"
if ! command -v "$PYTHON" &> /dev/null; then
    echo "Python 3.12が見つかりません。以下を実行してください:"
    echo "  brew install python@3.12 python-tk@3.12"
    exit 1
fi
PYVER=$("$PYTHON" --version 2>&1)
echo "OK $PYVER"

# スクリプトのあるディレクトリに移動
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# venv作成
if [ ! -d venv ]; then
    echo "仮想環境を作成中..."
    "$PYTHON" -m venv venv
fi
echo "OK venv"

# 依存パッケージインストール
echo "パッケージをインストール中..."
./venv/bin/pip install -q -r requirements.txt

# 保存先フォルダ作成
APPS_ROOT="/Users/nock_re/Library/CloudStorage/GoogleDrive-yagukyou@gmail.com/マイドライブ/_Apps2026"
if [ -f config.json ]; then
    APPS_ROOT=$("$PYTHON" -c "
import json, os
with open('config.json', encoding='utf-8') as f:
    c = json.load(f)
print(os.path.expanduser(c.get('apps_root', '/Users/nock_re/Library/CloudStorage/GoogleDrive-yagukyou@gmail.com/マイドライブ/_Apps2026')))
")
fi
mkdir -p "$APPS_ROOT/text"
mkdir -p "$APPS_ROOT/images"
echo "OK 保存先: $APPS_ROOT"

# 起動スクリプト作成
cat > "$SCRIPT_DIR/start.command" << 'STARTEOF'
#!/bin/bash
cd "$(dirname "$0")"
./venv/bin/python data_share_client.py
STARTEOF
chmod +x "$SCRIPT_DIR/start.command"
echo "OK start.command"

# ログイン時自動起動（LaunchAgent）
PLIST_NAME="com.rapidshare.sokushare"
PLIST_PATH="$HOME/Library/LaunchAgents/${PLIST_NAME}.plist"

cat > "$PLIST_PATH" << PLISTEOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>${PLIST_NAME}</string>
    <key>ProgramArguments</key>
    <array>
        <string>${SCRIPT_DIR}/venv/bin/python</string>
        <string>${SCRIPT_DIR}/data_share_client.py</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <false/>
    <key>StandardOutPath</key>
    <string>${SCRIPT_DIR}/sokushare.log</string>
    <key>StandardErrorPath</key>
    <string>${SCRIPT_DIR}/sokushare_error.log</string>
</dict>
</plist>
PLISTEOF

launchctl unload "$PLIST_PATH" 2>/dev/null || true
launchctl load "$PLIST_PATH"
echo "OK ログイン時自動起動を設定"

echo ""
echo "========================================="
echo "  セットアップ完了！"
echo "========================================="
echo ""
echo "  メニューバーに青い丸アイコンが出れば成功！"
echo "  次回からはMac起動時に自動で立ち上がります。"
echo ""
