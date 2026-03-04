// アイコン生成（SVG → レスポンス）
// ファビコン、PWAアイコン兼用

const ICON_SVG = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512">
  <defs>
    <linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#4a90d9"/>
      <stop offset="100%" style="stop-color:#357abd"/>
    </linearGradient>
  </defs>
  <!-- 角丸背景 -->
  <rect width="512" height="512" rx="96" fill="url(#bg)"/>
  <!-- 上向き矢印（送信のイメージ） -->
  <path d="M256 100 L370 240 L310 240 L310 380 L202 380 L202 240 L142 240 Z"
        fill="white" opacity="0.95"/>
  <!-- 下の横線（共有プラットフォーム感） -->
  <rect x="142" y="400" width="228" height="28" rx="14" fill="white" opacity="0.5"/>
</svg>`;

export function handleIcon(request: Request): Response {
  const url = new URL(request.url);
  const path = url.pathname;

  // /favicon.ico → SVGで返す
  if (path === '/favicon.ico' || path === '/favicon.svg') {
    return new Response(ICON_SVG, {
      headers: {
        'Content-Type': 'image/svg+xml',
        'Cache-Control': 'public, max-age=86400',
      },
    });
  }

  // /icon-192.svg, /icon-512.svg → PWA用（同じSVGだがサイズヒント）
  if (path.startsWith('/icon-')) {
    return new Response(ICON_SVG, {
      headers: {
        'Content-Type': 'image/svg+xml',
        'Cache-Control': 'public, max-age=86400',
      },
    });
  }

  // /manifest.json → PWAマニフェスト
  if (path === '/manifest.json') {
    const manifest = {
      name: 'Data Share',
      short_name: 'Share',
      description: 'テキスト・画像をスマホ⇔PC間で即座に共有',
      start_url: '/',
      display: 'standalone',
      background_color: '#0f0f23',
      theme_color: '#4a90d9',
      icons: [
        { src: '/icon-192.svg', sizes: '192x192', type: 'image/svg+xml' },
        { src: '/icon-512.svg', sizes: '512x512', type: 'image/svg+xml' },
      ],
    };
    return new Response(JSON.stringify(manifest), {
      headers: {
        'Content-Type': 'application/manifest+json',
        'Cache-Control': 'public, max-age=86400',
      },
    });
  }

  return new Response('Not Found', { status: 404 });
}

// HTMLのhead内に埋め込むメタタグ
export const iconMetaTags = `
<link rel="icon" type="image/svg+xml" href="/favicon.svg">
<link rel="manifest" href="/manifest.json">
<meta name="theme-color" content="#4a90d9">
<link rel="apple-touch-icon" href="/icon-192.svg">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="apple-mobile-web-app-title" content="Data Share">`;
