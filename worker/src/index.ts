// Data Share - Cloudflare Workers メインエントリ
import { Env } from './types';
import { uploadPageHtml } from './templates/upload';
import { handleUpload } from './handlers/upload';
import { handleView } from './handlers/view';
import { handlePoll } from './handlers/poll';
import { handleGetItem } from './handlers/item';
import { handleCleanup } from './handlers/cleanup';
import { handleIcon } from './handlers/icon';

// レートリミット用（メモリ内、ワーカー再起動でリセット）
const rateLimitMap = new Map<string, { count: number; resetAt: number }>();
const RATE_LIMIT = 30;     // 30回/分
const RATE_WINDOW = 60_000; // 1分

function checkRateLimit(ip: string): boolean {
  const now = Date.now();
  const entry = rateLimitMap.get(ip);
  if (!entry || now > entry.resetAt) {
    rateLimitMap.set(ip, { count: 1, resetAt: now + RATE_WINDOW });
    return true;
  }
  entry.count++;
  return entry.count <= RATE_LIMIT;
}

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const url = new URL(request.url);
    const path = url.pathname;
    const method = request.method;

    // レートリミット（POSTのみ）
    if (method === 'POST') {
      const ip = request.headers.get('cf-connecting-ip') || 'unknown';
      if (!checkRateLimit(ip)) {
        return new Response(JSON.stringify({ ok: false, error: 'レートリミット超過。1分後に再試行してください。' }), {
          status: 429,
          headers: { 'Content-Type': 'application/json; charset=utf-8' },
        });
      }
    }

    // ルーティング
    // GET / → アップロードページ
    if (method === 'GET' && path === '/') {
      return new Response(uploadPageHtml(), {
        headers: { 'Content-Type': 'text/html; charset=utf-8' },
      });
    }

    // POST /api/upload → アップロード処理
    if (method === 'POST' && path === '/api/upload') {
      return handleUpload(request, env);
    }

    // GET /api/poll → ポーリング
    if (method === 'GET' && path === '/api/poll') {
      return handlePoll(env, request);
    }

    // GET /view/:id → 閲覧ページ
    const viewMatch = path.match(/^\/view\/([A-Za-z0-9]{12})$/);
    if (method === 'GET' && viewMatch) {
      return handleView(viewMatch[1], env);
    }

    // GET /api/item/:id → JSON データ取得
    const itemMatch = path.match(/^\/api\/item\/([A-Za-z0-9]{12})$/);
    if (method === 'GET' && itemMatch) {
      return handleGetItem(itemMatch[1], env, false);
    }

    // GET /api/item/:id/raw → バイナリ直接取得
    const rawMatch = path.match(/^\/api\/item\/([A-Za-z0-9]{12})\/raw$/);
    if (method === 'GET' && rawMatch) {
      return handleGetItem(rawMatch[1], env, true);
    }

    // アイコン・マニフェスト
    if (path === '/favicon.ico' || path === '/favicon.svg' || path.startsWith('/icon-') || path === '/manifest.json') {
      return handleIcon(request);
    }

    // 404
    return new Response('Not Found', { status: 404 });
  },

  // cron トリガー: R2 の期限切れオブジェクト削除
  async scheduled(_controller: ScheduledController, env: Env): Promise<void> {
    await handleCleanup(env);
  },
} satisfies ExportedHandler<Env>;
