# Data_Share 引き継ぎメモ

## 現在の状況
- **Cloudflare Workers**: デプロイ済み → https://data-share.yagukyou.workers.dev
- **KV**: `DATA_SHARE_KV` (id: 348a89215cab42939b76044f24b996ff)
- **R2**: `data-share-files` バケット作成済み
- **cronトリガー**: 毎分R2クリーンアップ稼働中
- **PCクライアント**: exe化済み (`client/dist/DataShare.exe` 約21MB)

## 実装済み機能
- テキスト/画像アップロード (スマホブラウザ)
- 閲覧ページ + コピー/ダウンロードボタン
- ポーリングAPI
- PCクライアント: ポーリング → トースト通知 → クリップボード自動コピー
- テキスト自動保存 (`D:/Dropbox/.★自作アプリ2026-★/text/`、最新10件ローテ)
- 画像自動ダウンロード (`D:/Dropbox/.★自作アプリ2026-★/images/`、最新10件ローテ)
- 履歴ウィンドウ (トレイメニュー「履歴を表示」、1時間保持)
- システムトレイ常駐 (青=通常、緑=受信あり)
- PC→スマホ: クリップボード送信メニュー
- PyInstaller exe化 + install.bat

## PCクライアント起動方法
- exe: `client/dist/DataShare.exe` を実行（同フォルダにconfig.jsonが必要）
- venv: `client/install.bat` を実行

## 注意事項
- curlでの日本語テスト送信は文字化けする（Git Bashの制約）→ Python か ブラウザで送ること
- User-Agentヘッダが必要（Cloudflareのボット対策で403になる場合あり）

## ファイル構成
```
worker/     → Cloudflare Workers (TypeScript) ★デプロイ済み
client/     → PC常駐クライアント (Python)
  dist/     → DataShare.exe + config.json
explain/    → プロジェクト説明
```
