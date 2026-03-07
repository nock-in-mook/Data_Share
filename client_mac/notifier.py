# macOS 通知（osascript 使用）
import subprocess
import os
import tempfile


def show_notification(title: str, message: str, file_path: str | None = None,
                      text_content: str | None = None):
    """macOS通知を表示する（通知センター経由）"""
    try:
        # osascript で通知表示
        script = f'display notification "{_escape(message)}" with title "{_escape(title)}"'
        subprocess.run(
            ["osascript", "-e", script],
            timeout=5, capture_output=True,
        )

        # テキストの場合: テキストビューアを起動
        if text_content:
            _launch_text_viewer(text_content)
        # 画像の場合: プレビューで開く
        elif file_path:
            open_file(file_path)

    except Exception as e:
        print(f"[通知エラー] {e}")
        print(f"  {title}: {message}")


def _escape(s: str) -> str:
    """AppleScript用エスケープ"""
    return s.replace("\\", "\\\\").replace('"', '\\"')


def _launch_text_viewer(content: str):
    """テキスト全文ビューアを起動（TextEditで開く）"""
    tmp = tempfile.gettempdir()
    content_file = os.path.join(tmp, "sokushare_received.txt")
    with open(content_file, "w", encoding="utf-8") as f:
        f.write(content)
    subprocess.Popen(["open", "-a", "TextEdit", content_file])


def open_file(path: str):
    """macOSのデフォルトアプリでファイルを開く"""
    try:
        subprocess.Popen(["open", path])
    except Exception:
        pass


def open_folder(path: str):
    """Finderでファイルの場所を開く"""
    try:
        subprocess.Popen(["open", "-R", path])
    except Exception:
        pass
