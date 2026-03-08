# Dropbox → Googleドライブ移行: パス修正TODO

## やること
このプロジェクトの作業ディレクトリを `G:/マイドライブ/_Apps2026/Data_Share/` に切り替えてから、以下を実行する。

### 1. Windows PCクライアント（client/data_share_client.py 39行目）
```
旧: APPS_ROOT = Path("D:/Dropbox/_Apps2026")
新: APPS_ROOT = Path("G:/マイドライブ/_Apps2026")
```

### 2. Mac版クライアント（client_mac/config.json）
```
旧: "apps_root": "/Users/nock_re/Dropbox/_Apps2026"
新: "apps_root": "/Users/nock_re/Library/CloudStorage/GoogleDrive-yagukyou@gmail.com/マイドライブ/_Apps2026"
```

### 3. Mac版デフォルトパス（client_mac/data_share_client.py 37-38行目）
```
旧: # 自動保存先（Dropboxフォルダ）— config.json で上書き可能
    DEFAULT_APPS_ROOT = Path.home() / "Dropbox" / "shared_files"
新: # 自動保存先（Googleドライブ）— config.json で上書き可能
    DEFAULT_APPS_ROOT = Path.home() / "Library" / "CloudStorage" / "GoogleDrive-yagukyou@gmail.com" / "マイドライブ" / "_Apps2026"
```

### 4. exe再ビルド（パス修正後）
```bash
cd client
venv/Scripts/python.exe -m PyInstaller RapidShare.spec
```

### 5. HANDOFF.md のパス表記を更新（ドキュメント）

## 備考
- gitリモートの再設定が必要かも（Gドライブ側で `git remote -v` を確認）
- `.claude/settings.local.json` にもDropboxパスがある（スタートアップ登録のVBS）
