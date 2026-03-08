# Data_Share (即シェア君) 引き継ぎメモ

## 最終更新: 2026-03-09

## 直近の作業: Dropbox→Googleドライブ移行 + Mac版機能反映
- 全パスをDropbox→Googleドライブに更新（Windows/Mac両方）
- exe名を `即シェア君.exe` に変更（タスクトレイ表示名対応）
- Mac版にfile対応・多重起動防止・send_file等を反映

## 次のアクション
- Mac版の動作確認（Macで実際に起動テスト）
- 必要に応じてMac版のexe化（PyInstaller）

## 現在の状況
- **Cloudflare Workers**: デプロイ済み → https://data-share.yagukyou.workers.dev
- **KV**: `DATA_SHARE_KV` (id: 348a89215cab42939b76044f24b996ff)
- **R2**: `data-share-files` バケット作成済み
- **cronトリガー**: 5分ごとR2クリーンアップ（KV List無料枠対策）
- **PCクライアント**: exe化済み (`client/dist/RapidShare.exe`)
- **スタートメニュー/スタートアップ**: .lnk ショートカット方式
- **コンテキストメニュー**: レジストリ登録済み（`setup_context_menu.ps1`）
- **Slack通知**: Workers Secret設定済み、デプロイ済み

## 実装済み機能
- テキスト/画像/ファイルアップロード (スマホブラウザ + PC右クリック)
- 複数画像同時アップロード対応
- 画像自動圧縮（1MB以上→JPEG 1920px、ブラウザ側）
- ファイル送信（任意ファイル、50MB上限）
- 閲覧ページ + コピー/ダウンロードボタン（テキスト/画像/ファイル対応）
- ポーリングAPI (5秒間隔、ロック時30秒)
- PCクライアント: ポーリング → トースト通知 → クリップボード自動コピー
- テキスト自動保存 (`G:/マイドライブ/_Apps2026/text/`、最新50件ローテ)
- 画像自動ダウンロード (`G:/マイドライブ/_Apps2026/images/`、最新50件ローテ)
- ファイル自動ダウンロード (`G:/マイドライブ/_Apps2026/others/`、最新50件ローテ)
- 履歴ウィンドウ (最大20件表示、48時間保持)
- 通知「開く」ボタン
- システムトレイ常駐 (青=通常、緑=受信あり)
- PC→スマホ: クリップボード送信メニュー
- PC→スマホ: ファイル右クリック→「即シェア君に送る」
- 多重起動防止（Windows Named Mutex）
- **Slack通知（アップロード時にWebhookで自動通知）**
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

---
## 完了: Googleドライブ移行パス修正 (2026-03-08)
- client/data_share_client.py、client_mac/ のパスを全てGoogleドライブに更新済み
