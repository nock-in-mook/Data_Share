# Data_Share (即シェア君) 引き継ぎメモ

## 最終更新: 2026-03-09

## 直近の作業: Windows版の旧exe更新 + スタートアップ修正
- このPCで旧 `RapidShare.exe`（Dropboxパス `D:\Dropbox\...`）がまだ動いていた
- 旧プロセスを停止し、スタートアップショートカットを `G:\マイドライブ\...\即シェア君.exe` に更新
- 新しい `即シェア君.exe` を起動確認済み
- レジストリにタスクトレイ関連の残骸なし（クリーン）

## 次のアクション
- Mac版の継続テスト（実運用で問題が出ないか確認）
- 必要に応じてMac版のexe化（PyInstaller）
- 他のPCでも同様にDropbox→Googleドライブ移行が完了しているか確認

## 現在の状況
- **Cloudflare Workers**: デプロイ済み → https://data-share.yagukyou.workers.dev
- **KV**: `DATA_SHARE_KV` (id: 348a89215cab42939b76044f24b996ff)
- **R2**: `data-share-files` バケット作成済み
- **cronトリガー**: 5分ごとR2クリーンアップ（KV List無料枠対策）
- **PCクライアント**: exe化済み (`client/dist/即シェア君.exe`)
- **Macクライアント**: venv方式で動作中（Python 3.9）
- **Slack通知**: Workers Secret設定済み、デプロイ済み

## 既知の注意点
- macOS付属Python 3.9 + Tk 8.5.9 ではtkinterがクラッシュする → 履歴はHTMLベースで対応済み
- urllib3のNotOpenSSLWarning（LibreSSL 2.8.3）は無害、動作に影響なし
- curlでの日本語テスト送信は文字化けする（Git Bashの制約）→ Python か ブラウザで送ること

## ファイル構成
```
worker/     → Cloudflare Workers (TypeScript) デプロイ済み
client/     → PC常駐クライアント (Python)
client_mac/ → Mac常駐クライアント (Python 3.9)
explain/    → プロジェクト説明
```
