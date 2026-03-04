// アップロードページHTML（スマホ最適化）
import { iconMetaTags } from '../handlers/icon';

export function uploadPageHtml(): string {
  return `<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no">
<title>Data Share</title>
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
  h1 {
    font-size: 1.4rem;
    margin: 16px 0;
    color: #7cb3ff;
  }
  .container {
    width: 100%;
    max-width: 480px;
  }
  textarea {
    width: 100%;
    height: 150px;
    background: #1a1a2e;
    color: #e0e0e0;
    border: 2px solid #333;
    border-radius: 12px;
    padding: 14px;
    font-size: 16px;
    resize: vertical;
    outline: none;
    transition: border-color 0.2s;
  }
  textarea:focus { border-color: #7cb3ff; }
  .btn {
    width: 100%;
    padding: 16px;
    margin-top: 12px;
    border: none;
    border-radius: 12px;
    font-size: 1.1rem;
    font-weight: 600;
    cursor: pointer;
    transition: transform 0.1s, opacity 0.2s;
  }
  .btn:active { transform: scale(0.97); }
  .btn-primary {
    background: #4a90d9;
    color: #fff;
  }
  .btn-primary:disabled {
    opacity: 0.4;
    cursor: not-allowed;
  }
  .btn-image {
    background: #2d6a4f;
    color: #fff;
    margin-top: 8px;
    position: relative;
    overflow: hidden;
  }
  .btn-image input[type="file"] {
    position: absolute;
    inset: 0;
    opacity: 0;
    cursor: pointer;
    font-size: 200px;
  }
  .result {
    margin-top: 20px;
    padding: 16px;
    background: #1a2a1a;
    border: 2px solid #4a90d9;
    border-radius: 12px;
    display: none;
    word-break: break-all;
  }
  .result a {
    color: #7cb3ff;
    text-decoration: none;
  }
  .result .copy-url {
    display: inline-block;
    margin-top: 8px;
    padding: 8px 16px;
    background: #333;
    border-radius: 8px;
    font-size: 0.9rem;
    cursor: pointer;
  }
  .spinner {
    display: none;
    margin: 16px auto;
    width: 36px;
    height: 36px;
    border: 4px solid #333;
    border-top-color: #7cb3ff;
    border-radius: 50%;
    animation: spin 0.8s linear infinite;
  }
  @keyframes spin { to { transform: rotate(360deg); } }
  .error {
    margin-top: 12px;
    padding: 12px;
    background: #2a1a1a;
    border: 1px solid #d94a4a;
    border-radius: 8px;
    color: #ff7b7b;
    display: none;
  }
  .paste-hint {
    margin-top: 12px;
    padding: 10px;
    background: #1a1a2e;
    border-radius: 8px;
    font-size: 0.85rem;
    color: #888;
    text-align: center;
  }
</style>
</head>
<body>
<div class="container">
  <h1>Data Share</h1>

  <textarea id="text" placeholder="共有したいテキストを入力..."></textarea>
  <button class="btn btn-primary" id="sendBtn" onclick="sendText()">送信</button>

  <button class="btn btn-image">
    画像を選択
    <input type="file" accept="image/*" onchange="sendImage(this.files[0])">
  </button>

  <p class="paste-hint">画像はクリップボードから貼り付けもOK</p>

  <div class="spinner" id="spinner"></div>
  <div class="error" id="error"></div>

  <div class="result" id="result">
    <div>送信完了！ (5分で自動削除)</div>
    <div style="margin-top:8px"><a id="resultLink" href="#" target="_blank"></a></div>
    <span class="copy-url" onclick="copyUrl()">URLをコピー</span>
  </div>
</div>

<script>
const $ = id => document.getElementById(id);

// テキスト送信
async function sendText() {
  const text = $('text').value.trim();
  if (!text) return;
  $('sendBtn').disabled = true;
  await upload({ type: 'text', content: text });
  $('sendBtn').disabled = false;
}

// 画像送信
async function sendImage(file) {
  if (!file) return;
  await upload({ type: 'image', file });
}

// クリップボード画像ペースト
document.addEventListener('paste', (e) => {
  const items = e.clipboardData?.items;
  if (!items) return;
  for (const item of items) {
    if (item.type.startsWith('image/')) {
      e.preventDefault();
      sendImage(item.getAsFile());
      return;
    }
  }
});

async function upload(data) {
  $('spinner').style.display = 'block';
  $('result').style.display = 'none';
  $('error').style.display = 'none';

  try {
    let resp;
    if (data.type === 'text') {
      resp = await fetch('/api/upload', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ type: 'text', content: data.content }),
      });
    } else {
      const fd = new FormData();
      fd.append('type', 'image');
      fd.append('file', data.file);
      resp = await fetch('/api/upload', { method: 'POST', body: fd });
    }

    const json = await resp.json();
    if (!json.ok) throw new Error(json.error || '送信失敗');

    const url = location.origin + json.url;
    $('resultLink').href = url;
    $('resultLink').textContent = url;
    $('result').style.display = 'block';
    $('text').value = '';
  } catch (err) {
    $('error').textContent = err.message;
    $('error').style.display = 'block';
  } finally {
    $('spinner').style.display = 'none';
  }
}

function copyUrl() {
  const url = $('resultLink').href;
  navigator.clipboard.writeText(url).then(() => {
    const el = document.querySelector('.copy-url');
    el.textContent = 'コピーしました！';
    setTimeout(() => el.textContent = 'URLをコピー', 1500);
  });
}
</script>
</body>
</html>`;
}
