# Windows トースト通知
import subprocess
import webbrowser
import tempfile
import os


def show_notification(title: str, message: str, url: str | None = None):
    """Windowsトースト通知を表示する"""
    try:
        from winotify import Notification, audio

        toast = Notification(
            app_id="即シェア君",
            title=title,
            msg=message,
            duration="short",
        )
        toast.set_audio(audio.Default, loop=False)

        if url:
            toast.add_actions(label="ブラウザで開く", launch=url)

        toast.show()
    except Exception as e:
        # winotify が使えない場合はフォールバック
        print(f"[通知エラー] {e}")
        print(f"  {title}: {message}")


def copy_to_clipboard(text: str):
    """tkinter で直接クリップボードにコピー（同一プロセス内で完結）"""
    try:
        import tkinter as tk
        root = tk.Tk()
        root.withdraw()
        root.clipboard_clear()
        root.clipboard_append(text)
        root.update()
        root.after(200)
        root.update()
        root.destroy()
    except Exception as e:
        print(f"[クリップボードエラー] {e}")


def open_in_browser(url: str):
    """URLをブラウザで開く"""
    webbrowser.open(url)
