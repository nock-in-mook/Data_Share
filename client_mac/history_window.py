# 履歴ウィンドウ（HTMLベース） — macOS版
# JSONを読んでHTMLを生成し、ブラウザで表示
# tkinterはmacOS付属Python 3.9のTk 8.5.9でクラッシュするため不使用
import os
import json
import subprocess
import tempfile
import html as html_mod
import sys
import time
import signal
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse, quote

# ローカルサーバーのポート
SERVER_PORT = 19876


def _build_html(items, port):
    """履歴HTMLを生成"""
    rows_html = ""
    if not items:
        rows_html = '<div class="empty">まだ受信なし</div>'
    else:
        for i, item in enumerate(reversed(items)):
            item_type = item.get("item_type", "text")
            time_str = html_mod.escape(item.get("time_str", ""))
            preview = html_mod.escape(item.get("preview", "").replace("\n", " ")[:120])
            content = item.get("content", "")
            file_path = item.get("file_path", "")
            alt = "alt" if i % 2 == 1 else ""

            if item_type == "text":
                name = preview or "テキスト"
                icon = "📋"
                color = "#e0e0e0"
            elif item_type == "image":
                name = html_mod.escape(os.path.basename(file_path)) if file_path else "画像"
                if len(name) > 25:
                    name = name[:22] + "..."
                icon = "🖼"
                color = "#8ecae6"
            else:
                name = html_mod.escape(os.path.basename(file_path)) if file_path else "ファイル"
                if len(name) > 25:
                    name = name[:22] + "..."
                icon = "📎"
                color = "#c4a35a"

            # 行クリック時のアクション
            if item_type == "text":
                escaped = html_mod.escape(content).replace("'", "\\'").replace("\n", "\\n")
                onclick = f"copyText('{escaped}')"
            elif item_type == "image" and file_path:
                escaped_path = html_mod.escape(file_path).replace("'", "\\'")
                onclick = f"openFile('{escaped_path}')"
            elif item_type == "file" and file_path:
                escaped_path = html_mod.escape(file_path).replace("'", "\\'")
                onclick = f"openFolder('{escaped_path}')"
            else:
                onclick = ""

            # ボタン
            buttons = ""
            if item_type == "text":
                escaped = html_mod.escape(content).replace("'", "\\'").replace("\n", "\\n")
                buttons += f'<button class="btn copy" onclick="event.stopPropagation();copyText(\'{escaped}\')">📋</button>'
            if file_path:
                escaped_path = html_mod.escape(file_path).replace("'", "\\'")
                buttons += f'<button class="btn folder" onclick="event.stopPropagation();openFolder(\'{escaped_path}\')">📁</button>'

            rows_html += f'''<div class="row {alt}" onclick="{onclick}" style="cursor:pointer">
  <span class="time">{time_str}</span>
  <span class="sep"></span>
  <span class="label" style="color:{color}">{icon} {name}</span>
  <span class="buttons">{buttons}</span>
</div>
'''

    count = len(items)
    return f'''<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>即シェア君 履歴</title>
<style>
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  body {{ background:#1a1a2e; color:#e0e0e0; font-family:"Helvetica Neue",sans-serif; font-size:14px; padding:10px; }}
  .header {{ color:#7cb3ff; font-weight:bold; font-size:15px; padding:8px 4px; }}
  .row {{ display:flex; align-items:center; padding:4px 8px; height:32px; background:#252540; border-radius:4px; margin-bottom:1px; }}
  .row:hover {{ background:#303060; }}
  .row.alt {{ background:#2a2a4a; }}
  .row.alt:hover {{ background:#303060; }}
  .time {{ font-family:Menlo,monospace; font-size:12px; color:#888; min-width:55px; }}
  .sep {{ width:1px; height:18px; background:#3a3a5a; margin:0 8px; }}
  .label {{ flex:1; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }}
  .buttons {{ display:flex; gap:4px; }}
  .btn {{ border:none; border-radius:4px; padding:2px 8px; cursor:pointer; font-size:13px; }}
  .btn.copy {{ background:#3a7bd5; color:#fff; }}
  .btn.folder {{ background:#444; color:#fff; }}
  .btn:hover {{ opacity:0.8; }}
  .empty {{ color:#666; text-align:center; padding:30px; }}
  .toast {{ position:fixed; top:50%; left:50%; transform:translate(-50%,-50%); background:#3a7bd5; color:#fff; padding:8px 20px; border-radius:8px; font-weight:bold; display:none; z-index:99; }}
</style>
</head>
<body>
<div class="header">履歴 ({count}件)</div>
{rows_html}
<div class="toast" id="toast">コピーしました！</div>
<script>
var BASE = "http://127.0.0.1:{port}";
var refreshTimer = null;

function copyText(t) {{
  t = t.replace(/\\\\n/g, "\\n");
  navigator.clipboard.writeText(t).then(showToast.bind(null, "コピーしました！"));
}}
function openFile(p) {{
  fetch(BASE + "/action?cmd=open&path=" + encodeURIComponent(p));
}}
function openFolder(p) {{
  event.stopPropagation();
  fetch(BASE + "/action?cmd=reveal&path=" + encodeURIComponent(p));
}}
function showToast(msg) {{
  var el = document.getElementById("toast");
  el.textContent = msg;
  el.style.display = "block";
  setTimeout(function(){{ el.style.display = "none"; }}, 800);
}}

// 3秒ごとに履歴を再読み込み
function autoRefresh() {{
  fetch(BASE + "/history").then(r => r.text()).then(html => {{
    document.body.innerHTML = html;
    refreshTimer = setTimeout(autoRefresh, 3000);
  }}).catch(() => {{
    refreshTimer = setTimeout(autoRefresh, 3000);
  }});
}}
refreshTimer = setTimeout(autoRefresh, 3000);
</script>
</body>
</html>'''


def _body_only(items, port):
    """bodyの中身だけ返す（自動更新用）"""
    full = _build_html(items, port)
    # <body>と</body>の間を抽出
    start = full.find("<body>") + len("<body>")
    end = full.find("</body>")
    return full[start:end]


class HistoryHandler(BaseHTTPRequestHandler):
    """履歴表示用ローカルHTTPサーバー"""
    json_path = ""

    def log_message(self, format, *args):
        pass  # ログ抑制

    def do_GET(self):
        parsed = urlparse(self.path)

        if parsed.path == "/" or parsed.path == "":
            items = self._load_items()
            html = _build_html(items, SERVER_PORT)
            self._respond(200, "text/html", html.encode("utf-8"))

        elif parsed.path == "/history":
            items = self._load_items()
            body = _body_only(items, SERVER_PORT)
            self._respond(200, "text/html", body.encode("utf-8"))

        elif parsed.path == "/action":
            params = parse_qs(parsed.query)
            cmd = params.get("cmd", [""])[0]
            path = params.get("path", [""])[0]
            if cmd == "open" and path:
                subprocess.Popen(["open", path])
            elif cmd == "reveal" and path:
                subprocess.Popen(["open", "-R", path])
            self._respond(200, "text/plain", b"ok")

        else:
            self._respond(404, "text/plain", b"not found")

    def _load_items(self):
        try:
            with open(self.json_path, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []

    def _respond(self, code, content_type, body):
        self.send_response(code)
        self.send_header("Content-Type", f"{content_type}; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def show_history_server(json_path):
    """ローカルサーバーを起動してブラウザで開く"""
    HistoryHandler.json_path = json_path

    # 既存サーバーがあればブラウザで開くだけ
    import socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.settimeout(0.5)
        sock.connect(("127.0.0.1", SERVER_PORT))
        sock.close()
        # 既に起動してる → ブラウザで開くだけ
        subprocess.Popen(["open", f"http://127.0.0.1:{SERVER_PORT}"])
        return
    except (ConnectionRefusedError, OSError):
        pass
    finally:
        sock.close()

    # サーバー起動
    server = HTTPServer(("127.0.0.1", SERVER_PORT), HistoryHandler)
    signal.signal(signal.SIGTERM, lambda *a: sys.exit(0))

    # ブラウザで開く
    subprocess.Popen(["open", f"http://127.0.0.1:{SERVER_PORT}"])

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: history_window.py <history.json>")
        sys.exit(1)
    show_history_server(sys.argv[1])
