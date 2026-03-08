# 即シェア君 Mac常駐クライアント
# ポーリングで新着を検知し、通知 + クリップボード自動コピー
# テキスト自動保存 + 画像自動ダウンロード + 履歴ウィンドウ
import sys
import os
import time
import json
import threading
import queue
import webbrowser
import subprocess
import tempfile

# DockにPythonアイコンを表示しない（メニューバー常駐アプリ化）
try:
    import AppKit
    info = AppKit.NSBundle.mainBundle().infoDictionary()
    info["LSBackgroundOnly"] = "1"
except Exception:
    pass

from datetime import datetime, timedelta
from pathlib import Path

import requests

from notifier import show_notification
from tray import TrayApp

# ===== 設定 =====
BASE_URL = "https://data-share.YOUR_SUBDOMAIN.workers.dev"

POLL_INTERVAL_ACTIVE = 5     # 通常時: 5秒
POLL_INTERVAL_IDLE = 30      # スクリーンセーバー/ロック時: 30秒
POLL_ENDPOINT = "/api/poll"
ITEM_ENDPOINT = "/api/item"

# 自動保存先（Googleドライブ）— config.json で上書き可能
DEFAULT_APPS_ROOT = Path.home() / "Library" / "CloudStorage" / "GoogleDrive-yagukyou@gmail.com" / "マイドライブ" / "_Apps2026"
TEXT_SAVE_DIR = DEFAULT_APPS_ROOT / "text"
IMAGE_SAVE_DIR = DEFAULT_APPS_ROOT / "images"
OTHERS_SAVE_DIR = DEFAULT_APPS_ROOT / "others"
MAX_SAVED_FILES = 50  # 各フォルダの最大ファイル数

# 履歴保持時間
HISTORY_DURATION = timedelta(hours=48)


def is_screen_locked() -> bool:
    """macOSがスクリーンロック状態かどうか判定"""
    try:
        result = subprocess.run(
            ["ioreg", "-n", "Root", "-d1", "-a"],
            capture_output=True, text=True, timeout=5,
        )
        # CGSSessionScreenIsLocked が true ならロック中
        return "CGSSessionScreenIsLocked</key>\n\t\t<true/>" in result.stdout
    except Exception:
        return False


def clipboard_copy(text: str):
    """pbcopy でクリップボードにコピー（スレッドセーフ）"""
    try:
        subprocess.run(
            ["pbcopy"],
            input=text, text=True, timeout=5,
        )
    except Exception as e:
        print(f"[clipboard error] {e}")


def ensure_dir(path: Path):
    """フォルダがなければ作成"""
    path.mkdir(parents=True, exist_ok=True)


def rotate_files(directory: Path, max_files: int):
    """フォルダ内のファイルを古い順に削除して max_files 以下に保つ"""
    files = sorted(directory.iterdir(), key=lambda f: f.stat().st_mtime)
    while len(files) > max_files:
        oldest = files.pop(0)
        try:
            oldest.unlink()
        except Exception:
            pass


class HistoryItem:
    """受信履歴の1件"""
    def __init__(self, item_type: str, preview: str, content: str = "",
                 file_path: str = "", view_url: str = ""):
        self.timestamp = datetime.now()
        self.item_type = item_type  # "text", "image", "file"
        self.preview = preview
        self.content = content      # テキスト全文
        self.file_path = file_path  # 画像の保存パス
        self.view_url = view_url

    def is_expired(self) -> bool:
        return datetime.now() - self.timestamp > HISTORY_DURATION

    def time_str(self) -> str:
        return self.timestamp.strftime("%H:%M:%S")


class DataShareClient:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        self.last_seen_id = None
        self.running = True
        self.tray = None
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "DataShareClient/1.0"})
        # クリップボードコピーをメインスレッドに委譲するためのキュー
        self.clip_queue: queue.Queue[str] = queue.Queue()
        # 受信履歴
        self.history: list[HistoryItem] = []
        self.history_lock = threading.Lock()
        # 履歴ウィンドウのコールバック
        self.open_history_request = threading.Event()
        # 履歴JSON共有パス（履歴ウィンドウと共有）
        self._history_json = os.path.join(tempfile.gettempdir(), "sokushare_history.json")

        # 保存フォルダ初期化
        ensure_dir(TEXT_SAVE_DIR)
        ensure_dir(IMAGE_SAVE_DIR)
        ensure_dir(OTHERS_SAVE_DIR)

    def add_history(self, item: HistoryItem):
        """履歴に追加（期限切れも同時に掃除）+ JSON書き出し"""
        with self.history_lock:
            self.history = [h for h in self.history if not h.is_expired()]
            self.history.append(item)
            self._write_history_json()

    def _write_history_json(self):
        """履歴をJSONファイルに書き出す（履歴ウィンドウと共有）"""
        try:
            data = []
            for h in self.history:
                data.append({
                    "item_type": h.item_type,
                    "preview": h.preview,
                    "content": h.content,
                    "file_path": h.file_path,
                    "view_url": h.view_url,
                    "time_str": h.time_str(),
                })
            with open(self._history_json, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False)
        except Exception:
            pass

    def get_history(self):
        """有効な履歴を返す"""
        with self.history_lock:
            self.history = [h for h in self.history if not h.is_expired()]
            return list(self.history)

    def poll_once(self):
        """1回ポーリングして新着があれば返す"""
        try:
            params = {}
            if self.last_seen_id:
                params["lastId"] = self.last_seen_id

            resp = self.session.get(
                f"{self.base_url}{POLL_ENDPOINT}",
                params=params,
                timeout=10,
            )
            resp.raise_for_status()
            data = resp.json()

            if data.get("hasNew"):
                self.last_seen_id = data["id"]
                return data
            return None

        except requests.ConnectionError:
            return None
        except Exception as e:
            print(f"[polling error] {e}")
            return None

    def fetch_item(self, item_id: str):
        """アイテムの詳細データを取得"""
        try:
            resp = self.session.get(
                f"{self.base_url}{ITEM_ENDPOINT}/{item_id}",
                timeout=10,
            )
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            print(f"[fetch error] {e}")
            return None

    def save_text(self, content: str) -> str:
        """テキストをファイルに保存して、パスを返す"""
        try:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_path = TEXT_SAVE_DIR / f"share_{ts}.txt"
            file_path.write_text(content, encoding="utf-8")
            rotate_files(TEXT_SAVE_DIR, MAX_SAVED_FILES)
            return str(file_path)
        except Exception as e:
            print(f"[text save error] {e}")
            return ""

    def download_image(self, item_id: str, file_name: str, mime_type: str) -> str:
        """画像をR2からダウンロードしてローカルに保存、パスを返す"""
        try:
            resp = self.session.get(
                f"{self.base_url}{ITEM_ENDPOINT}/{item_id}/raw",
                timeout=30,
            )
            resp.raise_for_status()

            # 拡張子の決定
            ext_map = {
                "image/jpeg": ".jpg", "image/png": ".png",
                "image/gif": ".gif", "image/webp": ".webp",
                "image/svg+xml": ".svg", "image/bmp": ".bmp",
            }
            ext = ext_map.get(mime_type, ".bin")

            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            # 元ファイル名からベース名を取る（安全な文字のみ）
            safe_name = "".join(c for c in Path(file_name).stem if c.isalnum() or c in "-_")
            if not safe_name:
                safe_name = "image"
            file_path = IMAGE_SAVE_DIR / f"{ts}_{safe_name}{ext}"
            file_path.write_bytes(resp.content)
            rotate_files(IMAGE_SAVE_DIR, MAX_SAVED_FILES)
            return str(file_path)
        except Exception as e:
            print(f"[image download error] {e}")
            return ""

    def download_file(self, item_id: str, file_name: str) -> str:
        """ファイルをR2からダウンロードしてothersフォルダに保存、パスを返す"""
        try:
            resp = self.session.get(
                f"{self.base_url}{ITEM_ENDPOINT}/{item_id}/raw",
                timeout=30,
            )
            resp.raise_for_status()

            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            p = Path(file_name)
            safe_name = "".join(c for c in p.stem if c.isalnum() or c in "-_")
            ext = p.suffix if p.suffix else ""
            if not safe_name:
                safe_name = "file"
            file_path = OTHERS_SAVE_DIR / f"{ts}_{safe_name}{ext}"
            file_path.write_bytes(resp.content)
            rotate_files(OTHERS_SAVE_DIR, MAX_SAVED_FILES)
            return str(file_path)
        except Exception as e:
            print(f"[file download error] {e}")
            return ""

    def handle_new_item(self, poll_data: dict):
        """新着アイテムを処理（通知 + クリップボード + 自動保存 + 履歴追加）"""
        item_id = poll_data["id"]
        item_type = poll_data["type"]
        preview = poll_data.get("preview", "")
        view_url = f"{self.base_url}/view/{item_id}"

        # トレイアイコンを緑に変える（5分間）
        if self.tray:
            self.tray.flash_received(duration=300)

        if item_type == "text":
            item = self.fetch_item(item_id)
            if item and item.get("ok"):
                content = item.get("content", "")
                # クリップボードにコピー
                self.clip_queue.put(content)
                # テキストファイルに自動保存
                saved_path = self.save_text(content)
                # 履歴に追加
                self.add_history(HistoryItem(
                    item_type="text", preview=preview,
                    content=content, file_path=saved_path, view_url=view_url,
                ))
                show_notification(
                    "テキストを受信（コピー済み）",
                    f"{preview[:50]}..." if len(preview) > 50 else preview,
                )
            else:
                show_notification("テキストを受信", preview)

        elif item_type == "image":
            item = self.fetch_item(item_id)
            if item and item.get("ok"):
                file_name = item.get("fileName", "image")
                mime_type = item.get("mimeType", "image/png")
                # 画像を自動ダウンロード
                saved_path = self.download_image(item_id, file_name, mime_type)
                if saved_path:
                    # クリップボードにファイルパスをコピー
                    self.clip_queue.put(saved_path)
                    # 履歴に追加
                    self.add_history(HistoryItem(
                        item_type="image", preview=preview,
                        file_path=saved_path, view_url=view_url,
                    ))
                    show_notification(
                        "画像を保存しました",
                        f"{preview or '画像'} → {Path(saved_path).name}",
                    )
                else:
                    # ダウンロード失敗時はURLをコピー
                    self.clip_queue.put(view_url)
                    self.add_history(HistoryItem(
                        item_type="image", preview=preview, view_url=view_url,
                    ))
                    show_notification("画像を受信", preview or "画像ファイル")
            else:
                self.clip_queue.put(view_url)
                show_notification("画像を受信", preview or "画像ファイル")

        elif item_type == "file":
            item = self.fetch_item(item_id)
            if item and item.get("ok"):
                file_name = item.get("fileName", "file")
                saved_path = self.download_file(item_id, file_name)
                if saved_path:
                    self.clip_queue.put(saved_path)
                    self.add_history(HistoryItem(
                        item_type="file", preview=preview,
                        file_path=saved_path, view_url=view_url,
                    ))
                    show_notification(
                        "ファイルを保存しました",
                        f"{preview or 'ファイル'} → {Path(saved_path).name}",
                    )
                else:
                    self.clip_queue.put(view_url)
                    self.add_history(HistoryItem(
                        item_type="file", preview=preview, view_url=view_url,
                    ))
                    show_notification("ファイルを受信", preview or "ファイル")
            else:
                self.clip_queue.put(view_url)
                show_notification("ファイルを受信", preview or "ファイル")

    def send_file(self, file_path: str):
        """ファイルをサーバーに送信"""
        try:
            p = Path(file_path)
            if not p.exists():
                show_notification("送信失敗", f"ファイルが見つかりません: {p.name}")
                return
            if p.stat().st_size > 50 * 1024 * 1024:
                show_notification("送信失敗", "ファイルが大きすぎます (上限50MB)")
                return

            import mimetypes
            mime, _ = mimetypes.guess_type(file_path)
            if not mime:
                mime = "application/octet-stream"

            with open(file_path, "rb") as f:
                resp = self.session.post(
                    f"{self.base_url}/api/upload",
                    files={"file": (p.name, f, mime)},
                    timeout=30,
                )
            resp.raise_for_status()
            data = resp.json()
            if data.get("ok"):
                show_notification(
                    "ファイルを送信しました",
                    p.name,
                )
            else:
                show_notification("送信失敗", data.get("error", ""))

        except Exception as e:
            show_notification("送信失敗", str(e))

    def send_clipboard(self):
        """PCのクリップボードの内容をサーバーに送信"""
        try:
            result = subprocess.run(
                ["pbpaste"],
                capture_output=True, text=True, timeout=5,
            )
            text = result.stdout.strip()
            if not text:
                show_notification("送信失敗", "クリップボードが空です")
                return

            resp = self.session.post(
                f"{self.base_url}/api/upload",
                json={"type": "text", "content": text},
                timeout=10,
            )
            resp.raise_for_status()
            data = resp.json()
            if data.get("ok"):
                show_notification(
                    "クリップボードを送信しました",
                    f"{text[:50]}..." if len(text) > 50 else text,
                )
            else:
                show_notification("送信失敗", data.get("error", ""))

        except Exception as e:
            show_notification("送信失敗", str(e))

    def poll_loop(self):
        """ポーリングメインループ（バックグラウンドスレッド）"""
        if self.tray:
            self.tray.set_status("監視中")

        while self.running:
            data = self.poll_once()
            if data:
                self.handle_new_item(data)

            interval = POLL_INTERVAL_IDLE if is_screen_locked() else POLL_INTERVAL_ACTIVE
            for _ in range(interval):
                if not self.running:
                    break
                time.sleep(1)

    def clipboard_loop(self):
        """クリップボード処理ループ（バックグラウンドスレッド）"""
        while self.running:
            try:
                text = self.clip_queue.get(timeout=0.3)
                clipboard_copy(text)
            except queue.Empty:
                pass
            # 履歴ウィンドウ表示リクエストをチェック
            if self.open_history_request.is_set():
                self.open_history_request.clear()
                self._show_history_window()

    def _show_history_window(self):
        """履歴ウィンドウを別プロセスで表示（Tkはメインスレッド必須のため）"""
        self._write_history_json()
        script_dir = os.path.dirname(os.path.abspath(__file__))
        script = os.path.join(script_dir, "history_window.py")
        subprocess.Popen([sys.executable, script, self._history_json])

    def request_open_history(self):
        """履歴ウィンドウ表示をリクエスト（別スレッドから呼ばれる）"""
        self.open_history_request.set()

    def stop(self):
        self.running = False

    def run(self):
        """メインエントリ"""
        self.tray = TrayApp(
            on_send_clipboard=self.send_clipboard,
            on_open_page=lambda: webbrowser.open(self.base_url),
            on_quit=self.stop,
            on_show_history=self.request_open_history,
        )

        # ポーリングをバックグラウンドスレッドで開始
        poll_thread = threading.Thread(target=self.poll_loop, daemon=True)
        poll_thread.start()

        # クリップボード処理をバックグラウンドスレッドで開始
        clip_thread = threading.Thread(target=self.clipboard_loop, daemon=True)
        clip_thread.start()

        # pystray をメインスレッドで実行（macOSはGUIがメインスレッド必須）
        self.tray.run()


def get_app_dir() -> str:
    """アプリのディレクトリを返す（exe化時も正しく動く）"""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def acquire_single_instance() -> bool:
    """多重起動防止（ロックファイル方式）。既に起動中ならFalseを返す"""
    import fcntl
    lock_path = os.path.join(tempfile.gettempdir(), "sokushare_mac.lock")
    try:
        # グローバルに保持（GCで閉じないように）
        acquire_single_instance._lock_file = open(lock_path, "w")
        fcntl.flock(acquire_single_instance._lock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
        return True
    except (IOError, OSError):
        return False


def main():
    # 多重起動防止
    if not acquire_single_instance():
        print("[info] 即シェア君は既に起動しています")
        return

    config_path = os.path.join(get_app_dir(), "config.json")
    base_url = BASE_URL

    if os.path.exists(config_path):
        with open(config_path, encoding="utf-8") as f:
            config = json.load(f)
            base_url = config.get("base_url", BASE_URL)
            # Mac用: 保存先ディレクトリを config から読む
            global TEXT_SAVE_DIR, IMAGE_SAVE_DIR, OTHERS_SAVE_DIR
            apps_root = Path(config.get("apps_root", str(DEFAULT_APPS_ROOT)))
            TEXT_SAVE_DIR = Path(config.get("text_dir", str(apps_root / "text")))
            IMAGE_SAVE_DIR = Path(config.get("image_dir", str(apps_root / "images")))
            OTHERS_SAVE_DIR = Path(config.get("others_dir", str(apps_root / "others")))

    if "YOUR_SUBDOMAIN" in base_url:
        print("[error] config.json に base_url を設定してください")
        sys.exit(1)

    client = DataShareClient(base_url)
    client.run()


if __name__ == "__main__":
    main()
