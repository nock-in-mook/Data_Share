# 履歴ウィンドウ（tkinter）コンパクト1行表示
# ブロッキング方式 + after()でリアルタイム更新
import os
import subprocess
import tkinter as tk

# レイアウト定数
ROW_HEIGHT = 26
MAX_ROWS = 20
WIN_WIDTH = 520
WIN_PAD = 10
HEADER_HEIGHT = 32
PREVIEW_CHARS = 25
UPDATE_INTERVAL = 2000  # 2秒ごとに更新

# 色
BG = "#1a1a2e"
ROW_BG = "#252540"
ROW_BG_ALT = "#2a2a4a"
BTN_COPY_BG = "#3a7bd5"
BTN_FOLDER_BG = "#444"
ACCENT = "#7cb3ff"


def show_history(items: list, get_history_fn=None):
    """履歴ウィンドウを表示（ブロッキング）"""
    win = tk.Toplevel() if _has_tk_root() else tk.Tk()
    # チカチカ防止
    win.withdraw()
    win.title("即シェア君")
    win.configure(bg=BG)
    win.attributes("-topmost", True)
    win.resizable(False, False)
    win.bind("<Escape>", lambda e: win.destroy())

    # ヘッダ
    hdr = tk.Frame(win, bg=BG, height=HEADER_HEIGHT)
    hdr.pack(fill="x", padx=WIN_PAD, pady=(6, 2))
    hdr.pack_propagate(False)
    header_label = tk.Label(
        hdr, text="履歴", font=("Segoe UI", 10, "bold"),
        fg=ACCENT, bg=BG,
    )
    header_label.pack(side="left")

    # 行コンテナ
    rows_frame = tk.Frame(win, bg=BG)
    rows_frame.pack(fill="both", expand=True, padx=WIN_PAD, pady=(0, WIN_PAD))

    # 前回の件数を記録（変化がなければ再描画しない）
    state = {"last_count": -1}

    def refresh():
        current_items = get_history_fn() if get_history_fn else items
        # 件数が変わったときだけ再描画
        if len(current_items) == state["last_count"]:
            if win.winfo_exists():
                win.after(UPDATE_INTERVAL, refresh)
            return
        state["last_count"] = len(current_items)

        for w in rows_frame.winfo_children():
            w.destroy()

        header_label.config(text=f"履歴 ({len(current_items)}件)")

        if not current_items:
            tk.Label(
                rows_frame, text="まだ受信なし", font=("Segoe UI", 10),
                fg="#666", bg=BG,
            ).pack(pady=20)
        else:
            for i, item in enumerate(reversed(current_items)):
                _build_row(rows_frame, item, i % 2 == 1, win)

        # ウィンドウ高さ調整
        row_count = max(min(len(current_items), MAX_ROWS), 1)
        h = HEADER_HEIGHT + ROW_HEIGHT * row_count + WIN_PAD * 2 + 8
        # 現在位置を維持
        geo = win.geometry()
        pos = geo.split("+", 1)[1] if "+" in geo else None
        if pos:
            win.geometry(f"{WIN_WIDTH}x{h}+{pos}")
        else:
            win.geometry(f"{WIN_WIDTH}x{h}")

        # リアルタイム更新（get_history_fnがある場合のみ）
        if get_history_fn and win.winfo_exists():
            win.after(UPDATE_INTERVAL, refresh)

    # 初回描画
    refresh()

    # 画面中央配置してから表示
    win.update_idletasks()
    h = win.winfo_reqheight()
    x = (win.winfo_screenwidth() - WIN_WIDTH) // 2
    y = (win.winfo_screenheight() - h) // 2
    win.geometry(f"+{x}+{y}")
    win.deiconify()
    # 最前面で表示した後、すぐにフリーにする
    win.after(500, lambda: win.attributes("-topmost", False))

    if not _has_tk_root():
        win.mainloop()
    else:
        win.wait_window()


def _build_row(parent, item, alt: bool, win):
    bg = ROW_BG_ALT if alt else ROW_BG
    row = tk.Frame(parent, bg=bg, height=ROW_HEIGHT)
    row.pack(fill="x", pady=0)
    row.pack_propagate(False)

    # ダブルクリックで詳細表示
    def on_dblclick(e=None):
        if item.item_type == "text":
            _show_text_detail(win, item)
        elif item.item_type == "image" and item.file_path:
            _open_file(item.file_path)
        elif item.item_type == "file" and item.file_path:
            _open_folder(item.file_path)

    # 時刻
    time_lbl = tk.Label(
        row, text=item.time_str(), font=("Consolas", 9),
        fg="#888", bg=bg, padx=6,
    )
    time_lbl.pack(side="left")
    time_lbl.bind("<Double-1>", on_dblclick)

    # 区切り線
    tk.Frame(row, bg="#3a3a5a", width=1).pack(side="left", fill="y", pady=4)

    if item.item_type == "text":
        # ボタンを先にpack（右端に配置）
        if item.file_path:
            fp = str(item.file_path)
            _make_btn(row, "\U0001f4c1", BTN_FOLDER_BG, bg,
                      lambda _e=None, p=fp: _open_folder(p))
        content = str(item.content)
        _make_btn(row, "\U0001f4cb", BTN_COPY_BG, bg,
                  lambda _e=None, c=content, w=win: _copy_direct(c, w))

        # 区切り線
        tk.Frame(row, bg="#3a3a5a", width=1).pack(side="right", fill="y", pady=4)

        # テキストプレビュー
        preview = item.preview.replace("\n", " ")[:PREVIEW_CHARS]
        lbl = tk.Label(
            row, text=preview, font=("Segoe UI", 9),
            fg="#e0e0e0", bg=bg, anchor="w",
        )
        lbl.pack(side="left", fill="x", expand=True, padx=6)
        lbl.bind("<Double-1>", on_dblclick)

    elif item.item_type == "image":
        if item.file_path:
            fp = str(item.file_path)
            _make_btn(row, "\U0001f4c1", BTN_FOLDER_BG, bg,
                      lambda _e=None, p=fp: _open_folder(p))

        # 区切り線
        tk.Frame(row, bg="#3a3a5a", width=1).pack(side="right", fill="y", pady=4)

        name = os.path.basename(item.file_path) if item.file_path else "画像"
        short = name[:20] + "..." if len(name) > 20 else name
        lbl = tk.Label(
            row, text=f"\U0001f5bc {short}", font=("Segoe UI", 9),
            fg="#8ecae6", bg=bg, anchor="w",
        )
        lbl.pack(side="left", fill="x", expand=True, padx=6)
        lbl.bind("<Double-1>", on_dblclick)

    elif item.item_type == "file":
        if item.file_path:
            fp = str(item.file_path)
            _make_btn(row, "\U0001f4c1", BTN_FOLDER_BG, bg,
                      lambda _e=None, p=fp: _open_folder(p))

        # 区切り線
        tk.Frame(row, bg="#3a3a5a", width=1).pack(side="right", fill="y", pady=4)

        name = os.path.basename(item.file_path) if item.file_path else "ファイル"
        short = name[:20] + "..." if len(name) > 20 else name
        lbl = tk.Label(
            row, text=f"\U0001f4ce {short}", font=("Segoe UI", 9),
            fg="#c4a7e7", bg=bg, anchor="w",
        )
        lbl.pack(side="left", fill="x", expand=True, padx=6)
        lbl.bind("<Double-1>", on_dblclick)

    # 行全体にもダブルクリックを設定
    row.bind("<Double-1>", on_dblclick)


def _make_btn(parent, icon: str, btn_bg: str, row_bg: str, command):
    """角丸風ボタン"""
    frame = tk.Frame(parent, bg=row_bg, padx=2, pady=3)
    frame.pack(side="right")
    btn = tk.Label(
        frame, text=icon, font=("Segoe UI", 10),
        bg=btn_bg, fg="#fff", padx=6, pady=0,
        cursor="hand2", relief="flat", borderwidth=0,
    )
    btn.pack()
    btn.bind("<Enter>", lambda e, b=btn: b.configure(bg="#5a9ae6"))
    btn.bind("<Leave>", lambda e, b=btn, c=btn_bg: b.configure(bg=c))
    btn.bind("<Button-1>", command)


def _copy_direct(text: str, win: tk.Toplevel | tk.Tk):
    """tkinterで直接クリップボードにコピー（スレッド安全）"""
    try:
        win.clipboard_clear()
        win.clipboard_append(text)
        win.update()
        # フラッシュ表示
        flash = tk.Label(
            win, text=" Copied! ", font=("Segoe UI", 9, "bold"),
            fg="#fff", bg=BTN_COPY_BG, padx=12, pady=4,
        )
        flash.place(relx=0.5, rely=0.5, anchor="center")
        win.after(500, flash.destroy)
    except Exception:
        pass


def _has_tk_root() -> bool:
    try:
        return tk._default_root is not None
    except Exception:
        return False


def _show_text_detail(parent, item):
    """テキスト全文を表示するポップアップ"""
    popup = tk.Toplevel(parent)
    popup.title(f"テキスト — {item.time_str()}")
    popup.configure(bg=BG)
    popup.attributes("-topmost", True)
    popup.resizable(True, True)
    popup.geometry("500x350")
    popup.bind("<Escape>", lambda e: popup.destroy())

    # テキスト表示エリア（スクロール付き）
    text_frame = tk.Frame(popup, bg=BG)
    text_frame.pack(fill="both", expand=True, padx=10, pady=(10, 5))

    scrollbar = tk.Scrollbar(text_frame)
    scrollbar.pack(side="right", fill="y")

    text_widget = tk.Text(
        text_frame, wrap="word", font=("Segoe UI", 11),
        bg="#252540", fg="#e0e0e0", insertbackground="#e0e0e0",
        selectbackground=BTN_COPY_BG, relief="flat",
        yscrollcommand=scrollbar.set, padx=10, pady=8,
    )
    text_widget.pack(fill="both", expand=True)
    scrollbar.config(command=text_widget.yview)

    text_widget.insert("1.0", item.content or "")
    text_widget.config(state="disabled")  # 読み取り専用

    # コピーボタン
    btn_frame = tk.Frame(popup, bg=BG)
    btn_frame.pack(fill="x", padx=10, pady=(0, 10))

    def copy_all():
        popup.clipboard_clear()
        popup.clipboard_append(item.content or "")
        popup.update()
        copy_btn.config(text="コピーしました！")
        popup.after(1000, lambda: copy_btn.config(text="全文コピー"))

    copy_btn = tk.Label(
        btn_frame, text="全文コピー", font=("Segoe UI", 10, "bold"),
        bg=BTN_COPY_BG, fg="#fff", padx=16, pady=6,
        cursor="hand2", relief="flat",
    )
    copy_btn.pack(side="right")
    copy_btn.bind("<Button-1>", lambda e: copy_all())
    copy_btn.bind("<Enter>", lambda e: copy_btn.configure(bg="#5a9ae6"))
    copy_btn.bind("<Leave>", lambda e: copy_btn.configure(bg=BTN_COPY_BG))

    # 画面中央配置
    popup.update_idletasks()
    x = (popup.winfo_screenwidth() - 500) // 2
    y = (popup.winfo_screenheight() - 350) // 2
    popup.geometry(f"+{x}+{y}")


def _open_file(path: str):
    """デフォルトアプリでファイルを開き、最前面に出す"""
    try:
        import ctypes
        user32 = ctypes.windll.user32
        # Alt キー送信でフォアグラウンド権限を解放
        user32.keybd_event(0x12, 0, 0, 0)  # Alt down
        user32.keybd_event(0x12, 0, 2, 0)  # Alt up
        # 開く
        os.startfile(os.path.normpath(path))
    except Exception:
        pass


def _open_folder(path: str):
    try:
        subprocess.Popen(
            ["explorer", "/select,", os.path.normpath(path)],
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
    except Exception:
        pass
