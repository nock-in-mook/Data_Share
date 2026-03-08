# システムトレイアイコン
import threading
import pystray
from PIL import Image, ImageDraw

# 通常: 青、受信済み: 緑
COLOR_NORMAL = (74, 144, 217, 255)
COLOR_RECEIVED = (46, 204, 113, 255)


def create_icon_image(color=COLOR_NORMAL) -> Image.Image:
    """トレイアイコン画像を生成"""
    size = 64
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.ellipse([4, 4, size - 4, size - 4], fill=color)
    # 白い矢印
    cx, cy = size // 2, size // 2
    draw.polygon(
        [(cx, cy - 18), (cx + 14, cy + 2), (cx + 6, cy + 2),
         (cx + 6, cy + 18), (cx - 6, cy + 18), (cx - 6, cy + 2),
         (cx - 14, cy + 2)],
        fill=(255, 255, 255, 255),
    )
    return img


class TrayApp:
    def __init__(self, on_send_clipboard=None, on_open_page=None,
                 on_quit=None, on_show_history=None):
        self.on_send_clipboard = on_send_clipboard
        self.on_open_page = on_open_page
        self.on_quit = on_quit
        self.on_show_history = on_show_history
        self.icon = None
        self._status = "接続中..."
        self._revert_timer = None

    def set_status(self, status: str):
        self._status = status
        if self.icon:
            self.icon.title = f"即シェア君 - {status}"

    def flash_received(self, duration=300):
        """アイコンを緑に変えて、duration秒後に青に戻す"""
        if not self.icon:
            return
        if self._revert_timer:
            self._revert_timer.cancel()
        self.icon.icon = create_icon_image(COLOR_RECEIVED)
        self.icon.title = "即シェア君 - 受信あり！"
        self._revert_timer = threading.Timer(duration, self._revert_icon)
        self._revert_timer.daemon = True
        self._revert_timer.start()

    def _revert_icon(self):
        """アイコンを通常色に戻す"""
        if self.icon:
            self.icon.icon = create_icon_image(COLOR_NORMAL)
            self.icon.title = f"即シェア君 - {self._status}"
        self._revert_timer = None

    def _on_click(self, icon, item):
        """左クリック → 履歴ウィンドウ"""
        if self.on_show_history:
            self.on_show_history()

    def _build_menu(self):
        return pystray.Menu(
            pystray.MenuItem(
                "履歴を表示",
                lambda: self.on_show_history and self.on_show_history(),
                default=True,  # ダブルクリック時のデフォルトアクション
            ),
            pystray.MenuItem(
                "クリップボードを送信",
                lambda: self.on_send_clipboard and self.on_send_clipboard(),
            ),
            pystray.MenuItem(
                "アップロードページを開く",
                lambda: self.on_open_page and self.on_open_page(),
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(
                "終了",
                lambda: self._quit(),
            ),
        )

    def _quit(self):
        if self.on_quit:
            self.on_quit()
        if self.icon:
            self.icon.stop()

    def run(self):
        """トレイアイコンを表示（ブロッキング）"""
        self.icon = pystray.Icon(
            name="即シェア君",
            icon=create_icon_image(),
            title="即シェア君",
            menu=self._build_menu(),
        )
        self.icon.run()

    def run_in_thread(self) -> threading.Thread:
        """バックグラウンドスレッドでトレイアイコンを起動"""
        t = threading.Thread(target=self.run, daemon=True)
        t.start()
        return t
