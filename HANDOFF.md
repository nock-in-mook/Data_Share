# Data_Share (即シェア君) 引き継ぎメモ

## 最終更新: 2026-03-09

## 直近の作業: Mac版Python3.9互換修正 + 履歴HTML化
- Python3.10+専用の型ヒント（str|None等）をPython3.9互換に修正
- tkinterがmacOS付属Tk 8.5.9でクラッシュする問題 → HTMLベース+ローカルHTTPサーバーに置き換え
- 画像/ファイル受信時の自動open廃止（履歴から操作する方式に）
- 履歴テキストプレビュー文字数を40→120に拡大
- venv再作成（pythonバイナリが消えていた）

## 次のアクション
- Mac版の継続テスト（実運用で問題が出ないか確認）
- 必要に応じてMac版のexe化（PyInstaller）

## 現在の状況
- **Cloudflare Workers**: デプロイ済み → https://data-share.yagukyou.workers.dev
- **KV**: `DATA_SHARE_KV` (id: 348a89215cab42939b76044f24b996ff)
- **R2**: `data-share-files` バケット作成済み
- **cronトリガー**: 5分ごとR2クリーンアップ（KV List無料枠対策）
- **PCクライアント**: exe化済み (`client/dist/RapidShare.exe`)
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
