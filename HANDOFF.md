# Data_Share (即シェア君) 引き継ぎメモ

## 最終更新: 2026-03-08

## 直近の作業: PC→スマホ ファイル送信機能
- ファイル右クリック→「即シェア君に送る」コンテキストメニュー実装
- Worker: type='file' 対応（画像以外の任意ファイルをアップロード可能）
- Web UI: 「ファイルを送信」ボタン追加
- PCクライアント: others/ フォルダにファイル自動保存
- ファイルサイズ上限: 50MB
- クリップボードコピーをPowerShell方式に変更（tkinterバックグラウンド問題修正）
- 多重起動防止（Windows Named Mutex）追加
- 履歴ウィンドウ: 最前面は出現時のみ、その後フリー

## 次のアクション
- **Slack通知実装**: Webhook URL取得済み → Workers Secretに保存してアップロード時に通知
- **Mac版（client_mac/）に今回の追加機能を反映**（下記参照）

## Mac版に必要な変更
1. `OTHERS_SAVE_DIR` 追加（`others/` フォルダ対応）
2. `download_file()` メソッド追加
3. `handle_new_item()` に `type='file'` の処理追加
4. `send_file()` メソッド追加（右クリック送信はMac不要だがコマンドライン対応）
5. クリップボードコピーを `pbcopy` 方式に変更（Mac版は元からsubprocess使用か確認）
6. 多重起動防止（macOS向け: ロックファイル方式）
7. 履歴ウィンドウに `file` タイプの行追加
8. 履歴ウィンドウの最前面を出現時のみに変更

## 現在の状況
- **Cloudflare Workers**: デプロイ済み → https://data-share.yagukyou.workers.dev
- **KV**: `DATA_SHARE_KV` (id: 348a89215cab42939b76044f24b996ff)
- **R2**: `data-share-files` バケット作成済み
- **cronトリガー**: 5分ごとR2クリーンアップ（KV List無料枠対策）
- **PCクライアント**: exe化済み (`client/dist/RapidShare.exe`)
- **スタートメニュー/スタートアップ**: .lnk ショートカット方式
- **コンテキストメニュー**: レジストリ登録済み（`setup_context_menu.ps1`）

## 実装済み機能
- テキスト/画像/ファイルアップロード (スマホブラウザ + PC右クリック)
- **複数画像同時アップロード対応**
- **画像自動圧縮（1MB以上→JPEG 1920px、ブラウザ側）**
- **ファイル送信（任意ファイル、50MB上限）**
- 閲覧ページ + コピー/ダウンロードボタン（テキスト/画像/ファイル対応）
- ポーリングAPI (5秒間隔、ロック時30秒)
- PCクライアント: ポーリング → トースト通知 → クリップボード自動コピー
- テキスト自動保存 (`D:/Dropbox/_Apps2026/text/`、最新50件ローテ)
- 画像自動ダウンロード (`D:/Dropbox/_Apps2026/images/`、最新50件ローテ)
- **ファイル自動ダウンロード (`D:/Dropbox/_Apps2026/others/`、最新50件ローテ)**
- **履歴ウィンドウ (最大20件表示、48時間保持)**
  - テキスト → tkinterポップアップ（全文表示+コピーボタン）
  - 画像 → デフォルトビューア
  - ファイル → フォルダを開く（📎アイコン表示）
- **通知「開く」ボタン**
- システムトレイ常駐 (青=通常、緑=受信あり)
- PC→スマホ: クリップボード送信メニュー
- **PC→スマホ: ファイル右クリック→「即シェア君に送る」**
- **多重起動防止（Windows Named Mutex）**
- PyInstaller exe化 (RapidShare.exe) + アイコン埋め込み
- スタートメニュー/スタートアップ登録
- Safari bfcache対策

## ビルド方法
```bash
cd client
venv/Scripts/python.exe -m PyInstaller RapidShare.spec
# → dist/RapidShare.exe
```
※ 必ず venv 内の Python でビルドすること（グローバルだと requests が入らない）

## 注意事項
- curlでの日本語テスト送信は文字化けする（Git Bashの制約）→ Python か ブラウザで送ること
- User-Agentヘッダが必要（Cloudflareのボット対策で403になる場合あり）
- `py -3.14` を使うこと（デフォルトだとランタイム見つからないエラー）
- KV List操作は無料枠1,000回/日 → cronは5分間隔に制限済み

## ファイル構成
```
worker/     → Cloudflare Workers (TypeScript) デプロイ済み
client/     → PC常駐クライアント (Python)
  dist/     → RapidShare.exe + config.json
  setup_context_menu.ps1 → 右クリックメニュー登録
client_mac/ → Mac常駐クライアント (Python) ← 追加機能の反映が必要
explain/    → プロジェクト説明
インストール用EXEファイル/ → 配布用
申し送りメモ.md → フォルダ移動作戦の詳細記録
```
