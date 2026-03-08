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
  .btn-image input[type="file"],
  .btn-file input[type="file"] {
    position: absolute;
    inset: 0;
    opacity: 0;
    cursor: pointer;
    font-size: 200px;
  }
  .btn-file {
    background: #6a4c93;
    color: #fff;
    margin-top: 8px;
    position: relative;
    overflow: hidden;
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
    画像を選択（複数可）
    <input type="file" accept="image/*" multiple onchange="sendImages(this.files)">
  </button>

  <button class="btn btn-file">
    ファイルを送信
    <input type="file" onchange="sendFile(this.files[0])">
  </button>

  <p class="paste-hint">画像はクリップボードから貼り付けもOK</p>

  <div class="spinner" id="spinner"></div>
  <div class="error" id="error"></div>

  <div class="result" id="result">
    <div id="resultMsg">送信完了！ (5分で自動削除)</div>
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

// 画像圧縮（大きすぎる画像をリサイズ）
function compressImage(file, maxSize = 1920, quality = 0.85) {
  return new Promise((resolve) => {
    // 1MB以下ならそのまま送信
    if (file.size <= 1024 * 1024) {
      resolve(file);
      return;
    }
    const img = new Image();
    img.onload = () => {
      let { width, height } = img;
      // 長辺がmaxSize以下ならリサイズ不要だが、ファイルサイズが大きいので再圧縮
      if (width > maxSize || height > maxSize) {
        if (width > height) {
          height = Math.round(height * maxSize / width);
          width = maxSize;
        } else {
          width = Math.round(width * maxSize / height);
          height = maxSize;
        }
      }
      const canvas = document.createElement('canvas');
      canvas.width = width;
      canvas.height = height;
      const ctx = canvas.getContext('2d');
      ctx.drawImage(img, 0, 0, width, height);
      canvas.toBlob((blob) => {
        resolve(new File([blob], file.name || 'image.jpg', { type: 'image/jpeg' }));
      }, 'image/jpeg', quality);
    };
    img.onerror = () => resolve(file); // 圧縮失敗時はそのまま送信
    img.src = URL.createObjectURL(file);
  });
}

// 画像送信（1枚）
async function sendImage(file) {
  if (!file) return;
  const compressed = await compressImage(file);
  await upload({ type: 'image', file: compressed });
}

// 画像送信（複数枚）
async function sendImages(files) {
  if (!files || files.length === 0) return;
  if (files.length === 1) {
    await sendImage(files[0]);
    return;
  }
  // 複数枚: 順番に送信して結果をまとめて表示
  $('spinner').style.display = 'block';
  $('result').style.display = 'none';
  $('error').style.display = 'none';
  let ok = 0, fail = 0;
  for (const file of files) {
    try {
      const compressed = await compressImage(file);
      const fd = new FormData();
      fd.append('type', 'image');
      fd.append('file', compressed);
      const controller = new AbortController();
      const timeout = setTimeout(() => controller.abort(), 30000);
      const resp = await fetch('/api/upload', { method: 'POST', body: fd, signal: controller.signal });
      clearTimeout(timeout);
      const json = await resp.json();
      if (json.ok) ok++; else fail++;
    } catch { fail++; }
  }
  $('spinner').style.display = 'none';
  if (ok > 0) {
    $('resultMsg').textContent = ok + '枚送信完了！' + (fail > 0 ? ' (' + fail + '枚失敗)' : '') + ' (5分で自動削除)';
    $('resultLink').textContent = '';
    $('resultLink').href = '#';
    $('result').style.display = 'block';
  }
  if (fail > 0 && ok === 0) {
    $('error').textContent = '全ての画像の送信に失敗しました';
    $('error').style.display = 'block';
  }
}

// ファイル送信（任意のファイル）
async function sendFile(file) {
  if (!file) return;
  const fd = new FormData();
  fd.append('file', file);
  await upload({ type: 'file', formData: fd });
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
    // タイムアウト設定（30秒）
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 30000);

    if (data.type === 'text') {
      resp = await fetch('/api/upload', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ type: 'text', content: data.content }),
        signal: controller.signal,
      });
    } else if (data.formData) {
      // ファイル送信（FormData直渡し）
      resp = await fetch('/api/upload', { method: 'POST', body: data.formData, signal: controller.signal });
    } else {
      const fd = new FormData();
      fd.append('file', data.file);
      resp = await fetch('/api/upload', { method: 'POST', body: fd, signal: controller.signal });
    }
    clearTimeout(timeout);

    const json = await resp.json();
    if (!json.ok) throw new Error(json.error || '送信失敗');

    const url = location.origin + json.url;
    $('resultLink').href = url;
    $('resultLink').textContent = url;
    $('result').style.display = 'block';
    $('text').value = '';
  } catch (err) {
    if (err.name === 'AbortError') {
      $('error').textContent = 'タイムアウトしました。画像が大きすぎるか、回線が遅い可能性があります。';
    } else {
      $('error').textContent = err.message || '送信に失敗しました';
    }
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

// Safari bfcache対策: バックフォワードキャッシュから復帰したらリロード
window.addEventListener('pageshow', (e) => {
  if (e.persisted) location.reload();
});
</script>
</body>
</html>`;
}
