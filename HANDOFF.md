# Data_Share (即シェア君) 引き継ぎメモ

## 最終更新: 2026-03-18

## 直近の作業: 新しいMacに即シェア君をセットアップ
- Homebrew で Python 3.12 + python-tk@3.12 をインストール
- install.sh を実行して venv・依存パッケージ・LaunchAgent を設定
- LaunchAgent の `ProcessType=Interactive` 追加で起動問題を解決
- ログパスをGoogleドライブからローカル(/tmp/)に変更（Googleドライブパスだと起動時にコケる）
- メニューバーに青丸アイコン表示、常駐動作確認済み

## 次のアクション
- Mac版の実運用テスト（テキスト・画像・ファイル共有が正常に動作するか）
- 必要に応じてMac版のexe化（PyInstaller）
- Windows版との相互送受信テスト

## 現在の状況
- **Cloudflare Workers**: デプロイ済み → https://data-share.yagukyou.workers.dev
- **KV**: `DATA_SHARE_KV` (id: 348a89215cab42939b76044f24b996ff)
- **R2**: `data-share-files` バケット作成済み
- **cronトリガー**: 5分ごとR2クリーンアップ（KV List無料枠対策）
- **PCクライアント**: exe化済み (`client/dist/即シェア君.exe`)
- **Macクライアント**: venv方式で動作中（Python 3.12, LaunchAgent常駐）
- **Slack通知**: Workers Secret設定済み、デプロイ済み

## 既知の注意点
- macOS LaunchAgentでGUIアプリを起動するには `ProcessType=Interactive` が必要
- ログ出力先はGoogleドライブパスだとLaunchAgent起動時に失敗する → /tmp/ に出力
- urllib3のNotOpenSSLWarning（LibreSSL）は無害、動作に影響なし

## ファイル構成
```
worker/     → Cloudflare Workers (TypeScript) デプロイ済み
client/     → PC常駐クライアント (Python)
client_mac/ → Mac常駐クライアント (Python 3.12)
explain/    → プロジェクト説明
```
