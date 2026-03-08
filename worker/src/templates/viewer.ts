// 閲覧ページHTML（テキスト/画像両対応）
import { ItemData } from '../types';
import { iconMetaTags } from '../handlers/icon';

export function viewerPageHtml(item: ItemData, id: string): string {
  const isText = item.type === 'text';

  let contentSection: string;
  if (isText) {
    contentSection = `<div class="text-content" id="content">${escapeHtml(item.content || '')}</div>
       <button class="btn btn-primary" onclick="copyText()">テキストをコピー</button>`;
  } else if (item.type === 'image') {
    contentSection = `<div class="image-content">
         <img src="/api/item/${id}/raw" alt="shared image" style="max-width:100%;border-radius:8px;">
       </div>
       <a class="btn btn-primary" href="/api/item/${id}/raw" download="${escapeHtml(item.fileName || 'image')}" style="display:block;text-align:center;text-decoration:none;">
         画像をダウンロード
       </a>`;
  } else {
    // ファイル
    contentSection = `<div style="text-align:center;padding:24px;">
         <div style="font-size:3rem;margin-bottom:12px;">📄</div>
         <div style="font-size:1.1rem;margin-bottom:8px;">${escapeHtml(item.fileName || 'ファイル')}</div>
         <div style="font-size:0.85rem;color:#888;">${escapeHtml(item.mimeType || '')}</div>
       </div>
       <a class="btn btn-primary" href="/api/item/${id}/raw" download="${escapeHtml(item.fileName || 'file')}" style="display:block;text-align:center;text-decoration:none;">
         ファイルをダウンロード
       </a>`;
  }

  return `<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no">
<title>Data Share - 閲覧</title>
${iconMetaTags}
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    background: #0f0f23;
    color: #e0e0e0;
    min-height: 100dvh;
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 20px;
  }
  h1 { font-size: 1.4rem; margin: 16px 0; color: #7cb3ff; }
  .container { width: 100%; max-width: 480px; }
  .text-content {
    background: #1a1a2e;
    border: 2px solid #333;
    border-radius: 12px;
    padding: 16px;
    white-space: pre-wrap;
    word-break: break-all;
    max-height: 50vh;
    overflow-y: auto;
    font-size: 15px;
    line-height: 1.6;
  }
  .image-content {
    margin-bottom: 12px;
    text-align: center;
  }
  .btn {
    width: 100%;
    padding: 16px;
    margin-top: 12px;
    border: none;
    border-radius: 12px;
    font-size: 1.1rem;
    font-weight: 600;
    cursor: pointer;
    transition: transform 0.1s;
  }
  .btn:active { transform: scale(0.97); }
  .btn-primary { background: #4a90d9; color: #fff; }
  .meta {
    margin-top: 16px;
    font-size: 0.8rem;
    color: #666;
    text-align: center;
  }
  .copied {
    position: fixed;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    background: rgba(74, 144, 217, 0.95);
    color: #fff;
    padding: 16px 32px;
    border-radius: 12px;
    font-size: 1.2rem;
    font-weight: 600;
    display: none;
    z-index: 100;
  }
</style>
</head>
<body>
<div class="container">
  <h1>Data Share</h1>
  ${contentSection}
  <p class="meta">5分で自動削除されます</p>
</div>
<div class="copied" id="copied">コピーしました！</div>
<script>
function copyText() {
  const el = document.getElementById('content');
  navigator.clipboard.writeText(el.textContent).then(() => {
    const c = document.getElementById('copied');
    c.style.display = 'block';
    setTimeout(() => c.style.display = 'none', 1200);
  });
}
</script>
</body>
</html>`;
}

export function notFoundHtml(): string {
  return `<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Data Share - 見つかりません</title>
<style>
  body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    background: #0f0f23;
    color: #e0e0e0;
    display: flex;
    justify-content: center;
    align-items: center;
    min-height: 100dvh;
    text-align: center;
  }
  .msg { font-size: 1.2rem; color: #888; }
  a { color: #7cb3ff; }
</style>
</head>
<body>
<div>
  <div class="msg">このデータは削除済みか、存在しません</div>
  <p style="margin-top:16px"><a href="/">新しいデータを共有する</a></p>
</div>
</body>
</html>`;
}

function escapeHtml(s: string): string {
  return s
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}
