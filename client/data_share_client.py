# 即シェア君 PC常駐クライアント
# ポーリングで新着を検知し、トースト通知 + クリップボード自動コピー
# テキスト自動保存 + 画像自動ダウンロード + 履歴ウィンドウ
import sys
import os
import time
import json
import threading
import queue
import ctypes
import webbrowser
import tkinter as tk

# 高DPI対応（tkinterのぼやけ防止）
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)  # Per-Monitor DPI Aware
except Exception:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
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

# 自動保存先（自作アプリ親フォルダ）
APPS_ROOT = Path("D:/Dropbox/_Apps2026")
TEXT_SAVE_DIR = APPS_ROOT / "text"
IMAGE_SAVE_DIR = APPS_ROOT / "images"
MAX_SAVED_FILES = 50  # 各フォルダの最大ファイル数

# 履歴保持時間
HISTORY_DURATION = timedelta(hours=48)


def is_screen_locked() -> bool:
    """Windowsがロック状態かどうか判定"""
    try:
        user32 = ctypes.windll.user32
        hDesktop = user32.OpenDesktopW("Default", 0, False, 0x0100)
        if hDesktop:
            result = user32.SwitchDesktop(hDesktop)
            user32.CloseDesktop(hDesktop)
            return not result
        return True
    except Exception:
        return False


# メインスレッド専用の Tk インスタンス（使い回す）
_tk_root = None

def clipboard_copy_mainthread(text: str):
    """メインスレッドで tkinter を使ってクリップボードにコピー"""
    global _tk_root
    if _tk_root is None:
        _tk_root = tk.Tk()
        _tk_root.withdraw()
    _tk_root.clipboard_clear()
    _tk_root.clipboard_append(text)
    _tk_root.update()


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
        self.item_type = item_type  # "text" or "image"
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
        # 履歴ウィンドウのコールバック（メインスレッドで開く）
        self.open_history_request = threading.Event()
        self._history_window = None

        # 保存フォルダ初期化
        ensure_dir(TEXT_SAVE_DIR)
        ensure_dir(IMAGE_SAVE_DIR)

    def add_history(self, item: HistoryItem):
        """履歴に追加（期限切れも同時に掃除）"""
        with self.history_lock:
            self.history = [h for h in self.history if not h.is_expired()]
            self.history.append(item)

    def get_history(self) -> list[HistoryItem]:
        """有効な履歴を返す"""
        with self.history_lock:
            self.history = [h for h in self.history if not h.is_expired()]
            return list(self.history)

    def poll_once(self) -> dict | None:
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

    def fetch_item(self, item_id: str) -> dict | None:
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
                    text_content=content,
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
                        url=saved_path,
                    )
                else:
                    # ダウンロード失敗時はURLをコピー
                    self.clip_queue.put(view_url)
                    self.add_history(HistoryItem(
                        item_type="image", preview=preview, view_url=view_url,
                    ))
                    show_notification("画像を受信", preview or "画像ファイル", url=view_url)
            else:
                # アイテム取得失敗 → URLだけコピー
                self.clip_queue.put(view_url)
                show_notification("画像を受信", preview or "画像ファイル", url=view_url)

    def send_clipboard(self):
        """PCのクリップボードの内容をサーバーに送信"""
        try:
            import subprocess
            result = subprocess.run(
                ["powershell", "-Command", "Get-Clipboard"],
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW,
                timeout=5,
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
                    url=f"{self.base_url}{data['url']}",
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
        """クリップボード処理ループ + 履歴ウィンドウ表示（メインスレッドで実行）"""
        while self.running:
            try:
                text = self.clip_queue.get(timeout=0.3)
                clipboard_copy_mainthread(text)
            except queue.Empty:
                pass
            # 履歴ウィンドウ表示リクエストをチェック
            if self.open_history_request.is_set():
                self.open_history_request.clear()
                self._show_history_window()

    def _show_history_window(self):
        """履歴ウィンドウを表示（メインスレッドで実行）"""
        from history_window import show_history
        show_history(self.get_history(), get_history_fn=self.get_history)

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

        # pystray をバックグラウンド、メインスレッドでクリップボード処理
        tray_thread = self.tray.run_in_thread()

        # メインスレッドでクリップボード + 履歴ウィンドウキューを処理
        self.clipboard_loop()


def get_app_dir() -> str:
    """アプリのディレクトリを返す（exe化時も正しく動く）"""
    if getattr(sys, 'frozen', False):
        # PyInstallerでexe化されている場合 → exeと同じフォルダ
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def show_text_viewer():
    """--view-text モード: 一時ファイルからテキストを読んでtkinterで表示"""
    import tempfile

    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except Exception:
        pass

    # フォアグラウンド権限取得
    user32 = ctypes.windll.user32
    user32.keybd_event(0x12, 0, 0, 0)
    user32.keybd_event(0x12, 0, 2, 0)

    content_file = os.path.join(tempfile.gettempdir(), "rapid_share_text.txt")
    try:
        with open(content_file, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception:
        content = ""

    BG = "#1a1a2e"
    ACCENT = "#3a7bd5"

    root = tk.Tk()
    root.title("即シェア君 — テキスト")
    root.configure(bg=BG)
    root.attributes("-topmost", True)
    root.geometry("500x350")
    root.bind("<Escape>", lambda e: root.destroy())

    text_frame = tk.Frame(root, bg=BG)
    text_frame.pack(fill="both", expand=True, padx=10, pady=(10, 5))
    scrollbar = tk.Scrollbar(text_frame)
    scrollbar.pack(side="right", fill="y")
    text_widget = tk.Text(
        text_frame, wrap="word", font=("Segoe UI", 11),
        bg="#252540", fg="#e0e0e0", insertbackground="#e0e0e0",
        selectbackground=ACCENT, relief="flat",
        yscrollcommand=scrollbar.set, padx=10, pady=8,
    )
    text_widget.pack(fill="both", expand=True)
    scrollbar.config(command=text_widget.yview)
    text_widget.insert("1.0", content)
    text_widget.config(state="disabled")

    btn_frame = tk.Frame(root, bg=BG)
    btn_frame.pack(fill="x", padx=10, pady=(0, 10))

    def copy_all():
        root.clipboard_clear()
        root.clipboard_append(content)
        root.update()
        copy_btn.config(text="コピーしました！")
        root.after(1000, lambda: copy_btn.config(text="全文コピー"))

    copy_btn = tk.Label(
        btn_frame, text="全文コピー", font=("Segoe UI", 10, "bold"),
        bg=ACCENT, fg="#fff", padx=16, pady=6, cursor="hand2", relief="flat",
    )
    copy_btn.pack(side="right")
    copy_btn.bind("<Button-1>", lambda e: copy_all())
    copy_btn.bind("<Enter>", lambda e: copy_btn.configure(bg="#5a9ae6"))
    copy_btn.bind("<Leave>", lambda e: copy_btn.configure(bg=ACCENT))

    root.update_idletasks()
    x = (root.winfo_screenwidth() - 500) // 2
    y = (root.winfo_screenheight() - 350) // 2
    root.geometry(f"+{x}+{y}")
    root.mainloop()


def main():
    # --view-text モード: テキストビューアとして起動
    if "--view-text" in sys.argv:
        show_text_viewer()
        return

    config_path = os.path.join(get_app_dir(), "config.json")
    base_url = BASE_URL

    if os.path.exists(config_path):
        with open(config_path, encoding="utf-8") as f:
            config = json.load(f)
            base_url = config.get("base_url", BASE_URL)

    if "YOUR_SUBDOMAIN" in base_url:
        print("[error] config.json に base_url を設定してください")
        sys.exit(1)

    client = DataShareClient(base_url)
    client.run()


if __name__ == "__main__":
    main()
