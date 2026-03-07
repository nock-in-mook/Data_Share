# Windows トースト通知
import subprocess
import webbrowser
import tempfile
import os


def _make_open_vbs(path: str) -> str:
    """フォアグラウンドでファイルを開く一時VBSスクリプトを生成"""
    vbs_path = os.path.join(tempfile.gettempdir(), "rapid_share_open.vbs")
    escaped = path.replace('"', '""')
    with open(vbs_path, "w", encoding="utf-8") as f:
        f.write('Set s = CreateObject("WScript.Shell")\n')
        f.write('s.SendKeys "%"\n')  # Alt送信でフォアグラウンド許可
        f.write(f's.Run """{escaped}""", 1, False\n')
    return vbs_path


def _make_text_viewer(content: str) -> str:
    """テキスト全文ビューアを起動するVBSスクリプトを生成（EXE自身の--view-textモード使用）"""
    tmp = tempfile.gettempdir()

    # テキスト内容を一時ファイルに保存
    content_file = os.path.join(tmp, "rapid_share_text.txt")
    with open(content_file, "w", encoding="utf-8") as f:
        f.write(content)

    # 自分自身のEXE/スクリプトパスを取得
    import sys
    if getattr(sys, 'frozen', False):
        # EXE版: RapidShare.exe --view-text
        exe_path = sys.executable
        cmd = f'"""{exe_path}""" --view-text'
    else:
        # 開発版: pythonw data_share_client.py --view-text
        script_dir = os.path.dirname(os.path.abspath(__file__))
        script = os.path.join(script_dir, "data_share_client.py")
        venv_pythonw = os.path.join(script_dir, "venv", "Scripts", "pythonw.exe")
        if os.path.exists(venv_pythonw):
            cmd = f'"""{venv_pythonw}""" """{script}""" --view-text'
        else:
            cmd = f'pythonw """{script}""" --view-text'

    # VBS ラッパー
    vbs_path = os.path.join(tmp, "rapid_share_text_open.vbs")
    with open(vbs_path, "w", encoding="utf-8") as f:
        f.write('Set s = CreateObject("WScript.Shell")\n')
        f.write('s.SendKeys "%"\n')
        f.write(f's.Run {cmd}, 0, False\n')
    return vbs_path


def show_notification(title: str, message: str, url: str | None = None,
                      text_content: str | None = None):
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

        if text_content:
            # テキスト: tkinterビューアで開く
            viewer = _make_text_viewer(text_content)
            toast.add_actions(label="開く", launch=viewer)
        elif url:
            # 画像等: デフォルトアプリでフォアグラウンド起動
            vbs = _make_open_vbs(url)
            toast.add_actions(label="開く", launch=vbs)

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
